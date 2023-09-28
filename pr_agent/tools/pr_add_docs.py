import copy
import logging
import textwrap
from typing import List, Dict
from jinja2 import Environment, StrictUndefined

from pr_agent.algo.ai_handler import AiHandler
from pr_agent.algo.pr_processing import get_pr_diff, retry_with_fallback_models, get_pr_multi_diffs
from pr_agent.algo.token_handler import TokenHandler
from pr_agent.algo.utils import load_yaml
from pr_agent.config_loader import get_settings
from pr_agent.git_providers import BitbucketProvider, get_git_provider
from pr_agent.git_providers.git_provider import get_main_pr_language


def get_docs_for_language(language):
    if language.lower() == 'java':
        return "javadocs"
    elif language.lower() in ['python', 'lisp', 'clojure']:
        return "docstrings"
    elif language.lower() in ['javascript', 'typescript']:
        return "jsdocs"
    elif language.lower() == 'c++':
        return "doxygen"
    else:
        return "docs"


class PRAddDocs:
    def __init__(self, pr_url: str, cli_mode=False, args: list = None):

        self.git_provider = get_git_provider()(pr_url)
        self.main_language = get_main_pr_language(
            self.git_provider.get_languages(), self.git_provider.get_files()
        )

        # extended mode
        try:
            self.is_extended = any(["extended" in arg for arg in args])
        except:
            self.is_extended = False

        self.ai_handler = AiHandler()
        self.patches_diff = None
        self.prediction = None
        self.cli_mode = cli_mode
        self.vars = {
            "title": self.git_provider.pr.title,
            "branch": self.git_provider.get_pr_branch(),
            "description": self.git_provider.get_pr_description(),
            "language": self.main_language,
            "diff": "",  # empty diff for initial calculation
            "extra_instructions": get_settings().pr_add_docs_prompt.extra_instructions,
            "commit_messages_str": self.git_provider.get_commit_messages(),
            'docs_for_language': get_docs_for_language(self.main_language),
        }
        self.token_handler = TokenHandler(self.git_provider.pr,
                                          self.vars,
                                          get_settings().pr_add_docs_prompt.system,
                                          get_settings().pr_add_docs_prompt.user)

    async def run(self):
        try:
            logging.info('Generating code Docs for PR...')
            if get_settings().config.publish_output:
                self.git_provider.publish_comment("Preparing review...", is_temporary=True)

            logging.info('Preparing PR review...')
            if not self.is_extended:
                await retry_with_fallback_models(self._prepare_prediction)
                data = self._prepare_pr_code_docs()
            else:
                data = await retry_with_fallback_models(self._prepare_prediction_extended)
            if (not data) or (not 'Code Documentation' in data):
                logging.info('No code documentation found for PR.')
                return

            if get_settings().config.publish_output:
                logging.info('Pushing PR review...')
                self.git_provider.remove_initial_comment()
                logging.info('Pushing inline code documentation...')
                self.push_inline_docs_suggestions(data)
        except Exception as e:
            logging.error(f"Failed to generate code documentation for PR, error: {e}")

    async def _prepare_prediction(self, model: str):
        logging.info('Getting PR diff...')
        self.patches_diff = get_pr_diff(self.git_provider,
                                        self.token_handler,
                                        model,
                                        add_line_numbers_to_hunks=True,
                                        disable_extra_lines=True)

        logging.info('Getting AI prediction...')
        self.prediction = await self._get_prediction(model)

    async def _get_prediction(self, model: str):
        variables = copy.deepcopy(self.vars)
        variables["diff"] = self.patches_diff  # update diff
        environment = Environment(undefined=StrictUndefined)
        system_prompt = environment.from_string(get_settings().pr_add_docs_prompt.system).render(variables)
        user_prompt = environment.from_string(get_settings().pr_add_docs_prompt.user).render(variables)
        if get_settings().config.verbosity_level >= 2:
            logging.info(f"\nSystem prompt:\n{system_prompt}")
            logging.info(f"\nUser prompt:\n{user_prompt}")
        response, finish_reason = await self.ai_handler.chat_completion(model=model, temperature=0.2,
                                                                        system=system_prompt, user=user_prompt)

        return response

    def _prepare_pr_code_docs(self) -> Dict:
        review = self.prediction.strip()
        data = load_yaml(review)
        if isinstance(data, list):
            data = {'Code Documentation': data}
        return data

    def push_inline_docs_suggestions(self, data):
        code_suggestions = []

        if not data['Code Documentation']:
            return self.git_provider.publish_comment('No code documentation found to improve this PR.')

        for d in data['Code Documentation']:
            try:
                if get_settings().config.verbosity_level >= 2:
                    logging.info(f"add_docs: {d}")
                relevant_file = d['relevant file'].strip()
                relevant_line = int(d['relevant line'])  # absolute position
                documentation = d['documentation']
                if documentation:
                    new_code_snippet = self.dedent_code(relevant_file, relevant_line, documentation, add_original_line=True)

                    body = f"**Suggestion:** Proposed documentation\n```suggestion\n" + new_code_snippet + "\n```"
                    code_suggestions.append({'body': body, 'relevant_file': relevant_file,
                                         'relevant_lines_start': relevant_line,
                                         'relevant_lines_end': relevant_line})
            except Exception:
                if get_settings().config.verbosity_level >= 2:
                    logging.info(f"Could not parse code docs: {d}")

        is_successful = self.git_provider.publish_code_suggestions(code_suggestions)
        if not is_successful:
            logging.info("Failed to publish code docs, trying to publish each docs separately")
            for code_suggestion in code_suggestions:
                self.git_provider.publish_code_suggestions([code_suggestion])

    def dedent_code(self, relevant_file, relevant_lines_start, new_code_snippet, add_original_line=False):
        try:  # dedent code snippet
            self.diff_files = self.git_provider.diff_files if self.git_provider.diff_files \
                else self.git_provider.get_diff_files()
            original_initial_line = None
            for file in self.diff_files:
                if file.filename.strip() == relevant_file:
                    original_initial_line = file.head_file.splitlines()[relevant_lines_start - 1]
                    break
            if original_initial_line:
                suggested_initial_line = new_code_snippet.splitlines()[0]
                original_initial_spaces = len(original_initial_line) - len(original_initial_line.lstrip())
                suggested_initial_spaces = len(suggested_initial_line) - len(suggested_initial_line.lstrip())
                delta_spaces = original_initial_spaces - suggested_initial_spaces
                if delta_spaces > 0:
                    new_code_snippet = textwrap.indent(new_code_snippet, delta_spaces * " ").rstrip('\n')
                if add_original_line:
                    new_code_snippet = original_initial_line + "\n" + new_code_snippet
        except Exception as e:
            if get_settings().config.verbosity_level >= 2:
                logging.info(f"Could not dedent code snippet for file {relevant_file}, error: {e}")

        return new_code_snippet

    async def _prepare_prediction_extended(self, model: str) -> dict:
        logging.info('Getting PR diff...')
        patches_diff_list = get_pr_multi_diffs(self.git_provider, self.token_handler, model,
                                               max_calls=get_settings().pr_code_suggestions.max_number_of_calls)

        logging.info('Getting multi AI predictions...')
        prediction_list = []
        for i, patches_diff in enumerate(patches_diff_list):
            logging.info(f"Processing chunk {i + 1} of {len(patches_diff_list)}")
            self.patches_diff = patches_diff
            prediction = await self._get_prediction(model)
            prediction_list.append(prediction)
        self.prediction_list = prediction_list

        data = {}
        for prediction in prediction_list:
            self.prediction = prediction
            data_per_chunk = self._prepare_pr_code_docs()
            if "Code Documentation" in data:
                data["Code Documentation"].extend(data_per_chunk["Code Documentation"])
            else:
                data.update(data_per_chunk)
        self.data = data
        return data