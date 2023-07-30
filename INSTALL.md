
## Installation

---

#### Method 1: Use Docker image (no installation required)sdf

To request a review for a PR, or ask a question about a PR, you can run directly from the Docker image. Here's how:

1. To request a review for a PR, run the following command:

```
docker run --rm -it -e OPENAI.KEY=<your key> -e GITHUB.USER_TOKEN=<your token> codiumai/pr-agent --pr_url <pr_url> review
```

2. To ask a question about a PR, run the following command:

```
docker run --rm -it -e OPENAI.KEY=<your key> -e GITHUB.USER_TOKEN=<your token> codiumai/pr-agent --pr_url <pr_url> ask "<your question>"
```

Possible questions you can ask include:

- What is the main theme of this PR?
- Is the PR ready for merge?
- What are the main changes in this PR?
- Should this PR be split into smaller parts?
- Can you compose a rhymed song about this PR?

---

#### Method 2: Run as a GitHub Action

You can use our pre-built Github Action Docker image to run PR-Agent as a Github Action. 

1. Add the following file to your repository under `.github/workflows/pr_agent.yml`:

```yaml
on:
  pull_request:
  issue_comment:
jobs:
  pr_agent_job:
    runs-on: ubuntu-latest
    name: Run pr agent on every pull request, respond to user comments
    steps:
      - name: PR Agent action step
        id: pragent
        uses: Codium-ai/pr-agent@main
        env:
          OPENAI_KEY: ${{ secrets.OPENAI_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

2. Add the following secret to your repository under `Settings > Secrets`:

```
OPENAI_KEY: <your key>
```

The GITHUB_TOKEN secret is automatically created by GitHub.

3. Merge this change to your main branch. 
When you open your next PR, you should see a comment from `github-actions` bot with a review of your PR, and instructions on how to use the rest of the tools.

4. You may configure PR-Agent by adding environment variables under the env section corresponding to any configurable property in the [configuration](./CONFIGURATION.md) file. Some examples:
```yaml
      env:
        # ... previous environment values
        OPENAI.ORG: "<Your organization name under your OpenAI account>"
        PR_REVIEWER.REQUIRE_TESTS_REVIEW: "false" # Disable tests review
        PR_CODE_SUGGESTIONS.NUM_CODE_SUGGESTIONS: 6 # Increase number of code suggestions
```

---

#### Method 3: Run from source

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
# Edit .secrets.toml file
```

4. Add the pr_agent folder to your PYTHONPATH, then run the cli.py script:

```
export PYTHONPATH=[$PYTHONPATH:]<PATH to pr_agent folder>
python pr_agent/cli.py --pr_url <pr_url> review
python pr_agent/cli.py --pr_url <pr_url> ask <your question>
python pr_agent/cli.py --pr_url <pr_url> describe
python pr_agent/cli.py --pr_url <pr_url> improve
```

---

#### Method 4: Run as a polling server
Request reviews by tagging your Github user on a PR

Follow steps 1-3 of method 2.
Run the following command to start the server:

```
python pr_agent/servers/github_polling.py
```

---

#### Method 5: Run as a GitHub App
Allowing you to automate the review process on your private or public repositories.

1. Create a GitHub App from the [Github Developer Portal](https://docs.github.com/en/developers/apps/creating-a-github-app).

   - Set the following permissions:
     - Pull requests: Read & write
     - Issue comment: Read & write
     - Metadata: Read-only
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

---

####  Deploy as a Lambda Function

1. Follow steps 1-5 of [Method 5](#method-5-run-as-a-github-app).
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
6. Go back to steps 8-9 of [Method 5](#method-5-run-as-a-github-app) with the function url as your Webhook URL.
    The Webhook URL would look like `https://<LAMBDA_FUNCTION_URL>/api/v1/github_webhooks`
