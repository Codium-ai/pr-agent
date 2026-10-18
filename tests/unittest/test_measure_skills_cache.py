import importlib.util
from decimal import Decimal
from pathlib import Path

from pr_agent.algo.prompt_fragments import render_skills_prefix
from pr_agent.algo.run_details import RunDetails
from pr_agent.algo.skills_loader import _format_skill, discover_skills
from pr_agent.algo.token_handler import TokenEncoder

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "measure_skills_cache.py"

# Bedrock Claude Sonnet 4.5 will not write a prompt cache block below this many
# prefix tokens; the fixture skill must clear it comfortably.
MIN_PREFIX_TOKENS = 1024


def _module():
    spec = importlib.util.spec_from_file_location("measure_skills_cache", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_create_fixture_skill_produces_cacheable_skills_context(tmp_path):
    module = _module()
    skill_dir = module.create_fixture_skill(tmp_path)

    skills = discover_skills([str(skill_dir)])
    assert [skill.name for skill in skills] == ["org-standards"]
    assert "Organizational engineering standards" in skills[0].description

    prefix = render_skills_prefix(skills_context=_format_skill(skills[0]))
    encoder = TokenEncoder.get_token_encoder("anthropic/claude")
    assert len(encoder.encode(prefix, disallowed_special=())) >= MIN_PREFIX_TOKENS


def test_row_from_details_flattens_run_details():
    module = _module()
    details = RunDetails(
        model_used="bedrock/anthropic.claude-sonnet-4-5-20250929-v1:0",
        prompt_tokens=1200,
        completion_tokens=300,
        cache_read_tokens=800,
        cache_creation_tokens=400,
        num_ai_calls=1,
        total_cost_usd=Decimal("0.0123"),
        known_cost_call_count=1,
    )
    row = module.row_from_details("review", True, details, "2026-10-18T12:00:00+00:00", 1.5)

    assert row["command"] == "review"
    assert row["result"] is True
    assert row["cache_read_tokens"] == 800
    assert row["cache_creation_tokens"] == 400
    assert row["total_cost_usd"] == "0.0123"
    assert row["command_failed"] is False


def test_row_from_details_marks_failed_run_without_details():
    module = _module()
    row = module.row_from_details("describe", False, None, "2026-10-18T12:00:00+00:00", 2.0)

    assert row["result"] is False
    assert row["command_failed"] is True
    assert row["model_used"] is None


def test_summarize_and_format_markdown_table():
    module = _module()
    rows = [
        {
            "command": "review",
            "result": True,
            "model_used": "bedrock/anthropic.claude-sonnet-4-5-20250929-v1:0",
            "num_ai_calls": 1,
            "prompt_tokens": 1000,
            "completion_tokens": 200,
            "cache_read_tokens": 0,
            "cache_creation_tokens": 900,
            "total_cost_usd": "0.021",
            "cost_status": "complete",
            "duration_seconds": 12.0,
            "command_failed": False,
            "started_at": "2026-10-18T12:00:00+00:00",
        },
        {
            "command": "describe",
            "result": True,
            "model_used": "bedrock/anthropic.claude-sonnet-4-5-20250929-v1:0",
            "num_ai_calls": 1,
            "prompt_tokens": 900,
            "completion_tokens": 150,
            "cache_read_tokens": 850,
            "cache_creation_tokens": 50,
            "total_cost_usd": "0.003",
            "cost_status": "complete",
            "duration_seconds": 8.0,
            "command_failed": False,
            "started_at": "2026-10-18T12:01:00+00:00",
        },
    ]

    totals = module.summarize(rows)
    assert totals["prompt_tokens"] == 1900
    assert totals["cache_read_tokens"] == 850
    assert totals["cache_creation_tokens"] == 950
    assert Decimal(totals["total_cost_usd"]) == Decimal("0.024")

    table = module.format_markdown_table(rows)
    assert "| review |" in table
    assert "| describe |" in table
    assert "cache read tok" in table
    assert "0.021" in table
