"""/parity — cross-language parity, performance and distribution review for polyglot repositories.

Flow: bucket the PR's files by language implementation (pure code, ``pr_agent.parity.layout``),
rank candidate target files in the implementations the PR did not touch, then (optionally) ask the
model to confirm which implementations need the equivalent change, where, and whether the change
has performance or distribution opportunities. The result is one PR comment.
"""
import copy
from functools import partial

from pr_agent.algo.ai_handlers.base_ai_handler import BaseAiHandler
from pr_agent.algo.ai_handlers.litellm_ai_handler import LiteLLMAIHandler
from pr_agent.algo.pr_processing import (
    OUTPUT_BUFFER_TOKENS_HARD_THRESHOLD,
    OUTPUT_BUFFER_TOKENS_SOFT_THRESHOLD,
    FallbackEligibleError,
    get_pr_diff,
    retry_with_fallback_models,
)
from pr_agent.algo.run_output import show_relevant_configurations
from pr_agent.algo.token_budget import AttemptTokenBudget
from pr_agent.algo.token_handler import TokenHandler
from pr_agent.algo.utils import ModelType, load_yaml
from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider
from pr_agent.git_providers.git_provider import get_main_pr_language
from pr_agent.log import get_logger
from pr_agent.parity.config import ParityConfig
from pr_agent.parity.layout import ParityLayout, build_layout, identifier_variants, suggested_new_paths
from pr_agent.parity.report import HEADER, render_report

_SNIPPET_LINES = 40
_SNIPPET_MAX_CHARS = 1500
_SNIPPETS_PER_LANGUAGE = 2


