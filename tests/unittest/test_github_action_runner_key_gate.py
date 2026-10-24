"""The runner's provider-key gate: stop before any tool runs (#4324)."""

import pytest

from pr_agent.servers import github_action_runner


@pytest.fixture
def action_env(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    # Deliberately nonexistent: the gate must stop before the event payload is read.
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(tmp_path / "missing-event.json"))
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


async def test_valid_key_proceeds_past_the_gate(monkeypatch, action_env, capsys):
    monkeypatch.setattr(github_action_runner, "missing_provider_key_reason", lambda: None)
    monkeypatch.setattr(
        github_action_runner, "get_setting_or_env",
        lambda key, default=None: default,
    )

    status = github_action_runner._ActionStatus()
    token = github_action_runner._action_status.set(status)
    try:
        # The gate passes; the missing event file then fails exactly as it would on main.
        with pytest.raises(FileNotFoundError):
            await github_action_runner.run_action()
    finally:
        github_action_runner._action_status.reset(token)

    assert "Stopping before any tool runs" not in capsys.readouterr().out
    assert status.failed is False
