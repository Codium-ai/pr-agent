import copy
import json
import logging
from typing import Optional

from jinja2 import Environment, StrictUndefined

from pr_agent.algo.ai_handler import AiHandler
from pr_agent.algo.pr_processing import get_pr_diff
from pr_agent.algo.token_handler import TokenHandler
from pr_agent.algo.utils import convert_to_markdown
from pr_agent.config_loader import settings
from pr_agent.git_providers import get_git_provider


class PRReviewer:
    def __init__(self, pr_url: str, installation_id: Optional[int] = None):

        self.git_provider = get_git_provider()(pr_url, installation_id)
        self.main_language = self.git_provider.get_main_pr_language()
        self.installation_id = installation_id
        self.ai_handler = AiHandler()
        self.patches_diff = None
        self.prediction = None
        self.vars = {
            "title": self.git_provider.pr.title,
            "branch": self.git_provider.get_pr_branch(),
            "description": self.git_provider.pr.body,
            "language": self.git_provider.get_main_pr_language(),
            "diff": "",  # empty diff for initial calculation
            "require_tests": settings.pr_reviewer.require_tests_review,
            "require_security": settings.pr_reviewer.require_security_review,
            "require_minimal_and_focused": settings.pr_reviewer.require_minimal_and_focused_review,
            'extended_code_suggestions': settings.pr_reviewer.extended_code_suggestions,
            'num_code_suggestions': settings.pr_reviewer.num_code_suggestions,
        }
        self.token_handler = TokenHandler(self.git_provider.pr,
                                          self.vars,
                                          settings.pr_review_prompt.system,
                                          settings.pr_review_prompt.user)

    async def review(self):
        logging.info('Reviewing PR...')
        if settings.config.publish_review:
            self.git_provider.publish_comment("Preparing review...", is_temporary=True)
        logging.info('Getting PR diff...')
        self.patches_diff = get_pr_diff(self.git_provider, self.token_handler)
        logging.info('Getting AI prediction...')
        self.prediction = await self._get_prediction()
        logging.info('Preparing PR review...')
        pr_comment = self._prepare_pr_review()
        if settings.config.publish_review:
            logging.info('Pushing PR review...')
            self.git_provider.publish_comment(pr_comment)
            self.git_provider.remove_initial_comment()
        return ""

    async def _get_prediction(self):
        variables = copy.deepcopy(self.vars)
        variables["diff"] = self.patches_diff  # update diff
        environment = Environment(undefined=StrictUndefined)
        system_prompt = environment.from_string(settings.pr_review_prompt.system).render(variables)
        user_prompt = environment.from_string(settings.pr_review_prompt.user).render(variables)
        if settings.config.verbosity_level >= 2:
            logging.info(f"\nSystem prompt:\n{system_prompt}")
            logging.info(f"\nUser prompt:\n{user_prompt}")
        model = settings.config.model
        response, finish_reason = await self.ai_handler.chat_completion(model=model, temperature=0.2,
                                                                        system=system_prompt, user=user_prompt)
        try:
            json.loads(response)
        except json.decoder.JSONDecodeError:
            logging.warning("Could not decode JSON")
            response = {}
        return response

    def _prepare_pr_review(self) -> str:
        review = self.prediction.strip()
        try:
            data = json.loads(review)
        except json.decoder.JSONDecodeError:
            logging.error("Unable to decode JSON response from AI")
            data = {}
        markdown_text = convert_to_markdown(data)
        markdown_text += "\nAdd a comment that says 'Please review' to ask for a new review after you update the PR.\n"
        markdown_text += "Add a comment that says 'Please answer <QUESTION...>' to ask a question about this PR.\n"
        if settings.config.verbosity_level >= 2:
            logging.info(f"Markdown response:\n{markdown_text}")
        return markdown_text
