import asyncio
import copy
import difflib
import re
import textwrap
import traceback
from functools import partial
from typing import Dict, List

from jinja2 import Environment, StrictUndefined

from pr_agent.algo.ai_handlers.base_ai_handler import BaseAiHandler
from pr_agent.algo.ai_handlers.litellm_ai_handler import LiteLLMAIHandler
from pr_agent.algo.pr_processing import (add_ai_metadata_to_diff_files,
                                         get_pr_diff, get_pr_multi_diffs,
                                         retry_with_fallback_models)
from pr_agent.algo.token_handler import TokenHandler
from pr_agent.algo.utils import (ModelType, load_yaml, replace_code_tags,
                                 show_relevant_configurations)
from pr_agent.config_loader import get_settings
from pr_agent.git_providers import (AzureDevopsProvider, GithubProvider,
                                    GitLabProvider, get_git_provider,
                                    get_git_provider_with_context)
from pr_agent.git_providers.git_provider import get_main_pr_language
from pr_agent.log import get_logger
from pr_agent.servers.help import HelpMessage
from pr_agent.tools.pr_description import insert_br_after_x_chars


class PRCodeSuggestions:
    def __init__(self, pr_url: str, cli_mode=False, args: list = None,
                 ai_handler: partial[BaseAiHandler,] = LiteLLMAIHandler):

        self.git_provider = get_git_provider_with_context(pr_url)
        self.main_language = get_main_pr_language(
            self.git_provider.get_languages(), self.git_provider.get_files()
        )

        # limit context specifically for the improve command, which has hard input to parse:
        if get_settings().pr_code_suggestions.max_context_tokens:
            MAX_CONTEXT_TOKENS_IMPROVE = get_settings().pr_code_suggestions.max_context_tokens
            if get_settings().config.max_model_tokens > MAX_CONTEXT_TOKENS_IMPROVE:
                get_logger().info(f"Setting max_model_tokens to {MAX_CONTEXT_TOKENS_IMPROVE} for PR improve")
                get_settings().config.max_model_tokens_original = get_settings().config.max_model_tokens
                get_settings().config.max_model_tokens = MAX_CONTEXT_TOKENS_IMPROVE

        # extended mode
        try:
            self.is_extended = self._get_is_extended(args or [])
        except:
            self.is_extended = False
        num_code_suggestions = int(get_settings().pr_code_suggestions.num_code_suggestions_per_chunk)


        self.ai_handler = ai_handler()
        self.ai_handler.main_pr_language = self.main_language
        self.patches_diff = None
        self.prediction = None
        self.pr_url = pr_url
        self.cli_mode = cli_mode
        self.pr_description, self.pr_description_files = (
            self.git_provider.get_pr_description(split_changes_walkthrough=True))
        if (self.pr_description_files and get_settings().get("config.is_auto_command", False) and
                get_settings().get("config.enable_ai_metadata", False)):
            add_ai_metadata_to_diff_files(self.git_provider, self.pr_description_files)
            get_logger().debug(f"AI metadata added to the this command")
        else:
            get_settings().set("config.enable_ai_metadata", False)
            get_logger().debug(f"AI metadata is disabled for this command")

        self.vars = {
            "title": self.git_provider.pr.title,
            "branch": self.git_provider.get_pr_branch(),
            "description": self.pr_description,
            "language": self.main_language,
            "diff": "",  # empty diff for initial calculation
            "diff_no_line_numbers": "",  # empty diff for initial calculation
            "num_code_suggestions": num_code_suggestions,
            "extra_instructions": get_settings().pr_code_suggestions.extra_instructions,
            "commit_messages_str": self.git_provider.get_commit_messages(),
            "relevant_best_practices": "",
            "is_ai_metadata": get_settings().get("config.enable_ai_metadata", False),
            "focus_only_on_problems": get_settings().get("pr_code_suggestions.focus_only_on_problems", False),
        }
        self.pr_code_suggestions_prompt_system = get_settings().pr_code_suggestions_prompt.system

        self.token_handler = TokenHandler(self.git_provider.pr,
                                          self.vars,
                                          self.pr_code_suggestions_prompt_system,
                                          get_settings().pr_code_suggestions_prompt.user)

        self.progress = f"## Generating PR code suggestions\n\n"
        self.progress += f"""\nWork in progress ...<br>\n<img src="https://codium.ai/images/pr_agent/dual_ball_loading-crop.gif" width=48>"""
        self.progress_response = None

    async def run(self):
        try:
            if not self.git_provider.get_files():
                get_logger().info(f"PR has no files: {self.pr_url}, skipping code suggestions")
                return None

            get_logger().info('Generating code suggestions for PR...')
            relevant_configs = {'pr_code_suggestions': dict(get_settings().pr_code_suggestions),
                                'config': dict(get_settings().config)}
            get_logger().debug("Relevant configs", artifacts=relevant_configs)
            if (get_settings().config.publish_output and get_settings().config.publish_output_progress and
                    not get_settings().config.get('is_auto_command', False)):
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

            if (data is None or 'code_suggestions' not in data or not data['code_suggestions']):
                pr_body = "## PR Code Suggestions ✨\n\nNo code suggestions found for the PR."
                get_logger().warning('No code suggestions found for the PR.')
                if get_settings().config.publish_output and get_settings().config.publish_output_no_suggestions:
                    get_logger().debug(f"PR output", artifact=pr_body)
                    if self.progress_response:
                        self.git_provider.edit_comment(self.progress_response, body=pr_body)
                    else:
                        self.git_provider.publish_comment(pr_body)
                else:
                    get_settings().data = {"artifact": ""}
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

                    # require self-review
                    if get_settings().pr_code_suggestions.demand_code_suggestions_self_review:
                        text = get_settings().pr_code_suggestions.code_suggestions_self_review_text
                        pr_body += f"\n\n- [ ]  {text}"
                        if get_settings().pr_code_suggestions.approve_pr_on_self_review:
                            pr_body += ' <!-- approve pr self-review -->'

                    # add usage guide
                    if (get_settings().pr_code_suggestions.enable_chat_text and get_settings().config.is_auto_command
                            and isinstance(self.git_provider, GithubProvider)):
                        pr_body += "\n\n>💡 Need additional feedback ? start a [PR chat](https://chromewebstore.google.com/detail/ephlnjeghhogofkifjloamocljapahnl) \n\n"
                    if get_settings().pr_code_suggestions.enable_help_text:
                        pr_body += "<hr>\n\n<details> <summary><strong>💡 Tool usage guide:</strong></summary><hr> \n\n"
                        pr_body += HelpMessage.get_improve_usage_guide()
                        pr_body += "\n</details>\n"

                    # Output the relevant configurations if enabled
                    if get_settings().get('config', {}).get('output_relevant_configurations', False):
                        pr_body += show_relevant_configurations(relevant_section='pr_code_suggestions')

                    # publish the PR comment
                    if get_settings().pr_code_suggestions.persistent_comment:
                        final_update_message = False
                        self.publish_persistent_comment_with_history(pr_body,
                                                                     initial_header="## PR Code Suggestions ✨",
                                                                     update_header=True,
                                                                     name="suggestions",
                                                                     final_update_message=final_update_message,
                                                                     max_previous_comments=get_settings().pr_code_suggestions.max_history_len,
                                                                     progress_response=self.progress_response)
                    else:
                        if self.progress_response:
                            self.git_provider.edit_comment(self.progress_response, body=pr_body)
                        else:
                            self.git_provider.publish_comment(pr_body)

                    # dual publishing mode
                    if int(get_settings().pr_code_suggestions.dual_publishing_score_threshold) > 0:
                        data_above_threshold = {'code_suggestions': []}
                        try:
                            for suggestion in data['code_suggestions']:
                                if int(suggestion.get('score', 0)) >= int(get_settings().pr_code_suggestions.dual_publishing_score_threshold) \
                                        and suggestion.get('improved_code'):
                                    data_above_threshold['code_suggestions'].append(suggestion)
                                    if not data_above_threshold['code_suggestions'][-1]['existing_code']:
                                        get_logger().info(f'Identical existing and improved code for dual publishing found')
                                        data_above_threshold['code_suggestions'][-1]['existing_code'] = suggestion[
                                            'improved_code']
                            if data_above_threshold['code_suggestions']:
                                get_logger().info(
                                    f"Publishing {len(data_above_threshold['code_suggestions'])} suggestions in dual publishing mode")
                                self.push_inline_code_suggestions(data_above_threshold)
                        except Exception as e:
                            get_logger().error(f"Failed to publish dual publishing suggestions, error: {e}")
                else:
                    self.push_inline_code_suggestions(data)
                    if self.progress_response:
                        self.git_provider.remove_comment(self.progress_response)
            else:
                get_logger().info('Code suggestions generated for PR, but not published since publish_output is False.')
                get_settings().data = {"artifact": data}
                return
        except Exception as e:
            get_logger().error(f"Failed to generate code suggestions for PR, error: {e}",
                               artifact={"traceback": traceback.format_exc()})
            if get_settings().config.publish_output:
                if self.progress_response:
                    self.progress_response.delete()
                else:
                    try:
                        self.git_provider.remove_initial_comment()
                        self.git_provider.publish_comment(f"Failed to generate code suggestions for PR")
                    except Exception as e:
                        pass

    def publish_persistent_comment_with_history(self, pr_comment: str,
                                                initial_header: str,
                                                update_header: bool = True,
                                                name='review',
                                                final_update_message=True,
                                                max_previous_comments=4,
                                                progress_response=None):

        if isinstance(self.git_provider, AzureDevopsProvider): # get_latest_commit_url is not supported yet
            if progress_response:
                self.git_provider.edit_comment(progress_response, pr_comment)
            else:
                self.git_provider.publish_comment(pr_comment)
            return

        history_header = f"#### Previous suggestions\n"
        last_commit_num = self.git_provider.get_latest_commit_url().split('/')[-1][:7]
        latest_suggestion_header = f"Latest suggestions up to {last_commit_num}"
        latest_commit_html_comment = f"<!-- {last_commit_num} -->"
        found_comment = None

        if max_previous_comments > 0:
            try:
                prev_comments = list(self.git_provider.get_issue_comments())
                for comment in prev_comments:
                    if comment.body.startswith(initial_header):
                        prev_suggestions = comment.body
                        found_comment = comment
                        comment_url = self.git_provider.get_comment_url(comment)

                        if history_header.strip() not in comment.body:
                            # no history section
                            # extract everything between <table> and </table> in comment.body including <table> and </table>
                            table_index = comment.body.find("<table>")
                            if table_index == -1:
                                self.git_provider.edit_comment(comment, pr_comment)
                                continue
                            # find http link from comment.body[:table_index]
                            up_to_commit_txt = self.extract_link(comment.body[:table_index])
                            prev_suggestion_table = comment.body[
                                                    table_index:comment.body.rfind("</table>") + len("</table>")]

                            tick = "✅ " if "✅" in prev_suggestion_table else ""
                            # surround with details tag
                            prev_suggestion_table = f"<details><summary>{tick}{name.capitalize()}{up_to_commit_txt}</summary>\n<br>{prev_suggestion_table}\n\n</details>"

                            new_suggestion_table = pr_comment.replace(initial_header, "").strip()

                            pr_comment_updated = f"{initial_header}\n{latest_commit_html_comment}\n\n"
                            pr_comment_updated += f"{latest_suggestion_header}\n{new_suggestion_table}\n\n___\n\n"
                            pr_comment_updated += f"{history_header}{prev_suggestion_table}\n"
                        else:
                            # get the text of the previous suggestions until the latest commit
                            sections = prev_suggestions.split(history_header.strip())
                            latest_table = sections[0].strip()
                            prev_suggestion_table = sections[1].replace(history_header, "").strip()

                            # get text after the latest_suggestion_header in comment.body
                            table_ind = latest_table.find("<table>")
                            up_to_commit_txt = self.extract_link(latest_table[:table_ind])

                            latest_table = latest_table[table_ind:latest_table.rfind("</table>") + len("</table>")]
                            # enforce max_previous_comments
                            count = prev_suggestions.count(f"\n<details><summary>{name.capitalize()}")
                            count += prev_suggestions.count(f"\n<details><summary>✅ {name.capitalize()}")
                            if count >= max_previous_comments:
                                # remove the oldest suggestion
                                prev_suggestion_table = prev_suggestion_table[:prev_suggestion_table.rfind(
                                    f"<details><summary>{name.capitalize()} up to commit")]

                            tick = "✅ " if "✅" in latest_table else ""
                            # Add to the prev_suggestions section
                            last_prev_table = f"\n<details><summary>{tick}{name.capitalize()}{up_to_commit_txt}</summary>\n<br>{latest_table}\n\n</details>"
                            prev_suggestion_table = last_prev_table + "\n" + prev_suggestion_table

                            new_suggestion_table = pr_comment.replace(initial_header, "").strip()

                            pr_comment_updated = f"{initial_header}\n"
                            pr_comment_updated += f"{latest_commit_html_comment}\n\n"
                            pr_comment_updated += f"{latest_suggestion_header}\n\n{new_suggestion_table}\n\n"
                            pr_comment_updated += "___\n\n"
                            pr_comment_updated += f"{history_header}\n"
                            pr_comment_updated += f"{prev_suggestion_table}\n"

                        get_logger().info(f"Persistent mode - updating comment {comment_url} to latest {name} message")
                        if progress_response:  # publish to 'progress_response' comment, because it refreshes immediately
                            self.git_provider.edit_comment(progress_response, pr_comment_updated)
                            self.git_provider.remove_comment(comment)
                        else:
                            self.git_provider.edit_comment(comment, pr_comment_updated)
                        return
            except Exception as e:
                get_logger().exception(f"Failed to update persistent review, error: {e}")
                pass

        # if we are here, we did not find a previous comment to update
        body = pr_comment.replace(initial_header, "").strip()
        pr_comment = f"{initial_header}\n\n{latest_commit_html_comment}\n\n{body}\n\n"
        if progress_response:
            self.git_provider.edit_comment(progress_response, pr_comment)
        else:
            self.git_provider.publish_comment(pr_comment)

    def extract_link(self, s):
        r = re.compile(r"<!--.*?-->")
        match = r.search(s)

        up_to_commit_txt = ""
        if match:
            up_to_commit_txt = f" up to commit {match.group(0)[4:-3].strip()}"
        return up_to_commit_txt

    async def _prepare_prediction(self, model: str) -> dict:
        self.patches_diff = get_pr_diff(self.git_provider,
                                        self.token_handler,
                                        model,
                                        add_line_numbers_to_hunks=True,
                                        disable_extra_lines=False)
        self.patches_diff_list = [self.patches_diff]
        self.patches_diff_no_line_number = self.remove_line_numbers([self.patches_diff])[0]

        if self.patches_diff:
            get_logger().debug(f"PR diff", artifact=self.patches_diff)
            self.prediction = await self._get_prediction(model, self.patches_diff, self.patches_diff_no_line_number)
        else:
            get_logger().warning(f"Empty PR diff")
            self.prediction = None

        data = self.prediction
        return data

    async def _get_prediction(self, model: str, patches_diff: str, patches_diff_no_line_number: str) -> dict:
        variables = copy.deepcopy(self.vars)
        variables["diff"] = patches_diff  # update diff
        variables["diff_no_line_numbers"] = patches_diff_no_line_number  # update diff
        environment = Environment(undefined=StrictUndefined)
        system_prompt = environment.from_string(self.pr_code_suggestions_prompt_system).render(variables)
        user_prompt = environment.from_string(get_settings().pr_code_suggestions_prompt.user).render(variables)
        response, finish_reason = await self.ai_handler.chat_completion(
            model=model, temperature=get_settings().config.temperature, system=system_prompt, user=user_prompt)
        if not get_settings().config.publish_output:
            get_settings().system_prompt = system_prompt
            get_settings().user_prompt = user_prompt

        # load suggestions from the AI response
        data = self._prepare_pr_code_suggestions(response)

        # self-reflect on suggestions (mandatory, since line numbers are generated now here)
        model_reflection = get_settings().config.model
        response_reflect = await self.self_reflect_on_suggestions(data["code_suggestions"],
                                                                  patches_diff, model=model_reflection)
        if response_reflect:
            response_reflect_yaml = load_yaml(response_reflect)
            code_suggestions_feedback = response_reflect_yaml["code_suggestions"]
            if len(code_suggestions_feedback) == len(data["code_suggestions"]):
                for i, suggestion in enumerate(data["code_suggestions"]):
                    try:
                        suggestion["score"] = code_suggestions_feedback[i]["suggestion_score"]
                        suggestion["score_why"] = code_suggestions_feedback[i]["why"]

                        if 'relevant_lines_start' not in suggestion:
                            relevant_lines_start = code_suggestions_feedback[i].get('relevant_lines_start', -1)
                            relevant_lines_end = code_suggestions_feedback[i].get('relevant_lines_end', -1)
                            suggestion['relevant_lines_start'] = relevant_lines_start
                            suggestion['relevant_lines_end'] = relevant_lines_end
                            if relevant_lines_start < 0 or relevant_lines_end < 0:
                                suggestion["score"] = 0

                        try:
                            if get_settings().config.publish_output:
                                suggestion_statistics_dict = {'score': int(suggestion["score"]),
                                                              'label': suggestion["label"].lower().strip()}
                                get_logger().info(f"PR-Agent suggestions statistics",
                                                  statistics=suggestion_statistics_dict, analytics=True)
                        except Exception as e:
                            get_logger().error(f"Failed to log suggestion statistics, error: {e}")
                            pass

                    except Exception as e:  #
                        get_logger().error(f"Error processing suggestion score {i}",
                                           artifact={"suggestion": suggestion,
                                                     "code_suggestions_feedback": code_suggestions_feedback[i]})
                        suggestion["score"] = 7
                        suggestion["score_why"] = ""

                    # if the before and after code is the same, clear one of them
                    try:
                        if suggestion['existing_code'] == suggestion['improved_code']:
                            get_logger().debug(
                                f"edited improved suggestion {i + 1}, because equal to existing code: {suggestion['existing_code']}")
                            if get_settings().pr_code_suggestions.commitable_code_suggestions:
                                suggestion['improved_code'] = ""  # we need 'existing_code' to locate the code in the PR
                            else:
                                suggestion['existing_code'] = ""
                    except Exception as e:
                        get_logger().error(f"Error processing suggestion {i + 1}, error: {e}")
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
                get_logger().info(f"Truncated suggestion from {len(suggestion['improved_code'])} "
                                  f"characters to {max_code_suggestion_length} characters")
                suggestion['improved_code'] = suggestion['improved_code'][:max_code_suggestion_length]
                suggestion['improved_code'] += f"\n{suggestion_truncation_message}"
        return suggestion

    def _prepare_pr_code_suggestions(self, predictions: str) -> Dict:
        data = load_yaml(predictions.strip(),
                         keys_fix_yaml=["relevant_file", "suggestion_content", "existing_code", "improved_code"],
                         first_key="code_suggestions", last_key="label")
        if isinstance(data, list):
            data = {'code_suggestions': data}

        # remove or edit invalid suggestions
        suggestion_list = []
        one_sentence_summary_list = []
        for i, suggestion in enumerate(data['code_suggestions']):
            try:
                needed_keys = ['one_sentence_summary', 'label', 'relevant_file']
                is_valid_keys = True
                for key in needed_keys:
                    if key not in suggestion:
                        is_valid_keys = False
                        get_logger().debug(
                            f"Skipping suggestion {i + 1}, because it does not contain '{key}':\n'{suggestion}")
                        break
                if not is_valid_keys:
                    continue

                if get_settings().get("pr_code_suggestions.focus_only_on_problems", False):
                    CRITICAL_LABEL = 'critical'
                    if CRITICAL_LABEL in suggestion['label'].lower(): # we want the published labels to be less declarative
                        suggestion['label'] = 'possible issue'

                if suggestion['one_sentence_summary'] in one_sentence_summary_list:
                    get_logger().debug(f"Skipping suggestion {i + 1}, because it is a duplicate: {suggestion}")
                    continue

                if 'const' in suggestion['suggestion_content'] and 'instead' in suggestion[
                    'suggestion_content'] and 'let' in suggestion['suggestion_content']:
                    get_logger().debug(
                        f"Skipping suggestion {i + 1}, because it uses 'const instead let': {suggestion}")
                    continue

                if ('existing_code' in suggestion) and ('improved_code' in suggestion):
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
                return self.git_provider.edit_comment(self.progress_response,
                                                      body='No suggestions found to improve this PR.')
            else:
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

                if d.get('score'):
                    body = f"**Suggestion:** {content} [{label}, importance: {d.get('score')}]\n```suggestion\n" + new_code_snippet + "\n```"
                else:
                    body = f"**Suggestion:** {content} [{label}]\n```suggestion\n" + new_code_snippet + "\n```"
                code_suggestions.append({'body': body, 'relevant_file': relevant_file,
                                         'relevant_lines_start': relevant_lines_start,
                                         'relevant_lines_end': relevant_lines_end,
                                         'original_suggestion': d})
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
                    if file.head_file:
                        file_lines = file.head_file.splitlines()
                        if relevant_lines_start > len(file_lines):
                            get_logger().warning(
                                "Could not dedent code snippet, because relevant_lines_start is out of range",
                                artifact={'filename': file.filename,
                                          'file_content': file.head_file,
                                          'relevant_lines_start': relevant_lines_start,
                                          'new_code_snippet': new_code_snippet})
                            return new_code_snippet
                        else:
                            original_initial_line = file_lines[relevant_lines_start - 1]
                    else:
                        get_logger().warning("Could not dedent code snippet, because head_file is missing",
                                             artifact={'filename': file.filename,
                                                       'relevant_lines_start': relevant_lines_start,
                                                       'new_code_snippet': new_code_snippet})
                        return new_code_snippet
                    break
            if original_initial_line:
                suggested_initial_line = new_code_snippet.splitlines()[0]
                original_initial_spaces = len(original_initial_line) - len(original_initial_line.lstrip())
                suggested_initial_spaces = len(suggested_initial_line) - len(suggested_initial_line.lstrip())
                delta_spaces = original_initial_spaces - suggested_initial_spaces
                if delta_spaces > 0:
                    new_code_snippet = textwrap.indent(new_code_snippet, delta_spaces * " ").rstrip('\n')
        except Exception as e:
            get_logger().error(f"Error when dedenting code snippet for file {relevant_file}, error: {e}")

        return new_code_snippet

    def _get_is_extended(self, args: list[str]) -> bool:
        """Check if extended mode should be enabled by the `--extended` flag or automatically according to the configuration"""
        if any(["extended" in arg for arg in args]):
            get_logger().info("Extended mode is enabled by the `--extended` flag")
            return True
        if get_settings().pr_code_suggestions.auto_extended_mode:
            # get_logger().info("Extended mode is enabled automatically based on the configuration toggle")
            return True
        return False

    def remove_line_numbers(self, patches_diff_list: List[str]) -> List[str]:
        # create a copy of the patches_diff_list, without line numbers for '__new hunk__' sections
        try:
            self.patches_diff_list_no_line_numbers = []
            for patches_diff in self.patches_diff_list:
                patches_diff_lines = patches_diff.splitlines()
                for i, line in enumerate(patches_diff_lines):
                    if line.strip():
                        if line[0].isdigit():
                            # find the first letter in the line that starts with a valid letter
                            for j, char in enumerate(line):
                                if not char.isdigit():
                                    patches_diff_lines[i] = line[j + 1:]
                                    break
                self.patches_diff_list_no_line_numbers.append('\n'.join(patches_diff_lines))
            return self.patches_diff_list_no_line_numbers
        except Exception as e:
            get_logger().error(f"Error removing line numbers from patches_diff_list, error: {e}")
            return patches_diff_list

    async def _prepare_prediction_extended(self, model: str) -> dict:
        self.patches_diff_list = get_pr_multi_diffs(self.git_provider, self.token_handler, model,
                                                    max_calls=get_settings().pr_code_suggestions.max_number_of_calls)

        # create a copy of the patches_diff_list, without line numbers for '__new hunk__' sections
        self.patches_diff_list_no_line_numbers = self.remove_line_numbers(self.patches_diff_list)

        if self.patches_diff_list:
            get_logger().info(f"Number of PR chunk calls: {len(self.patches_diff_list)}")
            get_logger().debug(f"PR diff:", artifact=self.patches_diff_list)

            # parallelize calls to AI:
            if get_settings().pr_code_suggestions.parallel_calls:
                prediction_list = await asyncio.gather(
                    *[self._get_prediction(model, patches_diff, patches_diff_no_line_numbers) for
                      patches_diff, patches_diff_no_line_numbers in
                      zip(self.patches_diff_list, self.patches_diff_list_no_line_numbers)])
                self.prediction_list = prediction_list
            else:
                prediction_list = []
                for patches_diff, patches_diff_no_line_numbers in zip(self.patches_diff_list, self.patches_diff_list_no_line_numbers):
                    prediction = await self._get_prediction(model, patches_diff, patches_diff_no_line_numbers)
                    prediction_list.append(prediction)

            data = {"code_suggestions": []}
            for j, predictions in enumerate(prediction_list):  # each call adds an element to the list
                if "code_suggestions" in predictions:
                    score_threshold = max(1, int(get_settings().pr_code_suggestions.suggestions_score_threshold))
                    for i, prediction in enumerate(predictions["code_suggestions"]):
                        try:
                            score = int(prediction.get("score", 1))
                            if score >= score_threshold:
                                data["code_suggestions"].append(prediction)
                            else:
                                get_logger().info(
                                    f"Removing suggestions {i} from call {j}, because score is {score}, and score_threshold is {score_threshold}",
                                    artifact=prediction)
                        except Exception as e:
                            get_logger().error(f"Error getting PR diff for suggestion {i} in call {j}, error: {e}",
                                               artifact={"prediction": prediction})
            self.data = data
        else:
            get_logger().warning(f"Empty PR diff list")
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
                    int(get_settings().pr_code_suggestions.num_code_suggestions_per_chunk),
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

            if get_settings().pr_code_suggestions.enable_intro_text and get_settings().config.is_auto_command:
                pr_body += "Explore these optional code suggestions:\n\n"

            language_extension_map_org = get_settings().language_extension_map_org
            extension_to_language = {}
            for language, extensions in language_extension_map_org.items():
                for ext in extensions:
                    extension_to_language[ext] = language

            pr_body += "<table>"
            header = f"Suggestion"
            delta = 66
            header += "&nbsp; " * delta
            pr_body += f"""<thead><tr><td>Category</td><td align=left>{header}</td><td align=center>Score</td></tr>"""
            pr_body += """<tbody>"""
            suggestions_labels = dict()
            # add all suggestions related to each label
            for suggestion in data['code_suggestions']:
                label = suggestion['label'].strip().strip("'").strip('"')
                if label not in suggestions_labels:
                    suggestions_labels[label] = []
                suggestions_labels[label].append(suggestion)

            # sort suggestions_labels by the suggestion with the highest score
            suggestions_labels = dict(
                sorted(suggestions_labels.items(), key=lambda x: max([s['score'] for s in x[1]]), reverse=True))
            # sort the suggestions inside each label group by score
            for label, suggestions in suggestions_labels.items():
                suggestions_labels[label] = sorted(suggestions, key=lambda x: x['score'], reverse=True)

            counter_suggestions = 0
            for label, suggestions in suggestions_labels.items():
                num_suggestions = len(suggestions)
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

                    suggestion_content = suggestion['suggestion_content'].rstrip()
                    CHAR_LIMIT_PER_LINE = 84
                    suggestion_content = insert_br_after_x_chars(suggestion_content, CHAR_LIMIT_PER_LINE)
                    # pr_body += f"<tr><td><details><summary>{suggestion_content}</summary>"
                    existing_code = suggestion['existing_code'].rstrip() + "\n"
                    improved_code = suggestion['improved_code'].rstrip() + "\n"

                    diff = difflib.unified_diff(existing_code.split('\n'),
                                                improved_code.split('\n'), n=999)
                    patch_orig = "\n".join(diff)
                    patch = "\n".join(patch_orig.splitlines()[5:]).strip('\n')

                    example_code = ""
                    example_code += f"```diff\n{patch.rstrip()}\n```\n"
                    if i == 0:
                        pr_body += f"""<td>\n\n"""
                    else:
                        pr_body += f"""<tr><td>\n\n"""
                    suggestion_summary = suggestion['one_sentence_summary'].strip().rstrip('.')
                    if "'<" in suggestion_summary and ">'" in suggestion_summary:
                        # escape the '<' and '>' characters, otherwise they are interpreted as html tags
                        get_logger().info(f"Escaped suggestion summary: {suggestion_summary}")
                        suggestion_summary = suggestion_summary.replace("'<", "`<")
                        suggestion_summary = suggestion_summary.replace(">'", ">`")
                    if '`' in suggestion_summary:
                        suggestion_summary = replace_code_tags(suggestion_summary)

                    pr_body += f"""\n\n<details><summary>{suggestion_summary}</summary>\n\n___\n\n"""
                    pr_body += f"""
**{suggestion_content}**

[{relevant_file} {range_str}]({code_snippet_link})

{example_code.rstrip()}
"""
                    pr_body += f"<details><summary>Suggestion importance[1-10]: {suggestion['score']}</summary>\n\n"
                    pr_body += f"Why: {suggestion['score_why']}\n\n"
                    pr_body += f"</details>"

                    pr_body += f"</details>"

                    # # add another column for 'score'
                    pr_body += f"</td><td align=center>{suggestion['score']}\n\n"

                    pr_body += f"</td></tr>"
                    counter_suggestions += 1

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
                         'num_code_suggestions': len(suggestion_list),
                         "is_ai_metadata": get_settings().get("config.enable_ai_metadata", False)}
            environment = Environment(undefined=StrictUndefined)
            system_prompt_reflect = environment.from_string(
                get_settings().pr_code_suggestions_reflect_prompt.system).render(
                variables)
            user_prompt_reflect = environment.from_string(
                get_settings().pr_code_suggestions_reflect_prompt.user).render(variables)
            with get_logger().contextualize(command="self_reflect_on_suggestions"):
                response_reflect, finish_reason_reflect = await self.ai_handler.chat_completion(model=model,
                                                                                                system=system_prompt_reflect,
                                                                                                user=user_prompt_reflect)
        except Exception as e:
            get_logger().info(f"Could not reflect on suggestions, error: {e}")
            return ""
        return response_reflect
