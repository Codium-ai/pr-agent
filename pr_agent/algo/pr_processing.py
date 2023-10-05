from __future__ import annotations

import difflib
import logging
import re
import traceback
from typing import Any, Callable, List, Tuple

from github import RateLimitExceededException

from pr_agent.algo import MAX_TOKENS
from pr_agent.algo.git_patch_processing import convert_to_hunks_with_lines_numbers, extend_patch, handle_patch_deletions
from pr_agent.algo.language_handler import sort_files_by_main_languages
from pr_agent.algo.token_handler import TokenHandler, get_token_encoder
from pr_agent.config_loader import get_settings
from pr_agent.git_providers.git_provider import FilePatchInfo, GitProvider

DELETED_FILES_ = "Deleted files:\n"

MORE_MODIFIED_FILES_ = "More modified files:\n"

OUTPUT_BUFFER_TOKENS_SOFT_THRESHOLD = 1000
OUTPUT_BUFFER_TOKENS_HARD_THRESHOLD = 600

def get_pr_diff(git_provider: GitProvider, token_handler: TokenHandler, model: str,
                add_line_numbers_to_hunks: bool = False, disable_extra_lines: bool = False) -> str:
    """
    Returns a string with the diff of the pull request, applying diff minimization techniques if needed.

    Args:
        git_provider (GitProvider): An object of the GitProvider class representing the Git provider used for the pull
        request.
        token_handler (TokenHandler): An object of the TokenHandler class used for handling tokens in the context of the
        pull request.
        model (str): The name of the model used for tokenization.
        add_line_numbers_to_hunks (bool, optional): A boolean indicating whether to add line numbers to the hunks in the
        diff. Defaults to False.
        disable_extra_lines (bool, optional): A boolean indicating whether to disable the extension of each patch with
        extra lines of context. Defaults to False.

    Returns:
        str: A string with the diff of the pull request, applying diff minimization techniques if needed.
    """

    if disable_extra_lines:
        PATCH_EXTRA_LINES = 0
    else:
        PATCH_EXTRA_LINES = get_settings().config.patch_extra_lines

    try:
        diff_files = git_provider.get_diff_files()
    except RateLimitExceededException as e:
        logging.error(f"Rate limit exceeded for git provider API. original message {e}")
        raise

    # get pr languages
    pr_languages = sort_files_by_main_languages(git_provider.get_languages(), diff_files)

    # generate a standard diff string, with patch extension
    patches_extended, total_tokens, patches_extended_tokens = pr_generate_extended_diff(
        pr_languages, token_handler, add_line_numbers_to_hunks, patch_extra_lines=PATCH_EXTRA_LINES)

    # if we are under the limit, return the full diff
    if total_tokens + OUTPUT_BUFFER_TOKENS_SOFT_THRESHOLD < MAX_TOKENS[model]:
        return "\n".join(patches_extended)

    # if we are over the limit, start pruning
    patches_compressed, modified_file_names, deleted_file_names = \
        pr_generate_compressed_diff(pr_languages, token_handler, model, add_line_numbers_to_hunks)

    final_diff = "\n".join(patches_compressed)
    if modified_file_names:
        modified_list_str = MORE_MODIFIED_FILES_ + "\n".join(modified_file_names)
        final_diff = final_diff + "\n\n" + modified_list_str
    if deleted_file_names:
        deleted_list_str = DELETED_FILES_ + "\n".join(deleted_file_names)
        final_diff = final_diff + "\n\n" + deleted_list_str
    return final_diff


def pr_generate_extended_diff(pr_languages: list,
                              token_handler: TokenHandler,
                              add_line_numbers_to_hunks: bool,
                              patch_extra_lines: int = 0) -> Tuple[list, int, list]:
    """
    Generate a standard diff string with patch extension, while counting the number of tokens used and applying diff
    minimization techniques if needed.

    Args:
    - pr_languages: A list of dictionaries representing the languages used in the pull request and their corresponding
      files.
    - token_handler: An object of the TokenHandler class used for handling tokens in the context of the pull request.
    - add_line_numbers_to_hunks: A boolean indicating whether to add line numbers to the hunks in the diff.
    """
    total_tokens = token_handler.prompt_tokens  # initial tokens
    patches_extended = []
    patches_extended_tokens = []
    for lang in pr_languages:
        for file in lang['files']:
            original_file_content_str = file.base_file
            patch = file.patch
            if not patch:
                continue

            # extend each patch with extra lines of context
            extended_patch = extend_patch(original_file_content_str, patch, num_lines=patch_extra_lines)
            full_extended_patch = f"\n\n## {file.filename}\n\n{extended_patch}\n"

            if add_line_numbers_to_hunks:
                full_extended_patch = convert_to_hunks_with_lines_numbers(extended_patch, file)

            patch_tokens = token_handler.count_tokens(full_extended_patch)
            file.tokens = patch_tokens
            total_tokens += patch_tokens
            patches_extended_tokens.append(patch_tokens)
            patches_extended.append(full_extended_patch)

    return patches_extended, total_tokens, patches_extended_tokens


