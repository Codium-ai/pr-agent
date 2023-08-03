from __future__ import annotations
import traceback
import logging
from typing import Callable, Tuple

from github import RateLimitExceededException

from pr_agent.algo import MAX_TOKENS
from pr_agent.algo.git_patch_processing import convert_to_hunks_with_lines_numbers, extend_patch, handle_patch_deletions
from pr_agent.algo.language_handler import sort_files_by_main_languages
from pr_agent.algo.token_handler import TokenHandler
from pr_agent.algo.utils import load_large_diff
from pr_agent.config_loader import get_settings
from pr_agent.git_providers.git_provider import GitProvider

DELETED_FILES_ = "Deleted files:\n"

MORE_MODIFIED_FILES_ = "More modified files:\n"

OUTPUT_BUFFER_TOKENS_SOFT_THRESHOLD = 1000
OUTPUT_BUFFER_TOKENS_HARD_THRESHOLD = 600
PATCH_EXTRA_LINES = 3

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
        global PATCH_EXTRA_LINES
        PATCH_EXTRA_LINES = 0

    try:
        diff_files = list(git_provider.get_diff_files())
    except RateLimitExceededException as e:
        logging.error(f"Rate limit exceeded for git provider API. original message {e}")
        raise

    # get pr languages
    pr_languages = sort_files_by_main_languages(git_provider.get_languages(), diff_files)

    # generate a standard diff string, with patch extension
    patches_extended, total_tokens = pr_generate_extended_diff(pr_languages, token_handler,
                                                               add_line_numbers_to_hunks)

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


def pr_generate_extended_diff(pr_languages: list, token_handler: TokenHandler,
                              add_line_numbers_to_hunks: bool) -> \
        Tuple[list, int]:
    """
    Generate a standard diff string with patch extension, while counting the number of tokens used and applying diff
    minimization techniques if needed.

    Args:
    - pr_languages: A list of dictionaries representing the languages used in the pull request and their corresponding
      files.
    - token_handler: An object of the TokenHandler class used for handling tokens in the context of the pull request.
    - add_line_numbers_to_hunks: A boolean indicating whether to add line numbers to the hunks in the diff.

    Returns:
    - patches_extended: A list of extended patches for each file in the pull request.
    - total_tokens: The total number of tokens used in the extended patches.
    """
    total_tokens = token_handler.prompt_tokens  # initial tokens
    patches_extended = []
    for lang in pr_languages:
        for file in lang['files']:
            original_file_content_str = file.base_file
            new_file_content_str = file.head_file
            patch = file.patch

            # handle the case of large patch, that initially was not loaded
            patch = load_large_diff(file, new_file_content_str, original_file_content_str, patch)

            if not patch:
                continue

            # extend each patch with extra lines of context
            extended_patch = extend_patch(original_file_content_str, patch, num_lines=PATCH_EXTRA_LINES)
            full_extended_patch = f"## {file.filename}\n\n{extended_patch}\n"

            if add_line_numbers_to_hunks:
                full_extended_patch = convert_to_hunks_with_lines_numbers(extended_patch, file)

            patch_tokens = token_handler.count_tokens(full_extended_patch)
            file.tokens = patch_tokens
            total_tokens += patch_tokens
            patches_extended.append(full_extended_patch)

    return patches_extended, total_tokens


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
        patch = load_large_diff(file, new_file_content_str, original_file_content_str, patch)
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
    model = get_settings().config.model
    fallback_models = get_settings().config.fallback_models
    if not isinstance(fallback_models, list):
        fallback_models = [fallback_models]
    all_models = [model] + fallback_models
    for i, model in enumerate(all_models):
        try:
            return await f(model)
        except Exception as e:
            logging.warning(f"Failed to generate prediction with {model}: {traceback.format_exc()}")
            if i == len(all_models) - 1:  # If it's the last iteration
                raise  # Re-raise the last exception
