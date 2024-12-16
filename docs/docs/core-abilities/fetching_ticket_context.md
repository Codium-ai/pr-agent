# Fetching Ticket Context for PRs
`Supported Git Platforms : GitHub, GitLab, Bitbucket`

## Overview
Qodo Merge PR Agent streamlines code review workflows by seamlessly connecting with multiple ticket management systems.
This integration enriches the review process by automatically surfacing relevant ticket information and context alongside code changes.

## Ticket systems supported
- GitHub
- Jira (💎)

Ticket data fetched:

1. Ticket Title
2. Ticket Description
3. Custom Fields (Acceptance criteria)
4. Subtasks (linked tasks)
5. Labels
6. Attached Images/Screenshots

## Affected Tools

Ticket Recognition Requirements:

- The PR description should contain a link to the ticket or if the branch name starts with the ticket id / number.
- For Jira tickets, you should follow the instructions in [Jira Integration](https://qodo-merge-docs.qodo.ai/core-abilities/fetching_ticket_context/#jira-integration) in order to authenticate with Jira.

### Describe tool
Qodo Merge PR Agent will recognize the ticket and use the ticket content (title, description, labels) to provide additional context for the code changes.
By understanding the reasoning and intent behind modifications, the LLM can offer more insightful and relevant code analysis.

### Review tool
Similarly to the `describe` tool, the `review` tool will use the ticket content to provide additional context for the code changes.

In addition, this feature will evaluate how well a Pull Request (PR) adheres to its original purpose/intent as defined by the associated ticket or issue mentioned in the PR description.
Each ticket will be assigned a label (Compliance/Alignment level), Indicates the degree to which the PR fulfills its original purpose, Options: Fully compliant, Partially compliant or Not compliant.


![Ticket Compliance](https://www.qodo.ai/images/pr_agent/ticket_compliance_review.png){width=768}

By default, the tool will automatically validate if the PR complies with the referenced ticket.
If you want to disable this feedback, add the following line to your configuration file:

```toml
[pr_reviewer]
require_ticket_analysis_review=false
```

## Providers

### Github Issues Integration

Qodo Merge PR Agent will automatically recognize Github issues mentioned in the PR description and fetch the issue content.
Examples of valid GitHub issue references:

- `https://github.com/<ORG_NAME>/<REPO_NAME>/issues/<ISSUE_NUMBER>`
- `#<ISSUE_NUMBER>`
- `<ORG_NAME>/<REPO_NAME>#<ISSUE_NUMBER>`

Since Qodo Merge PR Agent is integrated with GitHub, it doesn't require any additional configuration to fetch GitHub issues.

### Jira Integration 💎

We support both Jira Cloud and Jira Server/Data Center.
To integrate with Jira, you can link your PR to a ticket using either of these methods:

**Method 1: Description Reference:**

Include a ticket reference in your PR description using either the complete URL format https://<JIRA_ORG>.atlassian.net/browse/ISSUE-123 or the shortened ticket ID ISSUE-123.

**Method 2: Branch Name Detection:**

Name your branch with the ticket ID as a prefix (e.g., `ISSUE-123-feature-description` or `ISSUE-123/feature-description`).

!!! note "Jira Base URL"
    For shortened ticket IDs or branch detection (method 2), you must configure the Jira base URL in your configuration file under the [jira] section:

    ```toml
    [jira]
    jira_base_url = "https://<JIRA_ORG>.atlassian.net"
    ```

#### Jira Cloud 💎
There are two ways to authenticate with Jira Cloud:

**1) Jira App Authentication**

The recommended way to authenticate with Jira Cloud is to install the Qodo Merge app in your Jira Cloud instance. This will allow Qodo Merge to access Jira data on your behalf.

Installation steps:

1. Click [here](https://auth.atlassian.com/authorize?audience=api.atlassian.com&client_id=8krKmA4gMD8mM8z24aRCgPCSepZNP1xf&scope=read%3Ajira-work%20offline_access&redirect_uri=https%3A%2F%2Fregister.jira.pr-agent.codium.ai&state=qodomerge&response_type=code&prompt=consent) to install the Qodo Merge app in your Jira Cloud instance, click the `accept` button.<br>
![Jira Cloud App Installation](https://www.qodo.ai/images/pr_agent/jira_app_installation1.png){width=384}

2. After installing the app, you will be redirected to the Qodo Merge registration page. and you will see a success message.<br>
![Jira Cloud App success message](https://www.qodo.ai/images/pr_agent/jira_app_success.png){width=384}

3. Now you can use the Jira integration in Qodo Merge PR Agent.

**2) Email/Token Authentication**

You can create an API token from your Atlassian account:

1. Log in to https://id.atlassian.com/manage-profile/security/api-tokens.

2. Click Create API token.

3. From the dialog that appears, enter a name for your new token and click Create.

4. Click Copy to clipboard.

![Jira Cloud API Token](https://images.ctfassets.net/zsv3d0ugroxu/1RYvh9lqgeZjjNe5S3Hbfb/155e846a1cb38f30bf17512b6dfd2229/screenshot_NewAPIToken){width=384}

5. In your [configuration file](https://qodo-merge-docs.qodo.ai/usage-guide/configuration_options/) add the following lines:

```toml
[jira]
jira_api_token = "YOUR_API_TOKEN"
jira_api_email = "YOUR_EMAIL"
```


#### Jira Server/Data Center 💎

Currently, we only support the Personal Access Token (PAT) Authentication method.

1. Create a [Personal Access Token (PAT)](https://confluence.atlassian.com/enterprise/using-personal-access-tokens-1026032365.html) in your Jira account
2. In your Configuration file/Environment variables/Secrets file, add the following lines:

```toml
[jira]
jira_base_url = "YOUR_JIRA_BASE_URL" # e.g. https://jira.example.com
jira_api_token = "YOUR_API_TOKEN"
```
