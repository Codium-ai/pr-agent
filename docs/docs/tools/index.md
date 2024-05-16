# Tools

Here is a list of PR-Agent tools, each with a dedicated page that explains how to use it:

| Tool                                                                                     | Description                                                                                                                                 |
|------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| **[PR Description (`/describe`](./describe.md))**                                        | Automatically generating PR description - title, type, summary, code walkthrough and labels                                                 |
| **[PR Review (`/review`](./review.md))**                                                 | Adjustable feedback about the PR, possible issues, security concerns, review effort and more                                                |
| **[Code Suggestions (`/improve`](./improve.md))**                                        | Code suggestions for improving the PR                                                                                                       |
| **[Question Answering (`/ask ...`](./ask.md))**                                          | Answering free-text questions about the PR, or on specific code lines                                                                       |
| **[Update Changelog (`/update_changelog`](./update_changelog.md))**                      | Automatically updating the CHANGELOG.md file with the PR changes                                                                            |
| **[Find Similar Issue (`/similar_issue`](./similar_issues.md))**                         | Automatically retrieves and presents similar issues                                                                                         |
| **[Help (`/help`](./help.md))**                                                          | Provides a list of all the available tools. Also enables to trigger them interactively (💎)                                                 |
| **💎 [Add Documentation (`/add_docs`](./documentation.md))**                             | Generates documentation to methods/functions/classes that changed in the PR                                                                 |
| **💎 [Generate Custom Labels (`/generate_labels`](./custom_labels.md))**                 | Generates custom labels for the PR, based on specific guidelines defined by the user                                                        |
| **💎 [Analyze (`/analyze`](./analyze.md))**                                              | Identify code components that changed in the PR, and enables to interactively generate tests, docs, and code suggestions for each component |
| **💎 [Custom Prompt (`/custom_prompt`](./custom_prompt.md))**                            | Automatically generates custom suggestions for improving the PR code, based on specific guidelines defined by the user                      |
| **💎 [Generate Tests (`/test component_name`](./test.md))**                              | Automatically generates unit tests for a selected component, based on the PR code changes                                                   |
| **💎 [Improve Component (`/improve_component component_name`](./improve_component.md))** | Generates code suggestions for a specific code component that changed in the PR                                                             |
| **💎 [CI Feedback (`/checks ci_job`](./ci_feedback.md))**                                | Automatically generates feedback and analysis for a failed CI job                                                                           |

Note that the tools marked with 💎 are available only for PR-Agent Pro users.