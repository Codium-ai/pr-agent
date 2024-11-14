## Run as a GitLab Pipeline
You can use a pre-built Action Docker image to run Qodo Merge as a GitLab pipeline. This is a simple way to get started with Qodo Merge without setting up your own server.

(1) Add the following file to your repository under `.gitlab-ci.yml`:
```yaml
stages:
  - pr_agent

pr_agent_job:
  stage: pr_agent
  image:
    name: codiumai/pr-agent:latest
    entrypoint: [""]
  script:
    - cd /app
    - echo "Running PR Agent action step"
    - export MR_URL="$CI_MERGE_REQUEST_PROJECT_URL/merge_requests/$CI_MERGE_REQUEST_IID"
    - echo "MR_URL=$MR_URL"
    - export gitlab__url=$CI_SERVER_PROTOCOL://$CI_SERVER_FQDN
    - export gitlab__PERSONAL_ACCESS_TOKEN=$GITLAB_PERSONAL_ACCESS_TOKEN
    - export config__git_provider="gitlab"
    - export openai__key=$OPENAI_KEY
    - python -m pr_agent.cli --pr_url="$MR_URL" describe
    - python -m pr_agent.cli --pr_url="$MR_URL" review
    - python -m pr_agent.cli --pr_url="$MR_URL" improve
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
```
This script will run Qodo Merge on every new merge request. You can modify the `rules` section to run Qodo Merge on different events.
You can also modify the `script` section to run different Qodo Merge commands, or with different parameters by exporting different environment variables.


(2) Add the following masked variables to your GitLab repository (CI/CD -> Variables):

- `GITLAB_PERSONAL_ACCESS_TOKEN`: Your GitLab personal access token.

- `OPENAI_KEY`: Your OpenAI key.

Note that if your base branches are not protected, don't set the variables as `protected`, since the pipeline will not have access to them.

> **Note**: The `$CI_SERVER_FQDN` variable is available starting from GitLab version 16.10. If you're using an earlier version, this variable will not be available. However, you can combine `$CI_SERVER_HOST` and `$CI_SERVER_PORT` to achieve the same result. Please ensure you're using a compatible version or adjust your configuration.


## Run a GitLab webhook server

1. From the GitLab workspace or group, create an access token with "Reporter" role ("Developer" if using Pro version of the agent) and "api" scope.

2. Generate a random secret for your app, and save it for later. For example, you can use:

```
WEBHOOK_SECRET=$(python -c "import secrets; print(secrets.token_hex(10))")
```

3. Clone this repository:

```
git clone https://github.com/Codium-ai/pr-agent.git
```

4. Prepare variables and secrets. Skip this step if you plan on settings these as environment variables when running the agent:
  1. In the configuration file/variables:
    - Set `deployment_type` to "gitlab"

  2. In the secrets file/variables:
    - Set your AI model key in the respective section
    - In the [gitlab] section, set `personal_access_token` (with token from step 1) and `shared_secret` (with secret from step 2)


5. Build a Docker image for the app and optionally push it to a Docker repository. We'll use Dockerhub as an example:
```
docker build . -t gitlab_pr_agent --target gitlab_webhook -f docker/Dockerfile
docker push codiumai/pr-agent:gitlab_webhook  # Push to your Docker repository
```

6. Create a webhook in GitLab. Set the URL to ```http[s]://<PR_AGENT_HOSTNAME>/webhook```, the secret token to the generated secret from step 2, and enable the triggers `push`, `comments` and `merge request events`.

7. Test your installation by opening a merge request or commenting on a merge request using one of CodiumAI's commands.
boxes