class PRParity:
    def __init__(self, pr_url: str, cli_mode=False, args=None, ai_handler: partial[BaseAiHandler,] = LiteLLMAIHandler):
        self.git_provider = get_git_provider()(pr_url)
        self.config = ParityConfig.from_settings()
        self.cli_mode = cli_mode
        self.ai_handler = ai_handler()
        self.main_language = get_main_pr_language(self.git_provider.get_languages(), self.git_provider.get_files())
        if self.main_language:
            self.ai_handler.main_pr_language = self.main_language
        self.layout: ParityLayout | None = None
        self.prediction: dict | None = None
        self.vars: dict = {}
        self.token_handler: TokenHandler | None = None
        self._file_cache: dict[str, str] = {}

    # ------------------------------------------------------------------ repo access

    def _read_file(self, path: str) -> str:
        if path not in self._file_cache:
            try:
                self._file_cache[path] = self.git_provider.get_repo_file_content(path) or ""
            except Exception as e:  # noqa: BLE001 - unreadable candidate just loses its content score
                get_logger().debug(f"Could not read candidate file {path}: {e}")
                self._file_cache[path] = ""
        return self._file_cache[path]

    def _tree_paths(self) -> list[str]:
        getter = getattr(self.git_provider, "get_repo_tree_paths", None)
        if not callable(getter):
            return []
        try:
            return list(getter() or [])
        except Exception as e:  # noqa: BLE001 - no tree means no candidates, not a failed run
            get_logger().warning(f"Could not list the repository tree for /parity: {e}")
            return []

    # ------------------------------------------------------------------ run

    async def run(self):
        if not self.config.enabled:
            get_logger().info("/parity is disabled by configuration (pr_parity.enabled=false)")
            return
        get_logger().info("Checking cross-language parity...")

        diff_files = self.git_provider.get_diff_files()
        tree_paths = self._tree_paths()
        self.layout = build_layout(self.config, diff_files, tree_paths, read_file=self._read_file)

        skipped_reason = self._skipped_reason()
        if skipped_reason:
            get_logger().info(f"/parity: {skipped_reason}")
            if self.config.publish_when_nothing_to_report:
                self._publish(render_report(self.layout, skipped_reason=skipped_reason))
            return

        model_used = False
        if self.config.use_llm:
            temporary = False
            if get_settings().config.publish_output:
                try:
                    self.git_provider.publish_comment("Checking cross-language parity...", is_temporary=True)
                    temporary = True
                except Exception as e:  # noqa: BLE001
                    get_logger().debug(f"Could not publish the temporary parity comment: {e}")
            try:
                self._prepare_vars()
                await retry_with_fallback_models(self._prepare_prediction, model_type=ModelType.REGULAR)
                model_used = self.prediction is not None
            except Exception as e:  # noqa: BLE001 - degrade to the heuristic report, never drop the output
                get_logger().exception(f"/parity model step failed; publishing the heuristic report: {e}")
                self.prediction = None
            finally:
                if temporary:
                    try:
                        self.git_provider.remove_initial_comment()
                    except Exception as e:  # noqa: BLE001
                        get_logger().debug(f"Could not remove the temporary parity comment: {e}")

        report = render_report(self.layout, self.prediction, model_used=model_used)
        if get_settings().get("config", {}).get("output_relevant_configurations", False):
            report += show_relevant_configurations(relevant_section="pr_parity")
        get_logger().debug("PR output", artifact=report)
        self._publish(report)

    def _skipped_reason(self) -> str | None:
        layout = self.layout
        if not layout.in_layout:
            return (f"No files under `{self.config.root}/` changed; nothing to compare across implementations.")
        if not layout.missing_languages and not (
            self.config.check_performance or self.config.check_parallelism
            or self.config.check_language_fit or self.config.check_distribution
        ):
            return "Every implementation was changed in this PR."
        return None

    def _publish(self, report: str) -> None:
        if not get_settings().config.publish_output:
            return
        if self.config.persistent_comment:
            self.git_provider.publish_persistent_comment(report, initial_header=HEADER, update_header=True,
                                                         name="parity")
        else:
            self.git_provider.publish_comment(report)

    # ------------------------------------------------------------------ prompt

    def _prepare_vars(self) -> None:
        layout = self.layout
        cfg = self.config
        touched_names = [lang.language for lang in layout.touched_languages]
        if layout.shared_files:
            touched_names.append("shared")
        self.vars = {
            "title": self.git_provider.pr.title,
            "branch": self.git_provider.get_pr_branch(),
            "description": self.git_provider.get_pr_description(),
            "root": cfg.root,
            "shared_dir": cfg.shared_dir,
            "all_languages": [lang.language for lang in layout.languages],
            "touched_languages": touched_names or ["(none)"],
            "missing_languages": [lang.language for lang in layout.missing_languages] or ["(none)"],
            "touched_files": [{"language": lang.language, "files": [c.path for c in lang.changed_files]}
                              for lang in layout.touched_languages],
            "shared_files": [c.path for c in layout.shared_files],
            "outside_files": [c.path for c in layout.outside_files][:20],
            "candidates": self._candidate_vars(),
            "services_all": layout.services_all[:30],
            "services_touched": sorted(layout.services_touched),
            "check_performance": cfg.check_performance,
            "check_parallelism": cfg.check_parallelism,
            "check_language_fit": cfg.check_language_fit,
            "check_distribution": cfg.check_distribution,
            "extra_instructions": cfg.extra_instructions,
            "diff": "",
        }
        self.token_handler = TokenHandler(self.git_provider.pr, self.vars,
                                          get_settings().pr_parity_prompt.system,
                                          get_settings().pr_parity_prompt.user)

    def _candidate_vars(self) -> list[dict]:
        layout = self.layout
        touched_changed = [c for lang in layout.touched_languages for c in lang.changed_files]
        out = []
        for lang in layout.missing_languages:
            files = []
            for i, cand in enumerate(lang.candidates):
                entry = {"path": cand.path, "score": round(cand.score, 1), "reasons": cand.reasons, "snippet": ""}
                if i < _SNIPPETS_PER_LANGUAGE:
                    entry["snippet"] = self._snippet(cand.path, cand.identifier_hits or layout.identifiers[:10])
                files.append(entry)
            out.append({
                "language": lang.language,
                "directory": lang.directory,
                "files": files,
                "suggested_new": suggested_new_paths(self.config, lang.language, touched_changed)[:3],
            })
        return out

    def _snippet(self, path: str, identifiers: list[str]) -> str:
        content = self._read_file(path)
        if not content:
            return ""
        lines = content.splitlines()
        start = 0
        low_lines = [ln.lower() for ln in lines]
        variants = {v for ident in identifiers for v in identifier_variants(ident)}
        for idx, ln in enumerate(low_lines):
            if any(v in ln for v in variants):
                start = max(0, idx - 5)
                break
        window = lines[start:start + _SNIPPET_LINES]
        text = "\n".join(f"{start + i + 1}: {ln}" for i, ln in enumerate(window))
        if len(text) > _SNIPPET_MAX_CHARS:
            text = text[:_SNIPPET_MAX_CHARS] + "\n...(truncated)..."
        return text

    async def _prepare_prediction(self, model: str) -> None:
        self.prediction = None
        variables = copy.deepcopy(self.vars)
        output_token_reserve = getattr(self.ai_handler, "get_output_token_reserve", None)
        budget = AttemptTokenBudget.for_prompt_attempt(
            model, getattr(self.git_provider, "pr", None), variables,
            get_settings().pr_parity_prompt.system, get_settings().pr_parity_prompt.user,
            ai_handler=self.ai_handler, output_token_reserve=output_token_reserve,
        )
        budget.require_input_capacity(OUTPUT_BUFFER_TOKENS_SOFT_THRESHOLD, preserve_minimum=True)
        patches_diff = get_pr_diff(self.git_provider, budget.token_handler, model,
                                   output_token_reserve=output_token_reserve)
        if not patches_diff:
            raise FallbackEligibleError(f"No PR diff fits the /parity request for {model}")
        fitted = budget.fit_prompt_variable(variables, "diff", patches_diff, ai_handler=self.ai_handler,
                                            default_output_tokens=OUTPUT_BUFFER_TOKENS_HARD_THRESHOLD,
                                            preserve_minimum=True)
        if fitted.optional_text != patches_diff:
            raise FallbackEligibleError(f"The complete packed parity diff does not fit the token limit for {model}")
        response, _finish_reason = await self.ai_handler.chat_completion(
            model=model, temperature=get_settings().config.temperature,
            system=fitted.system_prompt, user=fitted.user_prompt,
        )
        self.prediction = self._parse(response)

    def _parse(self, response: str) -> dict | None:
        cfg = self.config
        last_key = "missing_languages"
        if cfg.check_performance or cfg.check_parallelism or cfg.check_language_fit:
            last_key = "performance"
        if cfg.check_distribution:
            last_key = "distribution"
        data = load_yaml(response.strip(),
                         keys_fix_yaml=["summary:", "reason:", "change:", "location:", "finding:", "suggestion:",
                                        "expected_gain:", "split_key:", "combine_step:", "costs:"],
                         first_key="summary", last_key=last_key)
        if not isinstance(data, dict) or "missing_languages" not in data:
            get_logger().warning("/parity: model response was not a valid parity report")
            return None
        return data


__all__ = ["PRParity"]