def pr_generate_compressed_diff(top_langs: list, token_handler: TokenHandler, model: str,
                                convert_hunks_to_line_numbers: bool) -> Tuple[list, list, list]:
    """
    Generate a compressed diff string for a pull request, using diff minimization techniques to reduce the number of
    tokens used.
    Args:
        top_langs (list): A list of dictionaries representing the languages used in the pull request and their
        corresponding files.
        token_handler (TokenHandler): An object of the TokenHandler class used for handling tokens in the context of the
        pull request.
        model (str): The model used for tokenization.
        convert_hunks_to_line_numbers (bool): A boolean indicating whether to convert hunks to line numbers in the diff.
    Returns:
        Tuple[list, list, list]: A tuple containing the following lists:
            - patches: A list of compressed diff patches for each file in the pull request.
            - modified_files_list: A list of file names that were skipped due to large patch size.
            - deleted_files_list: A list of file names that were deleted in the pull request.

    Minimization techniques to reduce the number of tokens:
    0. Start from the largest diff patch to smaller ones
    1. Don't use extend context lines around diff
    2. Minimize deleted files
    3. Minimize deleted hunks
    4. Minimize all remaining files when you reach token limit
    """

    patches = []
    modified_files_list = []
    deleted_files_list = []
    # sort each one of the languages in top_langs by the number of tokens in the diff
    sorted_files = []
    for lang in top_langs:
        sorted_files.extend(sorted(lang['files'], key=lambda x: x.tokens, reverse=True))

    total_tokens = token_handler.prompt_tokens
    for file in sorted_files:
        original_file_content_str = file.base_file
        new_file_content_str = file.head_file
        patch = file.patch
        if not patch:
            continue

        # removing delete-only hunks
        patch = handle_patch_deletions(patch, original_file_content_str,
                                       new_file_content_str, file.filename)
        if patch is None:
            if not deleted_files_list:
                total_tokens += token_handler.count_tokens(DELETED_FILES_)
            deleted_files_list.append(file.filename)
            total_tokens += token_handler.count_tokens(file.filename) + 1
            continue

        if convert_hunks_to_line_numbers:
            patch = convert_to_hunks_with_lines_numbers(patch, file)

        new_patch_tokens = token_handler.count_tokens(patch)

        # Hard Stop, no more tokens
        if total_tokens > MAX_TOKENS[model] - OUTPUT_BUFFER_TOKENS_HARD_THRESHOLD:
            logging.warning(f"File was fully skipped, no more tokens: {file.filename}.")
            continue

        # If the patch is too large, just show the file name
        if total_tokens + new_patch_tokens > MAX_TOKENS[model] - OUTPUT_BUFFER_TOKENS_SOFT_THRESHOLD:
            # Current logic is to skip the patch if it's too large
            # TODO: Option for alternative logic to remove hunks from the patch to reduce the number of tokens
            #  until we meet the requirements
            if get_settings().config.verbosity_level >= 2:
                logging.warning(f"Patch too large, minimizing it, {file.filename}")
            if not modified_files_list:
                total_tokens += token_handler.count_tokens(MORE_MODIFIED_FILES_)
            modified_files_list.append(file.filename)
            total_tokens += token_handler.count_tokens(file.filename) + 1
            continue

        if patch:
            if not convert_hunks_to_line_numbers:
                patch_final = f"## {file.filename}\n\n{patch}\n"
            else:
                patch_final = patch
            patches.append(patch_final)
            total_tokens += token_handler.count_tokens(patch_final)
            if get_settings().config.verbosity_level >= 2:
                logging.info(f"Tokens: {total_tokens}, last filename: {file.filename}")

    return patches, modified_files_list, deleted_files_list


async def retry_with_fallback_models(f: Callable):
    all_models = _get_all_models()
    all_deployments = _get_all_deployments(all_models)
    # try each (model, deployment_id) pair until one is successful, otherwise raise exception
    for i, (model, deployment_id) in enumerate(zip(all_models, all_deployments)):
        try:
            get_settings().set("openai.deployment_id", deployment_id)
            return await f(model)
        except Exception as e:
            logging.warning(
                f"Failed to generate prediction with {model}"
                f"{(' from deployment ' + deployment_id) if deployment_id else ''}: "
                f"{traceback.format_exc()}"
            )
            if i == len(all_models) - 1:  # If it's the last iteration
                raise  # Re-raise the last exception


def _get_all_models() -> List[str]:
    model = get_settings().config.model
    fallback_models = get_settings().config.fallback_models
    if not isinstance(fallback_models, list):
        fallback_models = [m.strip() for m in fallback_models.split(",")]
    all_models = [model] + fallback_models
    return all_models


