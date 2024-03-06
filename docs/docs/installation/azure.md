## Azure DevOps provider

To use Azure DevOps provider use the following settings in configuration.toml:
```
[config]
git_provider="azure"
use_repo_settings_file=false
```

Azure DevOps provider supports [PAT token](https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate?view=azure-devops&tabs=Windows) or [DefaultAzureCredential](https://learn.microsoft.com/en-us/azure/developer/python/sdk/authentication-overview#authentication-in-server-environments) authentication.
PAT is faster to create, but has build in experation date, and will use the user identity for API calls. 
Using DefaultAzureCredential you can use managed identity or Service principle, which are more secure and will create seperate ADO user identity (via AAD) to the agent.

If PAT was choosen, you can assign the value in .secrets.toml. 
If DefaultAzureCredential was choosen, you can assigned the additional env vars like AZURE_CLIENT_SECRET directly, 
or use managed identity/az cli (for local develpment) without any additional configuration.
in any case, 'org' value must be assigned in .secrets.toml:
```
[azure_devops]
org = "https://dev.azure.com/YOUR_ORGANIZATION/"
# pat = "YOUR_PAT_TOKEN" needed only if using PAT for authentication
```

### Azure DevOps Webhook

To trigger from an Azure webhook, you need to manually [add a webhook](https://learn.microsoft.com/en-us/azure/devops/service-hooks/services/webhooks?view=azure-devops). 
Use the "Pull request created" type to trigger a review, or "Pull request commented on" to trigger any supported comment with /<command> <args> comment on the relevant PR. Note that for the "Pull request commented on" trigger, only API v2.0 is supported.


For webhook security, create a sporadic username/password pair and configure the webhook username and password on both the server and Azure DevOps webhook. These will be sent as basic Auth data by the webhook with each request:
```
[azure_devops_server]
webhook_username = "<basic auth user>"
webhook_password = "<basic auth password>"
```
> :warning: **Ensure that the webhook endpoint is only accessible over HTTPS** to mitigate the risk of credential interception when using basic authentication.
