Qodo Merge is a versatile application compatible with GitHub, GitLab, and BitBucket, hosted by QodoAI.
See [here](https://qodo-merge-docs.qodo.ai/overview/pr_agent_pro/) for more details about the benefits of using Qodo Merge.

A complimentary two-week trial is provided to all new users. Following the trial period, user licenses (seats) are required for continued access.
To purchase user licenses, please visit our [pricing page](https://www.qodo.ai/pricing/).
Once subscribed, users can seamlessly deploy the application across any of their code repositories.

## Install Qodo Merge for GitHub

### GitHub Cloud

Qodo Merge for GitHub cloud is available for installation through the [GitHub Marketplace](https://github.com/apps/qodo-merge-pro).

![Qodo Merge](https://codium.ai/images/pr_agent/pr_agent_pro_install.png){width=468}

### GitHub Enterprise Server

To use Qodo Merge application on your private GitHub Enterprise Server, you will need to [contact](https://www.qodo.ai/contact/#pricing) Qodo for starting an Enterprise trial.

### GitHub Open Source Projects

For open-source projects, Qodo Merge is available for free usage. To install Qodo Merge for your open-source repositories, use the following marketplace [link](https://github.com/apps/qodo-merge-pro-for-open-source).

## Install Qodo Merge for Bitbucket

###  Bitbucket Cloud

Qodo Merge for Bitbucket Cloud is available for installation through the following [link](https://bitbucket.org/site/addons/authorize?addon_key=d6df813252c37258)

![Qodo Merge](https://qodo.ai/images/pr_agent/pr_agent_pro_bitbucket_install.png){width=468}

### Bitbucket Server

To use Qodo Merge application on your private Bitbucket Server, you will need to contact us for starting an [Enterprise](https://www.qodo.ai/pricing/) trial.


## Install Qodo Merge for GitLab 

### GitLab Cloud

Since GitLab platform does not support apps, installing Qodo Merge for GitLab is a bit more involved, and requires the following steps:

#### Step 1

Acquire a personal, project or group level access token. Enable the “api” scope in order to allow Qodo Merge to read pull requests, comment and respond to requests.

<figure markdown="1">
![Step 1](https://www.codium.ai/images/pr_agent/gitlab_pro_pat.png){width=750}
</figure>

Store the token in a safe place, you won’t be able to access it again after it was generated.

#### Step 2

Generate a shared secret and link it to the access token. Browse to [https://register.gitlab.pr-agent.codium.ai](https://register.gitlab.pr-agent.codium.ai).
Fill in your generated GitLab token and your company or personal name in the appropriate fields and click "Submit".

You should see "Success!" displayed above the Submit button, and a shared secret will be generated. Store it in a safe place, you won’t be able to access it again after it was generated.

#### Step 3

Install a webhook for your repository or groups, by clicking “webhooks” on the settings menu. Click the “Add new webhook” button.

<figure markdown="1">
![Step 3.1](https://www.codium.ai/images/pr_agent/gitlab_pro_add_webhook.png)
</figure>

In the webhook definition form, fill in the following fields:
URL: https://pro.gitlab.pr-agent.codium.ai/webhook

Secret token: Your QodoAI key
Trigger: Check the ‘comments’ and ‘merge request events’ boxes.
Enable SSL verification: Check the box.

<figure markdown="1">
![Step 3.2](https://www.codium.ai/images/pr_agent/gitlab_pro_webhooks.png){width=750}
</figure>

#### Step 4

You’re all set!

Open a new merge request or add a MR comment with one of Qodo Merge’s commands such as /review, /describe or /improve.

### GitLab Server

For a trial period of two weeks on your private GitLab Server, the same [installation steps](#gitlab-cloud) as for GitLab Cloud apply. After the trial period, you will need to [contact](https://www.qodo.ai/contact/#pricing) Qodo for moving to an Enterprise account.