def _get_all_deployments(all_models: List[str]) -> List[str]:
    deployment_id = get_settings().get("openai.deployment_id", None)
    fallback_deployments = get_settings().get("openai.fallback_deployments", [])
    if not isinstance(fallback_deployments, list) and fallback_deployments:
        fallback_deployments = [d.strip() for d in fallback_deployments.split(",")]
    if fallback_deployments:
        all_deployments = [deployment_id] + fallback_deployments
        if len(all_deployments) < len(all_models):
            raise ValueError(f"The number of deployments ({len(all_deployments)}) "
                             f"is less than the number of models ({len(all_models)})")
    else:
        all_deployments = [deployment_id] * len(all_models)
    return all_deployments


def find_line_number_of_relevant_line_in_file(diff_files: List[FilePatchInfo],
                                              relevant_file: str,
                                              relevant_line_in_file: str) -> Tuple[int, int]:
    """
    Find the line number and absolute position of a relevant line in a file.

    Args:
        diff_files (List[FilePatchInfo]): A list of FilePatchInfo objects representing the patches of files.
        relevant_file (str): The name of the file where the relevant line is located.
        relevant_line_in_file (str): The content of the relevant line.

    Returns:
        Tuple[int, int]: A tuple containing the line number and absolute position of the relevant line in the file.
    """
    position = -1
    absolute_position = -1
    re_hunk_header = re.compile(
        r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[ ]?(.*)")

    for file in diff_files:
        if file.filename.strip() == relevant_file:
            patch = file.patch
            patch_lines = patch.splitlines()

            # try to find the line in the patch using difflib, with some margin of error
            matches_difflib: list[str | Any] = difflib.get_close_matches(relevant_line_in_file,
                                                                         patch_lines, n=3, cutoff=0.93)
            if len(matches_difflib) == 1 and matches_difflib[0].startswith('+'):
                relevant_line_in_file = matches_difflib[0]

            delta = 0
            start1, size1, start2, size2 = 0, 0, 0, 0
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


def clip_tokens(text: str, max_tokens: int) -> str:
    """
    Clip the number of tokens in a string to a maximum number of tokens.

    Args:
        text (str): The string to clip.
        max_tokens (int): The maximum number of tokens allowed in the string.

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
        return clipped_text
    except Exception as e:
        logging.warning(f"Failed to clip tokens: {e}")
        return text


def get_pr_multi_diffs(git_provider: GitProvider,
                       token_handler: TokenHandler,
                       model: str,
                       max_calls: int = 5) -> List[str]:
    """
    Retrieves the diff files from a Git provider, sorts them by main language, and generates patches for each file.
    The patches are split into multiple groups based on the maximum number of tokens allowed for the given model.
    
    Args:
        git_provider (GitProvider): An object that provides access to Git provider APIs.
        token_handler (TokenHandler): An object that handles tokens in the context of a pull request.
        model (str): The name of the model.
        max_calls (int, optional): The maximum number of calls to retrieve diff files. Defaults to 5.
    
    Returns:
        List[str]: A list of final diff strings, split into multiple groups based on the maximum number of tokens allowed for the given model.
    
    Raises:
        RateLimitExceededException: If the rate limit for the Git provider API is exceeded.
    """
    try:
        diff_files = git_provider.get_diff_files()
    except RateLimitExceededException as e:
        logging.error(f"Rate limit exceeded for git provider API. original message {e}")
        raise

    # Sort files by main language
    pr_languages = sort_files_by_main_languages(git_provider.get_languages(), diff_files)

    # Sort files within each language group by tokens in descending order
    sorted_files = []
    for lang in pr_languages:
        sorted_files.extend(sorted(lang['files'], key=lambda x: x.tokens, reverse=True))

    patches = []
    final_diff_list = []
    total_tokens = token_handler.prompt_tokens
    call_number = 1
    for file in sorted_files:
        if call_number > max_calls:
            if get_settings().config.verbosity_level >= 2:
                logging.info(f"Reached max calls ({max_calls})")
            break

        original_file_content_str = file.base_file
        new_file_content_str = file.head_file
        patch = file.patch
        if not patch:
            continue

        # Remove delete-only hunks
        patch = handle_patch_deletions(patch, original_file_content_str, new_file_content_str, file.filename)
        if patch is None:
            continue

        patch = convert_to_hunks_with_lines_numbers(patch, file)
        new_patch_tokens = token_handler.count_tokens(patch)
        if patch and (total_tokens + new_patch_tokens > MAX_TOKENS[model] - OUTPUT_BUFFER_TOKENS_SOFT_THRESHOLD):
            final_diff = "\n".join(patches)
            final_diff_list.append(final_diff)
            patches = []
            total_tokens = token_handler.prompt_tokens
            call_number += 1
            if get_settings().config.verbosity_level >= 2:
                logging.info(f"Call number: {call_number}")

        if patch:
            patches.append(patch)
            total_tokens += new_patch_tokens
            if get_settings().config.verbosity_level >= 2:
                logging.info(f"Tokens: {total_tokens}, last filename: {file.filename}")

    # Add the last chunk
    if patches:
        final_diff = "\n".join(patches)
        final_diff_list.append(final_diff)

    return final_diff_list
