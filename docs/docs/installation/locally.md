## Using pip package

Install the package:

```
pip install pr-agent
```

Then run the relevant tool with the script below.
<br>
Make sure to fill in the required parameters (`user_token`, `openai_key`, `pr_url`, `command`):

```python
from pr_agent import cli
from pr_agent.config_loader import get_settings

def main():
    # Fill in the following values
    provider = "github" # github/gitlab/bitbucket/azure_devops
    user_token = "..."  #  user token
    openai_key = "..."  # OpenAI key
    pr_url = "..."      # PR URL, for example 'https://github.com/Codium-ai/pr-agent/pull/809'
    command = "/review" # Command to run (e.g. '/review', '/describe', '/ask="What is the purpose of this PR?"', ...)

    # Setting the configurations
    get_settings().set("CONFIG.git_provider", provider)
    get_settings().set("openai.key", openai_key)
    get_settings().set("github.user_token", user_token)

    # Run the command. Feedback will appear in GitHub PR comments
    cli.run_command(pr_url, command)


if __name__ == '__main__':
    main()
```

## Using Docker image

A list of the relevant tools can be found in the [tools guide](../tools/ask.md).

To invoke a tool (for example `review`), you can run directly from the Docker image. Here's how:

- For GitHub:
    ```
    docker run --rm -it -e OPENAI.KEY=<your key> -e GITHUB.USER_TOKEN=<your token> codiumai/pr-agent:latest --pr_url <pr_url> review
    ```
    If you are using GitHub enterprise server, you need to specify the custom url as variable.
    For example, if your GitHub server is at `https://github.mycompany.com`, add the following to the command:
    ```
    -e GITHUB.BASE_URL=https://github.mycompany.com/api/v3
    ```

- For GitLab:
    ```
    docker run --rm -it -e OPENAI.KEY=<your key> -e CONFIG.GIT_PROVIDER=gitlab -e GITLAB.PERSONAL_ACCESS_TOKEN=<your token> codiumai/pr-agent:latest --pr_url <pr_url> review
    ```

    If you have a dedicated GitLab instance, you need to specify the custom url as variable:
    ```
    -e GITLAB.URL=<your gitlab instance url>
    ```

- For BitBucket:
    ```
    docker run --rm -it -e CONFIG.GIT_PROVIDER=bitbucket -e OPENAI.KEY=$OPENAI_API_KEY -e BITBUCKET.BEARER_TOKEN=$BITBUCKET_BEARER_TOKEN codiumai/pr-agent:latest --pr_url=<pr_url> review
    ```

For other git providers, update CONFIG.GIT_PROVIDER accordingly, and check the `pr_agent/settings/.secrets_template.toml` file for the environment variables expected names and values.

---

## Run from source

1. Clone this repository:

```
git clone https://github.com/Codium-ai/pr-agent.git
```

2. Navigate to the `/pr-agent` folder and install the requirements in your favorite virtual environment:

```
pip install -e .
```

*Note: If you get an error related to Rust in the dependency installation then make sure Rust is installed and in your `PATH`, instructions: https://rustup.rs*

3. Copy the secrets template file and fill in your OpenAI key and your GitHub user token:

```
cp pr_agent/settings/.secrets_template.toml pr_agent/settings/.secrets.toml
chmod 600 pr_agent/settings/.secrets.toml
# Edit .secrets.toml file
```

4. Run the cli.py script:

```
python3 -m pr_agent.cli --pr_url <pr_url> review
python3 -m pr_agent.cli --pr_url <pr_url> ask <your question>
python3 -m pr_agent.cli --pr_url <pr_url> describe
python3 -m pr_agent.cli --pr_url <pr_url> improve
python3 -m pr_agent.cli --pr_url <pr_url> add_docs
python3 -m pr_agent.cli --pr_url <pr_url> generate_labels
python3 -m pr_agent.cli --issue_url <issue_url> similar_issue
...
```

[Optional] Add the pr_agent folder to your PYTHONPATH
```
export PYTHONPATH=$PYTHONPATH:<PATH to pr_agent folder>
```
