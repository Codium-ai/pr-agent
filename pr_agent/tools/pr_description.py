import copy
import json
import logging

from jinja2 import Environment, StrictUndefined

from pr_agent.algo.ai_handler import AiHandler
from pr_agent.algo.pr_processing import get_pr_diff, retry_with_fallback_models
from pr_agent.algo.token_handler import TokenHandler
from pr_agent.config_loader import settings
from pr_agent.git_providers import get_git_provider
from pr_agent.git_providers.git_provider import get_main_pr_language


class PRDescription:
    def __init__(self, pr_url: str):
        self.git_provider = get_git_provider()(pr_url)
        self.main_pr_language = get_main_pr_language(
            self.git_provider.get_languages(), self.git_provider.get_files()
        )
        self.ai_handler = AiHandler()
        self.vars = {
            "title": self.git_provider.pr.title,
            "branch": self.git_provider.get_pr_branch(),
            "description": self.git_provider.get_pr_description(),
            "language": self.main_pr_language,
            "diff": "",  # empty diff for initial calculation
        }
        self.token_handler = TokenHandler(self.git_provider.pr,
                                          self.vars,
                                          settings.pr_description_prompt.system,
                                          settings.pr_description_prompt.user)
        self.patches_diff = None
        self.prediction = None

    async def describe(self):
        logging.info('Generating a PR description...')
        if settings.config.publish_output:
            self.git_provider.publish_comment("Preparing pr description...", is_temporary=True)
        await retry_with_fallback_models(self._prepare_prediction)
        logging.info('Preparing answer...')
        pr_title, pr_body, pr_types, markdown_text = self._prepare_pr_answer()
        if settings.config.publish_output:
            logging.info('Pushing answer...')
            if settings.pr_description.publish_description_as_comment:
                self.git_provider.publish_comment(markdown_text)
            else:
                self.git_provider.publish_description(pr_title, pr_body)
                self.git_provider.publish_labels(pr_types)
            self.git_provider.remove_initial_comment()
        return ""

    async def _prepare_prediction(self, model: str):
        logging.info('Getting PR diff...')
        self.patches_diff = get_pr_diff(self.git_provider, self.token_handler, model)
        logging.info('Getting AI prediction...')
        self.prediction = await self._get_prediction(model)

    async def _get_prediction(self, model: str):
        variables = copy.deepcopy(self.vars)
        variables["diff"] = self.patches_diff  # update diff
        environment = Environment(undefined=StrictUndefined)
        system_prompt = environment.from_string(settings.pr_description_prompt.system).render(variables)
        user_prompt = environment.from_string(settings.pr_description_prompt.user).render(variables)
        if settings.config.verbosity_level >= 2:
            logging.info(f"\nSystem prompt:\n{system_prompt}")
            logging.info(f"\nUser prompt:\n{user_prompt}")
        response, finish_reason = await self.ai_handler.chat_completion(model=model, temperature=0.2,
                                                                        system=system_prompt, user=user_prompt)
        return response

    def _prepare_pr_answer(self):
        data = json.loads(self.prediction)
        markdown_text = ""
        for key, value in data.items():
            markdown_text += f"## {key}\n\n"
            markdown_text += f"{value}\n\n"
        pr_body = ""
        pr_types = []
        if 'PR Type' in data:
            pr_types = data['PR Type'].split(',')
        title = data['PR Title']
        del data['PR Title']
        for key, value in data.items():
            pr_body += f"{key}:\n"
            if 'walkthrough' in key.lower():
                pr_body += f"{value}\n"
            else:
                pr_body += f"**{value}**\n\n___\n"
        if settings.config.verbosity_level >= 2:
            logging.info(f"title:\n{title}\n{pr_body}")
        return title, pr_body, pr_types, markdown_text
