import copy
import logging
from datetime import date
from time import sleep
from typing import Tuple

from jinja2 import Environment, StrictUndefined

from pr_agent.algo.ai_handler import AiHandler
from pr_agent.algo.pr_processing import get_pr_diff, retry_with_fallback_models
from pr_agent.algo.token_handler import TokenHandler
from pr_agent.config_loader import get_settings
from pr_agent.git_providers import GithubProvider, get_git_provider
from pr_agent.git_providers.git_provider import get_main_pr_language

CHANGELOG_LINES = 50


class PRUpdateChangelog:
    def __init__(self, pr_url: str, cli_mode=False, args=None):

        self.git_provider = get_git_provider()(pr_url)
        self.main_language = get_main_pr_language(
            self.git_provider.get_languages(), self.git_provider.get_files()
        )
        self.commit_changelog = get_settings().pr_update_changelog.push_changelog_changes
        self._get_changlog_file()  # self.changelog_file_str
        self.ai_handler = AiHandler()
        self.patches_diff = None
        self.prediction = None
        self.cli_mode = cli_mode
        self.vars = {
            "title": self.git_provider.pr.title,
            "branch": self.git_provider.get_pr_branch(),
            "description": self.git_provider.get_pr_description(),
            "language": self.main_language,
            "diff": "",  # empty diff for initial calculation
            "changelog_file_str": self.changelog_file_str,
            "today": date.today(),
            "extra_instructions": get_settings().pr_update_changelog.extra_instructions,
            "commit_messages_str": self.git_provider.get_commit_messages(),
        }
        self.token_handler = TokenHandler(self.git_provider.pr,
                                          self.vars,
                                          get_settings().pr_update_changelog_prompt.system,
                                          get_settings().pr_update_changelog_prompt.user)

    async def run(self):
        # assert type(self.git_provider) == GithubProvider, "Currently only Github is supported"

        logging.info('Updating the changelog...')
        if get_settings().config.publish_output:
            self.git_provider.publish_comment("Preparing changelog updates...", is_temporary=True)
        await retry_with_fallback_models(self._prepare_prediction)
        logging.info('Preparing PR changelog updates...')
        new_file_content, answer = self._prepare_changelog_update()
        if get_settings().config.publish_output:
            self.git_provider.remove_initial_comment()
            logging.info('Publishing changelog updates...')
            if self.commit_changelog:
                logging.info('Pushing PR changelog updates to repo...')
                self._push_changelog_update(new_file_content, answer)
            else:
                logging.info('Publishing PR changelog as comment...')
                self.git_provider.publish_comment(f"**Changelog updates:**\n\n{answer}")

    async def _prepare_prediction(self, model: str):
        logging.info('Getting PR diff...')
        self.patches_diff = get_pr_diff(self.git_provider, self.token_handler, model)
        logging.info('Getting AI prediction...')
        self.prediction = await self._get_prediction(model)

    async def _get_prediction(self, model: str):
        variables = copy.deepcopy(self.vars)
        variables["diff"] = self.patches_diff  # update diff
        environment = Environment(undefined=StrictUndefined)
        system_prompt = environment.from_string(get_settings().pr_update_changelog_prompt.system).render(variables)
        user_prompt = environment.from_string(get_settings().pr_update_changelog_prompt.user).render(variables)
        if get_settings().config.verbosity_level >= 2:
            logging.info(f"\nSystem prompt:\n{system_prompt}")
            logging.info(f"\nUser prompt:\n{user_prompt}")
        response, finish_reason = await self.ai_handler.chat_completion(model=model, temperature=0.2,
                                                                        system=system_prompt, user=user_prompt)

        return response

    def _prepare_changelog_update(self) -> Tuple[str, str]:
        answer = self.prediction.strip().strip("```").strip()  # noqa B005
        if hasattr(self, "changelog_file"):
            existing_content = self.changelog_file.decoded_content.decode()
        else:
            existing_content = ""
        if existing_content:
            new_file_content = answer + "\n\n" + self.changelog_file.decoded_content.decode()
        else:
            new_file_content = answer

        if not self.commit_changelog:
            answer += "\n\n\n>to commit the new content to the CHANGELOG.md file, please type:" \
                      "\n>'/update_changelog --pr_update_changelog.push_changelog_changes=true'\n"

        if get_settings().config.verbosity_level >= 2:
            logging.info(f"answer:\n{answer}")

        return new_file_content, answer

    def _push_changelog_update(self, new_file_content, answer):
        self.git_provider.repo_obj.update_file(path=self.changelog_file.path,
                                               message="Update CHANGELOG.md",
                                               content=new_file_content,
                                               sha=self.changelog_file.sha,
                                               branch=self.git_provider.get_pr_branch())
        d = dict(body="CHANGELOG.md update",
                 path=self.changelog_file.path,
                 line=max(2, len(answer.splitlines())),
                 start_line=1)

        sleep(5)  # wait for the file to be updated
        last_commit_id = list(self.git_provider.pr.get_commits())[-1]
        try:
            self.git_provider.pr.create_review(commit=last_commit_id, comments=[d])
        except Exception:
            # we can't create a review for some reason, let's just publish a comment
            self.git_provider.publish_comment(f"**Changelog updates:**\n\n{answer}")


    def _get_default_changelog(self):
        example_changelog = \
"""
Example:
## <current_date>

### Added
...
### Changed
...
### Fixed
...
"""
        return example_changelog

    def _get_changlog_file(self):
        try:
            self.changelog_file = self.git_provider.repo_obj.get_contents("CHANGELOG.md",
                                                                          ref=self.git_provider.get_pr_branch())
            changelog_file_lines = self.changelog_file.decoded_content.decode().splitlines()
            changelog_file_lines = changelog_file_lines[:CHANGELOG_LINES]
            self.changelog_file_str = "\n".join(changelog_file_lines)
        except Exception:
            self.changelog_file_str = ""
            if self.commit_changelog:
                logging.info("No CHANGELOG.md file found in the repository. Creating one...")
                changelog_file = self.git_provider.repo_obj.create_file(path="CHANGELOG.md",
                                                                             message='add CHANGELOG.md',
                                                                             content="",
                                                                             branch=self.git_provider.get_pr_branch())
                self.changelog_file = changelog_file['content']

        if not self.changelog_file_str:
            self.changelog_file_str = self._get_default_changelog()
