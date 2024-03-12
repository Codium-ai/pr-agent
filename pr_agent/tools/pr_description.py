import copy
import re
from functools import partial
from typing import List, Tuple

from jinja2 import Environment, StrictUndefined

from pr_agent.algo.ai_handlers.base_ai_handler import BaseAiHandler
from pr_agent.algo.ai_handlers.litellm_ai_handler import LiteLLMAIHandler
from pr_agent.algo.pr_processing import get_pr_diff, retry_with_fallback_models
from pr_agent.algo.token_handler import TokenHandler
from pr_agent.algo.utils import load_yaml, set_custom_labels, get_user_labels, ModelType
from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider
from pr_agent.git_providers.git_provider import get_main_pr_language
from pr_agent.log import get_logger
from pr_agent.servers.help import HelpMessage


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
            get_logger().debug(f"Disabling semantic files types for {self.pr_id}, gfm_markdown not supported.")
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
        self.file_label_dict = None
        self.COLLAPSIBLE_FILE_LIST_THRESHOLD = 8

    async def run(self):
        try:
            get_logger().info(f"Generating a PR description for pr_id: {self.pr_id}")
            relevant_configs = {'pr_description': dict(get_settings().pr_description),
                                'config': dict(get_settings().config)}
            get_logger().debug("Relevant configs", artifacts=relevant_configs)
            if get_settings().config.publish_output:
                self.git_provider.publish_comment("Preparing PR description...", is_temporary=True)

            await retry_with_fallback_models(self._prepare_prediction, ModelType.TURBO) # turbo model because larger context

            if self.prediction:
                self._prepare_data()
            else:
                get_logger().error(f"Error getting AI prediction {self.pr_id}")
                self.git_provider.remove_initial_comment()
                return None

            if get_settings().pr_description.enable_semantic_files_types:
                self.file_label_dict = self._prepare_file_labels()

            pr_labels, pr_file_changes = [], []
            if get_settings().pr_description.publish_labels:
                pr_labels = self._prepare_labels()

            if get_settings().pr_description.use_description_markers:
                pr_title, pr_body, changes_walkthrough, pr_file_changes = self._prepare_pr_answer_with_markers()
            else:
                pr_title, pr_body, changes_walkthrough, pr_file_changes = self._prepare_pr_answer()
            if not self.git_provider.is_supported(
                    "publish_file_comments") or not get_settings().pr_description.inline_file_summary:
                pr_body += "\n\n" + changes_walkthrough
            get_logger().debug("PR output", artifact={"title": pr_title, "body": pr_body})

            # Add help text if gfm_markdown is supported
            if self.git_provider.is_supported("gfm_markdown") and get_settings().pr_description.enable_help_text:
                pr_body += "<hr>\n\n<details> <summary><strong>✨ Describe tool usage guide:</strong></summary><hr> \n\n"
                pr_body += HelpMessage.get_describe_usage_guide()
                pr_body += "\n</details>\n"
            elif get_settings().pr_description.enable_help_comment:
                pr_body += "\n\n___\n\n> ✨ **PR-Agent usage**:"
                pr_body += "\n>Comment `/help` on the PR to get a list of all available PR-Agent tools and their descriptions\n\n"

            if get_settings().config.publish_output:
                # publish labels
                if get_settings().pr_description.publish_labels and self.git_provider.is_supported("get_labels"):
                    original_labels = self.git_provider.get_pr_labels(update=True)
                    get_logger().debug(f"original labels", artifact=original_labels)
                    user_labels = get_user_labels(original_labels)
                    new_labels = pr_labels + user_labels
                    get_logger().debug(f"published labels", artifact=new_labels)
                    if sorted(new_labels) != sorted(original_labels):
                        self.git_provider.publish_labels(new_labels)
                    else:
                        get_logger().debug(f"Labels are the same, not updating")

                # publish description
                if get_settings().pr_description.publish_description_as_comment:
                    full_markdown_description = f"## Title\n\n{pr_title}\n\n___\n{pr_body}"
                    self.git_provider.publish_comment(full_markdown_description)
                else:
                    self.git_provider.publish_description(pr_title, pr_body)

                    # publish final update message
                    if (get_settings().pr_description.final_update_message):
                        latest_commit_url = self.git_provider.get_latest_commit_url()
                        if latest_commit_url:
                            pr_url = self.git_provider.get_pr_url()
                            update_comment = f"**[PR Description]({pr_url})** updated to latest commit ({latest_commit_url})"
                            self.git_provider.publish_comment(update_comment)
                self.git_provider.remove_initial_comment()
        except Exception as e:
            get_logger().error(f"Error generating PR description {self.pr_id}: {e}")
        
        return ""

    async def _prepare_prediction(self, model: str) -> None:
        if get_settings().pr_description.use_description_markers and 'pr_agent:' not in self.user_description:
            return None

        self.patches_diff = get_pr_diff(self.git_provider, self.token_handler, model)
        if self.patches_diff:
            get_logger().debug(f"PR diff", artifact=self.patches_diff)
            self.prediction = await self._get_prediction(model)
        else:
            get_logger().error(f"Error getting PR diff {self.pr_id}")
            self.prediction = None

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

        response, finish_reason = await self.ai_handler.chat_completion(
            model=model,
            temperature=0.2,
            system=system_prompt,
            user=user_prompt
        )

        return response

    def _prepare_data(self):
        # Load the AI prediction data into a dictionary
        self.data = load_yaml(self.prediction.strip())

        if get_settings().pr_description.add_original_user_description and self.user_description:
            self.data["User Description"] = self.user_description

        # re-order keys
        if 'User Description' in self.data:
            self.data['User Description'] = self.data.pop('User Description')
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

    def _prepare_pr_answer_with_markers(self) -> Tuple[str, str, str, List[dict]]:
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

        ai_walkthrough = self.data.get('pr_files')
        walkthrough_gfm = ""
        pr_file_changes = []
        if ai_walkthrough and not re.search(r'<!--\s*pr_agent:walkthrough\s*-->', body):
            try:
                walkthrough_gfm, pr_file_changes = self.process_pr_files_prediction(walkthrough_gfm,
                                                                                    self.file_label_dict)
                body = body.replace('pr_agent:walkthrough', walkthrough_gfm)
            except Exception as e:
                get_logger().error(f"Failing to process walkthrough {self.pr_id}: {e}")
                body = body.replace('pr_agent:walkthrough', "")

        return title, body, walkthrough_gfm, pr_file_changes

    def _prepare_pr_answer(self) -> Tuple[str, str, str, List[dict]]:
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
            markdown_text += f"## **{key}**\n\n"
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
        pr_body, changes_walkthrough = "", ""
        pr_file_changes = []
        for idx, (key, value) in enumerate(self.data.items()):
            if key == 'pr_files':
                value = self.file_label_dict
            else:
                key_publish = key.rstrip(':').replace("_", " ").capitalize()
                pr_body += f"## **{key_publish}**\n"
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
                changes_walkthrough, pr_file_changes = self.process_pr_files_prediction(changes_walkthrough, value)
                changes_walkthrough = f"## **Changes walkthrough**\n{changes_walkthrough}"
            else:
                # if the value is a list, join its items by comma
                if isinstance(value, list):
                    value = ', '.join(v for v in value)
                pr_body += f"{value}\n"
            if idx < len(self.data) - 1:
                pr_body += "\n\n___\n\n"

        return title, pr_body, changes_walkthrough, pr_file_changes,

    def _prepare_file_labels(self):
        file_label_dict = {}
        for file in self.data['pr_files']:
            try:
                filename = file['filename'].replace("'", "`").replace('"', '`')
                changes_summary = file['changes_summary']
                changes_title = file['changes_title'].strip()
                label = file.get('label')
                if label not in file_label_dict:
                    file_label_dict[label] = []
                file_label_dict[label].append((filename, changes_title, changes_summary))
            except Exception as e:
                get_logger().error(f"Error preparing file label dict {self.pr_id}: {e}")
                pass
        return file_label_dict

    def process_pr_files_prediction(self, pr_body, value):
        pr_comments = []
        # logic for using collapsible file list
        use_collapsible_file_list = get_settings().pr_description.collapsible_file_list
        num_files = 0
        if value:
            for semantic_label in value.keys():
                num_files += len(value[semantic_label])
        if use_collapsible_file_list == "adaptive":
            use_collapsible_file_list = num_files > self.COLLAPSIBLE_FILE_LIST_THRESHOLD

        if not self.git_provider.is_supported("gfm_markdown"):
            return pr_body
        try:
            pr_body += "<table>"
            header = f"Relevant files"
            delta = 75
            # header += "&nbsp; " * delta
            pr_body += f"""<thead><tr><th></th><th align="left">{header}</th></tr></thead>"""
            pr_body += """<tbody>"""
            for semantic_label in value.keys():
                s_label = semantic_label.strip("'").strip('"')
                pr_body += f"""<tr><td><strong>{s_label.capitalize()}</strong></td>"""
                list_tuples = value[semantic_label]

                if use_collapsible_file_list:
                    pr_body += f"""<td><details><summary>{len(list_tuples)} files</summary><table>"""
                else:
                    pr_body += f"""<td><table>"""
                for filename, file_changes_title, file_change_description in list_tuples:
                    filename = filename.replace("'", "`").rstrip()
                    filename_publish = filename.split("/")[-1]
                    file_changes_title_code = f"<code>{file_changes_title}</code>"
                    file_changes_title_code_br = insert_br_after_x_chars(file_changes_title_code, x=(delta - 5)).strip()
                    if len(file_changes_title_code_br) < (delta - 5):
                        file_changes_title_code_br += "&nbsp; " * ((delta - 5) - len(file_changes_title_code_br))
                    filename_publish = f"<strong>{filename_publish}</strong><dd>{file_changes_title_code_br}</dd>"
                    diff_plus_minus = ""
                    delta_nbsp = ""
                    diff_files = self.git_provider.diff_files
                    for f in diff_files:
                        if f.filename.lower() == filename.lower():
                            num_plus_lines = f.num_plus_lines
                            num_minus_lines = f.num_minus_lines
                            diff_plus_minus += f"+{num_plus_lines}/-{num_minus_lines}"
                            delta_nbsp = "&nbsp; " * max(0, (8 - len(diff_plus_minus)))
                            break

                    # try to add line numbers link to code suggestions
                    link = ""
                    if hasattr(self.git_provider, 'get_line_link'):
                        filename = filename.strip()
                        link = self.git_provider.get_line_link(filename, relevant_line_start=-1)

                    file_change_description_br = insert_br_after_x_chars(file_change_description, x=(delta - 5))
                    pr_body += f"""
<tr>
  <td>
    <details>
      <summary>{filename_publish}</summary>
<hr>

{filename}
{file_change_description_br}


</details>
    

  </td>
  <td><a href="{link}">{diff_plus_minus}</a>{delta_nbsp}</td>
</tr>                    
"""
                if use_collapsible_file_list:
                    pr_body += """</table></details></td></tr>"""
                else:
                    pr_body += """</table></td></tr>"""
            pr_body += """</tr></tbody></table>"""

        except Exception as e:
            get_logger().error(f"Error processing pr files to markdown {self.pr_id}: {e}")
            pass
        return pr_body, pr_comments


