commands_text = "> **/review [-i]**: Request a review of your Pull Request. For an incremental review, which only " \
                "considers changes since the last review, include the '-i' option.\n" \
                "> **/describe [-c]**: Modify the PR title and description based on the contents of the PR. " \
                "To get the description as comment instead of modifying the PR description, " \
                "include the '-c' option.\n" \
                "> **/improve**: Suggest improvements to the code in the PR. " \
                "These will be provided as pull request comments, ready to commit.\n" \
                "> **/ask \\<QUESTION\\>**: Pose a question about the PR.\n"


def bot_help_text(user: str):
    return f"> Tag me in a comment '@{user}' and add one of the following commands:\n" + commands_text


actions_help_text = "> To invoke the PR-Agent, add a comment using one of the following commands:\n" + \
                    commands_text
