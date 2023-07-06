from __future__ import annotations

import textwrap


def convert_to_markdown(output_data: dict) -> str:
    markdown_text = ""

    emojis = {
        "Main theme": "🎯",
        "Description and title": "🔍",
        "Type of PR": "📌",
        "Relevant tests added": "🧪",
        "Unrelated changes": "⚠️",
        "Minimal and focused": "✨",
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
            if "suggestion number" in sub_key.lower():
                # markdown_text += f"- **suggestion {sub_value}:**\n"  # prettier formatting
                pass
            elif "relevant file" in sub_key.lower():
                markdown_text += f"\n  - **{sub_key}:** {sub_value}\n"
            else:
                markdown_text += f"   **{sub_key}:** {sub_value}\n"

    markdown_text += "\n"
    return markdown_text

