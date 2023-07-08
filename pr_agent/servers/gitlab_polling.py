import asyncio
import time
from urllib.parse import urlparse
import gitlab
from pr_agent.agent.pr_agent import PRAgent

from pr_agent.config_loader import settings


gl = gitlab.Gitlab(
    settings.get("GITLAB.URL"),
    private_token=settings.get("GITLAB.PERSONAL_ACCESS_TOKEN")
)

# Set the list of projects to monitor
projects_to_monitor = settings.get("GITLAB.PROJECTS_TO_MONITOR")
magic_word = settings.get("GITLAB.MAGIC_WORD")

# Hold the previous seen comments
previous_comments = set()


def check_comments():
    print('Polling')
    new_comments = {}
    for project in projects_to_monitor:
        project = gl.projects.get(project)
        merge_requests = project.mergerequests.list(state='opened')
        for mr in merge_requests:
            notes = mr.notes.list(get_all=True)
            for note in notes:
                if note.id not in previous_comments and note.body.startswith(magic_word):
                    new_comments[note.id] = dict(
                        body=note.body[len(magic_word):],
                        project=project.name,
                        mr=mr
                    )
                    previous_comments.add(note.id)
                    print(f"New comment in project {project.name}, merge request {mr.title}: {note.body}")

    return new_comments


def handle_new_comments(new_comments):
    print('Handling new comments')
    agent = PRAgent()
    for _, comment in new_comments.items():
        print(f"Handling comment: {comment['body']}")
        asyncio.run(agent.handle_request(comment['mr'].web_url, comment['body']))


def run():
    assert settings.get('CONFIG.GIT_PROVIDER') == 'gitlab', 'This script is only for GitLab'
    # Initial run to populate previous_comments
    check_comments()

    # Run the check every minute
    while True:
        time.sleep(settings.get("GITLAB.POLLING_INTERVAL_SECONDS"))
        new_comments = check_comments()
        if new_comments:
            handle_new_comments(new_comments)

if __name__ == '__main__':
    run()
