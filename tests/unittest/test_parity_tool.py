import asyncio
from types import SimpleNamespace

import pytest

from pr_agent.algo.types import EDIT_TYPE, FilePatchInfo
from pr_agent.config_loader import get_settings
from pr_agent.parity.report import HEADER
from pr_agent.tools import pr_parity as tool_module
from pr_agent.tools.pr_parity import PRParity
from tests.unittest.test_parity_layout import TREE, TS_PATCH


class FakeProvider:
    def __init__(self, diff_files, tree=TREE, contents=None, with_tree=True):
        self.pr = SimpleNamespace(title="Add backoff", body="")
        self._diff_files = diff_files
        self._tree = tree
        self._contents = contents or {}
        self.comments = []
        self.persistent = []
        self.temporary = []
        self.removed_temporary = 0
        if not with_tree:
            self.get_repo_tree_paths = None  # a provider without tree support

    def get_diff_files(self):
        return self._diff_files

    def get_files(self):
        return [f.filename for f in self._diff_files]

    def get_languages(self):
        return {"TypeScript": 100}

    def get_repo_tree_paths(self, from_default_branch=False):
        return list(self._tree)

    def get_repo_file_content(self, path, from_default_branch=False):
        return self._contents.get(path, "")

    def get_pr_branch(self):
        return "feat/backoff"

    def get_pr_description(self, full=True):
        return ""

    def publish_comment(self, body, is_temporary=False, **kwargs):
        (self.temporary if is_temporary else self.comments).append(body)

    def publish_persistent_comment(self, body, initial_header, update_header=True, name="review", **kwargs):
        self.persistent.append((initial_header, name, body))

    def remove_initial_comment(self):
        self.removed_temporary += 1


class FakeAI:
    main_pr_language = None

    def __init__(self, response):
        self.response = response
        self.calls = []

    async def chat_completion(self, model, system, user, temperature=0.2, img_path=None):
        self.calls.append({"model": model, "system": system, "user": user})
        return self.response, "stop"


MODEL_YAML = """```yaml
summary: |
  Adds exponential backoff to the retry helper.
missing_languages:
- language: rust
  status: needs_change
  reason: |
    Same loop, no backoff.
  targets:
  - path: src/rust/src/http/retry.rs
    is_new: false
    location: fn retry_with_policy
    change: |
      Double the delay per attempt.
- language: golang
  status: not_applicable
  reason: |
    Transport handles retries.
  targets: []
- language: python
  status: unverified
  reason: |
    Helper not visible.
  targets: []
performance:
- kind: parallelizable
  file: src/typescript/src/http/retry.ts
  location: retryAll
  finding: |
    Serial awaits.
  suggestion: |
    Promise.all.
  expected_gain: |
    N -> 1 round trips.
distribution:
  verdict: not_worth_it
  reason: |
    Tiny requests.
  split_key: ''
  combine_step: ''
  costs: ''
```"""

DIFF = [FilePatchInfo("", "export function retryWithPolicy() {}", TS_PATCH, "src/typescript/src/http/retry.ts",
                      edit_type=EDIT_TYPE.MODIFIED)]


@pytest.fixture
def parity_settings(monkeypatch):
    settings = get_settings()
    saved = dict(settings.pr_parity)
    saved_publish = settings.config.publish_output
    settings.config.publish_output = True
    yield settings
    settings.config.publish_output = saved_publish
    for k, v in saved.items():
        settings.pr_parity[k] = v


def _make(monkeypatch, provider, ai, settings_overrides=None):
    settings = get_settings()
    for k, v in (settings_overrides or {}).items():
        settings.pr_parity[k] = v
    monkeypatch.setattr(tool_module, "get_git_provider", lambda: (lambda url: provider))
    monkeypatch.setattr(tool_module, "get_pr_diff", lambda *a, **k: TS_PATCH)

    async def fake_retry(fn, model_type=None, **kwargs):
        await fn("gpt-4o")

    monkeypatch.setattr(tool_module, "retry_with_fallback_models", fake_retry)
    return PRParity("https://example.invalid/pr/1", ai_handler=lambda: ai)


