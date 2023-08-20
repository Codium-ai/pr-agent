import copy
import json
import logging
from typing import List, Tuple

from jinja2 import Environment, StrictUndefined

from pr_agent.algo.ai_handler import AiHandler
from pr_agent.algo.pr_processing import get_pr_diff, retry_with_fallback_models
from pr_agent.algo.token_handler import TokenHandler
from pr_agent.algo.utils import load_yaml
from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider
from pr_agent.git_providers.git_provider import get_main_pr_language


class PRSimilarIssue:
    def __init__(self, pr_url: str, issue_url: str, args: list = None):
        load_data_from_local = True
        if not load_data_from_local:
            self.git_provider = get_git_provider()()
            repo_name, issue_number = self.git_provider._parse_issue_url(issue_url.split('=')[-1])
            self.git_provider.repo = repo_name
            self.git_provider.repo_obj = self.git_provider.github_client.get_repo(repo_name)
            repo_obj = self.git_provider.repo_obj

            def _process_issue(issue):
                header = body = issue_str = comments_str = ""
                if issue.pull_request:
                    return header, body, issue_str, comments_str
                header = issue.title
                body = issue.body
                comments_obj = list(issue.get_comments())
                comments_str = ""
                for i, comment in enumerate(comments_obj):
                    comments_str += f"comment {i}:\n{comment.body}\n\n\n"
                issue_str = f"Issue Header: \"{header}\"\n\nIssue Body:\n{body}"
                return header, body, issue_str, comments_str

            main_issue = repo_obj.get_issue(issue_number)
            assert not main_issue.pull_request
            _, _, main_issue_str, main_comments_str = _process_issue(main_issue)

            issues_str_list = []
            comments_str_list = []
            issues = list(repo_obj.get_issues(state='all')) # 'open', 'closed', 'all'
            for i, issue in enumerate(issues):
                if issue.url == main_issue.url:
                    continue
                if issue.pull_request:
                    continue
                _, _, issue_str, comments_str = _process_issue(issue)
                issues_str_list.append(issue_str)
                comments_str_list.append(comments_str)

            json_output = {}
            json_output['main_issue'] = {}
            json_output['main_issue']['issue'] = main_issue_str
            json_output['main_issue']['comment'] = main_comments_str
            json_output['issues'] = {}
            for i in range(len(issues_str_list)):
                json_output['issues'][f'issue_{i}'] = {}
                json_output['issues'][f'issue_{i}']['issue'] = issues_str_list[i]
                json_output['issues'][f'issue_{i}'][f'comments'] = comments_str_list[i]

            jsonFile = open("/Users/talrid/Desktop/issues_data.json", "w")
            jsonFile.write(json.dumps(json_output))
            jsonFile.close()
        else:
            jsonFile = open("/Users/talrid/Desktop/issues_data.json", "r")
            json_output=json.loads(jsonFile.read())

            from langchain.document_loaders import TextLoader
            from langchain.text_splitter import CharacterTextSplitter
            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)

            aaa=3
