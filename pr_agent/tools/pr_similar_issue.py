import time
from enum import Enum
from typing import List

import openai
import pandas as pd
import pinecone
from pinecone_datasets import Dataset, DatasetMetadata
from pydantic import BaseModel, Field

from pr_agent.algo import MAX_TOKENS
from pr_agent.algo.token_handler import TokenHandler
from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider
from pr_agent.log import get_logger

MODEL = "text-embedding-ada-002"


class PRSimilarIssue:
    def __init__(self, issue_url: str, args: list = None):

        self.cli_mode = get_settings().CONFIG.CLI_MODE
        self.max_issues_to_scan = get_settings().pr_similar_issue.max_issues_to_scan
        self.issue_url = issue_url
        self.git_provider = get_git_provider()()
        self.git_provider.repo_obj  = self.git_provider.parse_issue_url_and_get_repo_obj(issue_url.split('=')[-1])
        self.token_handler = TokenHandler()
        repo_obj = self.git_provider.repo_obj
        repo_name_for_index = self.repo_name_for_index = self.git_provider.get_repo_name_for_indexing(repo_obj)
        index_name = self.index_name = "codium-ai-pr-agent-issues"

        # assuming pinecone api key and environment are set in secrets file
        try:
            api_key = get_settings().pinecone.api_key
            environment = get_settings().pinecone.environment
        except Exception:
            if not self.cli_mode:
                issue_main = self.git_provider.parse_issue_url_and_get_issue(self.issue_url.split('=')[-1])
                issue_main.create_comment("Please set pinecone api key and environment in secrets file")
            raise Exception("Please set pinecone api key and environment in secrets file")

        # check if index exists, and if repo is already indexed
        run_from_scratch = False
        if run_from_scratch:  # for debugging
            pinecone.init(api_key=api_key, environment=environment)
            if index_name in pinecone.list_indexes():
                get_logger().info('Removing index...')
                pinecone.delete_index(index_name)
                get_logger().info('Done')

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
            get_logger().info('Indexing the entire repo...')

            get_logger().info('Getting issues...')
            issues = self.git_provider.get_repo_issues(repo_obj)
            get_logger().info('Done')
            self._update_index_with_issues(issues, repo_name_for_index, upsert=upsert)
        else:  # update index if needed
            pinecone_index = pinecone.Index(index_name=index_name)
            issues_to_update = []
            issues_paginated_list = self.git_provider.get_repo_issues(repo_obj)
            counter = 1
            for issue in issues_paginated_list:
                issue_pull_request = self.git_provider.check_if_issue_pull_request(issue)
                if issue_pull_request:
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
                get_logger().info(f'Updating index with {counter} new issues...')
                self._update_index_with_issues(issues_to_update, repo_name_for_index, upsert=True)
            else:
                get_logger().info('No new issues to update')

    async def run(self):
        get_logger().info('Getting issue...')
        issue_main, original_issue_number = self.git_provider.get_issue(self.issue_url.split('=')[-1])
        issue_str, comments, number = self._process_issue(issue_main)
        openai.api_key = get_settings().openai.key
        get_logger().info('Done')

        get_logger().info('Querying...')
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
            # skip example issue
            if 'example_issue_' in r["id"]:
                continue

            try:
                issue_number = int(r["id"].split('.')[0].split('_')[-1])
            except:
                get_logger().debug(f"Failed to parse issue number from {r['id']}")
                continue

            if original_issue_number == issue_number:
                continue
            if issue_number not in relevant_issues_number_list:
                relevant_issues_number_list.append(issue_number)
            if 'comment' in r["id"]:
                relevant_comment_number_list.append(int(r["id"].split('.')[1].split('_')[-1]))
            else:
                relevant_comment_number_list.append(-1)
            score_list.append(str("{:.2f}".format(r['score'])))
        get_logger().info('Done')

        get_logger().info('Publishing response...')
        similar_issues_str = "### Similar Issues\n___\n\n"
        for i, issue_number_similar in enumerate(relevant_issues_number_list):
            issue = self.git_provider.parse_issue_url_and_get_similar_issues(self.issue_url.split('=')[-1], issue_number_similar)
            title = issue.title
            url = self.git_provider.get_issue_url(issue)
            similar_issues_str += f"{i + 1}. **[{title}]({url})** (score={score_list[i]})\n\n"
        if get_settings().config.publish_output:
            response = self.git_provider.parse_issue_url_and_create_comment(similar_issues_str, self.issue_url.split('=')[-1], original_issue_number)
        get_logger().info(similar_issues_str)
        get_logger().info('Done')

    def _process_issue(self, issue):
        header = issue.title
        body = self.git_provider.get_issue_body(issue)
        number = self.git_provider.get_issue_number(issue)
        if get_settings().pr_similar_issue.skip_comments:
            comments = []
        else:
            comments = self.git_provider.parse_issue_url_and_get_comments(self.issue_url.split('=')[-1])
            print('comments: ', comments)
        issue_str = f"Issue Header: \"{header}\"\n\nIssue Body:\n{body}"
        return issue_str, comments, number

    def _update_index_with_issues(self, issues_list, repo_name_for_index, upsert=False):
        get_logger().info('Processing issues...')
        corpus = Corpus()
        example_issue_record = Record(
            id=f"example_issue_{repo_name_for_index}",
            text="example_issue",
            metadata=Metadata(repo=repo_name_for_index)
        )
        corpus.append(example_issue_record)

        counter = 0
        for issue in issues_list:

            issue_pull_request = self.git_provider.check_if_issue_pull_request(issue)
            if issue_pull_request:
                continue

            counter += 1
            if counter % 100 == 0:
                get_logger().info(f"Scanned {counter} issues")
            if counter >= self.max_issues_to_scan:
                get_logger().info(f"Scanned {self.max_issues_to_scan} issues, stopping")
                break

            issue_str, comments, number = self._process_issue(issue)
            issue_key = f"issue_{number}"
            username = self.git_provider.get_username(issue, self.issue_url.split('=')[-1])
            created_at = self.git_provider.get_issue_created_at(issue)
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
                        comment_body = self.git_provider.get_issue_comment_body(comment)
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
        get_logger().info('Done')

        get_logger().info('Embedding...')
        openai.api_key = get_settings().openai.key
        list_to_encode = list(df["text"].values)
        try:
            res = openai.Embedding.create(input=list_to_encode, engine=MODEL)
            embeds = [record['embedding'] for record in res['data']]
        except:
            embeds = []
            get_logger().error('Failed to embed entire list, embedding one by one...')
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
        get_logger().info('Done')

        api_key = get_settings().pinecone.api_key
        environment = get_settings().pinecone.environment
        if not upsert:
            get_logger().info('Creating index from scratch...')
            ds.to_pinecone_index(self.index_name, api_key=api_key, environment=environment)
            time.sleep(15)  # wait for pinecone to finalize indexing before querying
        else:
            get_logger().info('Upserting index...')
            namespace = ""
            batch_size: int = 100
            concurrency: int = 10
            pinecone.init(api_key=api_key, environment=environment)
            ds._upsert_to_index(self.index_name, namespace, batch_size, concurrency)
            time.sleep(5)  # wait for pinecone to finalize upserting before querying
        get_logger().info('Done')


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
