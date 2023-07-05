import argparse
import asyncio
import logging
import os

from pr_agent.tools.pr_reviewer import PRReviewer

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Review a PR from a URL')
    parser.add_argument('--pr_url', type=str, help='The URL of the PR to review', required=True)
    args = parser.parse_args()
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
    reviewer = PRReviewer(args.pr_url, None)
    asyncio.run(reviewer.review())
