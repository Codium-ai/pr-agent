import shlex
from functools import partial

from pr_agent.algo.ai_handlers.base_ai_handler import BaseAiHandler
from pr_agent.algo.ai_handlers.litellm_ai_handler import LiteLLMAIHandler
from pr_agent.algo.cli_args import CliArgs
from pr_agent.algo.utils import update_settings_from_args
from pr_agent.config_loader import get_settings
from pr_agent.git_providers.utils import apply_repo_settings
from pr_agent.log import get_logger
from pr_agent.tools.pr_add_docs import PRAddDocs
from pr_agent.tools.pr_code_suggestions import PRCodeSuggestions
from pr_agent.tools.pr_config import PRConfig
from pr_agent.tools.pr_description import PRDescription
from pr_agent.tools.pr_generate_labels import PRGenerateLabels
from pr_agent.tools.pr_help_message import PRHelpMessage
from pr_agent.tools.pr_line_questions import PR_LineQuestions
from pr_agent.tools.pr_questions import PRQuestions
from pr_agent.tools.pr_reviewer import PRReviewer
from pr_agent.tools.pr_similar_issue import PRSimilarIssue
from pr_agent.tools.pr_update_changelog import PRUpdateChangelog

command2class = {
    "auto_review": PRReviewer,
    "answer": PRReviewer,
    "review": PRReviewer,
    "review_pr": PRReviewer,
    "describe": PRDescription,
    "describe_pr": PRDescription,
    "improve": PRCodeSuggestions,
    "improve_code": PRCodeSuggestions,
    "ask": PRQuestions,
    "ask_question": PRQuestions,
    "ask_line": PR_LineQuestions,
    "update_changelog": PRUpdateChangelog,
    "config": PRConfig,
    "settings": PRConfig,
    "help": PRHelpMessage,
    "similar_issue": PRSimilarIssue,
    "add_docs": PRAddDocs,
    "generate_labels": PRGenerateLabels,
}

commands = list(command2class.keys())


commands2instructions = {
    # "auto_best_practices":"auto_best_practices",
    "improve_component":"pr_improve_component",
    "test":"pr_test",
    "update_changelog":"pr_update_changelog",
    "add_docs":"pr_add_docs",
    "improve":"pr_code_suggestions",
    "describe":"pr_description",
    "review":"pr_reviewer"
}

commands_with_extra_instructions = list(commands2instructions.keys())


class PRAgent:
    def __init__(self, ai_handler: partial[BaseAiHandler,] = LiteLLMAIHandler):
        self.ai_handler = ai_handler  # will be initialized in run_action

    async def handle_request(self, pr_url, request, notify=None) -> bool:
        # First, apply repo specific settings if exists
        apply_repo_settings(pr_url)

        # Then, apply user specific settings if exists
        if isinstance(request, str):
            request = request.replace("'", "\\'")
            lexer = shlex.shlex(request, posix=True)
            lexer.whitespace_split = True
            action, *args = list(lexer)
        else:
            action, *args = request

        # validate args
        is_valid, arg = CliArgs.validate_user_args(args)
        if not is_valid:
            get_logger().error(
                f"CLI argument for param '{arg}' is forbidden. Use instead a configuration file."
            )
            return False

        # Update settings from args
        args = update_settings_from_args(args)

        # Append the response language in the extra instructions
        response_language = get_settings().config.response_language
        if response_language != 'en-us':
            for key in get_settings():
                setting = get_settings().get(key)
                if str(type(setting)) == "<class 'dynaconf.utils.boxing.DynaBox'>":
                    if hasattr(setting, 'extra_instructions'):
                        extra_instructions = get_settings()[key.lower()].extra_instructions
                        get_settings()[key.lower()].extra_instructions = f"{extra_instructions} \n======\n\nLanguage preference from the user\n======\n In your reply only use the lanaguage with locale code: {response_language}"

        action = action.lstrip("/").lower()
        if action not in command2class:
            get_logger().error(f"Unknown command: {action}")
            return False
        with get_logger().contextualize(command=action, pr_url=pr_url):
            get_logger().info("PR-Agent request handler started", analytics=True)
            if action == "answer":
                if notify:
                    notify()
                await PRReviewer(pr_url, is_answer=True, args=args, ai_handler=self.ai_handler).run()
            elif action == "auto_review":
                await PRReviewer(pr_url, is_auto=True, args=args, ai_handler=self.ai_handler).run()
            elif action in command2class:
                if notify:
                    notify()

                await command2class[action](pr_url, ai_handler=self.ai_handler, args=args).run()
            else:
                return False
            return True
