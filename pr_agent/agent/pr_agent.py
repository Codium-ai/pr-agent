import re

from pr_agent.config_loader import settings
from pr_agent.tools.pr_code_suggestions import PRCodeSuggestions
from pr_agent.tools.pr_description import PRDescription
from pr_agent.tools.pr_information_from_user import PRInformationFromUser
from pr_agent.tools.pr_questions import PRQuestions
from pr_agent.tools.pr_reviewer import PRReviewer
from pr_agent.tools.pr_update_changelog import PRUpdateChangelog


class PRAgent:
    def __init__(self):
        pass

    async def handle_request(self, pr_url, request) -> bool:
        action, *args = request.strip().split()
        if any(cmd == action for cmd in ["/answer"]):
            await PRReviewer(pr_url, is_answer=True).review()
        elif any(cmd == action for cmd in ["/review", "/review_pr", "/reflect_and_review"]):
            if settings.pr_reviewer.ask_and_reflect or "/reflect_and_review" in request:
                await PRInformationFromUser(pr_url).generate_questions()
            else:
                await PRReviewer(pr_url, args=args).review()
        elif any(cmd == action for cmd in ["/describe", "/describe_pr"]):
            await PRDescription(pr_url).describe()
        elif any(cmd == action for cmd in ["/improve", "/improve_code"]):
            await PRCodeSuggestions(pr_url).suggest()
        elif any(cmd == action for cmd in ["/ask", "/ask_question"]):
            await PRQuestions(pr_url, args=args).answer()
        elif any(cmd == action for cmd in ["/update_changelog"]):
            await PRUpdateChangelog(pr_url, args=args).update_changelog()
        else:
            return False

        return True
