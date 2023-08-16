import copy
import json
import logging
import textwrap

from jinja2 import Environment, StrictUndefined

from pr_agent.algo.ai_handler import AiHandler
from pr_agent.algo.pr_processing import get_pr_diff, retry_with_fallback_models
from pr_agent.algo.token_handler import TokenHandler
from pr_agent.algo.utils import try_fix_json
from pr_agent.config_loader import get_settings
from pr_agent.git_providers import BitbucketProvider, get_git_provider
from pr_agent.git_providers.git_provider import get_main_pr_language


class PRCodeSuggestions:
    def __init__(self, pr_url: str, cli_mode=False, args: list = None):

        self.git_provider = get_git_provider()(pr_url)
        self.main_language = get_main_pr_language(
            self.git_provider.get_languages(), self.git_provider.get_files()
        )

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
            "num_code_suggestions": get_settings().pr_code_suggestions.num_code_suggestions,
            "extra_instructions": get_settings().pr_code_suggestions.extra_instructions,
            "commit_messages_str": self.git_provider.get_commit_messages(),
        }
        self.token_handler = TokenHandler(self.git_provider.pr,
                                          self.vars,
                                          get_settings().pr_code_suggestions_prompt.system,
                                          get_settings().pr_code_suggestions_prompt.user)

    async def run(self):
        assert type(self.git_provider) != BitbucketProvider, "Bitbucket is not supported for now"

        logging.info('Generating code suggestions for PR...')
        if get_settings().config.publish_output:
            self.git_provider.publish_comment("Preparing review...", is_temporary=True)
        await retry_with_fallback_models(self._prepare_prediction)
        logging.info('Preparing PR review...')
        data = self._prepare_pr_code_suggestions()
        if get_settings().config.publish_output:
            logging.info('Pushing PR review...')
            self.git_provider.remove_initial_comment()
            logging.info('Pushing inline code comments...')
            self.push_inline_code_suggestions(data)

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
        system_prompt = environment.from_string(get_settings().pr_code_suggestions_prompt.system).render(variables)
        user_prompt = environment.from_string(get_settings().pr_code_suggestions_prompt.user).render(variables)
        if get_settings().config.verbosity_level >= 2:
            logging.info(f"\nSystem prompt:\n{system_prompt}")
            logging.info(f"\nUser prompt:\n{user_prompt}")
        response, finish_reason = await self.ai_handler.chat_completion(model=model, temperature=0.2,
                                                                        system=system_prompt, user=user_prompt)

        return response

    def _prepare_pr_code_suggestions(self) -> str:
        review = self.prediction.strip()
        try:
            data = json.loads(review)
        except json.decoder.JSONDecodeError:
            if get_settings().config.verbosity_level >= 2:
                logging.info(f"Could not parse json response: {review}")
            data = try_fix_json(review, code_suggestions=True)
        return data

    def push_inline_code_suggestions(self, data):
        code_suggestions = []

        if not data['Code suggestions']:
            return self.git_provider.publish_comment('No suggestions found to improve this PR.')

        for d in data['Code suggestions']:
            try:
                if get_settings().config.verbosity_level >= 2:
                    logging.info(f"suggestion: {d}")
                relevant_file = d['relevant file'].strip()
                relevant_lines_str = d['relevant lines'].strip()
                if ',' in relevant_lines_str:  # handling 'relevant lines': '181, 190' or '178-184, 188-194'
                    relevant_lines_str = relevant_lines_str.split(',')[0]
                relevant_lines_start = int(relevant_lines_str.split('-')[0])  # absolute position
                relevant_lines_end = int(relevant_lines_str.split('-')[-1])
                content = d['suggestion content']
                new_code_snippet = d['improved code']

                if new_code_snippet:
                    new_code_snippet = self.dedent_code(relevant_file, relevant_lines_start, new_code_snippet)

                body = f"**Suggestion:** {content}\n```suggestion\n" + new_code_snippet + "\n```"
                code_suggestions.append({'body': body, 'relevant_file': relevant_file,
                                         'relevant_lines_start': relevant_lines_start,
                                         'relevant_lines_end': relevant_lines_end})
            except Exception:
                if get_settings().config.verbosity_level >= 2:
                    logging.info(f"Could not parse suggestion: {d}")

        self.git_provider.publish_code_suggestions(code_suggestions)

    def dedent_code(self, relevant_file, relevant_lines_start, new_code_snippet):
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
        except Exception as e:
            if get_settings().config.verbosity_level >= 2:
                logging.info(f"Could not dedent code snippet for file {relevant_file}, error: {e}")

        return new_code_snippet

