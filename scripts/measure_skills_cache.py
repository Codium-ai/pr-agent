#!/usr/bin/env python3
"""Measure cross-tool prompt-cache hits for the shared skills prefix (issue #4007).

Runs review, describe and improve back-to-back against one pull request inside a
single request cycle with publishing disabled, then reports the per-command cache
read/write tokens, token totals and estimated cost collected by
``pr_agent.algo.run_details``. Commands run sequentially so later tools reuse the
cache entry written under the first tool's Anthropic 5-minute TTL.

Requires a GitHub token in ``GITHUB__USER_TOKEN`` (or already loaded into
``github.user_token``) and, for Bedrock models, AWS credentials via the default
boto3 chain (``AWS_USE_IMDS=true`` opts PR-Agent into that chain). Example:

    GITHUB__USER_TOKEN=... AWS_USE_IMDS=true AWS_REGION=us-east-1 PYTHONPATH=. \\
        python scripts/measure_skills_cache.py --pr-url https://github.com/org/repo/pull/123

Pass ``--baseline`` to disable the cache injection points for a before/after
comparison of cost and output quality.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import json
import os
import sys
import tempfile
import time
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from starlette_context import context, request_cycle_context

from pr_agent.agent.pr_agent import PRAgent
from pr_agent.algo.ai_handlers.litellm_helpers import (
    DEFAULT_CALLBACK_TIMEOUT_SECONDS,
    drain_litellm_callbacks,
    litellm_callbacks_registered,
)
from pr_agent.algo.run_details import RunDetails, get_run_details
from pr_agent.config_loader import get_settings, global_settings
from pr_agent.log import get_logger, setup_logger

DEFAULT_MODEL = "bedrock/us.anthropic.claude-sonnet-4-5-20250929-v1:0"
DEFAULT_COMMANDS = ("review", "describe", "improve")
CACHE_CONTROL_POINT = {"location": "message", "role": "system"}

# Fixture skill topics; each section's body is the shared standards paragraph below.
_FIXTURE_TOPICS = (
    "naming and identifiers",
    "function scope",
    "error handling",
    "testing",
    "logging",
    "API compatibility",
    "security hygiene",
    "performance hot paths",
)
_FIXTURE_SECTION_TEMPLATE = (
    "When reviewing changes in {topic}, apply the shared standards below. Prefer explicit, "
    "intention-revealing names over abbreviations, and keep one responsibility per function so "
    "a reader never has to hold two behaviors in mind at once. Error handling must sit next to "
    "the failure it covers: catch the narrowest exception that still allows recovery, log enough "
    "context to reproduce the problem without leaking secrets, and never swallow an exception "
    "silently. New behavior needs a test that fails before the change and passes after it; a fix "
    "without a regression test is an invitation for the bug to return. Public interfaces keep "
    "backward compatibility unless a migration note explains the break. Comments explain why, "
    "not what, and are removed when the code no longer needs them."
)


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pr-url", required=True, help="Pull request URL to measure against")
    parser.add_argument(
        "--commands",
        nargs="+",
        default=list(DEFAULT_COMMANDS),
        help="Tool commands to run back-to-back within the cache TTL",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model id passed to config.model")
    parser.add_argument(
        "--skills-path",
        default=None,
        help="Existing skills directory; a fixture SKILL.md is generated when omitted",
    )
    parser.add_argument(
        "--baseline",
        action="store_true",
        help="Disable cache_control injection points for a before/after comparison",
    )
    parser.add_argument("--save-artifacts", default=None, help="Directory to write each command's output into")
    parser.add_argument("--json", dest="json_path", default=None, help="Write the measurement rows as JSON")
    return parser.parse_args(argv)


def create_fixture_skill(target_dir: Path) -> Path:
    """Write a deterministic SKILL.md fixture whose rendered prefix clears the cache minimum."""
    skill_dir = target_dir / "org-standards"
    skill_dir.mkdir(parents=True, exist_ok=True)
    sections = [
        f"## {topic.capitalize()}\n\n{_FIXTURE_SECTION_TEMPLATE.format(topic=topic)}" for topic in _FIXTURE_TOPICS
    ]
    body = "\n\n".join(sections)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: org-standards\n"
        "description: Organizational engineering standards; use when reviewing any pull request.\n"
        "---\n\n"
        f"{body}\n",
        encoding="utf-8",
    )
    return skill_dir


def row_from_details(
    command: str,
    result,
    details: RunDetails | None,
    started_at: str,
    wall_seconds: float,
) -> dict:
    """Flatten one command's outcome into a JSON-serialisable measurement row."""
    failed = bool(details is None or details.command_failed)
    return {
        "command": command,
        "result": result is True,
        "model_used": details.model_used if details else None,
        "num_ai_calls": details.num_ai_calls if details else 0,
        "prompt_tokens": details.prompt_tokens if details else 0,
        "completion_tokens": details.completion_tokens if details else 0,
        "cache_read_tokens": details.cache_read_tokens if details else 0,
        "cache_creation_tokens": details.cache_creation_tokens if details else 0,
        "total_cost_usd": str(details.total_cost_usd) if details else "0",
        "cost_status": details.cost_status if details else "unavailable",
        "duration_seconds": round(details.duration_seconds, 1) if details else round(wall_seconds, 1),
        "command_failed": failed,
        "started_at": started_at,
    }


