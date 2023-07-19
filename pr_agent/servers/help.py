commands_text = "> /review      Request a review of the latest update to the PR.\n" \
                "> /review -i   Incremental review - consider only the changes from the last review.\n" \
                "> /describe    Modify the PR title and description based on the contents of the PR.\n" \
                "> /improve     Suggest improvements to the code in the PR. " \
                "These will be provided as pull request comments, ready to commit.\n" \
                "> /ask <QUESTION>  Pose a question about the PR.\n"


def bot_help_text(user: str):
    return f"> Tag me in a comment '@{user}' and add one of the following commands:\n" + commands_text


actions_help_text = "> To invoke the PR-Agent, add a comment using one of the following commands:\n" + \
                    commands_text
