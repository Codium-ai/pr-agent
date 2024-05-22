from __future__ import annotations

import re

from pr_agent.config_loader import get_settings
from pr_agent.algo.types import EDIT_TYPE, FilePatchInfo
from pr_agent.log import get_logger


def extend_patch(original_file_str, patch_str, num_lines) -> str:
    """
    Extends the given patch to include a specified number of surrounding lines.
    
    Args:
        original_file_str (str): The original file to which the patch will be applied.
        patch_str (str): The patch to be applied to the original file.
        num_lines (int): The number of surrounding lines to include in the extended patch.
        
    Returns:
        str: The extended patch string.
    """
    if not patch_str or num_lines == 0:
        return patch_str

    if type(original_file_str) == bytes:
        try:
            original_file_str = original_file_str.decode('utf-8')
        except UnicodeDecodeError:
            return ""

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

                    res = list(match.groups())
                    for i in range(len(res)):
                        if res[i] is None:
                            res[i] = 0
                    try:
                        start1, size1, start2, size2 = map(int, res[:4])
                    except:  # '@@ -0,0 +1 @@' case
                        start1, size1, size2 = map(int, res[:3])
                        start2 = 0
                    section_header = res[4]
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
        if get_settings().config.verbosity_level >= 2:
            get_logger().error(f"Failed to extend patch: {e}")
        return patch_str

    # finish previous hunk
    if start1 != -1:
        extended_patch_lines.extend(
            original_lines[start1 + size1 - 1:start1 + size1 - 1 + num_lines])

    extended_patch_str = '\n'.join(extended_patch_lines)
    return extended_patch_str


def omit_deletion_hunks(patch_lines) -> str:
    """
    Omit deletion hunks from the patch and return the modified patch.
    Args:
    - patch_lines: a list of strings representing the lines of the patch
    Returns:
    - A string representing the modified patch with deletion hunks omitted
    """

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
                           new_file_content_str: str, file_name: str, edit_type: EDIT_TYPE = EDIT_TYPE.UNKNOWN) -> str:
    """
    Handle entire file or deletion patches.

    This function takes a patch, original file content, new file content, and file name as input.
    It handles entire file or deletion patches and returns the modified patch with deletion hunks omitted.

    Args:
        patch (str): The patch to be handled.
        original_file_content_str (str): The original content of the file.
        new_file_content_str (str): The new content of the file.
        file_name (str): The name of the file.

    Returns:
        str: The modified patch with deletion hunks omitted.

    """
    if not new_file_content_str and edit_type != EDIT_TYPE.ADDED:
        # logic for handling deleted files - don't show patch, just show that the file was deleted
        if get_settings().config.verbosity_level > 0:
            get_logger().info(f"Processing file: {file_name}, minimizing deletion file")
        patch = None # file was deleted
    else:
        patch_lines = patch.splitlines()
        patch_new = omit_deletion_hunks(patch_lines)
        if patch != patch_new:
            if get_settings().config.verbosity_level > 0:
                get_logger().info(f"Processing file: {file_name}, hunks were deleted")
            patch = patch_new
    return patch


