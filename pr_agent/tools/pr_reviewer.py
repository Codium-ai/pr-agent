import copy
import datetime
from collections import OrderedDict
from functools import partial
from typing import List, Tuple

import yaml
from jinja2 import Environment, StrictUndefined
from yaml import SafeLoader

from pr_agent.algo.ai_handlers.base_ai_handler import BaseAiHandler
from pr_agent.algo.ai_handlers.litellm_ai_handler import LiteLLMAIHandler
from pr_agent.algo.pr_processing import get_pr_diff, retry_with_fallback_models
from pr_agent.algo.token_handler import TokenHandler
from pr_agent.algo.utils import convert_to_markdown, load_yaml, try_fix_yaml, set_custom_labels, get_user_labels
from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider
from pr_agent.git_providers.git_provider import IncrementalPR, get_main_pr_language
from pr_agent.log import get_logger
from pr_agent.servers.help import actions_help_text, bot_help_text


class PRReviewer:
    """
    The PRReviewer class is responsible for reviewing a pull request and generating feedback using an AI model.
    """
    def __init__(self, pr_url: str, is_answer: bool = False, is_auto: bool = False, args: list = None,
                 ai_handler: partial[BaseAiHandler,] = LiteLLMAIHandler):
        """
        Initialize the PRReviewer object with the necessary attributes and objects to review a pull request.

        Args:
            pr_url (str): The URL of the pull request to be reviewed.
            is_answer (bool, optional): Indicates whether the review is being done in answer mode. Defaults to False.
            is_auto (bool, optional): Indicates whether the review is being done in automatic mode. Defaults to False.
            ai_handler (BaseAiHandler): The AI handler to be used for the review. Defaults to None.
            args (list, optional): List of arguments passed to the PRReviewer class. Defaults to None.
        """
        self.parse_args(args) # -i command

        self.git_provider = get_git_provider()(pr_url, incremental=self.incremental)
        self.main_language = get_main_pr_language(
            self.git_provider.get_languages(), self.git_provider.get_files()
        )
        self.pr_url = pr_url
        self.is_answer = is_answer
        self.is_auto = is_auto

        if self.is_answer and not self.git_provider.is_supported("get_issue_comments"):
            raise Exception(f"Answer mode is not supported for {get_settings().config.git_provider} for now")
        self.ai_handler = ai_handler()
        self.patches_diff = None
        self.prediction = None

        answer_str, question_str = self._get_user_answers()
        self.vars = {
            "title": self.git_provider.pr.title,
            "branch": self.git_provider.get_pr_branch(),
            "description": self.git_provider.get_pr_description(),
            "language": self.main_language,
            "diff": "",  # empty diff for initial calculation
            "require_score": get_settings().pr_reviewer.require_score_review,
            "require_tests": get_settings().pr_reviewer.require_tests_review,
            "require_security": get_settings().pr_reviewer.require_security_review,
            "require_focused": get_settings().pr_reviewer.require_focused_review,
            "require_estimate_effort_to_review": get_settings().pr_reviewer.require_estimate_effort_to_review,
            'num_code_suggestions': get_settings().pr_reviewer.num_code_suggestions,
            'question_str': question_str,
            'answer_str': answer_str,
            "extra_instructions": get_settings().pr_reviewer.extra_instructions,
            "commit_messages_str": self.git_provider.get_commit_messages(),
            "custom_labels": "",
            "enable_custom_labels": get_settings().config.enable_custom_labels,
        }

        self.token_handler = TokenHandler(
            self.git_provider.pr,
            self.vars,
            get_settings().pr_review_prompt.system,
            get_settings().pr_review_prompt.user
        )

    def parse_args(self, args: List[str]) -> None:
        """
        Parse the arguments passed to the PRReviewer class and set the 'incremental' attribute accordingly.

        Args:
            args: A list of arguments passed to the PRReviewer class.

        Returns:
            None
        """
        is_incremental = False
        if args and len(args) >= 1:
            arg = args[0]
            if arg == "-i":
                is_incremental = True
        self.incremental = IncrementalPR(is_incremental)

    async def run(self) -> None:
        """
        Review the pull request and generate feedback.
        """

        try:
            if self.is_auto and not get_settings().pr_reviewer.automatic_review:
                get_logger().info(f'Automatic review is disabled {self.pr_url}')
                return None
            if self.incremental.is_incremental and not self._can_run_incremental_review():
                return None

            get_logger().info(f'Reviewing PR: {self.pr_url} ...')

            if get_settings().config.publish_output:
                self.git_provider.publish_comment("Preparing review...", is_temporary=True)

            await retry_with_fallback_models(self._prepare_prediction)

            get_logger().info('Preparing PR review...')
            pr_comment = self._prepare_pr_review()

            if get_settings().config.publish_output:
                get_logger().info('Pushing PR review...')
                previous_review_comment = self._get_previous_review_comment()

                # publish the review
                if get_settings().pr_reviewer.persistent_comment and not self.incremental.is_incremental:
                    self.git_provider.publish_persistent_comment(pr_comment,
                                                                 initial_header="## PR Analysis",
                                                                 update_header=True)
                else:
                    self.git_provider.publish_comment(pr_comment)

                self.git_provider.remove_initial_comment()
                if previous_review_comment:
                    self._remove_previous_review_comment(previous_review_comment)
                if get_settings().pr_reviewer.inline_code_comments:
                    get_logger().info('Pushing inline code comments...')
                    self._publish_inline_code_comments()
        except Exception as e:
            get_logger().error(f"Failed to review PR: {e}")

    async def _prepare_prediction(self, model: str) -> None:
        """
        Prepare the AI prediction for the pull request review.

        Args:
            model: A string representing the AI model to be used for the prediction.

        Returns:
            None
        """
        get_logger().info('Getting PR diff...')
        self.patches_diff = get_pr_diff(self.git_provider, self.token_handler, model)
        get_logger().info('Getting AI prediction...')
        self.prediction = await self._get_prediction(model)

    async def _get_prediction(self, model: str) -> str:
        """
        Generate an AI prediction for the pull request review.

        Args:
            model: A string representing the AI model to be used for the prediction.

        Returns:
            A string representing the AI prediction for the pull request review.
        """
        variables = copy.deepcopy(self.vars)
        variables["diff"] = self.patches_diff  # update diff

        environment = Environment(undefined=StrictUndefined)
        system_prompt = environment.from_string(get_settings().pr_review_prompt.system).render(variables)
        user_prompt = environment.from_string(get_settings().pr_review_prompt.user).render(variables)

        if get_settings().config.verbosity_level >= 2:
            get_logger().info(f"\nSystem prompt:\n{system_prompt}")
            get_logger().info(f"\nUser prompt:\n{user_prompt}")

        response, finish_reason = await self.ai_handler.chat_completion(
            model=model,
            temperature=0.2,
            system=system_prompt,
            user=user_prompt
        )

        if get_settings().config.verbosity_level >= 2:
            get_logger().info(f"\nAI response:\n{response}")

        return response

    def _prepare_pr_review(self) -> str:
        """
        Prepare the PR review by processing the AI prediction and generating a markdown-formatted text that summarizes
        the feedback.
        """
        data = load_yaml(self.prediction.strip())

        # Move 'Security concerns' key to 'PR Analysis' section for better display
        pr_feedback = data.get('PR Feedback', {})
        security_concerns = pr_feedback.get('Security concerns')
        if security_concerns is not None:
            del pr_feedback['Security concerns']
            if type(security_concerns) == bool and security_concerns == False:
                data.setdefault('PR Analysis', {})['Security concerns'] = 'No security concerns found'
            else:
                data.setdefault('PR Analysis', {})['Security concerns'] = security_concerns

        #
        if 'Code feedback' in pr_feedback:
            code_feedback = pr_feedback['Code feedback']

            # Filter out code suggestions that can be submitted as inline comments
            if get_settings().pr_reviewer.inline_code_comments:
                del pr_feedback['Code feedback']
            else:
                for suggestion in code_feedback:
                    if ('relevant file' in suggestion) and (not suggestion['relevant file'].startswith('``')):
                        suggestion['relevant file'] = f"``{suggestion['relevant file']}``"

                    if 'relevant line' not in suggestion:
                        suggestion['relevant line'] = ''

                    relevant_line_str = suggestion['relevant line'].split('\n')[0]

                    # removing '+'
                    suggestion['relevant line'] = relevant_line_str.lstrip('+').strip()

                    # try to add line numbers link to code suggestions
                    if hasattr(self.git_provider, 'generate_link_to_relevant_line_number'):
                        link = self.git_provider.generate_link_to_relevant_line_number(suggestion)
                        if link:
                            suggestion['relevant line'] = f"[{suggestion['relevant line']}]({link})"
                    else:
                        pass


        # Add incremental review section
        if self.incremental.is_incremental:
            last_commit_url = f"{self.git_provider.get_pr_url()}/commits/" \
                              f"{self.git_provider.incremental.first_new_commit_sha}"
            last_commit_msg = self.incremental.commits_range[0].commit.message if self.incremental.commits_range else ""
            incremental_review_markdown_text = f"Starting from commit {last_commit_url}"
            if last_commit_msg:
                replacement = last_commit_msg.splitlines(keepends=False)[0].replace('_', r'\_')
                incremental_review_markdown_text += f"  \n_({replacement})_"
            data = OrderedDict(data)
            data.update({'Incremental PR Review': {
                "⏮️ Review for commits since previous PR-Agent review": incremental_review_markdown_text}})
            data.move_to_end('Incremental PR Review', last=False)

        markdown_text = convert_to_markdown(data, self.git_provider.is_supported("gfm_markdown"))
        user = self.git_provider.get_user_id()

        # Add help text if not in CLI mode
        if not get_settings().get("CONFIG.CLI_MODE", False):
            markdown_text += "\n### How to use\n"
            if self.git_provider.is_supported("gfm_markdown"):
                markdown_text += "\n <details> <summary> Instructions</summary>\n\n"
            bot_user = "[bot]" if get_settings().github_app.override_deployment_type else get_settings().github_app.bot_user
            if user and bot_user not in user:
                markdown_text += bot_help_text(user)
            else:
                markdown_text += actions_help_text
            if self.git_provider.is_supported("gfm_markdown"):
                markdown_text += "\n</details>\n"

        # Add custom labels from the review prediction (effort, security)
        self.set_review_labels(data)

        # Log markdown response if verbosity level is high
        if get_settings().config.verbosity_level >= 2:
            get_logger().info(f"Markdown response:\n{markdown_text}")

        if markdown_text == None or len(markdown_text) == 0:
            markdown_text = ""

        return markdown_text

    def _publish_inline_code_comments(self) -> None:
        """
        Publishes inline comments on a pull request with code suggestions generated by the AI model.
        """
        if get_settings().pr_reviewer.num_code_suggestions == 0:
            return

        data = load_yaml(self.prediction.strip())
        comments: List[str] = []
        for suggestion in data.get('PR Feedback', {}).get('Code feedback', []):
            relevant_file = suggestion.get('relevant file', '').strip()
            relevant_line_in_file = suggestion.get('relevant line', '').strip()
            content = suggestion.get('suggestion', '')
            if not relevant_file or not relevant_line_in_file or not content:
                get_logger().info("Skipping inline comment with missing file/line/content")
                continue

            if self.git_provider.is_supported("create_inline_comment"):
                comment = self.git_provider.create_inline_comment(content, relevant_file, relevant_line_in_file)
                if comment:
                    comments.append(comment)
            else:
                self.git_provider.publish_inline_comment(content, relevant_file, relevant_line_in_file)

        if comments:
                self.git_provider.publish_inline_comments(comments)

    def _get_user_answers(self) -> Tuple[str, str]:
        """
        Retrieves the question and answer strings from the discussion messages related to a pull request.

        Returns:
            A tuple containing the question and answer strings.
        """
        question_str = ""
        answer_str = ""

        if self.is_answer:
            discussion_messages = self.git_provider.get_issue_comments()

            for message in discussion_messages.reversed:
                if "Questions to better understand the PR:" in message.body:
                    question_str = message.body
                elif '/answer' in message.body:
                    answer_str = message.body

                if answer_str and question_str:
                    break

        return question_str, answer_str

    def _get_previous_review_comment(self):
        """
        Get the previous review comment if it exists.
        """
        try:
            if get_settings().pr_reviewer.remove_previous_review_comment and hasattr(self.git_provider, "get_previous_review"):
                return self.git_provider.get_previous_review(
                    full=not self.incremental.is_incremental,
                    incremental=self.incremental.is_incremental,
                )
        except Exception as e:
            get_logger().exception(f"Failed to get previous review comment, error: {e}")

    def _remove_previous_review_comment(self, comment):
        """
        Remove the previous review comment if it exists.
        """
        try:
            if get_settings().pr_reviewer.remove_previous_review_comment and comment:
                self.git_provider.remove_comment(comment)
        except Exception as e:
            get_logger().exception(f"Failed to remove previous review comment, error: {e}")

    def _can_run_incremental_review(self) -> bool:
        """Checks if we can run incremental review according the various configurations and previous review"""
        # checking if running is auto mode but there are no new commits
        if self.is_auto and not self.incremental.first_new_commit_sha:
            get_logger().info(f"Incremental review is enabled for {self.pr_url} but there are no new commits")
            return False
        # checking if there are enough commits to start the review
        num_new_commits = len(self.incremental.commits_range)
        num_commits_threshold = get_settings().pr_reviewer.minimal_commits_for_incremental_review
        not_enough_commits = num_new_commits < num_commits_threshold
        # checking if the commits are not too recent to start the review
        recent_commits_threshold = datetime.datetime.now() - datetime.timedelta(
            minutes=get_settings().pr_reviewer.minimal_minutes_for_incremental_review
        )
        last_seen_commit_date = (
            self.incremental.last_seen_commit.commit.author.date if self.incremental.last_seen_commit else None
        )
        all_commits_too_recent = (
            last_seen_commit_date > recent_commits_threshold if self.incremental.last_seen_commit else False
        )
        # check all the thresholds or just one to start the review
        condition = any if get_settings().pr_reviewer.require_all_thresholds_for_incremental_review else all
        if condition((not_enough_commits, all_commits_too_recent)):
            get_logger().info(
                f"Incremental review is enabled for {self.pr_url} but didn't pass the threshold check to run:"
                f"\n* Number of new commits = {num_new_commits} (threshold is {num_commits_threshold})"
                f"\n* Last seen commit date = {last_seen_commit_date} (threshold is {recent_commits_threshold})"
            )
            return False
        return True

    def set_review_labels(self, data):
        if (get_settings().pr_reviewer.enable_review_labels_security or
                get_settings().pr_reviewer.enable_review_labels_effort):
            try:
                review_labels = []
                if get_settings().pr_reviewer.enable_review_labels_effort:
                    estimated_effort = data['PR Analysis']['Estimated effort to review [1-5]']
                    estimated_effort_number = int(estimated_effort.split(',')[0])
                    if 1 <= estimated_effort_number <= 5: # 1, because ...
                        review_labels.append(f'Review effort [1-5]: {estimated_effort_number}')
                if get_settings().pr_reviewer.enable_review_labels_security:
                    security_concerns = data['PR Analysis']['Security concerns'] # yes, because ...
                    security_concerns_bool = 'yes' in security_concerns.lower() or 'true' in security_concerns.lower()
                    if security_concerns_bool:
                        review_labels.append('Possible security concern')

                current_labels = self.git_provider.get_pr_labels()
                current_labels_filtered = [label for label in current_labels if
                                           not label.lower().startswith('review effort [1-5]:') and not label.lower().startswith(
                                               'possible security concern')]
                if current_labels or review_labels:
                    get_logger().info(f"Setting review labels: {review_labels + current_labels_filtered}")
                    self.git_provider.publish_labels(review_labels + current_labels_filtered)
            except Exception as e:
                get_logger().error(f"Failed to set review labels, error: {e}")
