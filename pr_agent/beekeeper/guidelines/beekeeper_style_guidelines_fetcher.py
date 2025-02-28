# pr_agent/beekeeper/guidelines/beekeeper_style_guidelines_fetcher.py
import os
from loguru import logger
from github import Github
from pathlib import Path
import markdown
import html2text

class BeekeeperStyleGuidelinesFetcher:
    def __init__(self, repo_url, token=None, branch="main", target_folder=None):
        """
        Fetch style guidelines from a GitHub repository

        Args:
            repo_url: GitHub repository URL
            token: GitHub token for authentication
            branch: Branch to fetch guidelines from
            target_folder: Specific folder in the repo to fetch guidelines from (optional)
        """
        self.repo_url = repo_url
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.branch = branch
        self.target_folder = target_folder
        self.guidelines_cache = {}

    def fetch_guidelines(self, force_refresh=False):
        """Fetch all markdown files from the guidelines repository"""
        if self.guidelines_cache and not force_refresh:
            return self.guidelines_cache

        try:
            g = Github(self.token)
            repo = g.get_repo(self.repo_url)

            guidelines = {}

            # Start from target folder or root
            start_path = self.target_folder or ""
            try:
                contents = repo.get_contents(start_path, ref=self.branch)
            except Exception as e:
                logger.error(f"Error accessing path '{start_path}': {str(e)}")
                return {}

            # Process markdown files recursively
            while contents:
                content_file = contents.pop(0)
                if content_file.type == "dir":
                    contents.extend(repo.get_contents(content_file.path, ref=self.branch))
                elif content_file.path.endswith('.md'):
                    try:
                        file_content = content_file.decoded_content.decode('utf-8')

                        # Convert markdown to plain text
                        text_maker = html2text.HTML2Text()
                        text_maker.ignore_links = False
                        plain_text = text_maker.handle(markdown.markdown(file_content))

                        guidelines[content_file.path] = {
                            "markdown": file_content,
                            "plain_text": plain_text
                        }
                    except Exception as e:
                        logger.error(f"Error processing file {content_file.path}: {str(e)}")

            self.guidelines_cache = guidelines
            logger.info(f"Fetched {len(guidelines)} style guideline files from {self.repo_url}/{self.target_folder or ''}")
            return guidelines

        except Exception as e:
            logger.error(f"Error fetching style guidelines: {str(e)}")
            return {}

    def get_relevant_guidelines(self, file_paths):
        """Get guidelines relevant to the given file paths"""
        all_guidelines = self.fetch_guidelines()
        if not all_guidelines:
            return {}

        # Extract file extensions
        extensions = {Path(file).suffix.lstrip('.') for file in file_paths if Path(file).suffix}

        # Match guidelines to file extensions
        relevant_guidelines = {}
        for guideline_path, content in all_guidelines.items():
            # Simple matching based on file extension or language indicators
            for ext in extensions:
                if ext.lower() in guideline_path.lower():
                    relevant_guidelines[guideline_path] = content
                    break  # Once matched, no need to check other extensions

            # Also consider general guidelines that might not match specific extensions
            if "general" in guideline_path.lower() or "common" in guideline_path.lower():
                relevant_guidelines[guideline_path] = content

        return relevant_guidelines