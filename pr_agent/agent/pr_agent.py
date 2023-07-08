import re
from typing import Optional

from pr_agent.tools.pr_questions import PRQuestions
from pr_agent.tools.pr_reviewer import PRReviewer


class PRAgent:
    def __init__(self):
        pass

    async def handle_request(self, pr_url, request):
        if 'please review' in request.lower() or 'review' == request.lower().strip() or len(request) == 0:
            reviewer = PRReviewer(pr_url)
            await reviewer.review()

        else:
            if "please answer" in request.lower():
                question = re.split(r'(?i)please answer', request)[1].strip()
            elif request.lower().strip().startswith("answer"):
                question = re.split(r'(?i)answer', request)[1].strip()
            else:
                question = request
            answerer = PRQuestions(pr_url, question)
            await answerer.answer()
