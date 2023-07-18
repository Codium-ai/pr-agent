from __future__ import annotations

import difflib
from datetime import datetime
import json
import logging
import re
import textwrap

from pr_agent.config_loader import settings


def convert_to_markdown(output_data: dict) -> str:
    markdown_text = ""

    emojis = {
        "Main theme": "🎯",
        "Type of PR": "📌",
        "Relevant tests added": "🧪",
        "Unrelated changes": "⚠️",
        "Focused PR": "✨",
        "Security concerns": "🔒",
        "General PR suggestions": "💡",
        "Code suggestions": "🤖"
    }

    for key, value in output_data.items():
        if not value:
            continue
        if isinstance(value, dict):
            markdown_text += f"## {key}\n\n"
            markdown_text += convert_to_markdown(value)
        elif isinstance(value, list):
            if key.lower() == 'code suggestions':
                markdown_text += "\n"  # just looks nicer with additional line breaks
            emoji = emojis.get(key, "‣")  # Use a dash if no emoji is found for the key
            markdown_text += f"- {emoji} **{key}:**\n\n"
            for item in value:
                if isinstance(item, dict) and key.lower() == 'code suggestions':
                    markdown_text += parse_code_suggestion(item)
                elif item:
                    markdown_text += f"  - {item}\n"
        elif value != 'n/a':
            emoji = emojis.get(key, "‣")  # Use a dash if no emoji is found for the key
            markdown_text += f"- {emoji} **{key}:** {value}\n"
    return markdown_text


def parse_code_suggestion(code_suggestions: dict) -> str:
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

    markdown_text += "\n"
    return markdown_text


def try_fix_json(review, max_iter=10, code_suggestions=False):
    if review.endswith("}"):
        return fix_json_escape_char(review)
    # Try to fix JSON if it is broken/incomplete: parse until the last valid code suggestion
    data = {}
    if code_suggestions:
        closing_bracket = "]}"
    else:
        closing_bracket = "]}}"
    if review.rfind("'Code suggestions': [") > 0 or review.rfind('"Code suggestions": [') > 0:
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
                # Use regular expression to find the last occurrence of "}," with any number of whitespaces or newlines
                last_code_suggestion_ind = [m.end() for m in re.finditer(r"\}\s*,", review)][-1] - 1
                iter_count += 1
        if not valid_json:
            logging.error("Unable to decode JSON response from AI")
            data = {}
    return data


def fix_json_escape_char(json_message=None):
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
    datetime_format = '%a, %d %b %Y %H:%M:%S %Z'
    return datetime.strptime(date_str, datetime_format)


def load_large_diff(file, new_file_content_str: str, original_file_content_str: str, patch: str) -> str:
    if not patch:  # to Do - also add condition for file extension
        try:
            diff = difflib.unified_diff(original_file_content_str.splitlines(keepends=True),
                                        new_file_content_str.splitlines(keepends=True))
            if settings.config.verbosity_level >= 2:
                logging.warning(f"File was modified, but no patch was found. Manually creating patch: {file.filename}.")
            patch = ''.join(diff)
        except Exception:
            pass
    return patch
