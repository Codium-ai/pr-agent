from __future__ import annotations

import difflib
import json
import re
import textwrap
from datetime import datetime
from enum import Enum
from typing import Any, List, Tuple

import yaml
from starlette_context import context

from pr_agent.algo import MAX_TOKENS
from pr_agent.algo.token_handler import get_token_encoder
from pr_agent.config_loader import get_settings, global_settings
from pr_agent.algo.types import FilePatchInfo
from pr_agent.log import get_logger

class ModelType(str, Enum):
    REGULAR = "regular"
    TURBO = "turbo"

def get_setting(key: str) -> Any:
    try:
        key = key.upper()
        return context.get("settings", global_settings).get(key, global_settings.get(key, None))
    except Exception:
        return global_settings.get(key, None)


def emphasize_header(text: str) -> str:
    try:
        # Finding the position of the first occurrence of ": "
        colon_position = text.find(": ")

        # Splitting the string and wrapping the first part in <strong> tags
        if colon_position != -1:
            # Everything before the colon (inclusive) is wrapped in <strong> tags
            transformed_string = "<strong>" + text[:colon_position + 1] + "</strong>" + text[colon_position + 1:]
        else:
            # If there's no ": ", return the original string
            transformed_string = text

        return transformed_string
    except Exception as e:
        get_logger().exception(f"Failed to emphasize header: {e}")
        return text


def unique_strings(input_list: List[str]) -> List[str]:
    if not input_list or not isinstance(input_list, list):
        return input_list
    seen = set()
    unique_list = []
    for item in input_list:
        if item not in seen:
            unique_list.append(item)
            seen.add(item)
    return unique_list


def convert_to_markdown(output_data: dict, gfm_supported: bool = True, incremental_review=None) -> str:
    """
    Convert a dictionary of data into markdown format.
    Args:
        output_data (dict): A dictionary containing data to be converted to markdown format.
    Returns:
        str: The markdown formatted text generated from the input dictionary.
    """    

    emojis = {
        "Possible issues": "🔍",
        "Score": "🏅",
        "Relevant tests": "🧪",
        "Focused PR": "✨",
        "Security concerns": "🔒",
        "Insights from user's answers": "📝",
        "Code feedback": "🤖",
        "Estimated effort to review [1-5]": "⏱️",
    }
    markdown_text = ""
    if not incremental_review:
        markdown_text += f"## PR Review\n\n"
    else:
        markdown_text += f"## Incremental PR Review\n\n"
        markdown_text += f"⏮️ Review for commits since previous PR-Agent review {incremental_review}.\n\n"
    if gfm_supported:
        markdown_text += "<table>\n<tr>\n"
        # markdown_text += """<td> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Feedback&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</td> <td></td></tr>"""

    if not output_data or not output_data.get('review', {}):
        return ""

    for key, value in output_data['review'].items():
        if value is None or value == '' or value == {} or value == []:
            continue
        key_nice = key.replace('_', ' ').capitalize()
        emoji = emojis.get(key_nice, "")
        if gfm_supported:
            if 'Estimated effort to review' in key_nice:
                key_nice = 'Estimated&nbsp;effort&nbsp;to&nbsp;review [1-5]'
            if 'security concerns' in key_nice.lower():
                value = emphasize_header(value.strip())
                markdown_text += f"<tr><td> {emoji}&nbsp;<strong>{key_nice}</strong></td><td>\n\n{value}\n\n</td></tr>\n"
            elif 'possible issues' in key_nice.lower():
                value = value.strip()
                issues = value.split('\n- ')
                for i, _ in enumerate(issues):
                    issues[i] = issues[i].strip().strip('-').strip()
                issues = unique_strings(issues) # remove duplicates
                number_of_issues = len(issues)
                if number_of_issues > 1:
                    markdown_text += f"<tr><td rowspan={number_of_issues}> {emoji}&nbsp;<strong>{key_nice}</strong></td>\n"
                    for i, issue in enumerate(issues):
                        if not issue:
                            continue
                        issue = emphasize_header(issue)
                        if i == 0:
                            markdown_text += f"<td>\n\n{issue}</td></tr>\n"
                        else:
                            markdown_text += f"<tr>\n<td>\n\n{issue}</td></tr>\n"
                else:
                    value = emphasize_header(value.strip('-').strip())
                    markdown_text += f"<tr><td> {emoji}&nbsp;<strong>{key_nice}</strong></td><td>\n\n{value}\n\n</td></tr>\n"
            else:
                markdown_text += f"<tr><td> {emoji}&nbsp;<strong>{key_nice}</strong></td><td>\n\n{value}\n\n</td></tr>\n"
        else:
            if len(value.split()) > 1:
                markdown_text += f"{emoji} **{key_nice}:**\n\n {value}\n\n"
            else:
                markdown_text += f"{emoji} **{key_nice}:** {value}\n\n"
    if gfm_supported:
        markdown_text += "</table>\n"

    if 'code_feedback' in output_data:
        if gfm_supported:
            markdown_text += f"\n\n"
            markdown_text += f"<details><summary> <strong>Code feedback:</strong></summary>\n\n"
            markdown_text += "<hr>"
        else:
            markdown_text += f"\n\n** Code feedback:**\n\n"
        for i, value in enumerate(output_data['code_feedback']):
            if value is None or value == '' or value == {} or value == []:
                continue
            markdown_text += parse_code_suggestion(value, i, gfm_supported)+"\n\n"
        if markdown_text.endswith('<hr>'):
            markdown_text = markdown_text[:-4]
        if gfm_supported:
            markdown_text += f"</details>"
    #print(markdown_text)


    return markdown_text


