from __future__ import annotations

import difflib
import json
import logging
import re
import textwrap
from datetime import datetime
from typing import Any, List

import yaml
from starlette_context import context
from pr_agent.config_loader import get_settings, global_settings


def get_setting(key: str) -> Any:
    try:
        key = key.upper()
        return context.get("settings", global_settings).get(key, global_settings.get(key, None))
    except Exception:
        return global_settings.get(key, None)

def convert_to_markdown(output_data: dict, gfm_supported: bool=True) -> str:
    """
    Convert a dictionary of data into markdown format.
    Args:
        output_data (dict): A dictionary containing data to be converted to markdown format.
    Returns:
        str: The markdown formatted text generated from the input dictionary.
    """    
    markdown_text = ""

    emojis = {
        "Main theme": "🎯",
        "PR summary": "📝",
        "Type of PR": "📌",
        "Score": "🏅",
        "Relevant tests added": "🧪",
        "Unrelated changes": "⚠️",
        "Focused PR": "✨",
        "Security concerns": "🔒",
        "General suggestions": "💡",
        "Insights from user's answers": "📝",
        "Code feedback": "🤖",
        "Estimated effort to review [1-5]": "⏱️",
    }

    for key, value in output_data.items():
        if value is None or value == '' or value == {}:
            continue
        if isinstance(value, dict):
            markdown_text += f"## {key}\n\n"
            markdown_text += convert_to_markdown(value, gfm_supported)
        elif isinstance(value, list):
            emoji = emojis.get(key, "")
            if key.lower() == 'code feedback':
                if gfm_supported:
                    markdown_text += f"\n\n- **<details><summary> { emoji } Code feedback:**</summary>\n\n"
                else:
                    markdown_text += f"\n\n- **{emoji} Code feedback:**\n\n"
            else:
                markdown_text += f"- {emoji} **{key}:**\n\n"
            for item in value:
                if isinstance(item, dict) and key.lower() == 'code feedback':
                    markdown_text += parse_code_suggestion(item, gfm_supported)
                elif item:
                    markdown_text += f"  - {item}\n"
            if key.lower() == 'code feedback':
                if gfm_supported:
                    markdown_text += "</details>\n\n"
                else:
                    markdown_text += "\n\n"
        elif value != 'n/a':
            emoji = emojis.get(key, "")
            markdown_text += f"- {emoji} **{key}:** {value}\n"
    return markdown_text


def parse_code_suggestion(code_suggestions: dict, gfm_supported: bool=True) -> str:
    """
    Convert a dictionary of data into markdown format.

    Args:
        code_suggestions (dict): A dictionary containing data to be converted to markdown format.

    Returns:
        str: A string containing the markdown formatted text generated from the input dictionary.
    """
    markdown_text = ""
    for sub_key, sub_value in code_suggestions.items():
        if isinstance(sub_value, dict):  # "code example"
            markdown_text += f"  - **{sub_key}:**\n"
            for code_key, code_value in sub_value.items():  # 'before' and 'after' code
                code_str = f"```\n{code_value}\n```"
                code_str_indented = textwrap.indent(code_str, '        ')
                markdown_text += f"    - **{code_key}:**\n{code_str_indented}\n"
        else:
            if "relevant file" in sub_key.lower():
                markdown_text += f"\n  - **{sub_key}:** {sub_value}\n"
            else:
                markdown_text += f"   **{sub_key}:** {sub_value}\n"
            if not gfm_supported:
                if "relevant line" not in sub_key.lower(): # nicer presentation
                        markdown_text = markdown_text.rstrip('\n') + "\\\n"

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
            logging.error("Unable to decode JSON response from AI")
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
            logging.warning(f"File was modified, but no patch was found. Manually creating patch: {filename}.")
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
                        logging.error(f'Invalid argument format: {arg}')
                    other_args.append(arg)
                    continue
                key, value = _fix_key_value(*vals)
                get_settings().set(key, value)
                logging.info(f'Updated setting {key} to: "{value}"')
            else:
                other_args.append(arg)
    return other_args


def _fix_key_value(key: str, value: str):
    key = key.strip().upper()
    value = value.strip()
    try:
        value = yaml.safe_load(value)
    except Exception as e:
        logging.error(f"Failed to parse YAML for config override {key}={value}", exc_info=e)
    return key, value


def load_yaml(review_text: str) -> dict:
    review_text = review_text.removeprefix('```yaml').rstrip('`')
    try:
        data = yaml.safe_load(review_text)
    except Exception as e:
        logging.error(f"Failed to parse AI prediction: {e}")
        data = try_fix_yaml(review_text)
    return data

def try_fix_yaml(review_text: str) -> dict:
    review_text_lines = review_text.split('\n')
    data = {}
    for i in range(1, len(review_text_lines)):
        review_text_lines_tmp = '\n'.join(review_text_lines[:-i])
        try:
            data = yaml.load(review_text_lines_tmp, Loader=yaml.SafeLoader)
            logging.info(f"Successfully parsed AI prediction after removing {i} lines")
            break
        except:
            pass
    return data
