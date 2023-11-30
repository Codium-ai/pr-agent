
## Installation

To get started with PR-Agent quickly, you first need to acquire two tokens:

1. An OpenAI key from [here](https://platform.openai.com/), with access to GPT-4.
2. A GitHub\GitLab\BitBucket personal access token (classic) with the repo scope.

There are several ways to use PR-Agent:

**Locally**
- [Using Docker image (no installation required)](INSTALL.md#use-docker-image-no-installation-required)
- [Run from source](INSTALL.md#run-from-source)

**GitHub specific methods**
- [Run as a GitHub Action](INSTALL.md#run-as-a-github-action)
- [Run as a polling server](INSTALL.md#run-as-a-polling-server)
- [Run as a GitHub App](INSTALL.md#run-as-a-github-app)
- [Deploy as a Lambda Function](INSTALL.md#deploy-as-a-lambda-function)
- [AWS CodeCommit](INSTALL.md#aws-codecommit-setup)

**GitLab specific methods**
- [Run a GitLab webhook server](INSTALL.md#run-a-gitlab-webhook-server)

**BitBucket specific methods**
- [Run as a Bitbucket Pipeline](INSTALL.md#run-as-a-bitbucket-pipeline)
- [Run on a hosted app](INSTALL.md#run-on-a-hosted-bitbucket-app)
- [Bitbucket server and data center](INSTALL.md#bitbucket-server-and-data-center)
---

### Use Docker image (no installation required)

A list of the relevant tools can be found in the [tools guide](./docs/TOOLS_GUIDE.md).

To invoke a tool (for example `review`), you can run directly from the Docker image. Here's how:

- For GitHub:
```
docker run --rm -it -e OPENAI.KEY=<your key> -e GITHUB.USER_TOKEN=<your token> codiumai/pr-agent:latest --pr_url <pr_url> review
```

- For GitLab:
```
docker run --rm -it -e OPENAI.KEY=<your key> -e CONFIG.GIT_PROVIDER=gitlab -e GITLAB.PERSONAL_ACCESS_TOKEN=<your token> codiumai/pr-agent:latest --pr_url <pr_url> review
```

Note: If you have a dedicated GitLab instance, you need to specify the custom url as variable:
```
docker run --rm -it -e OPENAI.KEY=<your key> -e CONFIG.GIT_PROVIDER=gitlab -e GITLAB.PERSONAL_ACCESS_TOKEN=<your token> GITLAB.URL=<your gitlab instance url> codiumai/pr-agent:latest --pr_url <pr_url> review
```

- For BitBucket:
```
docker run --rm -it -e CONFIG.GIT_PROVIDER=bitbucket -e OPENAI.KEY=$OPENAI_API_KEY -e BITBUCKET.BEARER_TOKEN=$BITBUCKET_BEARER_TOKEN codiumai/pr-agent:latest --pr_url=<pr_url> review
```

For other git providers, update CONFIG.GIT_PROVIDER accordingly, and check the `pr_agent/settings/.secrets_template.toml` file for the environment variables expected names and values.

---


If you want to ensure you're running a specific version of the Docker image, consider using the image's digest:
```bash
docker run --rm -it -e OPENAI.KEY=<your key> -e GITHUB.USER_TOKEN=<your token> codiumai/pr-agent@sha256:71b5ee15df59c745d352d84752d01561ba64b6d51327f97d46152f0c58a5f678 --pr_url <pr_url> review
```

Or you can run a [specific released versions](./RELEASE_NOTES.md) of pr-agent, for example:
```
codiumai/pr-agent@v0.9
```

---

### Run from source

1. Clone this repository:

```
git clone https://github.com/Codium-ai/pr-agent.git
```

2. Install the requirements in your favorite virtual environment:

```
pip install -r requirements.txt
```

3. Copy the secrets template file and fill in your OpenAI key and your GitHub user token:

```
cp pr_agent/settings/.secrets_template.toml pr_agent/settings/.secrets.toml
chmod 600 pr_agent/settings/.secrets.toml
# Edit .secrets.toml file
```

4. Add the pr_agent folder to your PYTHONPATH, then run the cli.py script:

```
export PYTHONPATH=[$PYTHONPATH:]<PATH to pr_agent folder>
python3 -m pr_agent.cli --pr_url <pr_url> review
python3 -m pr_agent.cli --pr_url <pr_url> ask <your question>
python3 -m pr_agent.cli --pr_url <pr_url> describe
python3 -m pr_agent.cli --pr_url <pr_url> improve
python3 -m pr_agent.cli --pr_url <pr_url> add_docs
python3 -m pr_agent.cli --pr_url <pr_url> generate_labels
python3 -m pr_agent.cli --issue_url <issue_url> similar_issue
...
```

---

### Run as a GitHub Action

You can use our pre-built Github Action Docker image to run PR-Agent as a Github Action.

1. Add the following file to your repository under `.github/workflows/pr_agent.yml`:

```yaml
on:
  pull_request:
  issue_comment:
jobs:
  pr_agent_job:
    runs-on: ubuntu-latest
    permissions:
      issues: write
      pull-requests: write
      contents: write
    name: Run pr agent on every pull request, respond to user comments
    steps:
      - name: PR Agent action step
        id: pragent
        uses: Codium-ai/pr-agent@main
        env:
          OPENAI_KEY: ${{ secrets.OPENAI_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```
** if you want to pin your action to a specific release (v0.7 for example) for stability reasons, use:
```yaml
on:
  pull_request:
  issue_comment:

jobs:
  pr_agent_job:
    runs-on: ubuntu-latest
    permissions:
      issues: write
      pull-requests: write
      contents: write
    name: Run pr agent on every pull request, respond to user comments
    steps:
      - name: PR Agent action step
        id: pragent
        uses: Codium-ai/pr-agent@v0.7
        env:
          OPENAI_KEY: ${{ secrets.OPENAI_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```
2. Add the following secret to your repository under `Settings > Secrets and variables > Actions > New repository secret > Add secret`:

```
Name = OPENAI_KEY
Secret = <your key>
```

The GITHUB_TOKEN secret is automatically created by GitHub.

3. Merge this change to your main branch.
When you open your next PR, you should see a comment from `github-actions` bot with a review of your PR, and instructions on how to use the rest of the tools.

4. You may configure PR-Agent by adding environment variables under the env section corresponding to any configurable property in the [configuration](pr_agent/settings/configuration.toml) file. Some examples:
```yaml
      env:
        # ... previous environment values
        OPENAI.ORG: "<Your organization name under your OpenAI account>"
        PR_REVIEWER.REQUIRE_TESTS_REVIEW: "false" # Disable tests review
        PR_CODE_SUGGESTIONS.NUM_CODE_SUGGESTIONS: 6 # Increase number of code suggestions
```

---

### Run as a polling server
Request reviews by tagging your GitHub user on a PR

Follow [steps 1-3](#run-as-a-github-action) of the GitHub Action setup.

Run the following command to start the server:

```
python pr_agent/servers/github_polling.py
```

---

### Run as a GitHub App
Allowing you to automate the review process on your private or public repositories.

1. Create a GitHub App from the [Github Developer Portal](https://docs.github.com/en/developers/apps/creating-a-github-app).

   - Set the following permissions:
     - Pull requests: Read & write
     - Issue comment: Read & write
     - Metadata: Read-only
     - Contents: Read-only
   - Set the following events:
     - Issue comment
     - Pull request

2. Generate a random secret for your app, and save it for later. For example, you can use:

```
WEBHOOK_SECRET=$(python -c "import secrets; print(secrets.token_hex(10))")
```

3. Acquire the following pieces of information from your app's settings page:

   - App private key (click "Generate a private key" and save the file)
   - App ID

4. Clone this repository:

```
git clone https://github.com/Codium-ai/pr-agent.git
```

5. Copy the secrets template file and fill in the following:
    ```
    cp pr_agent/settings/.secrets_template.toml pr_agent/settings/.secrets.toml
    # Edit .secrets.toml file
    ```
   - Your OpenAI key.
   - Copy your app's private key to the private_key field.
   - Copy your app's ID to the app_id field.
   - Copy your app's webhook secret to the webhook_secret field.
   - Set deployment_type to 'app' in [configuration.toml](./pr_agent/settings/configuration.toml)

> The .secrets.toml file is not copied to the Docker image by default, and is only used for local development.
> If you want to use the .secrets.toml file in your Docker image, you can add remove it from the .dockerignore file.
> In most production environments, you would inject the secrets file as environment variables or as mounted volumes.
> For example, in order to inject a secrets file as a volume in a Kubernetes environment you can update your pod spec to include the following,
> assuming you have a secret named `pr-agent-settings` with a key named `.secrets.toml`:
```
       volumes:
        - name: settings-volume
          secret:
            secretName: pr-agent-settings
// ...
       containers:
// ...
          volumeMounts:
            - mountPath: /app/pr_agent/settings_prod
              name: settings-volume
```

> Another option is to set the secrets as environment variables in your deployment environment, for example `OPENAI.KEY` and `GITHUB.USER_TOKEN`.

6. Build a Docker image for the app and optionally push it to a Docker repository. We'll use Dockerhub as an example:

```
docker build . -t codiumai/pr-agent:github_app --target github_app -f docker/Dockerfile
docker push codiumai/pr-agent:github_app  # Push to your Docker repository
```

7. Host the app using a server, serverless function, or container environment. Alternatively, for development and
   debugging, you may use tools like smee.io to forward webhooks to your local machine.
    You can check [Deploy as a Lambda Function](#deploy-as-a-lambda-function)

8. Go back to your app's settings, and set the following:

   - Webhook URL: The URL of your app's server or the URL of the smee.io channel.
   - Webhook secret: The secret you generated earlier.

9. Install the app by navigating to the "Install App" tab and selecting your desired repositories.

> **Note:** When running PR-Agent from GitHub App, the default configuration file (configuration.toml) will be loaded.<br>
> However, you can override the default tool parameters by uploading a local configuration file `.pr_agent.toml`<br>
> For more information please check out the [USAGE GUIDE](./Usage.md#working-with-github-app)
---

### Deploy as a Lambda Function

1. Follow steps 1-5 of [Method 5](#run-as-a-github-app).
2. Build a docker image that can be used as a lambda function
    ```shell
    docker buildx build --platform=linux/amd64 . -t codiumai/pr-agent:serverless -f docker/Dockerfile.lambda
   ```
3. Push image to ECR
    ```shell
	docker tag codiumai/pr-agent:serverless <AWS_ACCOUNT>.dkr.ecr.<AWS_REGION>.amazonaws.com/codiumai/pr-agent:serverless
	docker push <AWS_ACCOUNT>.dkr.ecr.<AWS_REGION>.amazonaws.com/codiumai/pr-agent:serverless
    ```
4. Create a lambda function that uses the uploaded image. Set the lambda timeout to be at least 3m.
5. Configure the lambda function to have a Function URL.
6. Go back to steps 8-9 of [Method 5](#run-as-a-github-app) with the function url as your Webhook URL.
    The Webhook URL would look like `https://<LAMBDA_FUNCTION_URL>/api/v1/github_webhooks`

---

### AWS CodeCommit Setup

Not all features have been added to CodeCommit yet.  As of right now, CodeCommit has been implemented to run the pr-agent CLI on the command line, using AWS credentials stored in environment variables.  (More features will be added in the future.)  The following is a set of instructions to have pr-agent do a review of your CodeCommit pull request from the command line:

1. Create an IAM user that you will use to read CodeCommit pull requests and post comments
    * Note: That user should have CLI access only, not Console access
2. Add IAM permissions to that user, to allow access to CodeCommit (see IAM Role example below)
3. Generate an Access Key for your IAM user
4. Set the Access Key and Secret using environment variables (see Access Key example below)
5. Set the `git_provider` value to `codecommit` in the `pr_agent/settings/configuration.toml` settings file
6. Set the `PYTHONPATH` to include your `pr-agent` project directory
    * Option A: Add `PYTHONPATH="/PATH/TO/PROJECTS/pr-agent` to your `.env` file
    * Option B: Set `PYTHONPATH` and run the CLI in one command, for example:
        * `PYTHONPATH="/PATH/TO/PROJECTS/pr-agent python pr_agent/cli.py [--ARGS]`

##### AWS CodeCommit IAM Role Example

Example IAM permissions to that user to allow access to CodeCommit:

* Note: The following is a working example of IAM permissions that has read access to the repositories and write access to allow posting comments
* Note: If you only want pr-agent to review your pull requests, you can tighten the IAM permissions further, however this IAM example will work, and allow the pr-agent to post comments to the PR
* Note: You may want to replace the `"Resource": "*"` with your list of repos, to limit access to only those repos

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "codecommit:BatchDescribe*",
                "codecommit:BatchGet*",
                "codecommit:Describe*",
                "codecommit:EvaluatePullRequestApprovalRules",
                "codecommit:Get*",
                "codecommit:List*",
                "codecommit:PostComment*",
                "codecommit:PutCommentReaction",
                "codecommit:UpdatePullRequestDescription",
                "codecommit:UpdatePullRequestTitle"
            ],
            "Resource": "*"
        }
    ]
}
```

##### AWS CodeCommit Access Key and Secret

Example setting the Access Key and Secret using environment variables

```sh
export AWS_ACCESS_KEY_ID="XXXXXXXXXXXXXXXX"
export AWS_SECRET_ACCESS_KEY="XXXXXXXXXXXXXXXX"
export AWS_DEFAULT_REGION="us-east-1"
```

##### AWS CodeCommit CLI Example

After you set up AWS CodeCommit using the instructions above, here is an example CLI run that tells pr-agent to **review** a given pull request.
(Replace your specific PYTHONPATH and PR URL in the example)

```sh
PYTHONPATH="/PATH/TO/PROJECTS/pr-agent" python pr_agent/cli.py \
  --pr_url https://us-east-1.console.aws.amazon.com/codesuite/codecommit/repositories/MY_REPO_NAME/pull-requests/321 \
  review
```

---

### Run a GitLab webhook server

1. From the GitLab workspace or group, create an access token. Enable the "api" scope only.
2. Generate a random secret for your app, and save it for later. For example, you can use:

```
WEBHOOK_SECRET=$(python -c "import secrets; print(secrets.token_hex(10))")
```
3. Follow the instructions to build the Docker image, setup a secrets file and deploy on your own server from [Method 5](#run-as-a-github-app) steps 4-7.
4. In the secrets file, fill in the following:
    - Your OpenAI key.
    - In the [gitlab] section, fill in personal_access_token and shared_secret. The access token can be a personal access token, or a group or project access token.
    - Set deployment_type to 'gitlab' in [configuration.toml](./pr_agent/settings/configuration.toml)
5. Create a webhook in GitLab. Set the URL to the URL of your app's server. Set the secret token to the generated secret from step 2.
In the "Trigger" section, check the ‘comments’ and ‘merge request events’ boxes.
6. Test your installation by opening a merge request or commenting or a merge request using one of CodiumAI's commands.



### Run as a Bitbucket Pipeline


You can use the Bitbucket Pipeline system to run PR-Agent on every pull request open or update.

1. Add the following file in your repository bitbucket_pipelines.yml

```yaml
pipelines:
    pull-requests:
      '**':
        - step:
            name: PR Agent Review
            image: python:3.10
            services:
              - docker
            script:
              - docker run -e CONFIG.GIT_PROVIDER=bitbucket -e OPENAI.KEY=$OPENAI_API_KEY -e BITBUCKET.BEARER_TOKEN=$BITBUCKET_BEARER_TOKEN codiumai/pr-agent:latest --pr_url=https://bitbucket.org/$BITBUCKET_WORKSPACE/$BITBUCKET_REPO_SLUG/pull-requests/$BITBUCKET_PR_ID review
```

2. Add the following secure variables to your repository under Repository settings > Pipelines > Repository variables.
OPENAI_API_KEY: <your key>
BITBUCKET_BEARER_TOKEN: <your token>

You can get a Bitbucket token for your repository by following Repository Settings -> Security -> Access Tokens.

Note that comments on a PR are not supported in Bitbucket Pipeline.


### Run using CodiumAI-hosted Bitbucket app

Please contact <support@codium.ai> or visit [CodiumAI pricing page](https://www.codium.ai/pricing/) if you're interested in a hosted BitBucket app solution that provides full functionality including PR reviews and comment handling. It's based on the [bitbucket_app.py](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/git_providers/bitbucket_provider.py) implementation.


### Bitbucket Server and Data Center

Login into your on-prem instance of Bitbucket with your service account username and password.
Navigate to `Manage account`, `HTTP Access tokens`, `Create Token`.
Generate the token and add it to .secret.toml under `bitbucket_server` section

```toml
[bitbucket_server]
bearer_token = "<your key>"
```

#### Run it as CLI

Modify `configuration.toml`:

```toml
git_provider="bitbucket_server"
```

and pass the Pull request URL:
```shell
python cli.py --pr_url https://git.onpreminstanceofbitbucket.com/projects/PROJECT/repos/REPO/pull-requests/1 review
```

#### Run it as service

To run pr-agent as webhook, build the docker image:
```
docker build . -t codiumai/pr-agent:bitbucket_server_webhook --target bitbucket_server_webhook -f docker/Dockerfile
docker push codiumai/pr-agent:bitbucket_server_webhook  # Push to your Docker repository
```

Navigate to `Projects` or `Repositories`, `Settings`, `Webhooks`, `Create Webhook`.
Fill the name and URL, Authentication None select the Pull Request Opened checkbox to receive that event as webhook.

The URL should end with `/webhook`, for example: https://domain.com/webhook

=======
