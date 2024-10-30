## Local and global metadata injection with multi-stage analysis
(1)
Qodo Merge initially retrieves for each PR the following data:

- PR title and branch name
- PR original description
- Commit messages history
- PR diff patches, in [hunk diff](https://loicpefferkorn.net/2014/02/diff-files-what-are-hunks-and-how-to-extract-them/) format
- The entire content of the files that were modified in the PR

!!! tip "Tip: Organization-level metadata"
    In addition to the inputs above, Qodo Merge can incorporate supplementary preferences provided by the user, like [`extra_instructions` and `organization best practices`](https://qodo-merge-docs.qodo.ai/tools/improve/#extra-instructions-and-best-practices). This information can be used to enhance the PR analysis.

(2)
By default, the first command that Qodo Merge executes is [`describe`](https://qodo-merge-docs.qodo.ai/tools/describe/), which generates three types of outputs:

- PR Type (e.g. bug fix, feature, refactor, etc)
- PR Description - a bullet point summary of the PR
- Changes walkthrough - for each modified file, provide a one-line summary followed by a detailed bullet point list of the changes.

These AI-generated outputs are now considered as part of the PR metadata, and can be used in subsequent commands like `review` and `improve`.
This effectively enables multi-stage chain-of-thought analysis, without doing any additional API calls which will cost time and money.

For example, when generating code suggestions for different files, Qodo Merge can inject the AI-generated ["Changes walkthrough"](https://github.com/Codium-ai/pr-agent/pull/1202#issue-2511546839) file summary in the prompt:

```
## File: 'src/file1.py'
### AI-generated file summary:
- edited function `func1` that does X
- Removed function `func2` that was not used
- ....

@@ ... @@ def func1():
__new hunk__
11  unchanged code line0 in the PR
12  unchanged code line1 in the PR
13 +new code line2 added in the PR
14  unchanged code line3 in the PR
__old hunk__
 unchanged code line0
 unchanged code line1
-old code line2 removed in the PR
 unchanged code line3

@@ ... @@ def func2():
__new hunk__
...
__old hunk__
...
```

(3) The entire PR files that were retrieved are also used to expand and enhance the PR context (see [Dynamic Context](https://qodo-merge-docs.qodo.ai/core-abilities/dynamic_context/)).


(4) All the metadata described above represents several level of cumulative analysis - ranging from hunk level, to file level, to PR level, to organization level.
This comprehensive approach enables Qodo Merge AI models to generate more precise and contextually relevant suggestions and feedback.
