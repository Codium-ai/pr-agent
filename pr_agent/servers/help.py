commands_text = "> **/review**: Request a review of your Pull Request.   \n" \
                "> **/describe**: Update the PR title and description based on the contents of the PR.   \n" \
                "> **/improve [--extended]**: Suggest code improvements. Extended mode provides a higher quality feedback.   \n" \
                "> **/ask \\<QUESTION\\>**: Ask a question about the PR.   \n" \
                "> **/update_changelog**: Update the changelog based on the PR's contents.   \n" \
                "> see the [tools guide](https://github.com/Codium-ai/pr-agent/blob/main/docs/TOOLS_GUIDE.md) for more details.\n\n" \
                ">To edit any configuration parameter from the [configuration.toml](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/settings/configuration.toml), add --config_path=new_value.  \n" \
                ">For example: /review --pr_reviewer.extra_instructions=\"focus on the file: ...\"    \n" \
                ">To list the possible configuration parameters, add a **/config** comment.   \n" \


def bot_help_text(user: str):
    return f"> Tag me in a comment '@{user}' and add one of the following commands:  \n" + commands_text


actions_help_text = "> To invoke the PR-Agent, add a comment using one of the following commands:  \n" + \
                    commands_text
