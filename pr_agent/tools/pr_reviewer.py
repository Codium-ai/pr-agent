import copy
import json
import logging
from collections import OrderedDict
from typing import List, Tuple

import yaml
from jinja2 import Environment, StrictUndefined
from yaml import SafeLoader

from pr_agent.algo.ai_handler import AiHandler
from pr_agent.algo.pr_processing import get_pr_diff, retry_with_fallback_models, \
    find_line_number_of_relevant_line_in_file, clip_tokens
from pr_agent.algo.token_handler import TokenHandler
from pr_agent.algo.utils import convert_to_markdown, try_fix_json, try_fix_yaml, load_yaml
from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider
from pr_agent.git_providers.git_provider import IncrementalPR, get_main_pr_language
from pr_agent.servers.help import actions_help_text, bot_help_text


class PRReviewer:
    """
    The PRReviewer class is responsible for reviewing a pull request and generating feedback using an AI model.
    """
    def __init__(self, pr_url: str, is_answer: bool = False, is_auto: bool = False, args: list = None):
        """
        Initialize the PRReviewer object with the necessary attributes and objects to review a pull request.

        Args:
            pr_url (str): The URL of the pull request to be reviewed.
            is_answer (bool, optional): Indicates whether the review is being done in answer mode. Defaults to False.
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
        self.ai_handler = AiHandler()
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
                logging.info(f'Automatic review is disabled {self.pr_url}')
                return None

            logging.info(f'Reviewing PR: {self.pr_url} ...')

            if get_settings().config.publish_output:
                self.git_provider.publish_comment("Preparing review...", is_temporary=True)

            await retry_with_fallback_models(self._prepare_prediction)

            logging.info('Preparing PR review...')
            pr_comment = self._prepare_pr_review()

            if get_settings().config.publish_output:
                logging.info('Pushing PR review...')
                self.git_provider.publish_comment(pr_comment)
                self.git_provider.remove_initial_comment()

                if get_settings().pr_reviewer.inline_code_comments:
                    logging.info('Pushing inline code comments...')
                    self._publish_inline_code_comments()
        except Exception as e:
            logging.error(f"Failed to review PR: {e}")

    async def _prepare_prediction(self, model: str) -> None:
        """
        Prepare the AI prediction for the pull request review.

        Args:
            model: A string representing the AI model to be used for the prediction.

        Returns:
            None
        """
        logging.info('Getting PR diff...')
        self.patches_diff = get_pr_diff(self.git_provider, self.token_handler, model)
        logging.info('Getting AI prediction...')
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
            logging.info(f"\nSystem prompt:\n{system_prompt}")
            logging.info(f"\nUser prompt:\n{user_prompt}")

        response, finish_reason = await self.ai_handler.chat_completion(
            model=model,
            temperature=0.2,
            system=system_prompt,
            user=user_prompt
        )

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
                        # try:
                        #     relevant_file = suggestion['relevant file'].strip('`').strip("'")
                        #     relevant_line_str = suggestion['relevant line']
                        #     if not relevant_line_str:
                        #         return ""
                        #
                        #     position, absolute_position = find_line_number_of_relevant_line_in_file(
                        #         self.git_provider.diff_files, relevant_file, relevant_line_str)
                        #     if absolute_position != -1:
                        #         suggestion[
                        #             'relevant line'] = f"{suggestion['relevant line']} (line {absolute_position})"
                        # except:
                        #     pass


        # Add incremental review section
        if self.incremental.is_incremental:
            last_commit_url = f"{self.git_provider.get_pr_url()}/commits/" \
                              f"{self.git_provider.incremental.first_new_commit_sha}"
            data = OrderedDict(data)
            data.update({'Incremental PR Review': {
                "⏮️ Review for commits since previous PR-Agent review": f"Starting from commit {last_commit_url}"}})
            data.move_to_end('Incremental PR Review', last=False)

        markdown_text = convert_to_markdown(data, self.git_provider.is_supported("gfm_markdown"))
        user = self.git_provider.get_user_id()

        # Add help text if not in CLI mode
        if not get_settings().get("CONFIG.CLI_MODE", False):
            markdown_text += "\n### How to use\n"
            if user and '[bot]' not in user:
                markdown_text += bot_help_text(user)
            else:
                markdown_text += actions_help_text

        # Log markdown response if verbosity level is high
        if get_settings().config.verbosity_level >= 2:
            logging.info(f"Markdown response:\n{markdown_text}")

        if markdown_text == None or len(markdown_text) == 0:
            markdown_text = ""

        return markdown_text

    def _publish_inline_code_comments(self) -> None:
        """
        Publishes inline comments on a pull request with code suggestions generated by the AI model.
        """
        if get_settings().pr_reviewer.num_code_suggestions == 0:
            return

        review_text = self.prediction.strip()
        review_text = review_text.removeprefix('```yaml').rstrip('`')
        try:
            data = yaml.load(review_text, Loader=SafeLoader)
        except Exception as e:
            logging.error(f"Failed to parse AI prediction: {e}")
            data = try_fix_yaml(review_text)

        comments: List[str] = []
        for suggestion in data.get('PR Feedback', {}).get('Code feedback', []):
            relevant_file = suggestion.get('relevant file', '').strip()
            relevant_line_in_file = suggestion.get('relevant line', '').strip()
            content = suggestion.get('suggestion', '')
            if not relevant_file or not relevant_line_in_file or not content:
                logging.info("Skipping inline comment with missing file/line/content")
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
