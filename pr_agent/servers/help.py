commands_text = "> **/review [-i]**: Request a review of your Pull Request. For an incremental review, which only " \
                "considers changes since the last review, include the '-i' option.\n" \
                "> **/describe**: Modify the PR title and description based on the contents of the PR.\n" \
                "> **/improve**: Suggest improvements to the code in the PR. \n" \
                "> **/ask \\<QUESTION\\>**: Pose a question about the PR.\n\n" \
                ">To edit any configuration parameter from 'configuration.toml', add --config_path=new_value\n" \
                ">For example: /review --pr_reviewer.extra_instructions=\"focus on the file: ...\" \n" \
                ">To list the possible configuration parameters, use the **/config** command.\n" \


def bot_help_text(user: str):
    return f"> Tag me in a comment '@{user}' and add one of the following commands:\n" + commands_text


actions_help_text = "> To invoke the PR-Agent, add a comment using one of the following commands:\n" + \
                    commands_text
