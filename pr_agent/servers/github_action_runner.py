import json
import os


def run_action():
    GITHUB_EVENT_NAME = os.environ.get('GITHUB_EVENT_NAME', None)
    if not GITHUB_EVENT_NAME:
        print("GITHUB_EVENT_NAME not set")
        return
    GITHUB_EVENT_PATH = os.environ.get('GITHUB_EVENT_PATH', None)
    if not GITHUB_EVENT_PATH:
        print("GITHUB_EVENT_PATH not set")
        return
    event_payload = json.load(open(GITHUB_EVENT_PATH, 'r'))
    GITHUB_REPOSITORY = os.environ.get('GITHUB_REPOSITORY', None)
    if not GITHUB_REPOSITORY:
        print("GITHUB_REPOSITORY not set")
        return
    print(event_payload)
    print(GITHUB_REPOSITORY)
    print(GITHUB_EVENT_NAME)
    print(GITHUB_EVENT_PATH)
    print("Hello from run_action")
    RUNNER_DEBUG = os.environ.get('RUNNER_DEBUG', None)
    if not RUNNER_DEBUG:
        print("RUNNER_DEBUG not set")
        return
    print(RUNNER_DEBUG)


if __name__ == '__main__':
    run_action()
