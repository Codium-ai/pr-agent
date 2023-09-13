import copy
import json
import logging
from enum import Enum
from typing import List, Tuple
import pinecone
import openai
import pandas as pd
from pydantic import BaseModel, Field

from pr_agent.algo import MAX_TOKENS
from pr_agent.algo.token_handler import TokenHandler
from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider
from pinecone_datasets import Dataset, DatasetMetadata

MODEL = "text-embedding-ada-002"


class PRSimilarIssue:
    def __init__(self, issue_url: str, args: list = None):
        if get_settings().config.git_provider != "github":
            raise Exception("Only github is supported for similar issue tool")

        self.cli_mode = get_settings().CONFIG.CLI_MODE
        self.max_issues_to_scan = get_settings().pr_similar_issue.max_issues_to_scan
        self.issue_url = issue_url
        self.git_provider = get_git_provider()()
        repo_name, issue_number = self.git_provider._parse_issue_url(issue_url.split('=')[-1])
        self.git_provider.repo = repo_name
        self.git_provider.repo_obj = self.git_provider.github_client.get_repo(repo_name)
        self.token_handler = TokenHandler()
        repo_obj = self.git_provider.repo_obj
        repo_name_for_index = self.repo_name_for_index = repo_obj.full_name.lower().replace('/', '-').replace('_/', '-')
        index_name = self.index_name = "codium-ai-pr-agent-issues"

        # assuming pinecone api key and environment are set in secrets file
        try:
            api_key = get_settings().pinecone.api_key
            environment = get_settings().pinecone.environment
        except Exception:
            if not self.cli_mode:
                repo_name, original_issue_number = self.git_provider._parse_issue_url(self.issue_url.split('=')[-1])
                issue_main = self.git_provider.repo_obj.get_issue(original_issue_number)
                issue_main.create_comment("Please set pinecone api key and environment in secrets file")
            raise Exception("Please set pinecone api key and environment in secrets file")

        # check if index exists, and if repo is already indexed
        run_from_scratch = False
        upsert = True
        pinecone.init(api_key=api_key, environment=environment)
        if not index_name in pinecone.list_indexes():
            run_from_scratch = True
            upsert = False
        else:
            if get_settings().pr_similar_issue.force_update_dataset:
                upsert = True
            else:
                pinecone_index = pinecone.Index(index_name=index_name)
                res = pinecone_index.fetch([f"example_issue_{repo_name_for_index}"]).to_dict()
                if res["vectors"]:
                    upsert = False

        if run_from_scratch or upsert:  # index the entire repo
            logging.info('Indexing the entire repo...')

            logging.info('Getting issues...')
            issues = list(repo_obj.get_issues(state='all'))
            logging.info('Done')
            self._update_index_with_issues(issues, repo_name_for_index, upsert=upsert)
        else:  # update index if needed
            pinecone_index = pinecone.Index(index_name=index_name)
            issues_to_update = []
            issues_paginated_list = repo_obj.get_issues(state='all')
            counter = 1
            for issue in issues_paginated_list:
                if issue.pull_request:
                    continue
                issue_str, comments, number = self._process_issue(issue)
                issue_key = f"issue_{number}"
                id = issue_key + "." + "issue"
                res = pinecone_index.fetch([id]).to_dict()
                is_new_issue = True
                for vector in res["vectors"].values():
                    if vector['metadata']['repo'] == repo_name_for_index:
                        is_new_issue = False
                        break
                if is_new_issue:
                    counter += 1
                    issues_to_update.append(issue)
                else:
                    break

            if issues_to_update:
                logging.info(f'Updating index with {counter} new issues...')
                self._update_index_with_issues(issues_to_update, repo_name_for_index, upsert=True)
            else:
                logging.info('No new issues to update')

    async def run(self):
        logging.info('Getting issue...')
        repo_name, original_issue_number = self.git_provider._parse_issue_url(self.issue_url.split('=')[-1])
        issue_main = self.git_provider.repo_obj.get_issue(original_issue_number)
        issue_str, comments, number = self._process_issue(issue_main)
        openai.api_key = get_settings().openai.key
        logging.info('Done')

        logging.info('Querying...')
        res = openai.Embedding.create(input=[issue_str], engine=MODEL)
        embeds = [record['embedding'] for record in res['data']]
        pinecone_index = pinecone.Index(index_name=self.index_name)
        res = pinecone_index.query(embeds[0],
                                   top_k=5,
                                   filter={"repo": self.repo_name_for_index},
                                   include_metadata=True).to_dict()
        relevant_issues_number_list = []
        relevant_comment_number_list = []
        score_list = []
        for r in res['matches']:
            issue_number = int(r["id"].split('.')[0].split('_')[-1])
            if original_issue_number == issue_number:
                continue
            if issue_number not in relevant_issues_number_list:
                relevant_issues_number_list.append(issue_number)
            if 'comment' in r["id"]:
                relevant_comment_number_list.append(int(r["id"].split('.')[1].split('_')[-1]))
            else:
                relevant_comment_number_list.append(-1)
            score_list.append(str("{:.2f}".format(r['score'])))
        logging.info('Done')

        logging.info('Publishing response...')
        similar_issues_str = "### Similar Issues\n___\n\n"
        for i, issue_number_similar in enumerate(relevant_issues_number_list):
            issue = self.git_provider.repo_obj.get_issue(issue_number_similar)
            title = issue.title
            url = issue.html_url
            if relevant_comment_number_list[i] != -1:
                url = list(issue.get_comments())[relevant_comment_number_list[i]].html_url
            similar_issues_str += f"{i + 1}. **[{title}]({url})** (score={score_list[i]})\n\n"
        if get_settings().config.publish_output:
            response = issue_main.create_comment(similar_issues_str)
        logging.info(similar_issues_str)
        logging.info('Done')

    def _process_issue(self, issue):
        header = issue.title
        body = issue.body
        number = issue.number
        if get_settings().pr_similar_issue.skip_comments:
            comments = []
        else:
            comments = list(issue.get_comments())
        issue_str = f"Issue Header: \"{header}\"\n\nIssue Body:\n{body}"
        return issue_str, comments, number

    def _update_index_with_issues(self, issues_list, repo_name_for_index, upsert=False):
        logging.info('Processing issues...')
        corpus = Corpus()
        example_issue_record = Record(
            id=f"example_issue_{repo_name_for_index}",
            text="example_issue",
            metadata=Metadata(repo=repo_name_for_index)
        )
        corpus.append(example_issue_record)

        counter = 0
        for issue in issues_list:
            if issue.pull_request:
                continue

            counter += 1
            if counter % 100 == 0:
                logging.info(f"Scanned {counter} issues")
            if counter >= self.max_issues_to_scan:
                logging.info(f"Scanned {self.max_issues_to_scan} issues, stopping")
                break

            issue_str, comments, number = self._process_issue(issue)
            issue_key = f"issue_{number}"
            username = issue.user.login
            created_at = str(issue.created_at)
            if len(issue_str) < 8000 or \
                    self.token_handler.count_tokens(issue_str) < MAX_TOKENS[MODEL]:  # fast reject first
                issue_record = Record(
                    id=issue_key + "." + "issue",
                    text=issue_str,
                    metadata=Metadata(repo=repo_name_for_index,
                                      username=username,
                                      created_at=created_at,
                                      level=IssueLevel.ISSUE)
                )
                corpus.append(issue_record)
                if comments:
                    for j, comment in enumerate(comments):
                        comment_body = comment.body
                        num_words_comment = len(comment_body.split())
                        if num_words_comment < 10 or not isinstance(comment_body, str):
                            continue

                        if len(comment_body) < 8000 or \
                                self.token_handler.count_tokens(comment_body) < MAX_TOKENS[MODEL]:
                            comment_record = Record(
                                id=issue_key + ".comment_" + str(j + 1),
                                text=comment_body,
                                metadata=Metadata(repo=repo_name_for_index,
                                                  username=username,  # use issue username for all comments
                                                  created_at=created_at,
                                                  level=IssueLevel.COMMENT)
                            )
                            corpus.append(comment_record)
        df = pd.DataFrame(corpus.dict()["documents"])
        logging.info('Done')

        logging.info('Embedding...')
        openai.api_key = get_settings().openai.key
        list_to_encode = list(df["text"].values)
        try:
            res = openai.Embedding.create(input=list_to_encode, engine=MODEL)
            embeds = [record['embedding'] for record in res['data']]
        except:
            embeds = []
            logging.error('Failed to embed entire list, embedding one by one...')
            for i, text in enumerate(list_to_encode):
                try:
                    res = openai.Embedding.create(input=[text], engine=MODEL)
                    embeds.append(res['data'][0]['embedding'])
                except:
                    embeds.append([0] * 1536)
        df["values"] = embeds
        meta = DatasetMetadata.empty()
        meta.dense_model.dimension = len(embeds[0])
        ds = Dataset.from_pandas(df, meta)
        logging.info('Done')

        api_key = get_settings().pinecone.api_key
        environment = get_settings().pinecone.environment
        if not upsert:
            logging.info('Creating index from scratch...')
            ds.to_pinecone_index(self.index_name, api_key=api_key, environment=environment)
        else:
            logging.info('Upserting index...')
            namespace = ""
            batch_size: int = 100
            concurrency: int = 10
            pinecone.init(api_key=api_key, environment=environment)
            ds._upsert_to_index(self.index_name, namespace, batch_size, concurrency)
        logging.info('Done')


class IssueLevel(str, Enum):
    ISSUE = "issue"
    COMMENT = "comment"


class Metadata(BaseModel):
    repo: str
    username: str = Field(default="@codium")
    created_at: str = Field(default="01-01-1970 00:00:00.00000")
    level: IssueLevel = Field(default=IssueLevel.ISSUE)

    class Config:
        use_enum_values = True


class Record(BaseModel):
    id: str
    text: str
    metadata: Metadata


class Corpus(BaseModel):
    documents: List[Record] = Field(default=[])

    def append(self, r: Record):
        self.documents.append(r)
