# pr_agent/beekeeper/guidelines/beekeeper_style_guidelines_checker.py
from pr_agent.beekeeper.guidelines.beekeeper_style_guidelines_fetcher import BeekeeperStyleGuidelinesFetcher
from loguru import logger

class BeekeeperStyleGuidelinesChecker:
    def __init__(self, config):
        self.config = config
        self.fetcher = BeekeeperStyleGuidelinesFetcher(
            repo_url=config.get("STYLE_GUIDELINES_REPO", "git@github.com:beekpr/beekeeper-engineering-hub"),
            token=config.get("GITHUB_TOKEN"),
            branch=config.get("STYLE_GUIDELINES_BRANCH", "master"),
            target_folder=config.get("STYLE_GUIDELINES_FOLDER", "guidelines")
        )

    def check_files_against_guidelines(self, pr_files):
        """Get style guidelines relevant to the PR files"""
        if not self.config.get("STYLE_GUIDELINES_REPO"):
            logger.warning("Style guidelines repository not configured")
            return ""

        file_paths = list(pr_files.keys())
        relevant_guidelines = self.fetcher.get_relevant_guidelines(file_paths)

        if not relevant_guidelines:
            logger.info("No relevant style guidelines found for these files")
            return ""

        # Format guidelines for inclusion in the LLM prompt
        formatted_guidelines = ["## Custom Coding Style Guidelines"]
        for guideline_path, content in relevant_guidelines.items():
            formatted_guidelines.append(f"### From {guideline_path}:\n{content['plain_text']}")

        return "\n\n".join(formatted_guidelines)