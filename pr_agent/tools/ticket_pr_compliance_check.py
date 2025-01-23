import re
import traceback

from pr_agent.config_loader import get_settings
from pr_agent.git_providers import GithubProvider
from pr_agent.log import get_logger

# Compile the regex pattern once, outside the function
GITHUB_TICKET_PATTERN = re.compile(
     r'(https://github[^/]+/[^/]+/[^/]+/issues/\d+)|(\b(\w+)/(\w+)#(\d+)\b)|(#\d+)'
)

def find_jira_tickets(text):
    # Regular expression patterns for JIRA tickets
    patterns = [
        r'\b[A-Z]{2,10}-\d{1,7}\b',  # Standard JIRA ticket format (e.g., PROJ-123)
        r'(?:https?://[^\s/]+/browse/)?([A-Z]{2,10}-\d{1,7})\b'  # JIRA URL or just the ticket
    ]

    tickets = set()
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if isinstance(match, tuple):
                # If it's a tuple (from the URL pattern), take the last non-empty group
                ticket = next((m for m in reversed(match) if m), None)
            else:
                ticket = match
            if ticket:
                tickets.add(ticket)

    return list(tickets)


def extract_ticket_links_from_pr_description(pr_description, repo_path, base_url_html='https://github.com'):
    """
    Extract all ticket links from PR description
    """
    github_tickets = set()
    try:
        # Use the updated pattern to find matches
        matches = GITHUB_TICKET_PATTERN.findall(pr_description)

        for match in matches:
            if match[0]:  # Full URL match
                github_tickets.add(match[0])
            elif match[1]:  # Shorthand notation match: owner/repo#issue_number
                owner, repo, issue_number = match[2], match[3], match[4]
                github_tickets.add(f'{base_url_html.strip("/")}/{owner}/{repo}/issues/{issue_number}')
            else:  # #123 format
                issue_number = match[5][1:]  # remove #
                if issue_number.isdigit() and len(issue_number) < 5 and repo_path:
                    github_tickets.add(f'{base_url_html.strip("/")}/{repo_path}/issues/{issue_number}')
    except Exception as e:
        get_logger().error(f"Error extracting tickets error= {e}",
                           artifact={"traceback": traceback.format_exc()})

    return list(github_tickets)


async def extract_tickets(git_provider):
    MAX_TICKET_CHARACTERS = 10000
    try:
        if isinstance(git_provider, GithubProvider):
            user_description = git_provider.get_user_description()
            tickets = extract_ticket_links_from_pr_description(user_description, git_provider.repo, git_provider.base_url_html)
            tickets_content = []
            if tickets:
                for ticket in tickets:
                    # extract ticket number and repo name
                    repo_name, original_issue_number = git_provider._parse_issue_url(ticket)

                    # get the ticket object
                    try:
                        issue_main = git_provider.repo_obj.get_issue(original_issue_number)
                    except Exception as e:
                        get_logger().error(f"Error getting issue_main error= {e}",
                                           artifact={"traceback": traceback.format_exc()})
                        continue

                    # clip issue_main.body max length
                    issue_body_str = issue_main.body
                    if not issue_body_str:
                        issue_body_str = ""
                    if len(issue_body_str) > MAX_TICKET_CHARACTERS:
                        issue_body_str = issue_body_str[:MAX_TICKET_CHARACTERS] + "..."

                    # extract labels
                    labels = []
                    try:
                        for label in issue_main.labels:
                            if isinstance(label, str):
                                labels.append(label)
                            else:
                                labels.append(label.name)
                    except Exception as e:
                        get_logger().error(f"Error extracting labels error= {e}",
                                           artifact={"traceback": traceback.format_exc()})
                    tickets_content.append(
                        {'ticket_id': issue_main.number,
                         'ticket_url': ticket, 'title': issue_main.title, 'body': issue_body_str,
                         'labels': ", ".join(labels)})
                return tickets_content

    except Exception as e:
        get_logger().error(f"Error extracting tickets error= {e}",
                           artifact={"traceback": traceback.format_exc()})


async def extract_and_cache_pr_tickets(git_provider, vars):
    if not get_settings().get('pr_reviewer.require_ticket_analysis_review', False):
        return
    related_tickets = get_settings().get('related_tickets', [])
    if not related_tickets:
        tickets_content = await extract_tickets(git_provider)
        if tickets_content:
            get_logger().info("Extracted tickets from PR description", artifact={"tickets": tickets_content})
            vars['related_tickets'] = tickets_content
            get_settings().set('related_tickets', tickets_content)
    else:  # if tickets are already cached
        get_logger().info("Using cached tickets", artifact={"tickets": related_tickets})
        vars['related_tickets'] = related_tickets


def check_tickets_relevancy():
    return True
