from pr_agent.algo.types import EDIT_TYPE, FilePatchInfo
from pr_agent.parity.config import ParityConfig
from pr_agent.parity.layout import build_layout
from pr_agent.parity.report import HEADER, render_report
from tests.unittest.test_parity_layout import TREE, TS_PATCH


def _layout():
    cfg = ParityConfig(auto_detect_languages=False)
    return build_layout(cfg, [
        FilePatchInfo("", "", TS_PATCH, "src/typescript/src/http/retry.ts", edit_type=EDIT_TYPE.MODIFIED),
        FilePatchInfo("", "", "", "src/shared/spec/retry.md", edit_type=EDIT_TYPE.MODIFIED),
    ], TREE)


PREDICTION = {
    "summary": "Adds exponential backoff to the retry helper.",
    "missing_languages": [
        {"language": "rust", "status": "needs_change", "reason": "Rust has the same loop without backoff.",
         "targets": [{"path": "src/rust/src/http/retry.rs", "is_new": False, "location": "fn retry_with_policy",
                      "change": "Double the delay each attempt, capped at max_backoff."}]},
        {"language": "golang", "status": "not_applicable", "reason": "Go delegates retries to the transport.",
         "targets": []},
        {"language": "python", "status": "unverified", "reason": "Could not see the retry helper.", "targets": []},
    ],
    "performance": [
        {"kind": "parallelizable", "file": "src/typescript/src/http/retry.ts", "location": "retryAll",
         "finding": "Serial awaits over independent requests.", "suggestion": "Promise.all with a limiter.",
         "expected_gain": "N round trips -> 1"},
    ],
    "distribution": {"verdict": "feasible", "reason": "Each batch is independent.", "split_key": "batch id",
                     "combine_step": "concatenate results", "costs": "ordering"},
}


def test_render_with_prediction_has_table_details_perf_and_distribution():
    md = render_report(_layout(), PREDICTION, model_used=True)
    assert md.startswith(HEADER)
    assert "**What changed:** Adds exponential backoff" in md
    assert "| typescript | ✅ changed | `src/typescript/src/http/retry.ts` | — |" in md
    assert "| rust | 🔴 needs change | — | `src/rust/src/http/retry.rs` → fn retry_with_policy |" in md
    assert "| golang | ⚪ not applicable | — | Go delegates retries to the transport. |" in md
    assert "| python | ❔ unverified | — | Could not see the retry helper. |" in md
    assert "Shared code changed" in md and "`src/shared/spec/retry.md`" in md
    assert "<details><summary><b>rust</b>: 🔴 needs change</summary>" in md
    assert "Double the delay each attempt" in md
    assert "### ⚡ Performance" in md and "**Can run in parallel**" in md and "Promise.all" in md
    assert "### 🧩 Distributing the work across servers" in md and "🟢 feasible" in md and "Split by: batch id" in md
    assert "Heuristic report" not in md


def test_render_heuristic_only_lists_candidates():
    md = render_report(_layout(), None, model_used=False)
    assert "| rust | 🟡 not changed | — | `src/rust/src/http/retry.rs`" in md
    assert "Candidate files (path and identifier matching)" in md
    assert "same relative path" in md
    assert "Heuristic report (no model call)" in md
    assert "### ⚡ Performance" not in md


def test_render_skipped_reason():
    md = render_report(_layout(), skipped_reason="No files under `src/` changed.")
    assert md == f"{HEADER}\n\n_No files under `src/` changed._\n"


def test_render_tolerates_malformed_prediction_entries():
    bad = {"summary": "x", "missing_languages": ["not-a-dict", {"language": "rust", "status": "needs_change",
                                                                 "targets": ["oops", {"path": "a.rs"}]}],
           "performance": ["nope"], "distribution": "nope"}
    md = render_report(_layout(), bad, model_used=True)
    assert "| rust | 🔴 needs change | — | `a.rs` |" in md
    assert "Distributing" not in md
