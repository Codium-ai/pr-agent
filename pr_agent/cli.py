import argparse
import asyncio
import logging
import os

from pr_agent.agent.pr_agent import PRAgent, commands
from pr_agent.config_loader import get_settings


def run(inargs=None):
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

To edit any configuration parameter from 'configuration.toml', just add -config_path=<value>.
For example: '- cli.py --pr-url=... review --pr_reviewer.extra_instructions="focus on the file: ..."'
""")
    parser.add_argument('--pr_url', type=str, help='The URL of the PR to review', required=True)
    parser.add_argument('command', type=str, help='The', choices=commands, default='review')
    parser.add_argument('rest', nargs=argparse.REMAINDER, default=[])
    args = parser.parse_args(inargs)
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
    command = args.command.lower()
    get_settings().set("CONFIG.CLI_MODE", True)
    result = asyncio.run(PRAgent().handle_request(args.pr_url, command + " " + " ".join(args.rest)))
    if not result:
        parser.print_help()


if __name__ == '__main__':
    run()