def parse_code_suggestion(code_suggestion: dict, i: int = 0, gfm_supported: bool = True) -> str:
    """
    Convert a dictionary of data into markdown format.

    Args:
        code_suggestion (dict): A dictionary containing data to be converted to markdown format.

    Returns:
        str: A string containing the markdown formatted text generated from the input dictionary.
    """
    markdown_text = ""
    if gfm_supported and 'relevant_line' in code_suggestion:
        markdown_text += '<table>'
        for sub_key, sub_value in code_suggestion.items():
            try:
                if sub_key.lower() == 'relevant_file':
                    relevant_file = sub_value.strip('`').strip('"').strip("'")
                    markdown_text += f"<tr><td>relevant file</td><td>{relevant_file}</td></tr>"
                    # continue
                elif sub_key.lower() == 'suggestion':
                    markdown_text += (f"<tr><td>{sub_key} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</td>"
                                      f"<td>\n\n<strong>\n\n{sub_value.strip()}\n\n</strong>\n</td></tr>")
                elif sub_key.lower() == 'relevant_line':
                    markdown_text += f"<tr><td>relevant line</td>"
                    sub_value_list = sub_value.split('](')
                    relevant_line = sub_value_list[0].lstrip('`').lstrip('[')
                    if len(sub_value_list) > 1:
                        link = sub_value_list[1].rstrip(')').strip('`')
                        markdown_text += f"<td><a href='{link}'>{relevant_line}</a></td>"
                    else:
                        markdown_text += f"<td>{relevant_line}</td>"
                    markdown_text += "</tr>"
            except Exception as e:
                get_logger().exception(f"Failed to parse code suggestion: {e}")
                pass
        markdown_text += '</table>'
        markdown_text += "<hr>"
    else:
        for sub_key, sub_value in code_suggestion.items():
            if isinstance(sub_key, str):
                sub_key = sub_key.rstrip()
            if isinstance(sub_value,str):
                sub_value = sub_value.rstrip()
            if isinstance(sub_value, dict):  # "code example"
                markdown_text += f"  - **{sub_key}:**\n"
                for code_key, code_value in sub_value.items():  # 'before' and 'after' code
                    code_str = f"```\n{code_value}\n```"
                    code_str_indented = textwrap.indent(code_str, '        ')
                    markdown_text += f"    - **{code_key}:**\n{code_str_indented}\n"
            else:
                if "relevant_file" in sub_key.lower():
                    markdown_text += f"\n  - **{sub_key}:** {sub_value}  \n"
                else:
                    markdown_text += f"   **{sub_key}:** {sub_value}  \n"
                if "relevant_line" not in sub_key.lower():  # nicer presentation
                    # markdown_text = markdown_text.rstrip('\n') + "\\\n" # works for gitlab
                    markdown_text = markdown_text.rstrip('\n') + "   \n"  # works for gitlab and bitbucker

        markdown_text += "\n"
    return markdown_text


