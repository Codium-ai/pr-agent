import re
from typing import Optional

from pr_agent.tools.pr_questions import PRQuestions
from pr_agent.tools.pr_reviewer import PRReviewer


class PRAgent:
    def __init__(self, installation_id: Optional[int] = None):
        self.installation_id = installation_id

    async def handle_request(self, pr_url, request):
        if 'please review' in request.lower():
            reviewer = PRReviewer(pr_url, self.installation_id)
            await reviewer.review()

        elif 'please answer' in request.lower():
            question = re.split(r'(?i)please answer', request)[1].strip()
            answerer = PRQuestions(pr_url, question, self.installation_id)
            await answerer.answer()
