from __future__ import annotations

import traceback
from typing import Callable, List, Tuple

from github import RateLimitExceededException

from pr_agent.algo.git_patch_processing import convert_to_hunks_with_lines_numbers, extend_patch, handle_patch_deletions
from pr_agent.algo.language_handler import sort_files_by_main_languages
from pr_agent.algo.file_filter import filter_ignored
from pr_agent.algo.token_handler import TokenHandler
from pr_agent.algo.utils import get_max_tokens, clip_tokens, ModelType
from pr_agent.config_loader import get_settings
from pr_agent.git_providers.git_provider import GitProvider
from pr_agent.algo.types import EDIT_TYPE, FilePatchInfo
from pr_agent.log import get_logger

DELETED_FILES_ = "Deleted files:\n"

MORE_MODIFIED_FILES_ = "Additional modified files (insufficient token budget to process):\n"

ADDED_FILES_ = "Additional added files (insufficient token budget to process):\n"

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
        diff_files_original = git_provider.get_diff_files()
    except RateLimitExceededException as e:
        get_logger().error(f"Rate limit exceeded for git provider API. original message {e}")
        raise

    diff_files = filter_ignored(diff_files_original)
    if diff_files != diff_files_original:
        try:
            get_logger().info(f"Filtered out {len(diff_files_original) - len(diff_files)} files")
            new_names = set([a.filename for a in diff_files])
            orig_names = set([a.filename for a in diff_files_original])
            get_logger().info(f"Filtered out files: {orig_names - new_names}")
        except Exception as e:
            pass


    # get pr languages
    pr_languages = sort_files_by_main_languages(git_provider.get_languages(), diff_files)
    if pr_languages:
        try:
            get_logger().info(f"PR main language: {pr_languages[0]['language']}")
        except Exception as e:
            pass

    # generate a standard diff string, with patch extension
    patches_extended, total_tokens, patches_extended_tokens = pr_generate_extended_diff(
        pr_languages, token_handler, add_line_numbers_to_hunks, patch_extra_lines=PATCH_EXTRA_LINES)

    # if we are under the limit, return the full diff
    if total_tokens + OUTPUT_BUFFER_TOKENS_SOFT_THRESHOLD < get_max_tokens(model):
        get_logger().info(f"Tokens: {total_tokens}, total tokens under limit: {get_max_tokens(model)}, "
                          f"returning full diff.")
        return "\n".join(patches_extended)

    # if we are over the limit, start pruning
    get_logger().info(f"Tokens: {total_tokens}, total tokens over limit: {get_max_tokens(model)}, "
                      f"pruning diff.")
    patches_compressed, modified_file_names, deleted_file_names, added_file_names, total_tokens_new = \
        pr_generate_compressed_diff(pr_languages, token_handler, model, add_line_numbers_to_hunks)

    # Insert additional information about added, modified, and deleted files if there is enough space
    max_tokens = get_max_tokens(model) - OUTPUT_BUFFER_TOKENS_HARD_THRESHOLD
    curr_token = total_tokens_new  # == token_handler.count_tokens(final_diff)+token_handler.prompt_tokens
    final_diff = "\n".join(patches_compressed)
    delta_tokens = 10
    if added_file_names and (max_tokens - curr_token) > delta_tokens:
        added_list_str = ADDED_FILES_ + "\n".join(added_file_names)
        added_list_str = clip_tokens(added_list_str, max_tokens - curr_token)
        if added_list_str:
            final_diff = final_diff + "\n\n" + added_list_str
            curr_token += token_handler.count_tokens(added_list_str) + 2
    if modified_file_names and (max_tokens - curr_token) > delta_tokens:
        modified_list_str = MORE_MODIFIED_FILES_ + "\n".join(modified_file_names)
        modified_list_str = clip_tokens(modified_list_str, max_tokens - curr_token)
        if modified_list_str:
            final_diff = final_diff + "\n\n" + modified_list_str
            curr_token += token_handler.count_tokens(modified_list_str) + 2
    if deleted_file_names and (max_tokens - curr_token) > delta_tokens:
        deleted_list_str = DELETED_FILES_ + "\n".join(deleted_file_names)
        deleted_list_str = clip_tokens(deleted_list_str, max_tokens - curr_token)
        if deleted_list_str:
            final_diff = final_diff + "\n\n" + deleted_list_str
    try:
        get_logger().debug(f"After pruning, added_list_str: {added_list_str}, modified_list_str: {modified_list_str}, "
                           f"deleted_list_str: {deleted_list_str}")
    except Exception as e:
        pass
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
            if not extended_patch:
                get_logger().warning(f"Failed to extend patch for file: {file.filename}")
                continue
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
                                convert_hunks_to_line_numbers: bool) -> Tuple[list, list, list, list, int]:
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
    added_files_list = []
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
                                       new_file_content_str, file.filename, file.edit_type)
        if patch is None:
            # if not deleted_files_list:
            #     total_tokens += token_handler.count_tokens(DELETED_FILES_)
            if file.filename not in deleted_files_list:
                deleted_files_list.append(file.filename)
            # total_tokens += token_handler.count_tokens(file.filename) + 1
            continue

        if convert_hunks_to_line_numbers:
            patch = convert_to_hunks_with_lines_numbers(patch, file)

        new_patch_tokens = token_handler.count_tokens(patch)

        # Hard Stop, no more tokens
        if total_tokens > get_max_tokens(model) - OUTPUT_BUFFER_TOKENS_HARD_THRESHOLD:
            get_logger().warning(f"File was fully skipped, no more tokens: {file.filename}.")
            continue

        # If the patch is too large, just show the file name
        if total_tokens + new_patch_tokens > get_max_tokens(model) - OUTPUT_BUFFER_TOKENS_SOFT_THRESHOLD:
            # Current logic is to skip the patch if it's too large
            # TODO: Option for alternative logic to remove hunks from the patch to reduce the number of tokens
            #  until we meet the requirements
            if get_settings().config.verbosity_level >= 2:
                get_logger().warning(f"Patch too large, minimizing it, {file.filename}")
            if file.edit_type == EDIT_TYPE.ADDED:
                # if not added_files_list:
                #     total_tokens += token_handler.count_tokens(ADDED_FILES_)
                if file.filename not in added_files_list:
                    added_files_list.append(file.filename)
                # total_tokens += token_handler.count_tokens(file.filename) + 1
            else:
                # if not modified_files_list:
                #     total_tokens += token_handler.count_tokens(MORE_MODIFIED_FILES_)
                if file.filename not in modified_files_list:
                    modified_files_list.append(file.filename)
                # total_tokens += token_handler.count_tokens(file.filename) + 1
            continue

        if patch:
            if not convert_hunks_to_line_numbers:
                patch_final = f"\n\n## file: '{file.filename.strip()}\n\n{patch.strip()}\n'"
            else:
                patch_final = "\n\n" + patch.strip()
            patches.append(patch_final)
            total_tokens += token_handler.count_tokens(patch_final)
            if get_settings().config.verbosity_level >= 2:
                get_logger().info(f"Tokens: {total_tokens}, last filename: {file.filename}")

    return patches, modified_files_list, deleted_files_list, added_files_list, total_tokens


