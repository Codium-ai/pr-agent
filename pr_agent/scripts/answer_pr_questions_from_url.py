import argparse
import asyncio
import logging
import os

from pr_agent.tools.pr_questions import PRQuestions

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Review a PR from a URL')
    parser.add_argument('--pr_url', type=str, help='The URL of the PR to review', required=True)
    parser.add_argument('--question_str', type=str, help='The question to answer', required=True)

    args = parser.parse_args()
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
    reviewer = PRQuestions(args.pr_url, args.question_str, None)
    asyncio.run(reviewer.answer())
