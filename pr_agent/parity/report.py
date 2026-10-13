"""Render a ``ParityLayout`` (+ optional model prediction) as the PR comment."""
from __future__ import annotations

from typing import Any

from pr_agent.parity.layout import ParityLayout

HEADER = "## 🌐 Polyglot parity check"

_STATUS_LABEL = {
    "changed": "✅ changed",
    "needs_change": "🔴 needs change",
    "not_applicable": "⚪ not applicable",
    "unverified": "❔ unverified",
    "not_changed": "🟡 not changed",
}


def _code(path: str) -> str:
    return f"`{path}`"


def _one_line(text: Any) -> str:
    return " ".join(str(text or "").split())


def _by_language(prediction: dict | None) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for item in (prediction or {}).get("missing_languages", []) or []:
        if isinstance(item, dict) and item.get("language"):
            out[str(item["language"]).strip().lower()] = item
    return out


def render_report(layout: ParityLayout, prediction: dict | None = None, *, model_used: bool = False,
                  skipped_reason: str | None = None) -> str:
    cfg = layout.config
    lines: list[str] = [HEADER, ""]

    if skipped_reason:
        lines.append(f"_{skipped_reason}_")
        return "\n".join(lines) + "\n"

    summary = _one_line((prediction or {}).get("summary"))
    if summary:
        lines += [f"**What changed:** {summary}", ""]

    predicted = _by_language(prediction)
    lines += ["| Implementation | Status | Changed files | Where the equivalent change belongs |",
              "|---|---|---|---|"]
    for lang in layout.languages:
        if lang.touched:
            files = ", ".join(_code(c.path) for c in lang.changed_files[:6])
            if len(lang.changed_files) > 6:
                files += f" +{len(lang.changed_files) - 6} more"
            lines.append(f"| {lang.language} | {_STATUS_LABEL['changed']} | {files} | — |")
            continue
        item = predicted.get(lang.language)
        if item:
            status = str(item.get("status", "unverified")).strip()
            label = _STATUS_LABEL.get(status, _STATUS_LABEL["unverified"])
            if status == "needs_change" and item.get("targets"):
                where = "<br>".join(
                    f"{_code(t.get('path', ''))}{' (new)' if t.get('is_new') else ''}"
                    f"{' → ' + _one_line(t.get('location')) if t.get('location') else ''}"
                    for t in item["targets"] if isinstance(t, dict)
                )
            else:
                where = _one_line(item.get("reason")) or "—"
        else:
            label = _STATUS_LABEL["not_changed"]
            if lang.candidates:
                where = "<br>".join(_code(c.path) for c in lang.candidates[:3])
            else:
                where = "no matching file; would be a new file under " + _code(lang.directory + "/")
        lines.append(f"| {lang.language} | {label} | — | {where} |")
    lines.append("")

    if layout.shared_files:
        shared = ", ".join(_code(c.path) for c in layout.shared_files[:8])
        lines += [f"**Shared code changed** ({_code(cfg.shared_dir + '/')}): {shared}. "
                  "Every implementation consumes it; check each one still agrees with the shared contract.", ""]

    # Per-language detail from the model.
    details: list[str] = []
    for lang in layout.missing_languages:
        item = predicted.get(lang.language)
        if not item:
            continue
        status = str(item.get("status", "")).strip()
        body: list[str] = []
        reason = _one_line(item.get("reason"))
        if reason:
            body.append(reason)
        if status == "needs_change":
            for t in item.get("targets") or []:
                if not isinstance(t, dict):
                    continue
                head = _code(t.get("path", "")) + (" (new file)" if t.get("is_new") else "")
                loc = _one_line(t.get("location"))
                if loc:
                    head += f" — {loc}"
                body.append(f"- {head}")
                change = str(t.get("change") or "").strip()
                if change:
                    body.append("  " + "\n  ".join(change.splitlines()))
        if body:
            label = _STATUS_LABEL.get(status, status)
            details.append(f"<details><summary><b>{lang.language}</b>: {label}</summary>\n\n"
                           + "\n".join(body) + "\n\n</details>")
    if details:
        lines += details + [""]

    # Heuristic candidates when there was no model (or it said nothing for a language).
    heuristic_langs = [lang for lang in layout.missing_languages if lang.language not in predicted and lang.candidates]
    if heuristic_langs:
        lines.append("<details><summary>Candidate files (path and identifier matching)</summary>\n")
        for lang in heuristic_langs:
            lines.append(f"**{lang.language}**")
            for c in lang.candidates:
                why = f" — {'; '.join(c.reasons)}" if c.reasons else ""
                lines.append(f"- {_code(c.path)}{why}")
            lines.append("")
        lines.append("</details>\n")

    perf = (prediction or {}).get("performance") or []
    if perf:
        lines += ["### ⚡ Performance", ""]
        kind_label = {"faster_approach": "Faster approach", "parallelizable": "Can run in parallel",
                      "language_fit": "Better suited to another language"}
        for f in perf:
            if not isinstance(f, dict):
                continue
            kind = kind_label.get(str(f.get("kind", "")), str(f.get("kind", "")))
            where = _code(f.get("file", "")) + (f" ({_one_line(f.get('location'))})" if f.get("location") else "")
            lines.append(f"- **{kind}** in {where}: {_one_line(f.get('finding'))}")
            if f.get("suggestion"):
                lines.append(f"  - Suggestion: {_one_line(f.get('suggestion'))}")
            if f.get("expected_gain"):
                lines.append(f"  - Expected gain: {_one_line(f.get('expected_gain'))}")
        lines.append("")

    dist = (prediction or {}).get("distribution")
    if isinstance(dist, dict) and dist.get("verdict"):
        verdict = str(dist.get("verdict"))
        verdict_label = {"feasible": "🟢 feasible", "not_worth_it": "🟡 not worth it",
                         "not_applicable": "⚪ not applicable"}.get(verdict, verdict)
        lines += ["### 🧩 Distributing the work across servers", "",
                  f"**{verdict_label}** — {_one_line(dist.get('reason'))}"]
        if verdict == "feasible":
            for key, label in (("split_key", "Split by"), ("combine_step", "Combine"), ("costs", "Costs")):
                if dist.get(key):
                    lines.append(f"- {label}: {_one_line(dist.get(key))}")
        if layout.services_touched:
            lines.append("- Services touched: " + ", ".join(_code(s) for s in layout.services_touched))
        lines.append("")

    if not model_used:
        lines += ["_Heuristic report (no model call). Enable `pr_parity.use_llm` for status, locations and "
                  "performance notes._", ""]
    return "\n".join(lines).rstrip() + "\n"
