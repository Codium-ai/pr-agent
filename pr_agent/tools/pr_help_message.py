from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider
from pr_agent.log import get_logger


class PRHelpMessage:
    def __init__(self, pr_url: str, args=None, ai_handler=None):
        self.git_provider = get_git_provider()(pr_url)

    async def run(self):
        try:
            get_logger().info('Getting PR Help Message...')
            pr_comment = "## PR Agent Walkthrough\n\n"
            pr_comment += "🤖 Welcome to the PR Agent, an AI-powered tool for automated pull request analysis, feedback, suggestions and more."""
            pr_comment += "\n\nHere is a list of tools you can use to interact with the PR Agent:\n"
            base_path = "https://github.com/Codium-ai/pr-agent/tree/main/docs"
            pr_comment += f"<table><tr><th>Tool</th><th align='left'>Description</th></tr>"
            pr_comment += f"\n<tr><td align='center'>\n\n<strong>[DESCRIBE]({base_path}/DESCRIBE.md)</strong></td><td>Generates PR description - title, type, summary, code walkthrough and labels</td></tr>"
            pr_comment += f"\n<tr><td align='center'>\n\n<strong>[REVIEW]({base_path}/REVIEW.md)</strong></td><td>Adjustable feedback about the PR, possible issues, security concerns, review effort and more</td></tr>"
            pr_comment += f"\n<tr><td align='center'>\n\n<strong>[IMPROVE]({base_path}/IMPROVE.md)</strong></td><td>Code suggestions for improving the PR.</td></tr>"
            pr_comment += f"\n<tr><td align='center'>\n\n<strong>[ASK]({base_path}/ASK.md)</strong></td><td>Answering free-text questions about the PR.</td></tr>"
            pr_comment += f"\n<tr><td align='center'>\n\n<strong>[SIMILAR ISSUE]({base_path}/SIMILAR_ISSUE.md)</strong></td><td>Automatically retrieves and presents similar issues.</td></tr>"
            pr_comment += f"\n<tr><td align='center'>\n\n<strong>[UPDATE CHANGELOG]({base_path}/UPDATE_CHANGELOG.md)</strong></td><td>Automatically updates the changelog.</td></tr>"
            pr_comment += f"\n<tr><td align='center'>\n\n<strong>[ADD DOCUMENTATION]({base_path}/ADD_DOCUMENTATION.md)</strong></td><td>Generates documentation to methods/functions/classes that changed in the PR.</td></tr>"
            pr_comment += f"\n<tr><td align='center'>\n\n<strong>[GENERATE CUSTOM LABELS]({base_path}/GENERATE_CUSTOM_LABELS.md)</strong></td><td>Generates custom labels for the PR, based on specific guidelines defined by the user</td></tr>"
            pr_comment += f"\n<tr><td align='center'>\n\n<strong>[ANALYZE]({base_path}/Analyze.md)</strong></td><td>Identifies code components that changed in the PR, and enables to interactively generate tests, docs, and code suggestions for each component.</td></tr>"
            pr_comment += f"\n<tr><td align='center'>\n\n<strong>[TEST]({base_path}/TEST.md)</strong></td><td>Generates unit tests for a selected component, based on the PR code change.</td></tr>"
            pr_comment += f"\n<tr><td align='center'>\n\n<strong>[CI FEEDBACK]({base_path}/CI_FEEDBACK.md)</strong></td><td>Generates feedback and analysis for a failed CI job.</td></tr>"
            pr_comment += f"\n<tr><td align='center'>\n\n<strong>[CUSTOM SUGGESTIONS]({base_path}/CUSTOM_SUGGESTIONS.md)</strong></td><td>Generates custom suggestions for improving the PR code, based on specific guidelines defined by the user.</td></tr>"
            pr_comment += "</table>\n\n"
            pr_comment += f"""\n\nNote that each tool be [invoked automatically](https://github.com/Codium-ai/pr-agent/blob/main/Usage.md#github-app-automatic-tools-for-pr-actions) when a new PR is opened, or called manually by [commenting on a PR](https://github.com/Codium-ai/pr-agent/blob/main/Usage.md#online-usage)."""
            if get_settings().config.publish_output:
                self.git_provider.publish_comment(pr_comment)
        except Exception as e:
            get_logger().error(f"Error while running PRHelpMessage: {e}")
        return ""