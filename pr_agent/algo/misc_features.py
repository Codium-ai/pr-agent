from slack_sdk import WebClient
import re
from pr_agent.config_loader import get_settings
from pr_agent.git_providers.git_provider import GitProvider
from pr_agent.log import get_logger

def send_notification(data: dict, git_provider: GitProvider):
    slack_setting = get_settings().slack
    # Send a notification to the slack channel or user
    slack_channel = slack_setting.slack_channel
    if slack_channel:
        # Send a message to the slack channel
        slack_token = slack_setting.token
        client = WebClient(token=slack_token)
        mr_details = git_provider.mr
        review_effort = data['review']['estimated_effort_to_review_[1-5]']
        # Grab the number from review effort
        review_effort = re.findall(r'\d+', review_effort) if review_effort else []
        message = """
        @here MR: <{MRLink}|{Title}>\nAuthor: @{Author}\nReview Effort [1-5]: {ReviewEffort}\nFiles changed: {FilesChanged}
        """.format(
            Title=mr_details.title,
            ReviewEffort=review_effort[0] if len(review_effort) > 0 else "N/A",
            Author=mr_details.author['username'],
            FilesChanged=mr_details.changes_count,
            MRLink=git_provider.get_pr_url()
        )
        try:
            client.chat_postMessage(
                channel=slack_channel, 
                blocks=[{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": message
                    }
                }],
                text=message
            )
        except Exception as e:
            get_logger().error(f"Failed to send Slack notification: {e}")
