import copy
from datetime import date
from functools import partial
from time import sleep
from typing import Tuple
from jinja2 import Environment, StrictUndefined
from pr_agent.algo.ai_handlers.base_ai_handler import BaseAiHandler
from pr_agent.algo.ai_handlers.litellm_ai_handler import LiteLLMAIHandler
from pr_agent.algo.pr_processing import get_pr_diff, retry_with_fallback_models
from pr_agent.algo.token_handler import TokenHandler
from pr_agent.algo.utils import ModelType, show_relevant_configurations
from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider, GithubProvider
from pr_agent.git_providers.git_provider import get_main_pr_language
from pr_agent.log import get_logger

CHANGELOG_LINES = 50


class PRUpdateChangelog:
    def __init__(self, pr_url: str, cli_mode=False, args=None, ai_handler: partial[BaseAiHandler,] = LiteLLMAIHandler):

        self.git_provider = get_git_provider()(pr_url)
        self.main_language = get_main_pr_language(
            self.git_provider.get_languages(), self.git_provider.get_files()
        )
        self.commit_changelog = get_settings().pr_update_changelog.push_changelog_changes
        self._get_changelog_file()  # self.changelog_file_str

        self.ai_handler = ai_handler()
        self.ai_handler.main_pr_language = self.main_language

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
        get_logger().info('Updating the changelog...')
        relevant_configs = {'pr_update_changelog': dict(get_settings().pr_update_changelog),
                            'config': dict(get_settings().config)}
        get_logger().debug("Relevant configs", artifacts=relevant_configs)

        # currently only GitHub is supported for pushing changelog changes
        if get_settings().pr_update_changelog.push_changelog_changes and not hasattr(
            self.git_provider, "create_or_update_pr_file"
        ):
            get_logger().error(
                "Pushing changelog changes is not currently supported for this code platform"
            )
            if get_settings().config.publish_output:
                self.git_provider.publish_comment(
                    "Pushing changelog changes is not currently supported for this code platform"
                )
            return

        if get_settings().config.publish_output:
            self.git_provider.publish_comment("Preparing changelog updates...", is_temporary=True)

        await retry_with_fallback_models(self._prepare_prediction, model_type=ModelType.TURBO)

        new_file_content, answer = self._prepare_changelog_update()

        # Output the relevant configurations if enabled
        if get_settings().get('config', {}).get('output_relevant_configurations', False):
            answer += show_relevant_configurations(relevant_section='pr_update_changelog')

        get_logger().debug(f"PR output", artifact=answer)

        if get_settings().config.publish_output:
            self.git_provider.remove_initial_comment()
            if self.commit_changelog:
                self._push_changelog_update(new_file_content, answer)
            else:
                self.git_provider.publish_comment(f"**Changelog updates:** 🔄\n\n{answer}")

    async def _prepare_prediction(self, model: str):
        self.patches_diff = get_pr_diff(self.git_provider, self.token_handler, model)
        if self.patches_diff:
            get_logger().debug(f"PR diff", artifact=self.patches_diff)
            self.prediction = await self._get_prediction(model)
        else:
            get_logger().error(f"Error getting PR diff")
            self.prediction = ""

    async def _get_prediction(self, model: str):
        variables = copy.deepcopy(self.vars)
        variables["diff"] = self.patches_diff  # update diff
        environment = Environment(undefined=StrictUndefined)
        system_prompt = environment.from_string(get_settings().pr_update_changelog_prompt.system).render(variables)
        user_prompt = environment.from_string(get_settings().pr_update_changelog_prompt.user).render(variables)
        response, finish_reason = await self.ai_handler.chat_completion(model=model, temperature=0.2,
                                                                        system=system_prompt, user=user_prompt)

        return response

    def _prepare_changelog_update(self) -> Tuple[str, str]:
        answer = self.prediction.strip().strip("```").strip()  # noqa B005
        if hasattr(self, "changelog_file"):
            existing_content = self.changelog_file
        else:
            existing_content = ""
        if existing_content:
            new_file_content = answer + "\n\n" + self.changelog_file
        else:
            new_file_content = answer

        if not self.commit_changelog:
            answer += "\n\n\n>to commit the new content to the CHANGELOG.md file, please type:" \
                      "\n>'/update_changelog --pr_update_changelog.push_changelog_changes=true'\n"

        return new_file_content, answer

    def _push_changelog_update(self, new_file_content, answer):
        self.git_provider.create_or_update_pr_file(
            file_path="CHANGELOG.md",
            branch=self.git_provider.get_pr_branch(),
            contents=new_file_content,
            message="Update CHANGELOG.md",
        )

        sleep(5)  # wait for the file to be updated
        try:
            if get_settings().config.git_provider == "github":
                last_commit_id = list(self.git_provider.pr.get_commits())[-1]
                d = dict(
                    body="CHANGELOG.md update",
                    path="CHANGELOG.md",
                    line=max(2, len(answer.splitlines())),
                    start_line=1,
                )
                self.git_provider.pr.create_review(commit=last_commit_id, comments=[d])
        except Exception:
            # we can't create a review for some reason, let's just publish a comment
            self.git_provider.publish_comment(f"**Changelog updates: 🔄**\n\n{answer}")

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

    def _get_changelog_file(self):
        try:
            self.changelog_file = self.git_provider.get_pr_file_content(
                "CHANGELOG.md", self.git_provider.get_pr_branch()
            )
            changelog_file_lines = self.changelog_file.splitlines()
            changelog_file_lines = changelog_file_lines[:CHANGELOG_LINES]
            self.changelog_file_str = "\n".join(changelog_file_lines)
        except Exception:
            self.changelog_file_str = ""
            self.changelog_file = ""

        if not self.changelog_file_str:
            self.changelog_file_str = self._get_default_changelog()
