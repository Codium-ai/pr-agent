import os
import traceback
import zipfile
import tempfile
import copy
from functools import partial

from jinja2 import Environment, StrictUndefined

from pr_agent.algo.ai_handlers.base_ai_handler import BaseAiHandler
from pr_agent.algo.ai_handlers.litellm_ai_handler import LiteLLMAIHandler
from pr_agent.algo.pr_processing import retry_with_fallback_models
from pr_agent.algo.token_handler import TokenHandler
from pr_agent.algo.utils import ModelType, load_yaml
from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider, GithubProvider, BitbucketServerProvider, \
    get_git_provider_with_context
from pr_agent.log import get_logger


def extract_header(snippet):
    res = ''
    lines = snippet.split('===Snippet content===')[0].split('\n')
    highest_header = ''
    highest_level = float('inf')
    for line in lines[::-1]:
        line = line.strip()
        if line.startswith('Header '):
            highest_header = line.split(': ')[1]
    if highest_header:
        res = f"#{highest_header.lower().replace(' ', '-')}"
    return res

class PRHelpMessage:
    def __init__(self, pr_url: str, args=None, ai_handler: partial[BaseAiHandler,] = LiteLLMAIHandler):
        self.git_provider = get_git_provider_with_context(pr_url)
        self.ai_handler = ai_handler()
        self.question_str = self.parse_args(args)
        self.num_retrieved_snippets = get_settings().get('pr_help.num_retrieved_snippets', 5)
        if self.question_str:
            self.vars = {
                "question": self.question_str,
                "snippets": "",
            }
            self.token_handler = TokenHandler(None,
                                              self.vars,
                                              get_settings().pr_help_prompts.system,
                                              get_settings().pr_help_prompts.user)

    async def _prepare_prediction(self, model: str):
        try:
            variables = copy.deepcopy(self.vars)
            environment = Environment(undefined=StrictUndefined)
            system_prompt = environment.from_string(get_settings().pr_help_prompts.system).render(variables)
            user_prompt = environment.from_string(get_settings().pr_help_prompts.user).render(variables)
            response, finish_reason = await self.ai_handler.chat_completion(
                model=model, temperature=get_settings().config.temperature, system=system_prompt, user=user_prompt)
            return response
        except Exception as e:
            get_logger().error(f"Error while preparing prediction: {e}")
            return ""

    def parse_args(self, args):
        if args and len(args) > 0:
            question_str = " ".join(args)
        else:
            question_str = ""
        return question_str

    def get_sim_results_from_s3_db(self, embeddings):
        get_logger().info("Loading the S3 index...")
        sim_results = []
        try:
            from langchain_chroma import Chroma
            from urllib import request
            with tempfile.TemporaryDirectory() as temp_dir:
                # Define the local file path within the temporary directory
                local_file_path = os.path.join(temp_dir, 'chroma_db.zip')

                bucket = 'pr-agent'
                file_name = 'chroma_db.zip'
                s3_url = f'https://{bucket}.s3.amazonaws.com/{file_name}'
                request.urlretrieve(s3_url, local_file_path)

                # # Download the file from S3 to the temporary directory
                # s3 = boto3.client('s3')
                # s3.download_file(bucket, file_name, local_file_path)

                # Extract the contents of the zip file
                with zipfile.ZipFile(local_file_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)

                vectorstore = Chroma(persist_directory=temp_dir + "/chroma_db",
                                     embedding_function=embeddings)
                sim_results = vectorstore.similarity_search_with_score(self.question_str, k=self.num_retrieved_snippets)
        except Exception as e:
            get_logger().error(f"Error while getting sim from S3: {e}",
                               artifact={"traceback": traceback.format_exc()})
        return sim_results

    def get_sim_results_from_local_db(self, embeddings):
        get_logger().info("Loading the local index...")
        sim_results = []
        try:
            from langchain_chroma import Chroma
            get_logger().info("Loading the Chroma index...")
            db_path = "./docs/chroma_db.zip"
            if not os.path.exists(db_path):
                db_path= "/app/docs/chroma_db.zip"
                if not os.path.exists(db_path):
                    get_logger().error("Local db not found")
                    return sim_results
            with tempfile.TemporaryDirectory() as temp_dir:

                # Extract the ZIP file
                with zipfile.ZipFile(db_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)

                vectorstore = Chroma(persist_directory=temp_dir + "/chroma_db",
                                     embedding_function=embeddings)

                # Do similarity search
                sim_results = vectorstore.similarity_search_with_score(self.question_str, k=self.num_retrieved_snippets)
        except Exception as e:
            get_logger().error(f"Error while getting sim from local db: {e}",
                               artifact={"traceback": traceback.format_exc()})
        return sim_results

    def get_sim_results_from_pinecone_db(self, embeddings):
        get_logger().info("Loading the Pinecone index...")
        sim_results = []
        try:
            from langchain_pinecone import PineconeVectorStore
            INDEX_NAME = "pr-agent-docs"
            vectorstore = PineconeVectorStore(
                index_name=INDEX_NAME, embedding=embeddings,
                pinecone_api_key=get_settings().pinecone.api_key
            )

            # Do similarity search
            sim_results = vectorstore.similarity_search_with_score(self.question_str, k=self.num_retrieved_snippets)
        except Exception as e:
            get_logger().error(f"Error while getting sim from Pinecone db: {e}",
                               artifact={"traceback": traceback.format_exc()})
        return sim_results

    async def run(self):
        try:
            if self.question_str:
                get_logger().info(f'Answering a PR question about the PR {self.git_provider.pr_url} ')

                if not get_settings().get('openai.key'):
                    if get_settings().config.publish_output:
                        self.git_provider.publish_comment(
                            "The `Help` tool chat feature requires an OpenAI API key for calculating embeddings")
                    else:
                        get_logger().error("The `Help` tool chat feature requires an OpenAI API key for calculating embeddings")
                    return

                # Initialize embeddings
                from langchain_openai import OpenAIEmbeddings
                embeddings = OpenAIEmbeddings(model="text-embedding-3-small",
                                              api_key=get_settings().openai.key)

                # Get similar snippets via similarity search
                if get_settings().pr_help.force_local_db:
                    sim_results = self.get_sim_results_from_local_db(embeddings)
                elif get_settings().get('pinecone.api_key'):
                    sim_results = self.get_sim_results_from_pinecone_db(embeddings)
                else:
                    sim_results = self.get_sim_results_from_s3_db(embeddings)
                    if not sim_results:
                        get_logger().info("Failed to load the S3 index. Loading the local index...")
                        sim_results = self.get_sim_results_from_local_db(embeddings)
                if not sim_results:
                    get_logger().error("Failed to retrieve similar snippets. Exiting...")
                    return

                # Prepare relevant snippets
                relevant_pages_full, relevant_snippets_full_header, relevant_snippets_str =\
                    await self.prepare_relevant_snippets(sim_results)
                self.vars['snippets'] = relevant_snippets_str.strip()

                # run the AI model
                response = await retry_with_fallback_models(self._prepare_prediction, model_type=ModelType.REGULAR)
                response_yaml = load_yaml(response)
                response_str = response_yaml.get('response')
                relevant_snippets_numbers = response_yaml.get('relevant_snippets')

                if not relevant_snippets_numbers:
                    if get_settings().config.publish_output:
                        answer_str = f"### Question: \n{self.question_str}\n\n"
                        answer_str += f"### Answer:\n\n"
                        answer_str += f"Could not find relevant information to answer the question. Please provide more details and try again."
                        self.git_provider.publish_comment(answer_str)
                    else:
                        get_logger().info(f"Could not find relevant snippets for the question: {self.question_str}")
                    return ""

                # prepare the answer
                answer_str = ""
                if response_str:
                    answer_str += f"### Question: \n{self.question_str}\n\n"
                    answer_str += f"### Answer:\n{response_str.strip()}\n\n"
                    answer_str += f"#### Relevant Sources:\n\n"
                    paged_published = []
                    for page in relevant_snippets_numbers:
                        page = int(page - 1)
                        if page < len(relevant_pages_full) and page >= 0:
                            if relevant_pages_full[page] in paged_published:
                                continue
                            link = f"{relevant_pages_full[page]}{relevant_snippets_full_header[page]}"
                            # answer_str += f"> - [{relevant_pages_full[page]}]({link})\n"
                            answer_str += f"> - {link}\n"
                            paged_published.append(relevant_pages_full[page])

                # publish the answer
                if get_settings().config.publish_output:
                    self.git_provider.publish_comment(answer_str)
                else:
                    get_logger().info(f"Answer:\n{answer_str}")
            else:
                if not isinstance(self.git_provider, BitbucketServerProvider) and not self.git_provider.is_supported("gfm_markdown"):
                    self.git_provider.publish_comment(
                        "The `Help` tool requires gfm markdown, which is not supported by your code platform.")
                    return

                get_logger().info('Getting PR Help Message...')
                relevant_configs = {'pr_help': dict(get_settings().pr_help),
                                    'config': dict(get_settings().config)}
                get_logger().debug("Relevant configs", artifacts=relevant_configs)
                pr_comment = "## PR Agent Walkthrough 🤖\n\n"
                pr_comment += "Welcome to the PR Agent, an AI-powered tool for automated pull request analysis, feedback, suggestions and more."""
                pr_comment += "\n\nHere is a list of tools you can use to interact with the PR Agent:\n"
                base_path = "https://pr-agent-docs.codium.ai/tools"

                tool_names = []
                tool_names.append(f"[DESCRIBE]({base_path}/describe/)")
                tool_names.append(f"[REVIEW]({base_path}/review/)")
                tool_names.append(f"[IMPROVE]({base_path}/improve/)")
                tool_names.append(f"[UPDATE CHANGELOG]({base_path}/update_changelog/)")
                tool_names.append(f"[ADD DOCS]({base_path}/documentation/) 💎")
                tool_names.append(f"[TEST]({base_path}/test/) 💎")
                tool_names.append(f"[IMPROVE COMPONENT]({base_path}/improve_component/) 💎")
                tool_names.append(f"[ANALYZE]({base_path}/analyze/) 💎")
                tool_names.append(f"[ASK]({base_path}/ask/)")
                tool_names.append(f"[GENERATE CUSTOM LABELS]({base_path}/custom_labels/) 💎")
                tool_names.append(f"[CI FEEDBACK]({base_path}/ci_feedback/) 💎")
                tool_names.append(f"[CUSTOM PROMPT]({base_path}/custom_prompt/) 💎")
                tool_names.append(f"[SIMILAR ISSUE]({base_path}/similar_issues/)")

                descriptions = []
                descriptions.append("Generates PR description - title, type, summary, code walkthrough and labels")
                descriptions.append("Adjustable feedback about the PR, possible issues, security concerns, review effort and more")
                descriptions.append("Code suggestions for improving the PR")
                descriptions.append("Automatically updates the changelog")
                descriptions.append("Generates documentation to methods/functions/classes that changed in the PR")
                descriptions.append("Generates unit tests for a specific component, based on the PR code change")
                descriptions.append("Code suggestions for a specific component that changed in the PR")
                descriptions.append("Identifies code components that changed in the PR, and enables to interactively generate tests, docs, and code suggestions for each component")
                descriptions.append("Answering free-text questions about the PR")
                descriptions.append("Generates custom labels for the PR, based on specific guidelines defined by the user")
                descriptions.append("Generates feedback and analysis for a failed CI job")
                descriptions.append("Generates custom suggestions for improving the PR code, derived only from a specific guidelines prompt defined by the user")
                descriptions.append("Automatically retrieves and presents similar issues")

                commands  =[]
                commands.append("`/describe`")
                commands.append("`/review`")
                commands.append("`/improve`")
                commands.append("`/update_changelog`")
                commands.append("`/add_docs`")
                commands.append("`/test`")
                commands.append("`/improve_component`")
                commands.append("`/analyze`")
                commands.append("`/ask`")
                commands.append("`/generate_labels`")
                commands.append("`/checks`")
                commands.append("`/custom_prompt`")
                commands.append("`/similar_issue`")

                checkbox_list = []
                checkbox_list.append(" - [ ] Run <!-- /describe -->")
                checkbox_list.append(" - [ ] Run <!-- /review -->")
                checkbox_list.append(" - [ ] Run <!-- /improve -->")
                checkbox_list.append(" - [ ] Run <!-- /update_changelog -->")
                checkbox_list.append(" - [ ] Run <!-- /add_docs -->")
                checkbox_list.append(" - [ ] Run <!-- /test -->")
                checkbox_list.append(" - [ ] Run <!-- /improve_component -->")
                checkbox_list.append(" - [ ] Run <!-- /analyze -->")
                checkbox_list.append("[*]")
                checkbox_list.append("[*]")
                checkbox_list.append("[*]")
                checkbox_list.append("[*]")
                checkbox_list.append("[*]")
                checkbox_list.append("[*]")
                checkbox_list.append("[*]")
                checkbox_list.append("[*]")

                if isinstance(self.git_provider, GithubProvider) and not get_settings().config.get('disable_checkboxes', False):
                    pr_comment += f"<table><tr align='left'><th align='left'>Tool</th><th align='left'>Description</th><th align='left'>Trigger Interactively :gem:</th></tr>"
                    for i in range(len(tool_names)):
                        pr_comment += f"\n<tr><td align='left'>\n\n<strong>{tool_names[i]}</strong></td>\n<td>{descriptions[i]}</td>\n<td>\n\n{checkbox_list[i]}\n</td></tr>"
                    pr_comment += "</table>\n\n"
                    pr_comment += f"""\n\n(1) Note that each tool be [triggered automatically](https://pr-agent-docs.codium.ai/usage-guide/automations_and_usage/#github-app-automatic-tools-when-a-new-pr-is-opened) when a new PR is opened, or called manually by [commenting on a PR](https://pr-agent-docs.codium.ai/usage-guide/automations_and_usage/#online-usage)."""
                    pr_comment += f"""\n\n(2) Tools marked with [*] require additional parameters to be passed. For example, to invoke the `/ask` tool, you need to comment on a PR: `/ask "<question content>"`. See the relevant documentation for each tool for more details."""
                elif isinstance(self.git_provider, BitbucketServerProvider):
                    # only support basic commands in BBDC
                    pr_comment = generate_bbdc_table(tool_names[:4], descriptions[:4])
                else:
                    pr_comment += f"<table><tr align='left'><th align='left'>Tool</th><th align='left'>Command</th><th align='left'>Description</th></tr>"
                    for i in range(len(tool_names)):
                        pr_comment += f"\n<tr><td align='left'>\n\n<strong>{tool_names[i]}</strong></td><td>{commands[i]}</td><td>{descriptions[i]}</td></tr>"
                    pr_comment += "</table>\n\n"
                    pr_comment += f"""\n\nNote that each tool be [invoked automatically](https://pr-agent-docs.codium.ai/usage-guide/automations_and_usage/) when a new PR is opened, or called manually by [commenting on a PR](https://pr-agent-docs.codium.ai/usage-guide/automations_and_usage/#online-usage)."""

                if get_settings().config.publish_output:
                    self.git_provider.publish_comment(pr_comment)
        except Exception as e:
            get_logger().exception(f"Error while running PRHelpMessage: {e}")
        return ""

    async def prepare_relevant_snippets(self, sim_results):
        # Get relevant snippets
        relevant_snippets_full = []
        relevant_pages_full = []
        relevant_snippets_full_header = []
        th = 0.75
        for s in sim_results:
            page = s[0].metadata['source']
            content = s[0].page_content
            score = s[1]
            relevant_snippets_full.append(content)
            relevant_snippets_full_header.append(extract_header(content))
            relevant_pages_full.append(page)
        # build the snippets string
        relevant_snippets_str = ""
        for i, s in enumerate(relevant_snippets_full):
            relevant_snippets_str += f"Snippet {i+1}:\n\n{s}\n\n"
            relevant_snippets_str += "-------------------\n\n"
        return relevant_pages_full, relevant_snippets_full_header, relevant_snippets_str


def generate_bbdc_table(column_arr_1, column_arr_2):
    # Generating header row
    header_row = "| Tool  | Description | \n"

    # Generating separator row
    separator_row = "|--|--|\n"

    # Generating data rows
    data_rows = ""
    max_len = max(len(column_arr_1), len(column_arr_2))
    for i in range(max_len):
        col1 = column_arr_1[i] if i < len(column_arr_1) else ""
        col2 = column_arr_2[i] if i < len(column_arr_2) else ""
        data_rows += f"| {col1} | {col2} |\n"

    # Combine all parts to form the complete table
    markdown_table = header_row + separator_row + data_rows
    return markdown_table
