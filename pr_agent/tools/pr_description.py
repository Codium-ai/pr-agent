import copy
import re
from functools import partial
from typing import List, Tuple

from jinja2 import Environment, StrictUndefined

from pr_agent.algo.ai_handlers.base_ai_handler import BaseAiHandler
from pr_agent.algo.ai_handlers.litellm_ai_handler import LiteLLMAIHandler
from pr_agent.algo.pr_processing import get_pr_diff, retry_with_fallback_models
from pr_agent.algo.token_handler import TokenHandler
from pr_agent.algo.utils import load_yaml, set_custom_labels, get_user_labels
from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider
from pr_agent.git_providers.git_provider import get_main_pr_language
from pr_agent.log import get_logger


class PRDescription:
    def __init__(self, pr_url: str, args: list = None,
                 ai_handler: partial[BaseAiHandler,] = LiteLLMAIHandler):
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
        self.pr_id = self.git_provider.get_pr_id()

        if get_settings().pr_description.enable_semantic_files_types and not self.git_provider.is_supported(
                "gfm_markdown"):
            get_logger().debug(f"Disabling semantic files types for {self.pr_id}")
            get_settings().pr_description.enable_semantic_files_types = False

        # Initialize the AI handler
        self.ai_handler = ai_handler()
    
        # Initialize the variables dictionary
        self.vars = {
            "title": self.git_provider.pr.title,
            "branch": self.git_provider.get_pr_branch(),
            "description": self.git_provider.get_pr_description(full=False),
            "language": self.main_pr_language,
            "diff": "",  # empty diff for initial calculation
            "extra_instructions": get_settings().pr_description.extra_instructions,
            "commit_messages_str": self.git_provider.get_commit_messages(),
            "enable_custom_labels": get_settings().config.enable_custom_labels,
            "custom_labels_class": "",  # will be filled if necessary in 'set_custom_labels' function
            "enable_file_walkthrough": get_settings().pr_description.enable_file_walkthrough,
            "enable_semantic_files_types": get_settings().pr_description.enable_semantic_files_types,
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

        try:
            get_logger().info(f"Generating a PR description {self.pr_id}")
            if get_settings().config.publish_output:
                self.git_provider.publish_comment("Preparing PR description...", is_temporary=True)

            await retry_with_fallback_models(self._prepare_prediction)

            get_logger().info(f"Preparing answer {self.pr_id}")
            if self.prediction:
                self._prepare_data()
            else:
                return None

            if get_settings().pr_description.enable_semantic_files_types:
                self._prepare_file_labels()

            pr_labels = []
            if get_settings().pr_description.publish_labels:
                pr_labels = self._prepare_labels()

            if get_settings().pr_description.use_description_markers:
                pr_title, pr_body = self._prepare_pr_answer_with_markers()
            else:
                pr_title, pr_body,  = self._prepare_pr_answer()
            full_markdown_description = f"## Title\n\n{pr_title}\n\n___\n{pr_body}"

            if get_settings().config.publish_output:
                get_logger().info(f"Pushing answer {self.pr_id}")
                if get_settings().pr_description.publish_description_as_comment:
                    get_logger().info(f"Publishing answer as comment")
                    self.git_provider.publish_comment(full_markdown_description)
                else:
                    self.git_provider.publish_description(pr_title, pr_body)
                    if get_settings().pr_description.publish_labels and self.git_provider.is_supported("get_labels"):
                        current_labels = self.git_provider.get_pr_labels()
                        user_labels = get_user_labels(current_labels)
                        self.git_provider.publish_labels(pr_labels + user_labels)

                    if (get_settings().pr_description.final_update_message and
                            hasattr(self.git_provider, 'pr_url') and self.git_provider.pr_url):
                        latest_commit_url = self.git_provider.get_latest_commit_url()
                        if latest_commit_url:
                            self.git_provider.publish_comment(
                                f"**[PR Description]({self.git_provider.pr_url})** updated to latest commit ({latest_commit_url})")
                self.git_provider.remove_initial_comment()
        except Exception as e:
            get_logger().error(f"Error generating PR description {self.pr_id}: {e}")
        
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
        if get_settings().pr_description.use_description_markers and 'pr_agent:' not in self.user_description:
            return None

        get_logger().info(f"Getting PR diff {self.pr_id}")
        self.patches_diff = get_pr_diff(self.git_provider, self.token_handler, model)
        get_logger().info(f"Getting AI prediction {self.pr_id}")
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
        set_custom_labels(variables, self.git_provider)
        self.variables = variables
        system_prompt = environment.from_string(get_settings().pr_description_prompt.system).render(variables)
        user_prompt = environment.from_string(get_settings().pr_description_prompt.user).render(variables)

        if get_settings().config.verbosity_level >= 2:
            get_logger().info(f"\nSystem prompt:\n{system_prompt}")
            get_logger().info(f"\nUser prompt:\n{user_prompt}")

        response, finish_reason = await self.ai_handler.chat_completion(
            model=model,
            temperature=0.2,
            system=system_prompt,
            user=user_prompt
        )

        if get_settings().config.verbosity_level >= 2:
            get_logger().info(f"\nAI response:\n{response}")

        return response

    def _prepare_data(self):
        # Load the AI prediction data into a dictionary
        self.data = load_yaml(self.prediction.strip())

        # re-order keys
        if 'title' in self.data:
            self.data['title'] = self.data.pop('title')
        if 'type' in self.data:
            self.data['type'] = self.data.pop('type')
        if 'labels' in self.data:
            self.data['labels'] = self.data.pop('labels')
        if 'description' in self.data:
            self.data['description'] = self.data.pop('description')
        if 'pr_files' in self.data:
            self.data['pr_files'] = self.data.pop('pr_files')

        if get_settings().pr_description.add_original_user_description and self.user_description:
            self.data["User Description"] = self.user_description


    def _prepare_labels(self) -> List[str]:
        pr_types = []

        # If the 'PR Type' key is present in the dictionary, split its value by comma and assign it to 'pr_types'
        if 'labels' in self.data:
            if type(self.data['labels']) == list:
                pr_types = self.data['labels']
            elif type(self.data['labels']) == str:
                pr_types = self.data['labels'].split(',')
        elif 'type' in self.data:
            if type(self.data['type']) == list:
                pr_types = self.data['type']
            elif type(self.data['type']) == str:
                pr_types = self.data['type'].split(',')

        # convert lowercase labels to original case
        try:
            if "labels_minimal_to_labels_dict" in self.variables:
                d: dict = self.variables["labels_minimal_to_labels_dict"]
                for i, label_i in enumerate(pr_types):
                    if label_i in d:
                        pr_types[i] = d[label_i]
        except Exception as e:
            get_logger().error(f"Error converting labels to original case {self.pr_id}: {e}")
        return pr_types

    def _prepare_pr_answer_with_markers(self) -> Tuple[str, str]:
        get_logger().info(f"Using description marker replacements {self.pr_id}")
        title = self.vars["title"]
        body = self.user_description
        if get_settings().pr_description.include_generated_by_header:
            ai_header = f"### 🤖 Generated by PR Agent at {self.git_provider.last_commit_id.sha}\n\n"
        else:
            ai_header = ""

        ai_type = self.data.get('type')
        if ai_type and not re.search(r'<!--\s*pr_agent:type\s*-->', body):
            pr_type = f"{ai_header}{ai_type}"
            body = body.replace('pr_agent:type', pr_type)

        ai_summary = self.data.get('description')
        if ai_summary and not re.search(r'<!--\s*pr_agent:summary\s*-->', body):
            summary = f"{ai_header}{ai_summary}"
            body = body.replace('pr_agent:summary', summary)

        if not re.search(r'<!--\s*pr_agent:walkthrough\s*-->', body):
            ai_walkthrough = self.data.get('PR Main Files Walkthrough')
            if ai_walkthrough:
                walkthrough = str(ai_header)
                for file in ai_walkthrough:
                    filename = file['filename'].replace("'", "`")
                    description = file['changes in file'].replace("'", "`")
                    walkthrough += f'- `{filename}`: {description}\n'

                body = body.replace('pr_agent:walkthrough', walkthrough)

        return title, body

    def _prepare_pr_answer(self) -> Tuple[str, str]:
        """
        Prepare the PR description based on the AI prediction data.

        Returns:
        - title: a string containing the PR title.
        - pr_body: a string containing the PR description body in a markdown format.
        """

        # Iterate over the dictionary items and append the key and value to 'markdown_text' in a markdown format
        markdown_text = ""
        # Don't display 'PR Labels'
        if 'labels' in self.data and self.git_provider.is_supported("get_labels"):
            self.data.pop('labels')
        if not get_settings().pr_description.enable_pr_type:
            self.data.pop('type')
        for key, value in self.data.items():
            markdown_text += f"## {key}\n\n"
            markdown_text += f"{value}\n\n"

        # Remove the 'PR Title' key from the dictionary
        ai_title = self.data.pop('title', self.vars["title"])
        if get_settings().pr_description.keep_original_user_title:
            # Assign the original PR title to the 'title' variable
            title = self.vars["title"]
        else:
            # Assign the value of the 'PR Title' key to 'title' variable
            title = ai_title

        # Iterate over the remaining dictionary items and append the key and value to 'pr_body' in a markdown format,
        # except for the items containing the word 'walkthrough'
        pr_body = ""
        for idx, (key, value) in enumerate(self.data.items()):
            if key == 'pr_files':
                value = self.file_label_dict
                key_publish = "PR changes walkthrough"
            else:
                key_publish = key.rstrip(':').replace("_", " ").capitalize()
            pr_body += f"## {key_publish}\n"
            if 'walkthrough' in key.lower():
                if self.git_provider.is_supported("gfm_markdown"):
                    pr_body += "<details> <summary>files:</summary>\n\n"
                for file in value:
                    filename = file['filename'].replace("'", "`")
                    description = file['changes_in_file']
                    pr_body += f'- `{filename}`: {description}\n'
                if self.git_provider.is_supported("gfm_markdown"):
                    pr_body += "</details>\n"
            elif 'pr_files' in key.lower():
                pr_body = self.process_pr_files_prediction(pr_body, value)
            else:
                # if the value is a list, join its items by comma
                if isinstance(value, list):
                    value = ', '.join(v for v in value)
                pr_body += f"{value}\n"
            if idx < len(self.data) - 1:
                pr_body += "\n\n___\n\n"

        if get_settings().config.verbosity_level >= 2:
            get_logger().info(f"title:\n{title}\n{pr_body}")

        return title, pr_body

    def _prepare_file_labels(self):
        self.file_label_dict = {}
        for file in self.data['pr_files']:
            try:
                filename = file['filename'].replace("'", "`").replace('"', '`')
                changes_summary = file['changes_summary']
                label = file['label']
                if label not in self.file_label_dict:
                    self.file_label_dict[label] = []
                self.file_label_dict[label].append((filename, changes_summary))
            except Exception as e:
                get_logger().error(f"Error preparing file label dict {self.pr_id}: {e}")
                pass

    def process_pr_files_prediction(self, pr_body, value):
        if not self.git_provider.is_supported("gfm_markdown"):
            get_logger().info(f"Disabling semantic files types for {self.pr_id} since gfm_markdown is not supported")
            return pr_body
        try:
            pr_body += "<table>"
            header = f"Relevant files"
            delta = 65
            header += "&nbsp; " * delta
            pr_body += f"""<thead><tr><th></th><th>{header}</th></tr></thead>"""
            pr_body += """<tbody>"""
            for semantic_label in value.keys():
                s_label = semantic_label.strip("'").strip('"')
                pr_body += f"""<tr><td><strong>{s_label.capitalize()}</strong></td>"""
                list_tuples = value[semantic_label]
                pr_body += f"""<td><details><summary>{len(list_tuples)} files</summary><table>"""
                for filename, file_change_description in list_tuples:
                    filename = filename.replace("'", "`")
                    filename_publish = filename.split("/")[-1]
                    filename_publish = f"{filename_publish}"
                    if len(filename_publish) < (delta - 5):
                        filename_publish += "&nbsp; " * ((delta - 5) - len(filename_publish))
                    diff_plus_minus = ""
                    diff_files = self.git_provider.diff_files
                    for f in diff_files:
                        if f.filename.lower() == filename.lower():
                            num_plus_lines = f.num_plus_lines
                            num_minus_lines = f.num_minus_lines
                            diff_plus_minus += f"+{num_plus_lines}/-{num_minus_lines}"
                            break

                    # try to add line numbers link to code suggestions
                    link = ""
                    if hasattr(self.git_provider, 'get_line_link'):
                        filename = filename.strip()
                        link = self.git_provider.get_line_link(filename, relevant_line_start=-1)

                    file_change_description = self._insert_br_after_x_chars(file_change_description, x=(delta - 5))
                    pr_body += f"""
<tr>
  <td>
    <details>
      <summary><strong>{filename_publish}</strong></summary>
      <ul>
        {filename}<br><br>

**{file_change_description}**
</ul>
    </details>
  </td>
  <td><a href="{link}"> {diff_plus_minus}</a></td>

</tr>                    
"""
                pr_body += """</table></details></td></tr>"""
            pr_body += """</tr></tbody></table>"""

        except Exception as e:
            get_logger().error(f"Error processing pr files to markdown {self.pr_id}: {e}")
            pass
        return pr_body

    def _insert_br_after_x_chars(self, text, x=70):
        """
        Insert <br> into a string after a word that increases its length above x characters.
        """
        if len(text) < x:
            return text

        words = text.split(' ')
        new_text = ""
        current_length = 0

        for word in words:
            # Check if adding this word exceeds x characters
            if current_length + len(word) > x:
                new_text += "<br>"  # Insert line break
                current_length = 0  # Reset counter

            # Add the word to the new text
            new_text += word + " "
            current_length += len(word) + 1  # Add 1 for the space

        return new_text.strip()  # Remove trailing space