def summarize(rows: list[dict]) -> dict:
    """Aggregate token and cost totals across measurement rows."""
    return {
        "prompt_tokens": sum(row["prompt_tokens"] for row in rows),
        "completion_tokens": sum(row["completion_tokens"] for row in rows),
        "cache_read_tokens": sum(row["cache_read_tokens"] for row in rows),
        "cache_creation_tokens": sum(row["cache_creation_tokens"] for row in rows),
        "num_ai_calls": sum(row["num_ai_calls"] for row in rows),
        "total_cost_usd": str(sum((Decimal(row["total_cost_usd"]) for row in rows), Decimal("0"))),
    }


def format_markdown_table(rows: list[dict]) -> str:
    """Render measurement rows as a GitHub-flavoured markdown table."""
    header = (
        "| command | model | calls | prompt tok | completion tok | cache read tok | cache write tok "
        "| cost (USD) | duration (s) | started (UTC) |\n"
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|"
    )
    body = [
        "| {command} | {model} | {calls} | {prompt} | {completion} | {cache_read} | {cache_write} "
        "| {cost} | {duration} | {started} |".format(
            command=row["command"],
            model=row["model_used"] or "-",
            calls=row["num_ai_calls"],
            prompt=row["prompt_tokens"],
            completion=row["completion_tokens"],
            cache_read=row["cache_read_tokens"],
            cache_write=row["cache_creation_tokens"],
            cost=row["total_cost_usd"],
            duration=row["duration_seconds"],
            started=row["started_at"],
        )
        for row in rows
    ]
    return "\n".join([header, *body])


def apply_harness_settings(model: str, skills_paths: list[str], baseline: bool) -> None:
    settings = get_settings()
    settings.set("config.git_provider", "github")
    settings.set("config.publish_output", False)
    settings.set("config.publish_output_progress", False)
    settings.set("config.fallback_models", [])
    settings.set("config.model", model)
    settings.set("config.output_run_cost", True)
    settings.set(
        "litellm.cache_control_injection_points",
        [] if baseline else [dict(CACHE_CONTROL_POINT)],
    )
    settings.set("skills.enabled", True)
    settings.set("skills.paths", list(skills_paths))
    user_token = os.environ.get("GITHUB__USER_TOKEN", "")
    if user_token:
        settings.set("github.user_token", user_token)


