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


async def test_missing_key_stops_before_tools_and_fails_the_action(
    monkeypatch, action_env, capsys
):
    reason = "no API key for 'openai'; set OPENAI_API_KEY or the provider settings key"
    monkeypatch.setattr(github_action_runner, "missing_provider_key_reason", lambda: reason)

    status = github_action_runner._ActionStatus()
    token = github_action_runner._action_status.set(status)
    try:
        await github_action_runner.run_action()
    finally:
        github_action_runner._action_status.reset(token)

    out = capsys.readouterr().out
    assert "Stopping before any tool runs" in out
    assert "OPENAI_API_KEY" in out
    assert status.failed is True


async def test_repository_settings_are_applied_before_key_gate(monkeypatch, action_env):
    order = []
    monkeypatch.setattr(
        github_action_runner, "apply_repo_settings",
        lambda pr_url: order.append(("repo_settings", pr_url)),
    )
    monkeypatch.setattr(
        github_action_runner, "missing_provider_key_reason",
        lambda: order.append("gate") or "no API key for 'openai'",
    )
    monkeypatch.setattr(
        github_action_runner, "get_setting_or_env", lambda key, default=None: default,
    )

    status = github_action_runner._ActionStatus()
    token = github_action_runner._action_status.set(status)
    try:
        await github_action_runner.run_action()
    finally:
        github_action_runner._action_status.reset(token)

    # A repo-level .pr_agent.toml can select a different provider, so its settings must
    # be applied before the gate judges the active provider's key.
    assert order == [("repo_settings", "https://github.com/owner/repo/pull/1"), "gate"]
    assert status.failed is True
