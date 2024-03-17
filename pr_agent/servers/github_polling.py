import asyncio
from datetime import datetime, timezone

import aiohttp

from pr_agent.agent.pr_agent import PRAgent
from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider
from pr_agent.log import LoggingFormat, get_logger, setup_logger

setup_logger(fmt=LoggingFormat.JSON, level="DEBUG")
NOTIFICATION_URL = "https://api.github.com/notifications"


def now() -> str:
    """
    Get the current UTC time in ISO 8601 format.
    
    Returns:
        str: The current UTC time in ISO 8601 format.
    """
    now_utc = datetime.now(timezone.utc).isoformat()
    now_utc = now_utc.replace("+00:00", "Z")
    return now_utc


async def polling_loop():
    """
    Polls for notifications and handles them accordingly.
    """
    handled_ids = set()
    since = [now()]
    last_modified = [None]
    git_provider = get_git_provider()()
    user_id = git_provider.get_user_id()
    agent = PRAgent()
    get_settings().set("CONFIG.PUBLISH_OUTPUT_PROGRESS", False)

    try:
        deployment_type = get_settings().github.deployment_type
        token = get_settings().github.user_token
    except AttributeError:
        deployment_type = 'none'
        token = None

    if deployment_type != 'user':
        raise ValueError("Deployment mode must be set to 'user' to get notifications")
    if not token:
        raise ValueError("User token must be set to get notifications")

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                await asyncio.sleep(5)
                headers = {
                    "Accept": "application/vnd.github.v3+json",
                    "Authorization": f"Bearer {token}"
                }
                params = {
                    "participating": "true"
                }
                if since[0]:
                    params["since"] = since[0]
                if last_modified[0]:
                    headers["If-Modified-Since"] = last_modified[0]

                async with session.get(NOTIFICATION_URL, headers=headers, params=params) as response:
                    if response.status == 200:
                        if 'Last-Modified' in response.headers:
                            last_modified[0] = response.headers['Last-Modified']
                            since[0] = None
                        notifications = await response.json()
                        if not notifications:
                            continue
                        for notification in notifications:
                            handled_ids.add(notification['id'])
                            if 'reason' in notification and notification['reason'] == 'mention':
                                if 'subject' in notification and notification['subject']['type'] == 'PullRequest':
                                    pr_url = notification['subject']['url']
                                    latest_comment = notification['subject']['latest_comment_url']
                                    async with session.get(latest_comment, headers=headers) as comment_response:
                                        if comment_response.status == 200:
                                            comment = await comment_response.json()
                                            if 'id' in comment:
                                                if comment['id'] in handled_ids:
                                                    continue
                                                else:
                                                    handled_ids.add(comment['id'])
                                            if 'user' in comment and 'login' in comment['user']:
                                                if comment['user']['login'] == user_id:
                                                    continue
                                            comment_body = comment['body'] if 'body' in comment else ''
                                            commenter_github_user = comment['user']['login'] \
                                                if 'user' in comment else ''
                                            get_logger().info(f"Commenter: {commenter_github_user}\nComment: {comment_body}")
                                            user_tag = "@" + user_id
                                            if user_tag not in comment_body:
                                                continue
                                            rest_of_comment = comment_body.split(user_tag)[1].strip()
                                            comment_id = comment['id']
                                            git_provider.set_pr(pr_url)
                                            success = await agent.handle_request(pr_url, rest_of_comment,
                                                                                 notify=lambda: git_provider.add_eyes_reaction(comment_id))  # noqa E501
                                            if not success:
                                                git_provider.set_pr(pr_url)

                    elif response.status != 304:
                        print(f"Failed to fetch notifications. Status code: {response.status}")

            except Exception as e:
                get_logger().error(f"Exception during processing of a notification: {e}")


if __name__ == '__main__':
    asyncio.run(polling_loop())