def count_chars_without_html(string):
    if '<' not in string:
        return len(string)
    no_html_string = re.sub('<[^>]+>', '', string)
    return len(no_html_string)


def insert_br_after_x_chars(text, x=70):
    """
    Insert <br> into a string after a word that increases its length above x characters.
    Use proper HTML tags for code and new lines.
    """
    if count_chars_without_html(text) < x:
        return text

    # replace odd instances of ` with <code> and even instances of ` with </code>
    text = replace_code_tags(text)

    # convert list items to <li>
    if text.startswith("- "):
        text = "<li>" + text[2:]
    text = text.replace("\n- ", '<br><li> ').replace("\n - ", '<br><li> ')

    # convert new lines to <br>
    text = text.replace("\n", '<br>')

    # split text into lines
    lines = text.split('<br>')
    words = []
    for i, line in enumerate(lines):
        words += line.split(' ')
        if i < len(lines) - 1:
            words[-1] += "<br>"

    new_text = []
    is_inside_code = False
    current_length = 0
    for word in words:
        is_saved_word = False
        if word == "<code>" or word == "</code>" or word == "<li>" or word == "<br>":
            is_saved_word = True

        len_word = count_chars_without_html(word)
        if not is_saved_word and (current_length + len_word > x):
            if is_inside_code:
                new_text.append("</code><br><code>")
            else:
                new_text.append("<br>")
            current_length = 0  # Reset counter
        new_text.append(word + " ")

        if not is_saved_word:
            current_length += len_word + 1  # Add 1 for the space

        if word == "<li>" or word == "<br>":
            current_length = 0

        if "<code>" in word:
            is_inside_code = True
        if "</code>" in word:
            is_inside_code = False
    return ''.join(new_text).strip()

def replace_code_tags(text):
    """
    Replace odd instances of ` with <code> and even instances of ` with </code>
    """
    parts = text.split('`')
    for i in range(1, len(parts), 2):
        parts[i] = '<code>' + parts[i] + '</code>'
    return ''.join(parts)