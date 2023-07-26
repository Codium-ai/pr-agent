import argparse
import asyncio
import logging
import os

from pr_agent.tools.pr_code_suggestions import PRCodeSuggestions
from pr_agent.tools.pr_description import PRDescription
from pr_agent.tools.pr_information_from_user import PRInformationFromUser
from pr_agent.tools.pr_questions import PRQuestions
from pr_agent.tools.pr_reviewer import PRReviewer
from pr_agent.tools.pr_update_changelog import PRUpdateChangelog


def run(args=None):
    parser = argparse.ArgumentParser(description='AI based pull request analyzer', usage=
"""\
Usage: cli.py --pr-url <URL on supported git hosting service> <command> [<args>].
For example:
- cli.py --pr-url=... review
- cli.py --pr-url=... describe
- cli.py --pr-url=... improve
- cli.py --pr-url=... ask "write me a poem about this PR"
- cli.py --pr-url=... reflect

Supported commands:
review / review_pr - Add a review that includes a summary of the PR and specific suggestions for improvement.
ask / ask_question [question] - Ask a question about the PR.
describe / describe_pr - Modify the PR title and description based on the PR's contents.
improve / improve_code - Suggest improvements to the code in the PR as pull request comments ready to commit.
reflect - Ask the PR author questions about the PR.
update_changelog - Update the changelog based on the PR's contents.
""")
    parser.add_argument('--pr_url', type=str, help='The URL of the PR to review', required=True)
    parser.add_argument('command', type=str, help='The', choices=['review', 'review_pr',
                                                                  'ask', 'ask_question',
                                                                  'describe', 'describe_pr',
                                                                  'improve', 'improve_code',
                                                                  'reflect', 'review_after_reflect',
                                                                   'update_changelog'],
                                                                   default='review')
    parser.add_argument('rest', nargs=argparse.REMAINDER, default=[])
    args = parser.parse_args(args)
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
    command = args.command.lower()
    commands = {
        'ask': _handle_ask_command,
        'ask_question': _handle_ask_command,
        'describe': _handle_describe_command,
        'describe_pr': _handle_describe_command,
        'improve': _handle_improve_command,
        'improve_code': _handle_improve_command,
        'review': _handle_review_command,
        'review_pr': _handle_review_command,
        'reflect': _handle_reflect_command,
        'review_after_reflect': _handle_review_after_reflect_command,
        'update_changelog': _handle_update_changelog,
    }
    if command in commands:
        commands[command](args.pr_url, args.rest)
    else:
        print(f"Unknown command: {command}")
        parser.print_help()


def _handle_ask_command(pr_url: str, rest: list):
    if len(rest) == 0:
        print("Please specify a question")
        return
    print(f"Question: {' '.join(rest)} about PR {pr_url}")
    reviewer = PRQuestions(pr_url, rest)
    asyncio.run(reviewer.answer())


def _handle_describe_command(pr_url: str, rest: list):
    print(f"PR description: {pr_url}")
    reviewer = PRDescription(pr_url)
    asyncio.run(reviewer.describe())


def _handle_improve_command(pr_url: str, rest: list):
    print(f"PR code suggestions: {pr_url}")
    reviewer = PRCodeSuggestions(pr_url)
    asyncio.run(reviewer.suggest())


def _handle_review_command(pr_url: str, rest: list):
    print(f"Reviewing PR: {pr_url}")
    reviewer = PRReviewer(pr_url, cli_mode=True, args=rest)
    asyncio.run(reviewer.review())


def _handle_reflect_command(pr_url: str, rest: list):
    print(f"Asking the PR author questions: {pr_url}")
    reviewer = PRInformationFromUser(pr_url)
    asyncio.run(reviewer.generate_questions())


def _handle_review_after_reflect_command(pr_url: str, rest: list):
    print(f"Processing author's answers and sending review: {pr_url}")
    reviewer = PRReviewer(pr_url, cli_mode=True, is_answer=True)
    asyncio.run(reviewer.review())

def _handle_update_changelog(pr_url: str, rest: list):
    print(f"Updating changlog for: {pr_url}")
    reviewer = PRUpdateChangelog(pr_url, cli_mode=True)
    asyncio.run(reviewer.update_changelog())

if __name__ == '__main__':
    run()
