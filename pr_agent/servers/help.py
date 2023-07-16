commands_text = "> /review - Ask for a new review after your update the PR\n" \
                "> /describe - Modify the PR title and description based " \
                "on the PR's contents.\n" \
                "> /improve - Suggest improvements to the code in the PR as pull " \
                "request comments ready to commit.\n" \
                "> /ask <QUESTION> - Ask a question about the PR.\n"


def bot_help_text(user: str):
    return f"> Tag me in a comment '@{user}' and add one of the following commands:\n" + commands_text


actions_help_text = "> Add a comment to to invoke PR-Agent, use one of the following commands:\n" + \
                    commands_text
