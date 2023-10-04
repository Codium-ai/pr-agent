# Similar Issue Tool
The similar issue tool retrieves the most similar issues to the current issue.
It can be invoked manually by commenting on any PR:
```
/similar_issue
```
For example:

<kbd><img src=./../pics/similar_issue_original_issue.png width="768"></kbd>
<kbd><img src=./../pics/similar_issue_comment.png width="768"></kbd>
<kbd><img src=./../pics/similar_issue.png width="768"></kbd>

Note that to perform retrieval, the `similar_issue` tool indexes all the repo previous issues (once).

To enable usage of the '**similar issue**' tool, you need to set the following keys in `.secrets.toml` (or in the relevant environment variables):
```
[pinecone]
api_key = "..."
environment = "..."
```
These parameters can be obtained by registering to [Pinecone](https://app.pinecone.io/?sessionType=signup/).


### How to use:
- To invoke the 'similar issue' tool from **CLI**, run:
`python3 cli.py --issue_url=... similar_issue`

- To invoke the 'similar' issue tool via online usage, [comment](https://github.com/Codium-ai/pr-agent/issues/178#issuecomment-1716934893) on a PR:
`/similar_issue`

- You can also enable the 'similar issue' tool to run automatically when a new issue is opened, by adding it to the [pr_commands list in the github_app section](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/settings/configuration.toml#L66)