async def retry_with_fallback_models(f: Callable, model_type: ModelType = ModelType.REGULAR):
    all_models = _get_all_models(model_type)
    all_deployments = _get_all_deployments(all_models)
    # try each (model, deployment_id) pair until one is successful, otherwise raise exception
    for i, (model, deployment_id) in enumerate(zip(all_models, all_deployments)):
        try:
            get_logger().debug(
                f"Generating prediction with {model}"
                f"{(' from deployment ' + deployment_id) if deployment_id else ''}"
            )
            get_settings().set("openai.deployment_id", deployment_id)
            return await f(model)
        except:
            get_logger().warning(
                f"Failed to generate prediction with {model}"
                f"{(' from deployment ' + deployment_id) if deployment_id else ''}: "
                f"{traceback.format_exc()}"
            )
            if i == len(all_models) - 1:  # If it's the last iteration
                raise  # Re-raise the last exception


def _get_all_models(model_type: ModelType = ModelType.REGULAR) -> List[str]:
    if model_type == ModelType.TURBO:
        model = get_settings().config.model_turbo
    else:
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
        get_logger().error(f"Rate limit exceeded for git provider API. original message {e}")
        raise

    diff_files = filter_ignored(diff_files)

    # Sort files by main language
    pr_languages = sort_files_by_main_languages(git_provider.get_languages(), diff_files)

    # Sort files within each language group by tokens in descending order
    sorted_files = []
    for lang in pr_languages:
        sorted_files.extend(sorted(lang['files'], key=lambda x: x.tokens, reverse=True))


    # try first a single run with standard diff string, with patch extension, and no deletions
    patches_extended, total_tokens, patches_extended_tokens = pr_generate_extended_diff(
        pr_languages, token_handler, add_line_numbers_to_hunks=True)
    if total_tokens + OUTPUT_BUFFER_TOKENS_SOFT_THRESHOLD < get_max_tokens(model):
        return ["\n".join(patches_extended)]

    patches = []
    final_diff_list = []
    total_tokens = token_handler.prompt_tokens
    call_number = 1
    for file in sorted_files:
        if call_number > max_calls:
            if get_settings().config.verbosity_level >= 2:
                get_logger().info(f"Reached max calls ({max_calls})")
            break

        original_file_content_str = file.base_file
        new_file_content_str = file.head_file
        patch = file.patch
        if not patch:
            continue

        # Remove delete-only hunks
        patch = handle_patch_deletions(patch, original_file_content_str, new_file_content_str, file.filename, file.edit_type)
        if patch is None:
            continue

        patch = convert_to_hunks_with_lines_numbers(patch, file)
        new_patch_tokens = token_handler.count_tokens(patch)

        if patch and (token_handler.prompt_tokens + new_patch_tokens) > get_max_tokens(
                model) - OUTPUT_BUFFER_TOKENS_SOFT_THRESHOLD:
            if get_settings().config.get('large_patch_policy', 'skip') == 'skip':
                get_logger().warning(f"Patch too large, skipping: {file.filename}")
                continue
            elif get_settings().config.get('large_patch_policy') == 'clip':
                delta_tokens = get_max_tokens(model) - OUTPUT_BUFFER_TOKENS_SOFT_THRESHOLD - token_handler.prompt_tokens
                patch_clipped = clip_tokens(patch, delta_tokens, delete_last_line=True, num_input_tokens=new_patch_tokens)
                new_patch_tokens = token_handler.count_tokens(patch_clipped)
                if patch_clipped and (token_handler.prompt_tokens + new_patch_tokens) > get_max_tokens(
                        model) - OUTPUT_BUFFER_TOKENS_SOFT_THRESHOLD:
                    get_logger().warning(f"Patch too large, skipping: {file.filename}")
                    continue
                else:
                    get_logger().info(f"Clipped large patch for file: {file.filename}")
                    patch = patch_clipped
            else:
                get_logger().warning(f"Patch too large, skipping: {file.filename}")
                continue

        if patch and (total_tokens + new_patch_tokens > get_max_tokens(model) - OUTPUT_BUFFER_TOKENS_SOFT_THRESHOLD):
            final_diff = "\n".join(patches)
            final_diff_list.append(final_diff)
            patches = []
            total_tokens = token_handler.prompt_tokens
            call_number += 1
            if get_settings().config.verbosity_level >= 2:
                get_logger().info(f"Call number: {call_number}")

        if patch:
            patches.append(patch)
            total_tokens += new_patch_tokens
            if get_settings().config.verbosity_level >= 2:
                get_logger().info(f"Tokens: {total_tokens}, last filename: {file.filename}")

    # Add the last chunk
    if patches:
        final_diff = "\n".join(patches)
        final_diff_list.append(final_diff)

    return final_diff_list