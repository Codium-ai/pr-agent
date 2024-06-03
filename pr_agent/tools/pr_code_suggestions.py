import asyncio
import copy
import textwrap
from functools import partial
from typing import Dict, List
from jinja2 import Environment, StrictUndefined

from pr_agent.algo.ai_handlers.base_ai_handler import BaseAiHandler
from pr_agent.algo.ai_handlers.litellm_ai_handler import LiteLLMAIHandler
from pr_agent.algo.pr_processing import get_pr_diff, get_pr_multi_diffs, retry_with_fallback_models
from pr_agent.algo.token_handler import TokenHandler
from pr_agent.algo.utils import load_yaml, replace_code_tags, ModelType, show_relevant_configurations
from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider
from pr_agent.git_providers.git_provider import get_main_pr_language
from pr_agent.log import get_logger
from pr_agent.servers.help import HelpMessage
from pr_agent.tools.pr_description import insert_br_after_x_chars
import difflib

class PRCodeSuggestions:
    def __init__(self, pr_url: str, cli_mode=False, args: list = None,
                 ai_handler: partial[BaseAiHandler,] = LiteLLMAIHandler):

        self.git_provider = get_git_provider()(pr_url)
        self.main_language = get_main_pr_language(
            self.git_provider.get_languages(), self.git_provider.get_files()
        )

        # limit context specifically for the improve command, which has hard input to parse:
        if get_settings().pr_code_suggestions.max_context_tokens:
            MAX_CONTEXT_TOKENS_IMPROVE = get_settings().pr_code_suggestions.max_context_tokens
            if get_settings().config.max_model_tokens > MAX_CONTEXT_TOKENS_IMPROVE:
                get_logger().info(f"Setting max_model_tokens to {MAX_CONTEXT_TOKENS_IMPROVE} for PR improve")
                get_settings().config.max_model_tokens = MAX_CONTEXT_TOKENS_IMPROVE


        # extended mode
        try:
            self.is_extended = self._get_is_extended(args or [])
        except:
            self.is_extended = False
        if self.is_extended:
            num_code_suggestions = get_settings().pr_code_suggestions.num_code_suggestions_per_chunk
        else:
            num_code_suggestions = get_settings().pr_code_suggestions.num_code_suggestions

        self.ai_handler = ai_handler()
        self.ai_handler.main_pr_language = self.main_language
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

        self.progress = f"## Generating PR code suggestions\n\n"
        self.progress += f"""\nWork in progress ...<br>\n<img src="https://codium.ai/images/pr_agent/dual_ball_loading-crop.gif" width=48>"""
        self.progress_response = None

    async def run(self):
        try:
            get_logger().info('Generating code suggestions for PR...')
            relevant_configs = {'pr_code_suggestions': dict(get_settings().pr_code_suggestions),
                                'config': dict(get_settings().config)}
            get_logger().debug("Relevant configs", artifacts=relevant_configs)
            if get_settings().config.publish_output and get_settings().config.publish_output_progress:
                if self.git_provider.is_supported("gfm_markdown"):
                    self.progress_response = self.git_provider.publish_comment(self.progress)
                else:
                    self.git_provider.publish_comment("Preparing suggestions...", is_temporary=True)

            if not self.is_extended:
                data = await retry_with_fallback_models(self._prepare_prediction)
            else:
                data = await retry_with_fallback_models(self._prepare_prediction_extended)
            if not data:
                data = {"code_suggestions": []}

            if data is None or 'code_suggestions' not in data or not data['code_suggestions']:
                get_logger().error('No code suggestions found for PR.')
                pr_body = "## PR Code Suggestions ✨\n\nNo code suggestions found for PR."
                get_logger().debug(f"PR output", artifact=pr_body)
                if self.progress_response:
                    self.git_provider.edit_comment(self.progress_response, body=pr_body)
                else:
                    self.git_provider.publish_comment(pr_body)
                return

            if (not self.is_extended and get_settings().pr_code_suggestions.rank_suggestions) or \
                    (self.is_extended and get_settings().pr_code_suggestions.rank_extended_suggestions):
                get_logger().info('Ranking Suggestions...')
                data['code_suggestions'] = await self.rank_suggestions(data['code_suggestions'])

            if get_settings().config.publish_output:
                self.git_provider.remove_initial_comment()
                if ((not get_settings().pr_code_suggestions.commitable_code_suggestions) and
                        self.git_provider.is_supported("gfm_markdown")):

                    # generate summarized suggestions
                    pr_body = self.generate_summarized_suggestions(data)
                    get_logger().debug(f"PR output", artifact=pr_body)

                    # add usage guide
                    if get_settings().pr_code_suggestions.enable_help_text:
                        pr_body += "<hr>\n\n<details> <summary><strong>💡 Tool usage guide:</strong></summary><hr> \n\n"
                        pr_body += HelpMessage.get_improve_usage_guide()
                        pr_body += "\n</details>\n"

                    # Output the relevant configurations if enabled
                    if get_settings().get('config', {}).get('output_relevant_configurations', False):
                        pr_body += show_relevant_configurations(relevant_section='pr_code_suggestions')

                    if get_settings().pr_code_suggestions.persistent_comment:
                        final_update_message = False
                        self.git_provider.publish_persistent_comment(pr_body,
                                                                     initial_header="## PR Code Suggestions ✨",
                                                                     update_header=True,
                                                                     name="suggestions",
                                                                     final_update_message=final_update_message, )
                        if self.progress_response:
                            self.progress_response.delete()
                    else:

                        if self.progress_response:
                            self.git_provider.edit_comment(self.progress_response, body=pr_body)
                        else:
                            self.git_provider.publish_comment(pr_body)

                else:
                    self.push_inline_code_suggestions(data)
                    if self.progress_response:
                        self.progress_response.delete()
        except Exception as e:
            get_logger().error(f"Failed to generate code suggestions for PR, error: {e}")
            if self.progress_response:
                self.progress_response.delete()
            else:
                try:
                    self.git_provider.remove_initial_comment()
                    self.git_provider.publish_comment(f"Failed to generate code suggestions for PR")
                except Exception as e:
                    pass

    async def _prepare_prediction(self, model: str) -> dict:
        self.patches_diff = get_pr_diff(self.git_provider,
                                        self.token_handler,
                                        model,
                                        add_line_numbers_to_hunks=True,
                                        disable_extra_lines=True)

        if self.patches_diff:
            get_logger().debug(f"PR diff", artifact=self.patches_diff)
            self.prediction = await self._get_prediction(model, self.patches_diff)
        else:
            get_logger().error(f"Error getting PR diff")
            self.prediction = None

        data = self.prediction
        return data

    async def _get_prediction(self, model: str, patches_diff: str) -> dict:
        variables = copy.deepcopy(self.vars)
        variables["diff"] = patches_diff  # update diff
        environment = Environment(undefined=StrictUndefined)
        system_prompt = environment.from_string(get_settings().pr_code_suggestions_prompt.system).render(variables)
        user_prompt = environment.from_string(get_settings().pr_code_suggestions_prompt.user).render(variables)
        response, finish_reason = await self.ai_handler.chat_completion(model=model, temperature=0.2,
                                                                        system=system_prompt, user=user_prompt)

        # load suggestions from the AI response
        data = self._prepare_pr_code_suggestions(response)

        # self-reflect on suggestions
        if get_settings().pr_code_suggestions.self_reflect_on_suggestions:
            model = get_settings().config.model_turbo # use turbo model for self-reflection, since it is an easier task
            response_reflect = await self.self_reflect_on_suggestions(data["code_suggestions"], patches_diff, model=model)
            if response_reflect:
                response_reflect_yaml = load_yaml(response_reflect)
                code_suggestions_feedback = response_reflect_yaml["code_suggestions"]
                if len(code_suggestions_feedback) == len(data["code_suggestions"]):
                    for i, suggestion in enumerate(data["code_suggestions"]):
                        try:
                            suggestion["score"] = code_suggestions_feedback[i]["suggestion_score"]
                            suggestion["score_why"] = code_suggestions_feedback[i]["why"]
                        except Exception as e: #
                            get_logger().error(f"Error processing suggestion score {i}",
                                               artifact={"suggestion": suggestion,
                                                         "code_suggestions_feedback": code_suggestions_feedback[i]})
                            suggestion["score"] = 7
                            suggestion["score_why"] = ""
            else:
                # get_logger().error(f"Could not self-reflect on suggestions. using default score 7")
                for i, suggestion in enumerate(data["code_suggestions"]):
                    suggestion["score"] = 7
                    suggestion["score_why"] = ""

        return data

    @staticmethod
    def _truncate_if_needed(suggestion):
        max_code_suggestion_length = get_settings().get("PR_CODE_SUGGESTIONS.MAX_CODE_SUGGESTION_LENGTH", 0)
        suggestion_truncation_message = get_settings().get("PR_CODE_SUGGESTIONS.SUGGESTION_TRUNCATION_MESSAGE", "")
        if max_code_suggestion_length > 0:
            if len(suggestion['improved_code']) > max_code_suggestion_length:
                suggestion['improved_code'] = suggestion['improved_code'][:max_code_suggestion_length]
                suggestion['improved_code'] += f"\n{suggestion_truncation_message}"
                get_logger().info(f"Truncated suggestion from {len(suggestion['improved_code'])} "
                                      f"characters to {max_code_suggestion_length} characters")
        return suggestion

    def _prepare_pr_code_suggestions(self, predictions: str) -> Dict:
        data = load_yaml(predictions.strip(),
                         keys_fix_yaml=["relevant_file", "suggestion_content", "existing_code", "improved_code"])
        if isinstance(data, list):
            data = {'code_suggestions': data}

        # remove or edit invalid suggestions
        suggestion_list = []
        one_sentence_summary_list = []
        for i, suggestion in enumerate(data['code_suggestions']):
            try:
                if (not suggestion or 'one_sentence_summary' not in suggestion or
                        'label' not in suggestion or 'relevant_file' not in suggestion):
                    get_logger().debug(f"Skipping suggestion {i + 1}, because it is invalid: {suggestion}")
                    continue

                if suggestion['one_sentence_summary'] in one_sentence_summary_list:
                    get_logger().debug(f"Skipping suggestion {i + 1}, because it is a duplicate: {suggestion}")
                    continue

                if 'const' in suggestion['suggestion_content'] and 'instead' in suggestion['suggestion_content'] and 'let' in suggestion['suggestion_content']:
                    get_logger().debug(f"Skipping suggestion {i + 1}, because it uses 'const instead let': {suggestion}")
                    continue

                if ('existing_code' in suggestion) and ('improved_code' in suggestion):
                    if suggestion['existing_code'] == suggestion['improved_code']:
                        get_logger().debug(
                            f"edited improved suggestion {i + 1}, because equal to existing code: {suggestion['existing_code']}")
                        if get_settings().pr_code_suggestions.commitable_code_suggestions:
                            suggestion['improved_code'] = "" # we need 'existing_code' to locate the code in the PR
                        else:
                            suggestion['existing_code'] = ""
                    suggestion = self._truncate_if_needed(suggestion)
                    one_sentence_summary_list.append(suggestion['one_sentence_summary'])
                    suggestion_list.append(suggestion)
                else:
                    get_logger().info(
                        f"Skipping suggestion {i + 1}, because it does not contain 'existing_code' or 'improved_code': {suggestion}")
            except Exception as e:
                get_logger().error(f"Error processing suggestion {i + 1}: {suggestion}, error: {e}")
        data['code_suggestions'] = suggestion_list

        return data

    def push_inline_code_suggestions(self, data):
        code_suggestions = []

        if not data['code_suggestions']:
            get_logger().info('No suggestions found to improve this PR.')
            if self.progress_response:
                return self.git_provider.edit_comment(self.progress_response, body='No suggestions found to improve this PR.')
            else:
                return self.git_provider.publish_comment('No suggestions found to improve this PR.')

        for d in data['code_suggestions']:
            try:
                relevant_file = d['relevant_file'].strip()
                relevant_lines_start = int(d['relevant_lines_start'])  # absolute position
                relevant_lines_end = int(d['relevant_lines_end'])
                content = d['suggestion_content'].rstrip()
                new_code_snippet = d['improved_code'].rstrip()
                label = d['label'].strip()

                if new_code_snippet:
                    new_code_snippet = self.dedent_code(relevant_file, relevant_lines_start, new_code_snippet)

                if d.get('score'):
                    body = f"**Suggestion:** {content} [{label}, importance: {d.get('score')}]\n```suggestion\n" + new_code_snippet + "\n```"
                else:
                    body = f"**Suggestion:** {content} [{label}]\n```suggestion\n" + new_code_snippet + "\n```"
                code_suggestions.append({'body': body, 'relevant_file': relevant_file,
                                             'relevant_lines_start': relevant_lines_start,
                                             'relevant_lines_end': relevant_lines_end})
            except Exception:
                get_logger().info(f"Could not parse suggestion: {d}")

        is_successful = self.git_provider.publish_code_suggestions(code_suggestions)
        if not is_successful:
            get_logger().info("Failed to publish code suggestions, trying to publish each suggestion separately")
            for code_suggestion in code_suggestions:
                self.git_provider.publish_code_suggestions([code_suggestion])

    def dedent_code(self, relevant_file, relevant_lines_start, new_code_snippet):
        try:  # dedent code snippet
            self.diff_files = self.git_provider.diff_files if self.git_provider.diff_files \
                else self.git_provider.get_diff_files()
            original_initial_line = None
            for file in self.diff_files:
                if file.filename.strip() == relevant_file:
                    if file.head_file:  # in bitbucket, head_file is empty. toDo: fix this
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
            get_logger().error(f"Could not dedent code snippet for file {relevant_file}, error: {e}")

        return new_code_snippet

    def _get_is_extended(self, args: list[str]) -> bool:
        """Check if extended mode should be enabled by the `--extended` flag or automatically according to the configuration"""
        if any(["extended" in arg for arg in args]):
            get_logger().info("Extended mode is enabled by the `--extended` flag")
            return True
        if get_settings().pr_code_suggestions.auto_extended_mode:
            get_logger().info("Extended mode is enabled automatically based on the configuration toggle")
            return True
        return False

    async def _prepare_prediction_extended(self, model: str) -> dict:
        self.patches_diff_list = get_pr_multi_diffs(self.git_provider, self.token_handler, model,
                                                    max_calls=get_settings().pr_code_suggestions.max_number_of_calls)
        if self.patches_diff_list:
            get_logger().info(f"Number of PR chunk calls: {len(self.patches_diff_list)}")
            get_logger().debug(f"PR diff:", artifact=self.patches_diff_list)

            # parallelize calls to AI:
            if get_settings().pr_code_suggestions.parallel_calls:
                prediction_list = await asyncio.gather(
                    *[self._get_prediction(model, patches_diff) for patches_diff in self.patches_diff_list])
                self.prediction_list = prediction_list
            else:
                prediction_list = []
                for i, patches_diff in enumerate(self.patches_diff_list):
                    prediction = await self._get_prediction(model, patches_diff)
                    prediction_list.append(prediction)

            data = {"code_suggestions": []}
            for j, predictions in enumerate(prediction_list):  # each call adds an element to the list
                if "code_suggestions" in predictions:
                    score_threshold = max(1, get_settings().pr_code_suggestions.suggestions_score_threshold)
                    for i, prediction in enumerate(predictions["code_suggestions"]):
                        try:
                            if get_settings().pr_code_suggestions.self_reflect_on_suggestions:
                                score = int(prediction["score"])
                                if score >= score_threshold:
                                    data["code_suggestions"].append(prediction)
                                else:
                                    get_logger().info(
                                        f"Removing suggestions {i} from call {j}, because score is {score}, and score_threshold is {score_threshold}",
                                        artifact=prediction)
                            else:
                                data["code_suggestions"].append(prediction)
                        except Exception as e:
                            get_logger().error(f"Error getting PR diff for suggestion {i} in call {j}, error: {e}")
            self.data = data
        else:
            get_logger().error(f"Error getting PR diff")
            self.data = data = None
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
        if not data:
            return suggestion_list
        for suggestion in data:
            suggestion_list.append(suggestion)
        data_sorted = [[]] * len(suggestion_list)

        if len(suggestion_list) == 1:
            return suggestion_list

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
            response, finish_reason = await self.ai_handler.chat_completion(model=model, system=system_prompt,
                                                                            user=user_prompt)

            sort_order = load_yaml(response)
            for s in sort_order['Sort Order']:
                suggestion_number = s['suggestion number']
                importance_order = s['importance order']
                data_sorted[importance_order - 1] = suggestion_list[suggestion_number - 1]

            if get_settings().pr_code_suggestions.final_clip_factor != 1:
                max_len = max(
                    len(data_sorted),
                    get_settings().pr_code_suggestions.num_code_suggestions,
                    get_settings().pr_code_suggestions.num_code_suggestions_per_chunk,
                )
                new_len = int(0.5 + max_len * get_settings().pr_code_suggestions.final_clip_factor)
                if new_len < len(data_sorted):
                    data_sorted = data_sorted[:new_len]
        except Exception as e:
            if get_settings().config.verbosity_level >= 1:
                get_logger().info(f"Could not sort suggestions, error: {e}")
            data_sorted = suggestion_list

        return data_sorted

    def generate_summarized_suggestions(self, data: Dict) -> str:
        try:
            pr_body = "## PR Code Suggestions ✨\n\n"

            if len(data.get('code_suggestions', [])) == 0:
                pr_body += "No suggestions found to improve this PR."
                return pr_body

            language_extension_map_org = get_settings().language_extension_map_org
            extension_to_language = {}
            for language, extensions in language_extension_map_org.items():
                for ext in extensions:
                    extension_to_language[ext] = language

            pr_body = "## PR Code Suggestions ✨\n\n"

            pr_body += "<table>"
            header = f"Suggestion"
            delta = 66
            header += "&nbsp; " * delta
            if get_settings().pr_code_suggestions.self_reflect_on_suggestions:
                pr_body += f"""<thead><tr><td>Category</td><td align=left>{header}</td><td align=center>Score</td></tr>"""
            else:
                pr_body += f"""<thead><tr><td>Category</td><td align=left>{header}</td></tr>"""
            pr_body += """<tbody>"""
            suggestions_labels = dict()
            # add all suggestions related to each label
            for suggestion in data['code_suggestions']:
                label = suggestion['label'].strip().strip("'").strip('"')
                if label not in suggestions_labels:
                    suggestions_labels[label] = []
                suggestions_labels[label].append(suggestion)

            # sort suggestions_labels by the suggestion with the highest score
            if get_settings().pr_code_suggestions.self_reflect_on_suggestions:
                suggestions_labels = dict(sorted(suggestions_labels.items(), key=lambda x: max([s['score'] for s in x[1]]), reverse=True))
                # sort the suggestions inside each label group by score
                for label, suggestions in suggestions_labels.items():
                    suggestions_labels[label] = sorted(suggestions, key=lambda x: x['score'], reverse=True)


            for label, suggestions in suggestions_labels.items():
                num_suggestions=len(suggestions)
                pr_body += f"""<tr><td rowspan={num_suggestions}><strong>{label.capitalize()}</strong></td>\n"""
                for i, suggestion in enumerate(suggestions):

                    relevant_file = suggestion['relevant_file'].strip()
                    relevant_lines_start = int(suggestion['relevant_lines_start'])
                    relevant_lines_end = int(suggestion['relevant_lines_end'])
                    range_str = ""
                    if relevant_lines_start == relevant_lines_end:
                        range_str = f"[{relevant_lines_start}]"
                    else:
                        range_str = f"[{relevant_lines_start}-{relevant_lines_end}]"

                    try:
                        code_snippet_link = self.git_provider.get_line_link(relevant_file, relevant_lines_start,
                                                                            relevant_lines_end)
                    except:
                        code_snippet_link = ""
                    # add html table for each suggestion

                    suggestion_content = suggestion['suggestion_content'].rstrip().rstrip()

                    suggestion_content = insert_br_after_x_chars(suggestion_content, 90)
                    # pr_body += f"<tr><td><details><summary>{suggestion_content}</summary>"
                    existing_code = suggestion['existing_code'].rstrip()+"\n"
                    improved_code = suggestion['improved_code'].rstrip()+"\n"

                    diff = difflib.unified_diff(existing_code.split('\n'),
                                                improved_code.split('\n'), n=999)
                    patch_orig = "\n".join(diff)
                    patch = "\n".join(patch_orig.splitlines()[5:]).strip('\n')

                    example_code = ""
                    example_code += f"```diff\n{patch}\n```\n"
                    if i==0:
                        pr_body += f"""<td>\n\n"""
                    else:
                        pr_body += f"""<tr><td>\n\n"""
                    suggestion_summary = suggestion['one_sentence_summary'].strip().rstrip('.')
                    if '`' in suggestion_summary:
                        suggestion_summary = replace_code_tags(suggestion_summary)

                    pr_body += f"""\n\n<details><summary>{suggestion_summary}</summary>\n\n___\n\n"""
                    pr_body += f"""
**{suggestion_content}**
    
[{relevant_file} {range_str}]({code_snippet_link})

{example_code}                   
"""
                    if get_settings().pr_code_suggestions.self_reflect_on_suggestions:
                        pr_body +=f"\n\n<details><summary><b>Suggestion importance[1-10]: {suggestion['score']}</b></summary>\n\n"
                        pr_body += f"Why: {suggestion['score_why']}\n\n"
                        pr_body += f"</details>"

                    pr_body += f"</details>"

                    # # add another column for 'score'
                    if get_settings().pr_code_suggestions.self_reflect_on_suggestions:
                        pr_body += f"</td><td align=center>{suggestion['score']}\n\n"

                    pr_body += f"</td></tr>"


                # pr_body += "</details>"
                # pr_body += """</td></tr>"""
            pr_body += """</tr></tbody></table>"""
            return pr_body
        except Exception as e:
            get_logger().info(f"Failed to publish summarized code suggestions, error: {e}")
            return ""

    async def self_reflect_on_suggestions(self, suggestion_list: List, patches_diff: str, model: str) -> str:
        if not suggestion_list:
            return ""

        try:
            suggestion_str = ""
            for i, suggestion in enumerate(suggestion_list):
                suggestion_str += f"suggestion {i + 1}: " + str(suggestion) + '\n\n'

            variables = {'suggestion_list': suggestion_list,
                         'suggestion_str': suggestion_str,
                         "diff": patches_diff,
                         'num_code_suggestions': len(suggestion_list)}
            environment = Environment(undefined=StrictUndefined)
            system_prompt_reflect = environment.from_string(get_settings().pr_code_suggestions_reflect_prompt.system).render(
                variables)
            user_prompt_reflect = environment.from_string(get_settings().pr_code_suggestions_reflect_prompt.user).render(variables)
            with get_logger().contextualize(command="self_reflect_on_suggestions"):
                response_reflect, finish_reason_reflect = await self.ai_handler.chat_completion(model=model,
                                                                                system=system_prompt_reflect,
                                                                                user=user_prompt_reflect)
        except Exception as e:
            get_logger().info(f"Could not reflect on suggestions, error: {e}")
            return ""
        return response_reflect