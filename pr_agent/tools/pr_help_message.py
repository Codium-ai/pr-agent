from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider, GithubProvider
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

            tool_names = []
            tool_names.append(f"[DESCRIBE]({base_path}/DESCRIBE.md)")
            tool_names.append(f"[REVIEW]({base_path}/REVIEW.md)")
            tool_names.append(f"[IMPROVE]({base_path}/IMPROVE.md)")
            tool_names.append(f"[ANALYZE]({base_path}/Analyze.md) 💎")
            tool_names.append(f"[UPDATE CHANGELOG]({base_path}/UPDATE_CHANGELOG.md)")
            tool_names.append(f"[ADD DOCUMENTATION]({base_path}/ADD_DOCUMENTATION.md) 💎")
            tool_names.append(f"[ASK]({base_path}/ASK.md)")
            tool_names.append(f"[GENERATE CUSTOM LABELS]({base_path}/GENERATE_CUSTOM_LABELS.md)")
            tool_names.append(f"[TEST]({base_path}/TEST.md) 💎")
            tool_names.append(f"[CI FEEDBACK]({base_path}/CI_FEEDBACK.md) 💎")
            tool_names.append(f"[CUSTOM SUGGESTIONS]({base_path}/CUSTOM_SUGGESTIONS.md) 💎")
            tool_names.append(f"[SIMILAR ISSUE]({base_path}/SIMILAR_ISSUE.md)")

            descriptions = []
            descriptions.append("Generates PR description - title, type, summary, code walkthrough and labels")
            descriptions.append("Adjustable feedback about the PR, possible issues, security concerns, review effort and more")
            descriptions.append("Code suggestions for improving the PR.")
            descriptions.append("Identifies code components that changed in the PR, and enables to interactively generate tests, docs, and code suggestions for each component.")
            descriptions.append("Automatically updates the changelog.")
            descriptions.append("Generates documentation to methods/functions/classes that changed in the PR.")
            descriptions.append("Answering free-text questions about the PR.")
            descriptions.append("Generates custom labels for the PR, based on specific guidelines defined by the user")
            descriptions.append("Generates unit tests for a specific component, based on the PR code change.")
            descriptions.append("Generates feedback and analysis for a failed CI job.")
            descriptions.append("Generates custom suggestions for improving the PR code, based on specific guidelines defined by the user.")
            descriptions.append("Automatically retrieves and presents similar issues.")

            commands  =[]
            commands.append("`/describe`")
            commands.append("`/review`")
            commands.append("`/improve`")
            commands.append("`/analyze`")
            commands.append("`/update_changelog`")
            commands.append("`/add_docs`")
            commands.append("`/ask`")
            commands.append("`/generate_labels`")
            commands.append("`/test`")
            commands.append("`/checks`")
            commands.append("`/custom_suggestions`")
            commands.append("`/similar_issue`")

            checkbox_list = []
            checkbox_list.append(" - [ ] Run <!-- /describe -->")
            checkbox_list.append(" - [ ] Run <!-- /review -->")
            checkbox_list.append(" - [ ] Run <!-- /improve -->")
            checkbox_list.append(" - [ ] Run <!-- /analyze -->")
            checkbox_list.append(" - [ ] Run <!-- /update_changelog -->")
            checkbox_list.append(" - [ ] Run <!-- /add_docs -->")
            checkbox_list.append("[*]")
            checkbox_list.append("[*]")
            checkbox_list.append("[*]")
            checkbox_list.append("[*]")
            checkbox_list.append("[*]")
            checkbox_list.append("[*]")

            if isinstance(self.git_provider, GithubProvider):
                pr_comment += f"<table><tr align='center'><th align='center'>Tool</th><th align='center'>Description</th><th align='center'>Invoke Interactively :gem:</th></tr>"
                for i in range(len(tool_names)):
                    pr_comment += f"\n<tr><td align='center'>\n\n<strong>{tool_names[i]}</strong></td>\n<td>{descriptions[i]}</td>\n<td>\n\n{checkbox_list[i]}\n</td></tr>"
                pr_comment += "</table>\n\n"
                pr_comment += f"""\n\n(1) Note that each tool be [triggered automatically](https://github.com/Codium-ai/pr-agent/blob/main/Usage.md#github-app-automatic-tools-for-pr-actions) when a new PR is opened, or called manually by [commenting on a PR](https://github.com/Codium-ai/pr-agent/blob/main/Usage.md#online-usage)."""
                pr_comment += f"""\n\n(2) Tools marked with [*] require additional parameters to be passed. For example, to invoke the `/ask` tool, you need to comment on a PR: `/ask "<question content>"`. See the relevant documentation for each tool for more details."""
            else:
                pr_comment += f"<table><tr align='center'><th align='center'>Tool</th><th align='left'>Command</th><th align='left'>Description</th></tr>"
                for i in range(len(tool_names)):
                    pr_comment += f"\n<tr><td align='center'>\n\n<strong>{tool_names[i]}</strong></td><td>{commands[i]}</td><td>{descriptions[i]}</td></tr>"
                pr_comment += "</table>\n\n"
                pr_comment += f"""\n\nNote that each tool be [invoked automatically](https://github.com/Codium-ai/pr-agent/blob/main/Usage.md#github-app-automatic-tools-for-pr-actions) when a new PR is opened, or called manually by [commenting on a PR](https://github.com/Codium-ai/pr-agent/blob/main/Usage.md#online-usage)."""
            if get_settings().config.publish_output:
                self.git_provider.publish_comment(pr_comment)
        except Exception as e:
            get_logger().error(f"Error while running PRHelpMessage: {e}")
        return ""