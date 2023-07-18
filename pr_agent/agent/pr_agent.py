import re

from pr_agent.config_loader import settings
from pr_agent.tools.pr_code_suggestions import PRCodeSuggestions
from pr_agent.tools.pr_description import PRDescription
from pr_agent.tools.pr_information_from_user import PRInformationFromUser
from pr_agent.tools.pr_questions import PRQuestions
from pr_agent.tools.pr_reviewer import PRReviewer


class PRAgent:
    def __init__(self):
        pass

    async def handle_request(self, pr_url, request) -> bool:
        if any(cmd in request for cmd in ["/answer"]):
            await PRReviewer(pr_url, is_answer=True).review()
        elif any(cmd in request for cmd in ["/review", "/review_pr", "/reflect_and_review"]):
            words = request.split(" ")
            incremental_review = False
            if len(words) > 1:
                arg = words[1]
                if arg == "-i":
                    incremental_review = True
            if settings.pr_reviewer.ask_and_reflect or "/reflect_and_review" in request:
                await PRInformationFromUser(pr_url).generate_questions()
            else:
                await PRReviewer(pr_url, is_incremental=incremental_review).review()
        elif any(cmd in request for cmd in ["/describe", "/describe_pr"]):
            await PRDescription(pr_url).describe()
        elif any(cmd in request for cmd in ["/improve", "/improve_code"]):
            await PRCodeSuggestions(pr_url).suggest()
        elif any(cmd in request for cmd in ["/ask", "/ask_question"]):
            pattern = r'(/ask|/ask_question)\s*(.*)'
            matches = re.findall(pattern, request, re.IGNORECASE)
            if matches:
                question = matches[0][1]
                await PRQuestions(pr_url, question).answer()
        else:
            return False

        return True