def try_fix_json(review, max_iter=10, code_suggestions=False):
    """
    Fix broken or incomplete JSON messages and return the parsed JSON data.

    Args:
    - review: A string containing the JSON message to be fixed.
    - max_iter: An integer representing the maximum number of iterations to try and fix the JSON message.
    - code_suggestions: A boolean indicating whether to try and fix JSON messages with code feedback.

    Returns:
    - data: A dictionary containing the parsed JSON data.

    The function attempts to fix broken or incomplete JSON messages by parsing until the last valid code suggestion.
    If the JSON message ends with a closing bracket, the function calls the fix_json_escape_char function to fix the
    message.
    If code_suggestions is True and the JSON message contains code feedback, the function tries to fix the JSON
    message by parsing until the last valid code suggestion.
    The function uses regular expressions to find the last occurrence of "}," with any number of whitespaces or
    newlines.
    It tries to parse the JSON message with the closing bracket and checks if it is valid.
    If the JSON message is valid, the parsed JSON data is returned.
    If the JSON message is not valid, the last code suggestion is removed and the process is repeated until a valid JSON
    message is obtained or the maximum number of iterations is reached.
    If a valid JSON message is not obtained, an error is logged and an empty dictionary is returned.
    """

    if review.endswith("}"):
        return fix_json_escape_char(review)

    data = {}
    if code_suggestions:
        closing_bracket = "]}"
    else:
        closing_bracket = "]}}"

    if (review.rfind("'Code feedback': [") > 0 or review.rfind('"Code feedback": [') > 0) or \
            (review.rfind("'Code suggestions': [") > 0 or review.rfind('"Code suggestions": [') > 0) :
        last_code_suggestion_ind = [m.end() for m in re.finditer(r"\}\s*,", review)][-1] - 1
        valid_json = False
        iter_count = 0

        while last_code_suggestion_ind > 0 and not valid_json and iter_count < max_iter:
            try:
                data = json.loads(review[:last_code_suggestion_ind] + closing_bracket)
                valid_json = True
                review = review[:last_code_suggestion_ind].strip() + closing_bracket
            except json.decoder.JSONDecodeError:
                review = review[:last_code_suggestion_ind]
                last_code_suggestion_ind = [m.end() for m in re.finditer(r"\}\s*,", review)][-1] - 1
                iter_count += 1

        if not valid_json:
            get_logger().error("Unable to decode JSON response from AI")
            data = {}

    return data


def fix_json_escape_char(json_message=None):
    """
    Fix broken or incomplete JSON messages and return the parsed JSON data.

    Args:
        json_message (str): A string containing the JSON message to be fixed.

    Returns:
        dict: A dictionary containing the parsed JSON data.

    Raises:
        None

    """
    try:
        result = json.loads(json_message)
    except Exception as e:
        # Find the offending character index:
        idx_to_replace = int(str(e).split(' ')[-1].replace(')', ''))
        # Remove the offending character:
        json_message = list(json_message)
        json_message[idx_to_replace] = ' '
        new_message = ''.join(json_message)
        return fix_json_escape_char(json_message=new_message)
    return result


def convert_str_to_datetime(date_str):
    """
    Convert a string representation of a date and time into a datetime object.

    Args:
        date_str (str): A string representation of a date and time in the format '%a, %d %b %Y %H:%M:%S %Z'

    Returns:
        datetime: A datetime object representing the input date and time.

    Example:
        >>> convert_str_to_datetime('Mon, 01 Jan 2022 12:00:00 UTC')
        datetime.datetime(2022, 1, 1, 12, 0, 0)
    """
    datetime_format = '%a, %d %b %Y %H:%M:%S %Z'
    return datetime.strptime(date_str, datetime_format)


def load_large_diff(filename, new_file_content_str: str, original_file_content_str: str) -> str:
    """
    Generate a patch for a modified file by comparing the original content of the file with the new content provided as
    input.

    Args:
        new_file_content_str: The new content of the file as a string.
        original_file_content_str: The original content of the file as a string.

    Returns:
        The generated or provided patch string.

    Raises:
        None.
    """
    patch = ""
    try:
        diff = difflib.unified_diff(original_file_content_str.splitlines(keepends=True),
                                    new_file_content_str.splitlines(keepends=True))
        if get_settings().config.verbosity_level >= 2:
            get_logger().warning(f"File was modified, but no patch was found. Manually creating patch: {filename}.")
        patch = ''.join(diff)
    except Exception:
        pass
    return patch


def update_settings_from_args(args: List[str]) -> List[str]:
    """
    Update the settings of the Dynaconf object based on the arguments passed to the function.

    Args:
        args: A list of arguments passed to the function.
        Example args: ['--pr_code_suggestions.extra_instructions="be funny',
                  '--pr_code_suggestions.num_code_suggestions=3']

    Returns:
        None

    Raises:
        ValueError: If the argument is not in the correct format.

    """
    other_args = []
    if args:
        for arg in args:
            arg = arg.strip()
            if arg.startswith('--'):
                arg = arg.strip('-').strip()
                vals = arg.split('=', 1)
                if len(vals) != 2:
                    if len(vals) > 2: # --extended is a valid argument
                        get_logger().error(f'Invalid argument format: {arg}')
                    other_args.append(arg)
                    continue
                key, value = _fix_key_value(*vals)
                get_settings().set(key, value)
                get_logger().info(f'Updated setting {key} to: "{value}"')
            else:
                other_args.append(arg)
    return other_args