def convert_to_hunks_with_lines_numbers(patch: str, file) -> str:
    """
    Convert a given patch string into a string with line numbers for each hunk, indicating the new and old content of
    the file.

    Args:
        patch (str): The patch string to be converted.
        file: An object containing the filename of the file being patched.

    Returns:
        str: A string with line numbers for each hunk, indicating the new and old content of the file.

    example output:
## src/file.ts
__new hunk__
881        line1
882        line2
883        line3
887 +      line4
888 +      line5
889        line6
890        line7
...
__old hunk__
        line1
        line2
-       line3
-       line4
        line5
        line6
           ...
    """
    
    patch_with_lines_str = f"\n\n## file: '{file.filename.strip()}'\n"
    patch_lines = patch.splitlines()
    RE_HUNK_HEADER = re.compile(
        r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[ ]?(.*)")
    new_content_lines = []
    old_content_lines = []
    match = None
    start1, size1, start2, size2 = -1, -1, -1, -1
    prev_header_line = []
    header_line =[]
    for line in patch_lines:
        if 'no newline at end of file' in line.lower():
            continue

        if line.startswith('@@'):
            header_line = line
            match = RE_HUNK_HEADER.match(line)
            if match and new_content_lines:  # found a new hunk, split the previous lines
                if new_content_lines:
                    if prev_header_line:
                        patch_with_lines_str += f'\n{prev_header_line}\n'
                    patch_with_lines_str = patch_with_lines_str.rstrip()+'\n__new hunk__\n'
                    for i, line_new in enumerate(new_content_lines):
                        patch_with_lines_str += f"{start2 + i} {line_new}\n"
                if old_content_lines:
                    patch_with_lines_str = patch_with_lines_str.rstrip()+'\n__old hunk__\n'
                    for line_old in old_content_lines:
                        patch_with_lines_str += f"{line_old}\n"
                new_content_lines = []
                old_content_lines = []
            if match:
                prev_header_line = header_line

            res = list(match.groups())
            for i in range(len(res)):
                if res[i] is None:
                    res[i] = 0
            try:
                start1, size1, start2, size2 = map(int, res[:4])
            except: # '@@ -0,0 +1 @@' case
                start1, size1, size2 = map(int, res[:3])
                start2 = 0

        elif line.startswith('+'):
            new_content_lines.append(line)
        elif line.startswith('-'):
            old_content_lines.append(line)
        else:
            new_content_lines.append(line)
            old_content_lines.append(line)

    # finishing last hunk
    if match and new_content_lines:
        if new_content_lines:
            patch_with_lines_str += f'\n{header_line}\n'
            patch_with_lines_str = patch_with_lines_str.rstrip()+ '\n__new hunk__\n'
            for i, line_new in enumerate(new_content_lines):
                patch_with_lines_str += f"{start2 + i} {line_new}\n"
        if old_content_lines:
            patch_with_lines_str = patch_with_lines_str.rstrip() + '\n__old hunk__\n'
            for line_old in old_content_lines:
                patch_with_lines_str += f"{line_old}\n"

    return patch_with_lines_str.rstrip()


def extract_hunk_lines_from_patch(patch: str, file_name, line_start, line_end, side) -> tuple[str, str]:

    patch_with_lines_str = f"\n\n## file: '{file_name.strip()}'\n\n"
    selected_lines = ""
    patch_lines = patch.splitlines()
    RE_HUNK_HEADER = re.compile(
        r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[ ]?(.*)")
    match = None
    start1, size1, start2, size2 = -1, -1, -1, -1
    skip_hunk = False
    selected_lines_num = 0
    for line in patch_lines:
        if 'no newline at end of file' in line.lower():
            continue

        if line.startswith('@@'):
            skip_hunk = False
            selected_lines_num = 0
            header_line = line

            match = RE_HUNK_HEADER.match(line)

            res = list(match.groups())
            for i in range(len(res)):
                if res[i] is None:
                    res[i] = 0
            try:
                start1, size1, start2, size2 = map(int, res[:4])
            except:  # '@@ -0,0 +1 @@' case
                start1, size1, size2 = map(int, res[:3])
                start2 = 0

            # check if line range is in this hunk
            if side.lower() == 'left':
                # check if line range is in this hunk
                if not (start1 <= line_start <= start1 + size1):
                    skip_hunk = True
                    continue
            elif side.lower() == 'right':
                if not (start2 <= line_start <= start2 + size2):
                    skip_hunk = True
                    continue
            patch_with_lines_str += f'\n{header_line}\n'

        elif not skip_hunk:
            if side.lower() == 'right' and line_start <= start2 + selected_lines_num <= line_end:
                selected_lines += line + '\n'
            if side.lower() == 'left' and start1 <= selected_lines_num + start1 <= line_end:
                selected_lines += line + '\n'
            patch_with_lines_str += line + '\n'
            if not line.startswith('-'): # currently we don't support /ask line for deleted lines
                selected_lines_num += 1

    return patch_with_lines_str.rstrip(), selected_lines.rstrip()