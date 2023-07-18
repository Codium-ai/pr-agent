import copy
import json
import logging

from jinja2 import Environment, StrictUndefined

from pr_agent.algo.ai_handler import AiHandler
from pr_agent.algo.pr_processing import get_pr_diff
from pr_agent.algo.token_handler import TokenHandler
from pr_agent.algo.utils import convert_to_markdown, try_fix_json
from pr_agent.config_loader import settings
from pr_agent.git_providers import get_git_provider
from pr_agent.git_providers.git_provider import get_main_pr_language
from pr_agent.servers.help import bot_help_text, actions_help_text


class PRReviewer:
    def __init__(self, pr_url: str, cli_mode=False, is_answer: bool = False):

        self.git_provider = get_git_provider()(pr_url)
        self.main_language = get_main_pr_language(
            self.git_provider.get_languages(), self.git_provider.get_files()
        )
        self.is_answer = is_answer
        if self.is_answer and not self.git_provider.is_supported("get_issue_comments"):
            raise Exception(f"Answer mode is not supported for {settings.config.git_provider} for now")
        answer_str = question_str = self._get_user_answers()
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
            "require_tests": settings.pr_reviewer.require_tests_review,
            "require_security": settings.pr_reviewer.require_security_review,
            "require_focused": settings.pr_reviewer.require_focused_review,
            'num_code_suggestions': settings.pr_reviewer.num_code_suggestions,
            #
            'question_str': question_str,
            'answer_str': answer_str,
        }
        self.token_handler = TokenHandler(self.git_provider.pr,
                                          self.vars,
                                          settings.pr_review_prompt.system,
                                          settings.pr_review_prompt.user)

    async def review(self):
        logging.info('Reviewing PR...')
        if settings.config.publish_output:
                self.git_provider.publish_comment("Preparing review...", is_temporary=True)
        logging.info('Getting PR diff...')
        self.patches_diff = get_pr_diff(self.git_provider, self.token_handler)
        logging.info('Getting AI prediction...')
        self.prediction = await self._get_prediction()
        logging.info('Preparing PR review...')
        pr_comment = self._prepare_pr_review()
        if settings.config.publish_output:
            logging.info('Pushing PR review...')
            self.git_provider.publish_comment(pr_comment)
            self.git_provider.remove_initial_comment()
            if settings.pr_reviewer.inline_code_comments:
                logging.info('Pushing inline code comments...')
                self._publish_inline_code_comments()
        return ""

    async def _get_prediction(self):
        variables = copy.deepcopy(self.vars)
        variables["diff"] = self.patches_diff  # update diff
        environment = Environment(undefined=StrictUndefined)
        system_prompt = environment.from_string(settings.pr_review_prompt.system).render(variables)
        user_prompt = environment.from_string(settings.pr_review_prompt.user).render(variables)
        if settings.config.verbosity_level >= 2:
            logging.info(f"\nSystem prompt:\n{system_prompt}")
            logging.info(f"\nUser prompt:\n{user_prompt}")
        model = settings.config.model
        response, finish_reason = await self.ai_handler.chat_completion(model=model, temperature=0.2,
                                                                        system=system_prompt, user=user_prompt)

        return response

    def _prepare_pr_review(self) -> str:
        review = self.prediction.strip()
        try:
            data = json.loads(review)
        except json.decoder.JSONDecodeError:
            data = try_fix_json(review)

        # reordering for nicer display
        if 'PR Feedback' in data:
            if 'Security concerns' in data['PR Feedback']:
                val = data['PR Feedback']['Security concerns']
                del data['PR Feedback']['Security concerns']
                data['PR Analysis']['Security concerns'] = val

        if settings.config.git_provider == 'github' and \
                settings.pr_reviewer.inline_code_comments and \
                'Code suggestions' in data['PR Feedback']:
            del data['PR Feedback']['Code suggestions']

        markdown_text = convert_to_markdown(data)
        user = self.git_provider.get_user_id()

        if not self.cli_mode:
            markdown_text += "\n### How to use\n"
            if user and '[bot]' not in user:
                markdown_text += bot_help_text(user)
            else:
                markdown_text += actions_help_text

        if settings.config.verbosity_level >= 2:
            logging.info(f"Markdown response:\n{markdown_text}")
        return markdown_text

    def _publish_inline_code_comments(self):
        if settings.pr_reviewer.num_code_suggestions == 0:
            return

        review = self.prediction.strip()
        try:
            data = json.loads(review)
        except json.decoder.JSONDecodeError:
            data = try_fix_json(review)

        if settings.config.pr_reviewer > 0:
            try:
                for d in data['PR Feedback']['Code suggestions']:
                    relevant_file = d['relevant file'].strip()
                    relevant_line_in_file = d['relevant line in file'].strip()
                    content = d['suggestion content']

                    self.git_provider.publish_inline_comment(content, relevant_file, relevant_line_in_file)
            except KeyError:
                pass

    def _get_user_answers(self):
        answer_str = question_str = ""
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
