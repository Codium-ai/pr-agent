from jinja2 import Environment, StrictUndefined
from tiktoken import encoding_for_model, get_encoding

from pr_agent.config_loader import get_settings


def get_token_encoder():
    return encoding_for_model(get_settings().config.model) if "gpt" in get_settings().config.model else get_encoding(
        "cl100k_base")

class TokenHandler:
    """
    A class for handling tokens in the context of a pull request.

    Attributes:
    - encoder: An object of the encoding_for_model class from the tiktoken module. Used to encode strings and count the
      number of tokens in them.
    - limit: The maximum number of tokens allowed for the given model, as defined in the MAX_TOKENS dictionary in the
      pr_agent.algo module.
    - prompt_tokens: The number of tokens in the system and user strings, as calculated by the _get_system_user_tokens
      method.
    """

    def __init__(self, pr=None, vars: dict = {}, system="", user=""):
        """
        Initializes the TokenHandler object.

        Args:
        - pr: The pull request object.
        - vars: A dictionary of variables.
        - system: The system string.
        - user: The user string.
        """
        self.encoder = get_token_encoder()
        if pr is not None:
            self.prompt_tokens = self._get_system_user_tokens(pr, self.encoder, vars, system, user)

    def _get_system_user_tokens(self, pr, encoder, vars: dict, system, user):
        """
        Calculates the number of tokens in the system and user strings.

        Args:
        - pr: The pull request object.
        - encoder: An object of the encoding_for_model class from the tiktoken module.
        - vars: A dictionary of variables.
        - system: The system string.
        - user: The user string.

        Returns:
        The sum of the number of tokens in the system and user strings.
        """
        environment = Environment(undefined=StrictUndefined)
        system_prompt = environment.from_string(system).render(vars)
        user_prompt = environment.from_string(user).render(vars)
        system_prompt_tokens = len(encoder.encode(system_prompt))
        user_prompt_tokens = len(encoder.encode(user_prompt))
        return system_prompt_tokens + user_prompt_tokens

    def count_tokens(self, patch: str) -> int:
        """
        Counts the number of tokens in a given patch string.

        Args:
        - patch: The patch string.

        Returns:
        The number of tokens in the patch string.
        """
        return len(self.encoder.encode(patch, disallowed_special=()))