def test_full_run_publishes_persistent_report(monkeypatch, parity_settings):
    provider = FakeProvider(DIFF, contents={"src/rust/src/http/retry.rs": "pub fn retry_with_policy() {}\n"})
    ai = FakeAI(MODEL_YAML)
    tool = _make(monkeypatch, provider, ai)
    asyncio.run(tool.run())

    assert len(provider.persistent) == 1
    header, name, body = provider.persistent[0]
    assert header == HEADER and name == "parity"
    assert "| rust | 🔴 needs change | — | `src/rust/src/http/retry.rs` → fn retry_with_policy |" in body
    assert "| golang | ⚪ not applicable |" in body and "| python | ❔ unverified |" in body
    assert "### ⚡ Performance" in body and "Distributing the work" in body
    assert provider.temporary == ["Checking cross-language parity..."] and provider.removed_temporary == 1

    prompt = ai.calls[0]
    assert "src/rust/src/http/retry.rs (score" in prompt["user"]
    assert "1: pub fn retry_with_policy() {}" in prompt["user"]  # snippet of the top candidate
    assert "It did NOT change: rust, golang, python" in prompt["system"]
    assert "src/shared" in prompt["system"]


def test_heuristic_only_when_llm_disabled(monkeypatch, parity_settings):
    provider = FakeProvider(DIFF)
    ai = FakeAI(MODEL_YAML)
    tool = _make(monkeypatch, provider, ai, {"use_llm": False})
    asyncio.run(tool.run())
    assert ai.calls == []
    (_h, _n, body), = provider.persistent
    assert "🟡 not changed" in body and "Heuristic report" in body


def test_model_failure_degrades_to_heuristic_report(monkeypatch, parity_settings):
    provider = FakeProvider(DIFF)
    ai = FakeAI("this is not yaml at all")
    tool = _make(monkeypatch, provider, ai)
    asyncio.run(tool.run())
    (_h, _n, body), = provider.persistent
    assert "🟡 not changed" in body and "Heuristic report" in body
    assert provider.removed_temporary == 1


def test_outside_layout_pr_is_silent_unless_configured(monkeypatch, parity_settings):
    diff = [FilePatchInfo("", "", "+hi\n", "docs/index.md", edit_type=EDIT_TYPE.MODIFIED)]
    provider = FakeProvider(diff)
    tool = _make(monkeypatch, provider, FakeAI(MODEL_YAML))
    asyncio.run(tool.run())
    assert provider.persistent == [] and provider.comments == []

    provider = FakeProvider(diff)
    tool = _make(monkeypatch, provider, FakeAI(MODEL_YAML), {"publish_when_nothing_to_report": True})
    asyncio.run(tool.run())
    (_h, _n, body), = provider.persistent
    assert "No files under `src/` changed" in body


def test_disabled_tool_does_nothing(monkeypatch, parity_settings):
    provider = FakeProvider(DIFF)
    tool = _make(monkeypatch, provider, FakeAI(MODEL_YAML), {"enabled": False})
    asyncio.run(tool.run())
    assert provider.persistent == [] and provider.temporary == []


def test_non_persistent_comment_and_provider_without_tree(monkeypatch, parity_settings):
    provider = FakeProvider(DIFF, with_tree=False)
    tool = _make(monkeypatch, provider, FakeAI(MODEL_YAML), {"persistent_comment": False, "use_llm": False})
    asyncio.run(tool.run())
    assert provider.persistent == []
    assert len(provider.comments) == 1
    assert "would be a new file under `src/rust/`" in provider.comments[0]


def test_parity_command_is_registered():
    from pr_agent.agent.pr_agent import command2class
    assert command2class["parity"] is PRParity and command2class["check_parity"] is PRParity