def _fix_key_value(key: str, value: str):
    key = key.strip().upper()
    value = value.strip()
    try:
        value = yaml.safe_load(value)
    except Exception as e:
        get_logger().debug(f"Failed to parse YAML for config override {key}={value}", exc_info=e)
    return key, value


def load_yaml(response_text: str, keys_fix_yaml: List[str] = []) -> dict:
    response_text = response_text.removeprefix('```yaml').rstrip('`')
    try:
        data = yaml.safe_load(response_text)
    except Exception as e:
        get_logger().error(f"Failed to parse AI prediction: {e}")
        data = try_fix_yaml(response_text, keys_fix_yaml=keys_fix_yaml)
    return data


def try_fix_yaml(response_text: str, keys_fix_yaml: List[str] = []) -> dict:
    response_text_lines = response_text.split('\n')

    keys = ['relevant line:', 'suggestion content:', 'relevant file:', 'existing code:', 'improved code:']
    keys = keys + keys_fix_yaml
    # first fallback - try to convert 'relevant line: ...' to relevant line: |-\n        ...'
    response_text_lines_copy = response_text_lines.copy()
    for i in range(0, len(response_text_lines_copy)):
        for key in keys:
            if key in response_text_lines_copy[i] and not '|-' in response_text_lines_copy[i]:
                response_text_lines_copy[i] = response_text_lines_copy[i].replace(f'{key}',
                                                                                  f'{key} |-\n        ')
    try:
        data = yaml.safe_load('\n'.join(response_text_lines_copy))
        get_logger().info(f"Successfully parsed AI prediction after adding |-\n")
        return data
    except:
        get_logger().info(f"Failed to parse AI prediction after adding |-\n")

    # second fallback - try to extract only range from first ```yaml to ````
    snippet_pattern = r'```(yaml)?[\s\S]*?```'
    snippet = re.search(snippet_pattern, '\n'.join(response_text_lines_copy))
    if snippet:
        snippet_text = snippet.group()
        try:
            data = yaml.safe_load(snippet_text.removeprefix('```yaml').rstrip('`'))
            get_logger().info(f"Successfully parsed AI prediction after extracting yaml snippet")
            return data
        except:
            pass

     # third fallback - try to remove leading and trailing curly brackets
    response_text_copy = response_text.strip().rstrip().removeprefix('{').removesuffix('}').rstrip(':\n')
    try:
        data = yaml.safe_load(response_text_copy)
        get_logger().info(f"Successfully parsed AI prediction after removing curly brackets")
        return data
    except:
        pass

    # fourth fallback - try to remove last lines
    data = {}
    for i in range(1, len(response_text_lines)):
        response_text_lines_tmp = '\n'.join(response_text_lines[:-i])
        try:
            data = yaml.safe_load(response_text_lines_tmp)
            get_logger().info(f"Successfully parsed AI prediction after removing {i} lines")
            return data
        except:
            pass


def set_custom_labels(variables, git_provider=None):
    if not get_settings().config.enable_custom_labels:
        return

    labels = get_settings().custom_labels
    if not labels:
        # set default labels
        labels = ['Bug fix', 'Tests', 'Bug fix with tests', 'Enhancement', 'Documentation', 'Other']
        labels_list = "\n      - ".join(labels) if labels else ""
        labels_list = f"      - {labels_list}" if labels_list else ""
        variables["custom_labels"] = labels_list
        return

    # Set custom labels
    variables["custom_labels_class"] = "class Label(str, Enum):"
    counter = 0
    labels_minimal_to_labels_dict = {}
    for k, v in labels.items():
        description = "'" + v['description'].strip('\n').replace('\n', '\\n') + "'"
        # variables["custom_labels_class"] += f"\n    {k.lower().replace(' ', '_')} = '{k}' # {description}"
        variables["custom_labels_class"] += f"\n    {k.lower().replace(' ', '_')} = {description}"
        labels_minimal_to_labels_dict[k.lower().replace(' ', '_')] = k
        counter += 1
    variables["labels_minimal_to_labels_dict"] = labels_minimal_to_labels_dict

