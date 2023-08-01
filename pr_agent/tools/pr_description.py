import copy
import json
import logging
from typing import Tuple, List

from jinja2 import Environment, StrictUndefined

from pr_agent.algo.ai_handler import AiHandler
from pr_agent.algo.pr_processing import get_pr_diff, retry_with_fallback_models
from pr_agent.algo.token_handler import TokenHandler
from pr_agent.algo.utils import update_settings_from_args
from pr_agent.config_loader import settings
from pr_agent.git_providers import get_git_provider
from pr_agent.git_providers.git_provider import get_main_pr_language


class PRDescription:
    def __init__(self, pr_url: str, args: list = None):
        """
        Initialize the PRDescription object with the necessary attributes and objects for generating a PR description using an AI model.
        Args:
            pr_url (str): The URL of the pull request.
            args (list, optional): List of arguments passed to the PRDescription class. Defaults to None.
        """
        update_settings_from_args(args)

        # Initialize the git provider and main PR language
        self.git_provider = get_git_provider()(pr_url)
        self.main_pr_language = get_main_pr_language(
            self.git_provider.get_languages(), self.git_provider.get_files()
        )
        commit_messages_str = self.git_provider.get_commit_messages()

        # Initialize the AI handler
        self.ai_handler = AiHandler()
    
        # Initialize the variables dictionary
        self.vars = {
            "title": self.git_provider.pr.title,
            "branch": self.git_provider.get_pr_branch(),
            "description": self.git_provider.get_pr_description(),
            "language": self.main_pr_language,
            "diff": "",  # empty diff for initial calculation
            "extra_instructions": settings.pr_description.extra_instructions,
            "commit_messages_str": commit_messages_str,
        }
    
        # Initialize the token handler
        self.token_handler = TokenHandler(
            self.git_provider.pr,
            self.vars,
            settings.pr_description_prompt.system,
            settings.pr_description_prompt.user,
        )
    
        # Initialize patches_diff and prediction attributes
        self.patches_diff = None
        self.prediction = None

    async def describe(self):
        """
        Generates a PR description using an AI model and publishes it to the PR.
        """
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
                if self.git_provider.is_supported("get_labels"):
                    current_labels = self.git_provider.get_labels()
                    if current_labels is None:
                        current_labels = []
                    self.git_provider.publish_labels(pr_types + current_labels)
            self.git_provider.remove_initial_comment()
        
        return ""

    async def _prepare_prediction(self, model: str) -> None:
        """
        Prepare the AI prediction for the PR description based on the provided model.

        Args:
            model (str): The name of the model to be used for generating the prediction.

        Returns:
            None

        Raises:
            Any exceptions raised by the 'get_pr_diff' and '_get_prediction' functions.

        """
        logging.info('Getting PR diff...')
        self.patches_diff = get_pr_diff(self.git_provider, self.token_handler, model)
        logging.info('Getting AI prediction...')
        self.prediction = await self._get_prediction(model)

    async def _get_prediction(self, model: str) -> str:
        """
        Generate an AI prediction for the PR description based on the provided model.

        Args:
            model (str): The name of the model to be used for generating the prediction.

        Returns:
            str: The generated AI prediction.
        """
        variables = copy.deepcopy(self.vars)
        variables["diff"] = self.patches_diff  # update diff

        environment = Environment(undefined=StrictUndefined)
        system_prompt = environment.from_string(settings.pr_description_prompt.system).render(variables)
        user_prompt = environment.from_string(settings.pr_description_prompt.user).render(variables)

        if settings.config.verbosity_level >= 2:
            logging.info(f"\nSystem prompt:\n{system_prompt}")
            logging.info(f"\nUser prompt:\n{user_prompt}")

        response, finish_reason = await self.ai_handler.chat_completion(
            model=model,
            temperature=0.2,
            system=system_prompt,
            user=user_prompt
        )

        return response

    def _prepare_pr_answer(self) -> Tuple[str, str, List[str], str]:
        """
        Prepare the PR description based on the AI prediction data.

        Returns:
        - title: a string containing the PR title.
        - pr_body: a string containing the PR body in a markdown format.
        - pr_types: a list of strings containing the PR types.
        - markdown_text: a string containing the AI prediction data in a markdown format.
        """
        # Load the AI prediction data into a dictionary
        data = json.loads(self.prediction)

        # Initialization
        markdown_text = pr_body = ""
        pr_types = []

        # Iterate over the dictionary items and append the key and value to 'markdown_text' in a markdown format
        for key, value in data.items():
            markdown_text += f"## {key}\n\n"
            markdown_text += f"{value}\n\n"

        # If the 'PR Type' key is present in the dictionary, split its value by comma and assign it to 'pr_types'
        if 'PR Type' in data:
            pr_types = data['PR Type'].split(',')

        # Assign the value of the 'PR Title' key to 'title' variable and remove it from the dictionary
        title = data.pop('PR Title')

        # Iterate over the remaining dictionary items and append the key and value to 'pr_body' in a markdown format,
        # except for the items containing the word 'walkthrough'
        for key, value in data.items():
            pr_body += f"## {key}:\n"
            if 'walkthrough' in key.lower():
                pr_body += f"{value}\n"
            else:
                pr_body += f"{value}\n\n___\n"

        if settings.config.verbosity_level >= 2:
            logging.info(f"title:\n{title}\n{pr_body}")

        return title, pr_body, pr_types, markdown_text