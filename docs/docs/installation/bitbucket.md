## Run as a Bitbucket Pipeline


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
OPENAI_API_KEY: `<your key>`
BITBUCKET_BEARER_TOKEN: `<your token>`

You can get a Bitbucket token for your repository by following Repository Settings -> Security -> Access Tokens.

Note that comments on a PR are not supported in Bitbucket Pipeline.


## Run using CodiumAI-hosted Bitbucket app

Please contact [support@codium.ai](mailto:support@codium.ai) or visit [CodiumAI pricing page](https://www.codium.ai/pricing/) if you're interested in a hosted BitBucket app solution that provides full functionality including PR reviews and comment handling. It's based on the [bitbucket_app.py](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/git_providers/bitbucket_provider.py) implementation.


## Bitbucket Server and Data Center

Login into your on-prem instance of Bitbucket with your service account username and password.
Navigate to `Manage account`, `HTTP Access tokens`, `Create Token`.
Generate the token and add it to .secret.toml under `bitbucket_server` section

```toml
[bitbucket_server]
bearer_token = "<your key>"
```

### Run it as CLI

Modify `configuration.toml`:

```toml
git_provider="bitbucket_server"
```

and pass the Pull request URL:
```shell
python cli.py --pr_url https://git.onpreminstanceofbitbucket.com/projects/PROJECT/repos/REPO/pull-requests/1 review
```

### Run it as service

To run pr-agent as webhook, build the docker image:
```
docker build . -t codiumai/pr-agent:bitbucket_server_webhook --target bitbucket_server_webhook -f docker/Dockerfile
docker push codiumai/pr-agent:bitbucket_server_webhook  # Push to your Docker repository
```

Navigate to `Projects` or `Repositories`, `Settings`, `Webhooks`, `Create Webhook`.
Fill the name and URL, Authentication None select the Pull Request Opened checkbox to receive that event as webhook.

The URL should end with `/webhook`, for example: https://domain.com/webhook
