import argparse
import asyncio
import logging
import os

from pr_agent.tools.pr_code_suggestions import PRCodeSuggestions
from pr_agent.tools.pr_description import PRDescription
from pr_agent.tools.pr_information_from_user import PRInformationFromUser
from pr_agent.tools.pr_questions import PRQuestions
from pr_agent.tools.pr_reviewer import PRReviewer


def run(args=None):
    parser = argparse.ArgumentParser(description='AI based pull request analyzer', usage="""\
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
""")
    parser.add_argument('--pr_url', type=str, help='The URL of the PR to review', required=True)
    parser.add_argument('command', type=str, help='The', choices=['review', 'review_pr',
                                                                  'ask', 'ask_question',
                                                                  'describe', 'describe_pr',
                                                                  'improve', 'improve_code',
                                                                  'reflect', 'review_after_reflect'],
                        default='review')
    parser.add_argument('rest', nargs=argparse.REMAINDER, default=[])
    args = parser.parse_args(args)
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
    command = args.command.lower()
    if command in ['ask', 'ask_question']:
        question = ' '.join(args.rest).strip()
        if len(question) == 0:
            print("Please specify a question")
            parser.print_help()
            return
        print(f"Question: {question} about PR {args.pr_url}")
        reviewer = PRQuestions(args.pr_url, question)
        asyncio.run(reviewer.answer())
    elif command in ['describe', 'describe_pr']:
        print(f"PR description: {args.pr_url}")
        reviewer = PRDescription(args.pr_url)
        asyncio.run(reviewer.describe())
    elif command in ['improve', 'improve_code']:
        print(f"PR code suggestions: {args.pr_url}")
        reviewer = PRCodeSuggestions(args.pr_url)
        asyncio.run(reviewer.suggest())
    elif command in ['review', 'review_pr']:
        print(f"Reviewing PR: {args.pr_url}")
        reviewer = PRReviewer(args.pr_url, cli_mode=True)
        asyncio.run(reviewer.review())
    elif command in ['reflect']:
        print(f"Asking the PR author questions: {args.pr_url}")
        reviewer = PRInformationFromUser(args.pr_url)
        asyncio.run(reviewer.generate_questions())
    elif command in ['review_after_reflect']:
        print(f"Processing author's answers and sending review: {args.pr_url}")
        reviewer = PRReviewer(args.pr_url, cli_mode=True, is_answer=True)
        asyncio.run(reviewer.review())
    else:
        print(f"Unknown command: {command}")
        parser.print_help()


if __name__ == '__main__':
    run()