def get_user_labels(current_labels: List[str] = None):
    """
    Only keep labels that has been added by the user
    """
    try:
        if current_labels is None:
            current_labels = []
        user_labels = []
        for label in current_labels:
            if label.lower() in ['bug fix', 'tests', 'enhancement', 'documentation', 'other']:
                continue
            if get_settings().config.enable_custom_labels:
                if label in get_settings().custom_labels:
                    continue
            user_labels.append(label)
        if user_labels:
            get_logger().debug(f"Keeping user labels: {user_labels}")
    except Exception as e:
        get_logger().exception(f"Failed to get user labels: {e}")
        return current_labels
    return user_labels


def get_max_tokens(model):
    settings = get_settings()
    if model in MAX_TOKENS:
        max_tokens_model = MAX_TOKENS[model]
    else:
        raise Exception(f"MAX_TOKENS must be set for model {model} in ./pr_agent/algo/__init__.py")

    if settings.config.max_model_tokens:
        max_tokens_model = min(settings.config.max_model_tokens, max_tokens_model)
        # get_logger().debug(f"limiting max tokens to {max_tokens_model}")
    return max_tokens_model


def clip_tokens(text: str, max_tokens: int, add_three_dots=True) -> str:
    """
    Clip the number of tokens in a string to a maximum number of tokens.

    Args:
        text (str): The string to clip.
        max_tokens (int): The maximum number of tokens allowed in the string.
        add_three_dots (bool, optional): A boolean indicating whether to add three dots at the end of the clipped
    Returns:
        str: The clipped string.
    """
    if not text:
        return text

    try:
        encoder = get_token_encoder()
        num_input_tokens = len(encoder.encode(text))
        if num_input_tokens <= max_tokens:
            return text
        num_chars = len(text)
        chars_per_token = num_chars / num_input_tokens
        num_output_chars = int(chars_per_token * max_tokens)
        clipped_text = text[:num_output_chars]
        if add_three_dots:
            clipped_text += "...(truncated)"
        return clipped_text
    except Exception as e:
        get_logger().warning(f"Failed to clip tokens: {e}")
        return text

def replace_code_tags(text):
    """
    Replace odd instances of ` with <code> and even instances of ` with </code>
    """
    parts = text.split('`')
    for i in range(1, len(parts), 2):
        parts[i] = '<code>' + parts[i] + '</code>'
    return ''.join(parts)


def find_line_number_of_relevant_line_in_file(diff_files: List[FilePatchInfo],
                                              relevant_file: str,
                                              relevant_line_in_file: str,
                                              absolute_position: int = None) -> Tuple[int, int]:
    position = -1
    if absolute_position is None:
        absolute_position = -1
    re_hunk_header = re.compile(
        r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[ ]?(.*)")

    for file in diff_files:
        if file.filename and (file.filename.strip() == relevant_file):
            patch = file.patch
            patch_lines = patch.splitlines()
            delta = 0
            start1, size1, start2, size2 = 0, 0, 0, 0
            if absolute_position != -1: # matching absolute to relative
                for i, line in enumerate(patch_lines):
                    # new hunk
                    if line.startswith('@@'):
                        delta = 0
                        match = re_hunk_header.match(line)
                        start1, size1, start2, size2 = map(int, match.groups()[:4])
                    elif not line.startswith('-'):
                        delta += 1

                    #
                    absolute_position_curr = start2 + delta - 1

                    if absolute_position_curr == absolute_position:
                        position = i
                        break
            else:
                # try to find the line in the patch using difflib, with some margin of error
                matches_difflib: list[str | Any] = difflib.get_close_matches(relevant_line_in_file,
                                                                             patch_lines, n=3, cutoff=0.93)
                if len(matches_difflib) == 1 and matches_difflib[0].startswith('+'):
                    relevant_line_in_file = matches_difflib[0]


                for i, line in enumerate(patch_lines):
                    if line.startswith('@@'):
                        delta = 0
                        match = re_hunk_header.match(line)
                        start1, size1, start2, size2 = map(int, match.groups()[:4])
                    elif not line.startswith('-'):
                        delta += 1

                    if relevant_line_in_file in line and line[0] != '-':
                        position = i
                        absolute_position = start2 + delta - 1
                        break

                if position == -1 and relevant_line_in_file[0] == '+':
                    no_plus_line = relevant_line_in_file[1:].lstrip()
                    for i, line in enumerate(patch_lines):
                        if line.startswith('@@'):
                            delta = 0
                            match = re_hunk_header.match(line)
                            start1, size1, start2, size2 = map(int, match.groups()[:4])
                        elif not line.startswith('-'):
                            delta += 1

                        if no_plus_line in line and line[0] != '-':
                            # The model might add a '+' to the beginning of the relevant_line_in_file even if originally
                            # it's a context line
                            position = i
                            absolute_position = start2 + delta - 1
                            break
    return position, absolute_position
