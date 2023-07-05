from jinja2 import Environment, StrictUndefined
from tiktoken import encoding_for_model

from pr_agent.algo import MAX_TOKENS
from pr_agent.config_loader import settings


class TokenHandler:
    def __init__(self, pr, vars: dict, system, user):
        self.encoder = encoding_for_model(settings.config.model)
        self.limit = MAX_TOKENS[settings.config.model]
        self.prompt_tokens = self._get_system_user_tokens(pr, self.encoder, vars, system, user)

    def _get_system_user_tokens(self, pr, encoder, vars: dict, system, user):
        environment = Environment(undefined=StrictUndefined)
        system_prompt = environment.from_string(system).render(vars)
        user_prompt = environment.from_string(user).render(vars)

        system_prompt_tokens = len(encoder.encode(system_prompt))
        user_prompt_tokens = len(encoder.encode(user_prompt))
        return system_prompt_tokens + user_prompt_tokens

    def count_tokens(self, patch: str) -> int:
        return len(self.encoder.encode(patch))