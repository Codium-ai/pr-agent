## Run a GitLab webhook server

1. From the GitLab workspace or group, create an access token. Enable the "api" scope only.

2. Generate a random secret for your app, and save it for later. For example, you can use:

```
WEBHOOK_SECRET=$(python -c "import secrets; print(secrets.token_hex(10))")
```
3. Follow the instructions to build the Docker image, setup a secrets file and deploy on your own server from [here](https://pr-agent-docs.codium.ai/installation/github/#run-as-a-github-app) steps 4-7.

4. In the secrets file, fill in the following:
    - Your OpenAI key.
    - In the [gitlab] section, fill in personal_access_token and shared_secret. The access token can be a personal access token, or a group or project access token.
    - Set deployment_type to 'gitlab' in [configuration.toml](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/settings/configuration.toml)
   
5. Create a webhook in GitLab. Set the URL to the URL of your app's server. Set the secret token to the generated secret from step 2.
In the "Trigger" section, check the ‘comments’ and ‘merge request events’ boxes.

6. Test your installation by opening a merge request or commenting or a merge request using one of CodiumAI's commands.