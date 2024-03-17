## Run as a GitHub Action

You can use our pre-built Github Action Docker image to run PR-Agent as a Github Action.

1) Add the following file to your repository under `.github/workflows/pr_agent.yml`:

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
2) Add the following secret to your repository under `Settings > Secrets and variables > Actions > New repository secret > Add secret`:

```
Name = OPENAI_KEY
Secret = <your key>
```

The GITHUB_TOKEN secret is automatically created by GitHub.

3) Merge this change to your main branch.
When you open your next PR, you should see a comment from `github-actions` bot with a review of your PR, and instructions on how to use the rest of the tools.

4) You may configure PR-Agent by adding environment variables under the env section corresponding to any configurable property in the [configuration](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/settings/configuration.toml) file. Some examples:
```yaml
      env:
        # ... previous environment values
        OPENAI.ORG: "<Your organization name under your OpenAI account>"
        PR_REVIEWER.REQUIRE_TESTS_REVIEW: "false" # Disable tests review
        PR_CODE_SUGGESTIONS.NUM_CODE_SUGGESTIONS: 6 # Increase number of code suggestions
```

---

## Run as a GitHub App
Allowing you to automate the review process on your private or public repositories.

1) Create a GitHub App from the [Github Developer Portal](https://docs.github.com/en/developers/apps/creating-a-github-app).

   - Set the following permissions:
     - Pull requests: Read & write
     - Issue comment: Read & write
     - Metadata: Read-only
     - Contents: Read-only
   - Set the following events:
     - Issue comment
     - Pull request
     - Push (if you need to enable triggering on PR update)

2) Generate a random secret for your app, and save it for later. For example, you can use:

```
WEBHOOK_SECRET=$(python -c "import secrets; print(secrets.token_hex(10))")
```

3) Acquire the following pieces of information from your app's settings page:

   - App private key (click "Generate a private key" and save the file)
   - App ID

4) Clone this repository:

```
git clone https://github.com/Codium-ai/pr-agent.git
```

5) Copy the secrets template file and fill in the following:
    
```
cp pr_agent/settings/.secrets_template.toml pr_agent/settings/.secrets.toml
# Edit .secrets.toml file
```

   - Your OpenAI key.
   - Copy your app's private key to the private_key field.
   - Copy your app's ID to the app_id field.
   - Copy your app's webhook secret to the webhook_secret field.
   - Set deployment_type to 'app' in [configuration.toml](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/settings/configuration.toml)

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

6) Build a Docker image for the app and optionally push it to a Docker repository. We'll use Dockerhub as an example:

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

> **Note:** When running PR-Agent from GitHub App, the default configuration file (configuration.toml) will be loaded.
> However, you can override the default tool parameters by uploading a local configuration file `.pr_agent.toml`
> For more information please check out the [USAGE GUIDE](../usage-guide/automations_and_usage.md#github-app)
---

## Deploy as a Lambda Function

1. Follow steps 1-5 from [here](#run-as-a-github-app).
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
6. In the environment variables of the Lambda function, specify `AZURE_DEVOPS_CACHE_DIR` to a writable location such as /tmp. (see [link](https://github.com/Codium-ai/pr-agent/pull/450#issuecomment-1840242269))
7. Go back to steps 8-9 of [Method 5](#run-as-a-github-app) with the function url as your Webhook URL.
    The Webhook URL would look like `https://<LAMBDA_FUNCTION_URL>/api/v1/github_webhooks`

---

## AWS CodeCommit Setup

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

---


#### AWS CodeCommit IAM Role Example

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

#### AWS CodeCommit Access Key and Secret

Example setting the Access Key and Secret using environment variables

```sh
export AWS_ACCESS_KEY_ID="XXXXXXXXXXXXXXXX"
export AWS_SECRET_ACCESS_KEY="XXXXXXXXXXXXXXXX"
export AWS_DEFAULT_REGION="us-east-1"
```

#### AWS CodeCommit CLI Example

After you set up AWS CodeCommit using the instructions above, here is an example CLI run that tells pr-agent to **review** a given pull request.
(Replace your specific PYTHONPATH and PR URL in the example)

```sh
PYTHONPATH="/PATH/TO/PROJECTS/pr-agent" python pr_agent/cli.py \
  --pr_url https://us-east-1.console.aws.amazon.com/codesuite/codecommit/repositories/MY_REPO_NAME/pull-requests/321 \
  review
```