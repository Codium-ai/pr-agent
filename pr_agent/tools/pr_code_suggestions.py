import copy
import textwrap
from functools import partial
from typing import Dict, List
from jinja2 import Environment, StrictUndefined

from pr_agent.algo.ai_handlers.base_ai_handler import BaseAiHandler
from pr_agent.algo.ai_handlers.litellm_ai_handler import LiteLLMAIHandler
from pr_agent.algo.pr_processing import get_pr_diff, get_pr_multi_diffs, retry_with_fallback_models
from pr_agent.algo.token_handler import TokenHandler
from pr_agent.algo.utils import load_yaml
from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider
from pr_agent.git_providers.git_provider import get_main_pr_language
from pr_agent.log import get_logger


class PRCodeSuggestions:
    def __init__(self, pr_url: str, cli_mode=False, args: list = None,
                 ai_handler: partial[BaseAiHandler,] = LiteLLMAIHandler):

        self.git_provider = get_git_provider()(pr_url)
        self.main_language = get_main_pr_language(
            self.git_provider.get_languages(), self.git_provider.get_files()
        )

        # extended mode
        try:
            self.is_extended = any(["extended" in arg for arg in args])
        except:
            self.is_extended = False
        if self.is_extended:
            num_code_suggestions = get_settings().pr_code_suggestions.num_code_suggestions_per_chunk
        else:
            num_code_suggestions = get_settings().pr_code_suggestions.num_code_suggestions

        self.ai_handler = ai_handler()
        self.patches_diff = None
        self.prediction = None
        self.cli_mode = cli_mode
        self.vars = {
            "title": self.git_provider.pr.title,
            "branch": self.git_provider.get_pr_branch(),
            "description": self.git_provider.get_pr_description(),
            "language": self.main_language,
            "diff": "",  # empty diff for initial calculation
            "num_code_suggestions": num_code_suggestions,
            "extra_instructions": get_settings().pr_code_suggestions.extra_instructions,
            "commit_messages_str": self.git_provider.get_commit_messages(),
        }
        self.token_handler = TokenHandler(self.git_provider.pr,
                                          self.vars,
                                          get_settings().pr_code_suggestions_prompt.system,
                                          get_settings().pr_code_suggestions_prompt.user)

    async def run(self):
        try:
            get_logger().info('Generating code suggestions for PR...')
            if get_settings().config.publish_output:
                self.git_provider.publish_comment("Preparing suggestions...", is_temporary=True)

            get_logger().info('Preparing PR code suggestions...')
            if not self.is_extended:
                await retry_with_fallback_models(self._prepare_prediction)
                data = self._prepare_pr_code_suggestions()
            else:
                data = await retry_with_fallback_models(self._prepare_prediction_extended)
            if (not data) or (not 'code_suggestions' in data):
                get_logger().info('No code suggestions found for PR.')
                return

            if (not self.is_extended and get_settings().pr_code_suggestions.rank_suggestions) or \
                    (self.is_extended and get_settings().pr_code_suggestions.rank_extended_suggestions):
                get_logger().info('Ranking Suggestions...')
                data['code_suggestions'] = await self.rank_suggestions(data['code_suggestions'])

            if get_settings().config.publish_output:
                get_logger().info('Pushing PR code suggestions...')
                self.git_provider.remove_initial_comment()
                if get_settings().pr_code_suggestions.summarize:
                    get_logger().info('Pushing summarize code suggestions...')
                    self.publish_summarizes_suggestions(data)
                else:
                    get_logger().info('Pushing inline code suggestions...')
                    self.push_inline_code_suggestions(data)
        except Exception as e:
            get_logger().error(f"Failed to generate code suggestions for PR, error: {e}")

    async def _prepare_prediction(self, model: str):
        get_logger().info('Getting PR diff...')
        self.patches_diff = get_pr_diff(self.git_provider,
                                        self.token_handler,
                                        model,
                                        add_line_numbers_to_hunks=True,
                                        disable_extra_lines=True)

        get_logger().info('Getting AI prediction...')
        self.prediction = await self._get_prediction(model)

    async def _get_prediction(self, model: str):
        variables = copy.deepcopy(self.vars)
        variables["diff"] = self.patches_diff  # update diff
        environment = Environment(undefined=StrictUndefined)
        system_prompt = environment.from_string(get_settings().pr_code_suggestions_prompt.system).render(variables)
        user_prompt = environment.from_string(get_settings().pr_code_suggestions_prompt.user).render(variables)
        if get_settings().config.verbosity_level >= 2:
            get_logger().info(f"\nSystem prompt:\n{system_prompt}")
            get_logger().info(f"\nUser prompt:\n{user_prompt}")
        response, finish_reason = await self.ai_handler.chat_completion(model=model, temperature=0.2,
                                                                        system=system_prompt, user=user_prompt)

        if get_settings().config.verbosity_level >= 2:
            get_logger().info(f"\nAI response:\n{response}")

        return response

    def _prepare_pr_code_suggestions(self) -> Dict:
        review = self.prediction.strip()
        data = load_yaml(review,
                         keys_fix_yaml=["relevant_file", "suggestion_content", "existing_code", "improved_code"])
        if isinstance(data, list):
            data = {'code_suggestions': data}

        # remove invalid suggestions
        suggestion_list = []
        for i, suggestion in enumerate(data['code_suggestions']):
            if suggestion['existing_code'] != suggestion['improved_code']:
                suggestion_list.append(suggestion)
            else:
                get_logger().debug(
                    f"Skipping suggestion {i + 1}, because existing code is equal to improved code {suggestion['existing_code']}")
        data['code_suggestions'] = suggestion_list

        return data

    def push_inline_code_suggestions(self, data):
        code_suggestions = []

        if not data['code_suggestions']:
            get_logger().info('No suggestions found to improve this PR.')
            return self.git_provider.publish_comment('No suggestions found to improve this PR.')

        for d in data['code_suggestions']:
            try:
                if get_settings().config.verbosity_level >= 2:
                    get_logger().info(f"suggestion: {d}")
                relevant_file = d['relevant_file'].strip()
                relevant_lines_start = int(d['relevant_lines_start'])  # absolute position
                relevant_lines_end = int(d['relevant_lines_end'])
                content = d['suggestion_content'].rstrip()
                new_code_snippet = d['improved_code'].rstrip()
                label = d['label'].strip()

                if new_code_snippet:
                    new_code_snippet = self.dedent_code(relevant_file, relevant_lines_start, new_code_snippet)

                if get_settings().pr_code_suggestions.include_improved_code:
                    body = f"**Suggestion:** {content} [{label}]\n```suggestion\n" + new_code_snippet + "\n```"
                    code_suggestions.append({'body': body, 'relevant_file': relevant_file,
                                             'relevant_lines_start': relevant_lines_start,
                                             'relevant_lines_end': relevant_lines_end})
                else:
                    if self.git_provider.is_supported("create_inline_comment"):
                        body = f"**Suggestion:** {content} [{label}]"
                        comment = self.git_provider.create_inline_comment(body, relevant_file, "",
                                                                          absolute_position=relevant_lines_end)
                        if comment:
                            code_suggestions.append(comment)
                    else:
                        get_logger().error("Inline comments are not supported by the git provider")
            except Exception:
                if get_settings().config.verbosity_level >= 2:
                    get_logger().info(f"Could not parse suggestion: {d}")

        if get_settings().pr_code_suggestions.include_improved_code:
            is_successful = self.git_provider.publish_code_suggestions(code_suggestions)
        else:
            is_successful = self.git_provider.publish_inline_comments(code_suggestions)
        if not is_successful:
            get_logger().info("Failed to publish code suggestions, trying to publish each suggestion separately")
            for code_suggestion in code_suggestions:
                if get_settings().pr_code_suggestions.include_improved_code:
                    self.git_provider.publish_code_suggestions([code_suggestion])
                else:
                    self.git_provider.publish_inline_comments([code_suggestion])

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
                get_logger().info(f"Could not dedent code snippet for file {relevant_file}, error: {e}")

        return new_code_snippet

    async def _prepare_prediction_extended(self, model: str) -> dict:
        get_logger().info('Getting PR diff...')
        patches_diff_list = get_pr_multi_diffs(self.git_provider, self.token_handler, model,
                                               max_calls=get_settings().pr_code_suggestions.max_number_of_calls)

        get_logger().info('Getting multi AI predictions...')
        prediction_list = []
        for i, patches_diff in enumerate(patches_diff_list):
            get_logger().info(f"Processing chunk {i + 1} of {len(patches_diff_list)}")
            self.patches_diff = patches_diff
            prediction = await self._get_prediction(model)
            prediction_list.append(prediction)
        self.prediction_list = prediction_list

        data = {}
        for prediction in prediction_list:
            self.prediction = prediction
            data_per_chunk = self._prepare_pr_code_suggestions()
            if "code_suggestions" in data:
                data["code_suggestions"].extend(data_per_chunk["code_suggestions"])
            else:
                data.update(data_per_chunk)
        self.data = data
        return data

    async def rank_suggestions(self, data: List) -> List:
        """
        Call a model to rank (sort) code suggestions based on their importance order.

        Args:
            data (List): A list of code suggestions to be ranked.

        Returns:
            List: The ranked list of code suggestions.
        """

        suggestion_list = []
        for suggestion in data:
            suggestion_list.append(suggestion)
        data_sorted = [[]] * len(suggestion_list)

        try:
            suggestion_str = ""
            for i, suggestion in enumerate(suggestion_list):
                suggestion_str += f"suggestion {i + 1}: " + str(suggestion) + '\n\n'

            variables = {'suggestion_list': suggestion_list, 'suggestion_str': suggestion_str}
            model = get_settings().config.model
            environment = Environment(undefined=StrictUndefined)
            system_prompt = environment.from_string(get_settings().pr_sort_code_suggestions_prompt.system).render(
                variables)
            user_prompt = environment.from_string(get_settings().pr_sort_code_suggestions_prompt.user).render(variables)
            if get_settings().config.verbosity_level >= 2:
                get_logger().info(f"\nSystem prompt:\n{system_prompt}")
                get_logger().info(f"\nUser prompt:\n{user_prompt}")
            response, finish_reason = await self.ai_handler.chat_completion(model=model, system=system_prompt,
                                                                            user=user_prompt)

            sort_order = load_yaml(response)
            for s in sort_order['Sort Order']:
                suggestion_number = s['suggestion number']
                importance_order = s['importance order']
                data_sorted[importance_order - 1] = suggestion_list[suggestion_number - 1]

            if get_settings().pr_code_suggestions.final_clip_factor != 1:
                new_len = int(0.5 + len(data_sorted) * get_settings().pr_code_suggestions.final_clip_factor)
                data_sorted = data_sorted[:new_len]
        except Exception as e:
            if get_settings().config.verbosity_level >= 1:
                get_logger().info(f"Could not sort suggestions, error: {e}")
            data_sorted = suggestion_list

        return data_sorted

    def publish_summarizes_suggestions(self, data: Dict):
        try:
            data_markdown = "## PR Code Suggestions\n\n"

            language_extension_map_org = get_settings().language_extension_map_org
            extension_to_language = {}
            for language, extensions in language_extension_map_org.items():
                for ext in extensions:
                    extension_to_language[ext] = language

            for s in data['code_suggestions']:
                try:
                    extension_s = s['relevant_file'].rsplit('.')[-1]
                    code_snippet_link = self.git_provider.get_line_link(s['relevant_file'], s['relevant_lines_start'],
                                                                        s['relevant_lines_end'])
                    label = s['label'].strip()
                    data_markdown += f"\n💡 [{label}]\n\n**{s['suggestion_content'].rstrip().rstrip()}**\n\n"
                    if code_snippet_link:
                        data_markdown += f" File: [{s['relevant_file']} ({s['relevant_lines_start']}-{s['relevant_lines_end']})]({code_snippet_link})\n\n"
                    else:
                        data_markdown += f"File: {s['relevant_file']} ({s['relevant_lines_start']}-{s['relevant_lines_end']})\n\n"
                    if self.git_provider.is_supported("gfm_markdown"):
                        data_markdown += "<details> <summary> Example code:</summary>\n\n"
                        data_markdown += f"___\n\n"
                    language_name = "python"
                    if extension_s and (extension_s in extension_to_language):
                        language_name = extension_to_language[extension_s]
                    data_markdown += f"Existing code:\n```{language_name}\n{s['existing_code'].rstrip()}\n```\n"
                    data_markdown += f"Improved code:\n```{language_name}\n{s['improved_code'].rstrip()}\n```\n"
                    if self.git_provider.is_supported("gfm_markdown"):
                        data_markdown += "</details>\n"
                    data_markdown += "\n___\n\n"
                except Exception as e:
                    get_logger().error(f"Could not parse suggestion: {s}, error: {e}")
            self.git_provider.publish_comment(data_markdown)
        except Exception as e:
            get_logger().info(f"Failed to publish summarized code suggestions, error: {e}")
