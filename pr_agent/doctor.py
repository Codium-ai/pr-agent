"""Preflight checks that catch a broken deployment before a full run (#4320).

`pr-agent doctor` reports, without touching any git provider, whether the active
configuration can actually reach a model: the model is set, its provider has a
usable API key, and a one-token completion succeeds. The exit code is 0 only when
every check passes, so CI setups can gate on it.
"""

import os

from pr_agent.algo.ai_handlers.cloud_auth import DUMMY_LITELLM_API_KEY, PROVIDER_API_KEY_ENV_VARS
from pr_agent.algo.ai_handlers.litellm_ai_handler import LiteLLMAIHandler
from pr_agent.config_loader import get_settings
from pr_agent.git_providers.git_provider import redact_credentials
from pr_agent.log import get_logger

DOCTOR_COMMANDS = ("doctor",)

_PING_SYSTEM = "You are a health check probe. Reply with exactly: ok"
_PING_USER = "ping"


def _active_provider(model: str) -> str:
    """Resolve the litellm provider of a model id, as a real call would."""
    if "/" in model:
        return model.split("/", 1)[0].strip().lower()
    # Unprefixed models are not always OpenAI's, and an OpenAI-compatible gateway keeps its
    # key under "openai" anyway: litellm's own resolver is the source of truth. Unknown ids
    # defer to the ping.
    try:
        from litellm import get_llm_provider

        return get_llm_provider(model=model)[1]
    except Exception:
        return "unknown"


def _check_config(model: str) -> tuple[bool, str]:
    if model:
        return True, f"config.model = {model}"
    return False, "config.model is empty; set it in configuration.toml or CONFIG__MODEL"


def _check_provider_key(handler: LiteLLMAIHandler, provider: str) -> tuple[bool, str]:
    """Check the key a real run would use, without ever printing its value."""
    env_vars = PROVIDER_API_KEY_ENV_VARS.get(provider, ())
    key = handler._captured_api_key(provider)
    if key and key != DUMMY_LITELLM_API_KEY:
        source = next((name for name in env_vars if os.environ.get(name)), None)
        origin = f"env {source}" if source else "settings"
        return True, f"API key for '{provider}' found ({origin})"
    if key == DUMMY_LITELLM_API_KEY:
        return False, f"API key for '{provider}' is the placeholder; set a real key"
    if env_vars:
        names = " or ".join(env_vars)
        return False, f"no API key for '{provider}'; set {names} or the provider settings key"
    # Unknown to the env table: keyless auth (Azure AD, Bedrock IAM) or an exotic
    # provider. The ping below decides whether the deployment actually works.
    return True, f"no static key for '{provider}' (keyless auth or custom provider); ping decides"


async def _check_model_ping(handler: LiteLLMAIHandler, model: str) -> tuple[bool, str]:
    try:
        await handler.chat_completion(model, _PING_SYSTEM, _PING_USER)
    except Exception as error:
        # Provider errors can quote request URLs or response bodies; redact the way the
        # rest of the codebase does before the text reaches stdout or a shareable log.
        reason = redact_credentials(str(error).split("\n")[0])[:200]
        get_logger().debug(f"Doctor model ping failed: {redact_credentials(repr(error))}")
        return False, f"model completion failed: {reason}"
    return True, "model completion succeeded"


async def run_doctor_checks() -> int:
    """Run every check, print one line per check, and return the process exit code."""
    model = str(get_settings().config.get("model", "") or "")
    provider = _active_provider(model)
    handler = LiteLLMAIHandler()

    results = [
        _check_config(model),
        _check_provider_key(handler, provider),
        await _check_model_ping(handler, model),
    ]

    lines = []
    for ok, detail in results:
        lines.append(f"{'✓' if ok else '✗'} {detail}")
    passed = sum(1 for ok, _ in results if ok)
    print("\n".join(lines))
    print(f"{passed} of {len(results)} checks passed")
    return 0 if passed == len(results) else 1
