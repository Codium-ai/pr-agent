"""The runner's provider-key gate: stop before any tool runs (#4324)."""

import json

import pytest

from pr_agent.servers import github_action_runner


@pytest.fixture
def action_env(monkeypatch, tmp_path):
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps({
        "action": "opened",
        "pull_request": {
            "html_url": "https://github.com/owner/repo/pull/1",
            "url": "https://api.github.com/repos/owner/repo/pulls/1",
        },
    }), encoding="utf-8")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    monkeypatch.delenv("OPENAI_KEY", raising=False)
    monkeypatch.delenv("OPENAI.KEY", raising=False)


async def test_missing_key_stops_before_tools_naming_the_env_variable(
    monkeypatch, action_env
):
    monkeypatch.setattr(
        github_action_runner, "missing_provider_key_env_vars",
        lambda: ("openai", ("OPENAI_API_KEY",)),
    )

    with pytest.raises(SystemExit, match="Stopping before any tool runs.*OPENAI_API_KEY"):
        await github_action_runner.run_action()


async def test_repository_settings_are_applied_before_key_gate(monkeypatch, action_env):
    order = []
    monkeypatch.setattr(
        github_action_runner, "apply_repo_settings",
        lambda pr_url: order.append(("repo_settings", pr_url)),
    )
    monkeypatch.setattr(
        github_action_runner, "missing_provider_key_env_vars",
        lambda: order.append("gate") or ("openai", ("OPENAI_API_KEY",)),
    )
    monkeypatch.setattr(
        github_action_runner, "get_setting_or_env", lambda key, default=None: default,
    )

    # A repo-level .pr_agent.toml can select a different provider, so its settings must
    # be applied before the gate judges the active provider's key.
    with pytest.raises(SystemExit):
        await github_action_runner.run_action()
    assert order == [("repo_settings", "https://github.com/owner/repo/pull/1"), "gate"]
