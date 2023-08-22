import copy
import json
import logging
from typing import List, Tuple

from jinja2 import Environment, StrictUndefined

from pr_agent.algo.ai_handler import AiHandler
from pr_agent.algo.pr_processing import get_pr_diff, retry_with_fallback_models
from pr_agent.algo.token_handler import TokenHandler
from pr_agent.algo.utils import load_yaml
from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider
from pr_agent.git_providers.git_provider import get_main_pr_language


class PRDescription:
    def __init__(self, pr_url: str, args: list = None):
        """
        Initialize the PRDescription object with the necessary attributes and objects for generating a PR description
        using an AI model.
        Args:
            pr_url (str): The URL of the pull request.
            args (list, optional): List of arguments passed to the PRDescription class. Defaults to None.
        """
        # Initialize the git provider and main PR language
        self.git_provider = get_git_provider()(pr_url)
        self.main_pr_language = get_main_pr_language(
            self.git_provider.get_languages(), self.git_provider.get_files()
        )

        # Initialize the AI handler
        self.ai_handler = AiHandler()
    
        # Initialize the variables dictionary
        self.vars = {
            "title": self.git_provider.pr.title,
            "branch": self.git_provider.get_pr_branch(),
            "description": self.git_provider.get_pr_description(),
            "language": self.main_pr_language,
            "diff": "",  # empty diff for initial calculation
            "extra_instructions": get_settings().pr_description.extra_instructions,
            "commit_messages_str": self.git_provider.get_commit_messages()
        }

        self.user_description = self.git_provider.get_user_description()
    
        # Initialize the token handler
        self.token_handler = TokenHandler(
            self.git_provider.pr,
            self.vars,
            get_settings().pr_description_prompt.system,
            get_settings().pr_description_prompt.user,
        )
    
        # Initialize patches_diff and prediction attributes
        self.patches_diff = None
        self.prediction = None

    async def run(self):
        """
        Generates a PR description using an AI model and publishes it to the PR.
        """
        logging.info('Generating a PR description...')
        if get_settings().config.publish_output:
            self.git_provider.publish_comment("Preparing pr description...", is_temporary=True)
        
        await retry_with_fallback_models(self._prepare_prediction)
        
        logging.info('Preparing answer...')
        pr_title, pr_body, pr_types, markdown_text = self._prepare_pr_answer()
        
        if get_settings().config.publish_output:
            logging.info('Pushing answer...')
            if get_settings().pr_description.publish_description_as_comment:
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
        system_prompt = environment.from_string(get_settings().pr_description_prompt.system).render(variables)
        user_prompt = environment.from_string(get_settings().pr_description_prompt.user).render(variables)

        if get_settings().config.verbosity_level >= 2:
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
        - markdown_text: a string containing the AI prediction data in a markdown format. used for publishing a comment
        """
        # Load the AI prediction data into a dictionary
        data = load_yaml(self.prediction.strip())

        if get_settings().pr_description.add_original_user_description and self.user_description:
            data["User Description"] = self.user_description

        # Initialization
        pr_types = []

        # Iterate over the dictionary items and append the key and value to 'markdown_text' in a markdown format
        markdown_text = ""
        for key, value in data.items():
            markdown_text += f"## {key}\n\n"
            markdown_text += f"{value}\n\n"

        # If the 'PR Type' key is present in the dictionary, split its value by comma and assign it to 'pr_types'
        if 'PR Type' in data:
            if type(data['PR Type']) == list:
                pr_types = data['PR Type']
            elif type(data['PR Type']) == str:
                pr_types = data['PR Type'].split(',')

        # Remove the 'PR Title' key from the dictionary
        ai_title = data.pop('PR Title')
        if get_settings().pr_description.keep_original_user_title:
            # Assign the original PR title to the 'title' variable
            title = self.vars["title"]
        else:
            # Assign the value of the 'PR Title' key to 'title' variable
            title = ai_title

        # Iterate over the remaining dictionary items and append the key and value to 'pr_body' in a markdown format,
        # except for the items containing the word 'walkthrough'
        pr_body = ""
        for idx, (key, value) in enumerate(data.items()):
            pr_body += f"## {key}:\n"
            if 'walkthrough' in key.lower():
                # for filename, description in value.items():
                for file in value:
                    filename = file['filename'].replace("'", "`")
                    description = file['changes in file']
                    pr_body += f'`{filename}`: {description}\n'
            else:
                # if the value is a list, join its items by comma
                if type(value) == list:
                    value = ', '.join(v for v in value)
                pr_body += f"{value}\n"
            if idx < len(data) - 1:
                pr_body += "\n___\n"

        if get_settings().config.verbosity_level >= 2:
            logging.info(f"title:\n{title}\n{pr_body}")

        return title, pr_body, pr_types, markdown_text