from __future__ import annotations

import logging
import re

from pr_agent.config_loader import settings


def extend_patch(original_file_str, patch_str, num_lines) -> str:
    """
    Extends the patch to include 'num_lines' more surrounding lines
    """
    if not patch_str or num_lines == 0:
        return patch_str

    if type(original_file_str) == bytes:
        original_file_str = original_file_str.decode('utf-8')

    original_lines = original_file_str.splitlines()
    patch_lines = patch_str.splitlines()
    extended_patch_lines = []

    start1, size1, start2, size2 = -1, -1, -1, -1
    RE_HUNK_HEADER = re.compile(
        r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[ ]?(.*)")
    try:
        for line in patch_lines:
            if line.startswith('@@'):
                match = RE_HUNK_HEADER.match(line)
                if match:
                    # finish previous hunk
                    if start1 != -1:
                        extended_patch_lines.extend(
                            original_lines[start1 + size1 - 1:start1 + size1 - 1 + num_lines])

                    start1, size1, start2, size2 = map(int, match.groups()[:4])
                    section_header = match.groups()[4]
                    extended_start1 = max(1, start1 - num_lines)
                    extended_size1 = size1 + (start1 - extended_start1) + num_lines
                    extended_start2 = max(1, start2 - num_lines)
                    extended_size2 = size2 + (start2 - extended_start2) + num_lines
                    extended_patch_lines.append(
                        f'@@ -{extended_start1},{extended_size1} '
                        f'+{extended_start2},{extended_size2} @@ {section_header}')
                    extended_patch_lines.extend(
                        original_lines[extended_start1 - 1:start1 - 1])  # one to zero based
                    continue
            extended_patch_lines.append(line)
    except Exception as e:
        if settings.config.verbosity_level >= 2:
            logging.error(f"Failed to extend patch: {e}")
        return patch_str

    # finish previous hunk
    if start1 != -1:
        extended_patch_lines.extend(
            original_lines[start1 + size1 - 1:start1 + size1 - 1 + num_lines])

    extended_patch_str = '\n'.join(extended_patch_lines)
    return extended_patch_str


def omit_deletion_hunks(patch_lines) -> str:
    temp_hunk = []
    added_patched = []
    add_hunk = False
    inside_hunk = False
    RE_HUNK_HEADER = re.compile(
        r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))?\ @@[ ]?(.*)")

    for line in patch_lines:
        if line.startswith('@@'):
            match = RE_HUNK_HEADER.match(line)
            if match:
                # finish previous hunk
                if inside_hunk and add_hunk:
                    added_patched.extend(temp_hunk)
                    temp_hunk = []
                    add_hunk = False
                temp_hunk.append(line)
                inside_hunk = True
        else:
            temp_hunk.append(line)
            edit_type = line[0]
            if edit_type == '+':
                add_hunk = True
    if inside_hunk and add_hunk:
        added_patched.extend(temp_hunk)

    return '\n'.join(added_patched)


def handle_patch_deletions(patch: str, original_file_content_str: str,
                           new_file_content_str: str, file_name: str) -> str:
    """
    Handle entire file or deletion patches
    """
    if not new_file_content_str:
        # logic for handling deleted files - don't show patch, just show that the file was deleted
        if settings.config.verbosity_level > 0:
            logging.info(f"Processing file: {file_name}, minimizing deletion file")
        patch = None # file was deleted
    else:
        patch_lines = patch.splitlines()
        patch_new = omit_deletion_hunks(patch_lines)
        if patch != patch_new:
            if settings.config.verbosity_level > 0:
                logging.info(f"Processing file: {file_name}, hunks were deleted")
            patch = patch_new
    return patch
