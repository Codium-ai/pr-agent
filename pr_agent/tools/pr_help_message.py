from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider, GithubProvider
from pr_agent.log import get_logger


class PRHelpMessage:
    def __init__(self, pr_url: str, args=None, ai_handler=None):
        self.git_provider = get_git_provider()(pr_url)

    async def run(self):
        try:
            if not self.git_provider.is_supported("gfm_markdown"):
                self.git_provider.publish_comment(
                    "The `Help` tool requires gfm markdown, which is not supported by your code platform.")
                return

            get_logger().info('Getting PR Help Message...')
            relevant_configs = {'pr_help': dict(get_settings().pr_help),
                                'config': dict(get_settings().config)}
            get_logger().debug("Relevant configs", artifacts=relevant_configs)
            pr_comment = "## PR Agent Walkthrough 🤖\n\n"
            pr_comment += "Welcome to the PR Agent, an AI-powered tool for automated pull request analysis, feedback, suggestions and more."""
            pr_comment += "\n\nHere is a list of tools you can use to interact with the PR Agent:\n"
            base_path = "https://pr-agent-docs.codium.ai/tools"

            tool_names = []
            tool_names.append(f"[DESCRIBE]({base_path}/describe/)")
            tool_names.append(f"[REVIEW]({base_path}/review/)")
            tool_names.append(f"[IMPROVE]({base_path}/improve/)")
            tool_names.append(f"[UPDATE CHANGELOG]({base_path}/update_changelog/)")
            tool_names.append(f"[ADD DOCS]({base_path}/documentation/) 💎")
            tool_names.append(f"[TEST]({base_path}/test/) 💎")
            tool_names.append(f"[IMPROVE COMPONENT]({base_path}/improve_component/) 💎")
            tool_names.append(f"[ANALYZE]({base_path}/analyze/) 💎")
            tool_names.append(f"[ASK]({base_path}/ask/)")
            tool_names.append(f"[GENERATE CUSTOM LABELS]({base_path}/custom_labels/) 💎")
            tool_names.append(f"[CI FEEDBACK]({base_path}/ci_feedback/) 💎")
            tool_names.append(f"[CUSTOM PROMPT]({base_path}/custom_prompt/) 💎")
            tool_names.append(f"[SIMILAR ISSUE]({base_path}/similar_issues/)")

            descriptions = []
            descriptions.append("Generates PR description - title, type, summary, code walkthrough and labels")
            descriptions.append("Adjustable feedback about the PR, possible issues, security concerns, review effort and more")
            descriptions.append("Code suggestions for improving the PR")
            descriptions.append("Automatically updates the changelog")
            descriptions.append("Generates documentation to methods/functions/classes that changed in the PR")
            descriptions.append("Generates unit tests for a specific component, based on the PR code change")
            descriptions.append("Code suggestions for a specific component that changed in the PR")
            descriptions.append("Identifies code components that changed in the PR, and enables to interactively generate tests, docs, and code suggestions for each component")
            descriptions.append("Answering free-text questions about the PR")
            descriptions.append("Generates custom labels for the PR, based on specific guidelines defined by the user")
            descriptions.append("Generates feedback and analysis for a failed CI job")
            descriptions.append("Generates custom suggestions for improving the PR code, derived only from a specific guidelines prompt defined by the user")
            descriptions.append("Automatically retrieves and presents similar issues")

            commands  =[]
            commands.append("`/describe`")
            commands.append("`/review`")
            commands.append("`/improve`")
            commands.append("`/update_changelog`")
            commands.append("`/add_docs`")
            commands.append("`/test`")
            commands.append("`/improve_component`")
            commands.append("`/analyze`")
            commands.append("`/ask`")
            commands.append("`/generate_labels`")
            commands.append("`/checks`")
            commands.append("`/custom_prompt`")
            commands.append("`/similar_issue`")

            checkbox_list = []
            checkbox_list.append(" - [ ] Run <!-- /describe -->")
            checkbox_list.append(" - [ ] Run <!-- /review -->")
            checkbox_list.append(" - [ ] Run <!-- /improve -->")
            checkbox_list.append(" - [ ] Run <!-- /update_changelog -->")
            checkbox_list.append(" - [ ] Run <!-- /add_docs -->")
            checkbox_list.append(" - [ ] Run <!-- /test -->")
            checkbox_list.append(" - [ ] Run <!-- /improve_component -->")
            checkbox_list.append(" - [ ] Run <!-- /analyze -->")
            checkbox_list.append("[*]")
            checkbox_list.append("[*]")
            checkbox_list.append("[*]")
            checkbox_list.append("[*]")
            checkbox_list.append("[*]")
            checkbox_list.append("[*]")
            checkbox_list.append("[*]")
            checkbox_list.append("[*]")

            if isinstance(self.git_provider, GithubProvider) and not get_settings().config.get('disable_checkboxes', False):
                pr_comment += f"<table><tr align='left'><th align='left'>Tool</th><th align='left'>Description</th><th align='left'>Trigger Interactively :gem:</th></tr>"
                for i in range(len(tool_names)):
                    pr_comment += f"\n<tr><td align='left'>\n\n<strong>{tool_names[i]}</strong></td>\n<td>{descriptions[i]}</td>\n<td>\n\n{checkbox_list[i]}\n</td></tr>"
                pr_comment += "</table>\n\n"
                pr_comment += f"""\n\n(1) Note that each tool be [triggered automatically](https://pr-agent-docs.codium.ai/usage-guide/automations_and_usage/#github-app-automatic-tools-when-a-new-pr-is-opened) when a new PR is opened, or called manually by [commenting on a PR](https://pr-agent-docs.codium.ai/usage-guide/automations_and_usage/#online-usage)."""
                pr_comment += f"""\n\n(2) Tools marked with [*] require additional parameters to be passed. For example, to invoke the `/ask` tool, you need to comment on a PR: `/ask "<question content>"`. See the relevant documentation for each tool for more details."""
            else:
                pr_comment += f"<table><tr align='left'><th align='left'>Tool</th><th align='left'>Command</th><th align='left'>Description</th></tr>"
                for i in range(len(tool_names)):
                    pr_comment += f"\n<tr><td align='left'>\n\n<strong>{tool_names[i]}</strong></td><td>{commands[i]}</td><td>{descriptions[i]}</td></tr>"
                pr_comment += "</table>\n\n"
                pr_comment += f"""\n\nNote that each tool be [invoked automatically](https://pr-agent-docs.codium.ai/usage-guide/automations_and_usage/) when a new PR is opened, or called manually by [commenting on a PR](https://pr-agent-docs.codium.ai/usage-guide/automations_and_usage/#online-usage)."""
            if get_settings().config.publish_output:
                self.git_provider.publish_comment(pr_comment)
        except Exception as e:
            get_logger().error(f"Error while running PRHelpMessage: {e}")
        return ""