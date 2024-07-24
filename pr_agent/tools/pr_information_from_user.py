import copy
from functools import partial

from jinja2 import Environment, StrictUndefined

from pr_agent.algo.ai_handlers.base_ai_handler import BaseAiHandler
from pr_agent.algo.ai_handlers.litellm_ai_handler import LiteLLMAIHandler
from pr_agent.algo.pr_processing import get_pr_diff, retry_with_fallback_models
from pr_agent.algo.token_handler import TokenHandler
from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider
from pr_agent.git_providers.git_provider import get_main_pr_language
from pr_agent.log import get_logger


class PRInformationFromUser:
    def __init__(self, pr_url: str, args: list = None,
                 ai_handler: partial[BaseAiHandler,] = LiteLLMAIHandler):
        self.git_provider = get_git_provider()(pr_url)
        self.main_pr_language = get_main_pr_language(
            self.git_provider.get_languages(), self.git_provider.get_files()
        )
        self.ai_handler = ai_handler()
        self.ai_handler.main_pr_language = self.main_pr_language

        self.vars = {
            "title": self.git_provider.pr.title,
            "branch": self.git_provider.get_pr_branch(),
            "description": self.git_provider.get_pr_description(),
            "language": self.main_pr_language,
            "diff": "",  # empty diff for initial calculation
            "commit_messages_str": self.git_provider.get_commit_messages(),
        }
        self.token_handler = TokenHandler(self.git_provider.pr,
                                          self.vars,
                                          get_settings().pr_information_from_user_prompt.system,
                                          get_settings().pr_information_from_user_prompt.user)
        self.patches_diff = None
        self.prediction = None

    async def run(self):
        get_logger().info('Generating question to the user...')
        if get_settings().config.publish_output:
            self.git_provider.publish_comment("Preparing questions...", is_temporary=True)
        await retry_with_fallback_models(self._prepare_prediction)
        get_logger().info('Preparing questions...')
        pr_comment = self._prepare_pr_answer()
        if get_settings().config.publish_output:
            get_logger().info('Pushing questions...')
            self.git_provider.publish_comment(pr_comment)
            self.git_provider.remove_initial_comment()
        return ""

    async def _prepare_prediction(self, model):
        get_logger().info('Getting PR diff...')
        self.patches_diff = get_pr_diff(self.git_provider, self.token_handler, model)
        get_logger().info('Getting AI prediction...')
        self.prediction = await self._get_prediction(model)

    async def _get_prediction(self, model: str):
        variables = copy.deepcopy(self.vars)
        variables["diff"] = self.patches_diff  # update diff
        environment = Environment(undefined=StrictUndefined)
        system_prompt = environment.from_string(get_settings().pr_information_from_user_prompt.system).render(variables)
        user_prompt = environment.from_string(get_settings().pr_information_from_user_prompt.user).render(variables)
        if get_settings().config.verbosity_level >= 2:
            get_logger().info(f"\nSystem prompt:\n{system_prompt}")
            get_logger().info(f"\nUser prompt:\n{user_prompt}")
        response, finish_reason = await self.ai_handler.chat_completion(model=model, temperature=0.2,
                                                                        system=system_prompt, user=user_prompt)
        return response

    def _prepare_pr_answer(self) -> str:
        model_output = self.prediction.strip()
        if get_settings().config.verbosity_level >= 2:
            get_logger().info(f"answer_str:\n{model_output}")
        answer_str = f"{model_output}\n\n Please respond to the questions above in the following format:\n\n" +\
                     "\n>/answer\n>1) ...\n>2) ...\n>...\n"
        return answer_str