async def run_async(args: argparse.Namespace, skills_paths: list[str]) -> int:
    apply_harness_settings(args.model, skills_paths, args.baseline)
    save_dir = Path(args.save_artifacts) if args.save_artifacts else None
    if save_dir is not None:
        save_dir.mkdir(parents=True, exist_ok=True)

    agent = PRAgent()
    rows: list[dict] = []
    for raw_command in args.commands:
        command = raw_command.lstrip("/").strip()
        original_settings = copy.deepcopy(get_settings())
        started_at = datetime.now(UTC).isoformat(timespec="seconds")
        get_logger().info(f"Running /{command} (baseline={args.baseline})...")
        wall_start = time.monotonic()
        result = await agent.handle_request(args.pr_url, [command])
        wall_seconds = time.monotonic() - wall_start
        details = get_run_details()
        row = row_from_details(command, result, details, started_at, wall_seconds)
        rows.append(row)
        get_logger().info(
            f"/{command}: cache_read={row['cache_read_tokens']} "
            f"cache_write={row['cache_creation_tokens']} cost=${row['total_cost_usd']} "
            f"result={row['result']}"
        )
        artifact_data = getattr(get_settings(), "data", None)
        artifact = dict(artifact_data).get("artifact") if artifact_data is not None else None
        if save_dir is not None and isinstance(artifact, str):
            (save_dir / f"{command}.md").write_text(artifact, encoding="utf-8")
        context["settings"] = copy.deepcopy(original_settings)

    if litellm_callbacks_registered():
        timeout = get_settings().litellm.get("callback_timeout_seconds", DEFAULT_CALLBACK_TIMEOUT_SECONDS)
        await drain_litellm_callbacks(timeout)

    totals = summarize(rows)
    print(f"\nModel: {args.model}")
    print(f"Mode: {'baseline (no cache injection)' if args.baseline else 'cache injection enabled'}")
    print(f"PR: {args.pr_url}\n")
    print(format_markdown_table(rows))
    print(
        "\nTotals: "
        f"prompt={totals['prompt_tokens']} completion={totals['completion_tokens']} "
        f"cache_read={totals['cache_read_tokens']} cache_write={totals['cache_creation_tokens']} "
        f"cost=${totals['total_cost_usd']} ai_calls={totals['num_ai_calls']}"
    )
    later_reads = [row["cache_read_tokens"] for row in rows[1:]]
    if later_reads and not args.baseline:
        verdict = all(read > 0 for read in later_reads)
        print(f"Cross-tool cache reads on 2nd/3rd commands: {'YES' if verdict else 'NO'}")

    payload = {
        "pr_url": args.pr_url,
        "model": args.model,
        "baseline": args.baseline,
        "skills_paths": list(skills_paths),
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "rows": rows,
        "totals": totals,
    }
    if args.json_path:
        Path(args.json_path).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    ok = all(row["result"] and not row["command_failed"] for row in rows)
    return 0 if ok else 1


def run(args: argparse.Namespace) -> int:
    setup_logger(os.environ.get("LOG_LEVEL", "INFO"))
    os.environ.setdefault("AWS_REGION", "us-east-1")
    os.environ.setdefault("AWS_USE_IMDS", "true")
    if not os.environ.get("GITHUB__USER_TOKEN") and not get_settings().get("github.user_token", ""):
        print("GITHUB__USER_TOKEN must be set to a GitHub token with read access to the PR", file=sys.stderr)
        return 2

    # Materialise the lazy global settings before copying: deepcopy of an unmaterialised
    # LazySettings drops the loaded TOML values, which every tool run would then miss.
    global_settings.keys()
    with request_cycle_context({}):
        context["settings"] = copy.deepcopy(global_settings)
        if args.skills_path:
            skills_paths = [str(Path(args.skills_path).expanduser().resolve())]
            return asyncio.run(run_async(args, skills_paths))
        with tempfile.TemporaryDirectory(prefix="pr-agent-cache-measurement-") as tmp:
            skills_paths = [str(create_fixture_skill(Path(tmp)))]
            return asyncio.run(run_async(args, skills_paths))


def main(argv=None) -> int:
    return run(parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
