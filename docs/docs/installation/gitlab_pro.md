## Install Hosted PR-Agent Pro for GitLab (Teams & Enterprise)

### Step 1

Acquire a personal, project or group level access token. Enable the “api” scope in order to allow PR-Agent to read pull requests, comment and respond to requests.

<kbd><img src=https://www.codium.ai/images/pr_agent/gitlab_pro_pat.png></kbd>

Store the token in a safe place, you won’t be able to access it again after it was generated.

### Step 2

Generate a shared secret and link it to the access token. Browse to [https://register.gitlab.pr-agent.codium.ai](https://register.gitlab.pr-agent.codium.ai).
Fill in your generated GitLab token and your company or personal name in the appropriate fields and click "Submit".

You should see "Success!" displayed above the Submit button, and a shared secret will be generated. Store it in a safe place, you won’t be able to access it again after it was generated.

### Step 3

Install a webhook for your repository or groups, by clicking “webhooks” on the settings menu. Click the “Add new webhook” button.

<kbd><img src=https://www.codium.ai/images/pr_agent/gitlab_pro_add_webhook.png></kbd>

In the webhook definition form, fill in the following fields:
URL: https://pro.gitlab.pr-agent.codium.ai/webhook

Secret token: Your CodiumAI key
Trigger: Check the ‘comments’ and ‘merge request events’ boxes.
Enable SSL verification: Check the box.

<kbd><img src=https://www.codium.ai/images/pr_agent/gitlab_pro_webhooks.png></kbd>

### Step 4

You’re all set!

Open a new merge request or add a MR comment with one of PR-Agent’s commands such as /review, /describe or /improve.