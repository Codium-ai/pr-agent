## PR-Agent chrome extension
[PR-Agent Chrome extension](https://chromewebstore.google.com/detail/pr-agent-chrome-extension/ephlnjeghhogofkifjloamocljapahnl) is a collection of tools that integrates seamlessly with your GitHub environment, aiming to enhance your PR-Agent usage experience, and providing additional features.

## Features

### PR Chat

The PR-Chat feature allows to freely chat with your PR code, within your GitHub environment.
It will seamlessly add the PR code as context to your chat session, and provide AI-powered feedback.

To enable private chat, simply install the PR-Agent Chrome extension. After installation, each PR's file-changed tab will include a chat box, where you may ask questions about your code.
This chat session is **private**, and won't be visible to other users.

All open-source repositories are supported. For private repositories, you will also need to install PR-Agent Pro.

<img src="https://codium.ai/images/pr_agent/pr_chat1.png" width="512">
<img src="https://codium.ai/images/pr_agent/pr_chat2.png" width="512">

The Chrome extension will not send any code to the server.
To access code from private repositories, we will first validate the user's identity and permissions, then generate responses using the existing PR-Agent Pro integration.

### Toolbar extension
With PR-Agent Chrome extension, it's [easier than ever](https://www.youtube.com/watch?v=gT5tli7X4H4) to interactively configure and experiment with the different tools and configuration options.

After you found the setup that works for you, you can also easily export it as a persistent configuration file, and use it for automatic commands.

<img src="https://codium.ai/images/pr_agent/toolbar1.png" width="512">

<img src="https://codium.ai/images/pr_agent/toolbar2.png" width="512">

### PR-Agent filters

PR-Agent filters is a sidepanel option. that allows you to filter different message in the conversation tab.

For example, you can choose to present only message from PR-Agent, or filter those messages, focusing only on user's comments.

<img src="https://codium.ai/images/pr_agent/pr_agent_filters1.png" width="256">

<img src="https://codium.ai/images/pr_agent/pr_agent_filters2.png" width="256">


### Enhanced code suggestions

PR-Agent Chrome extension adds the following capabilities to code suggestions tool's comments:

- Auto-expand the table when you are viewing a code block, to avoid clipping.
- Adding a "quote-and-reply" button, that enables to address and comment on a specific suggestion (for example, asking the author to fix the issue)


<img src="https://codium.ai/images/pr_agent/chrome_extension_code_suggestion1.png" width="512">

<img src="https://codium.ai/images/pr_agent/chrome_extension_code_suggestion2.png" width="512">

## Installation

Go to the marketplace and install the extension:
[PR-Agent Chrome Extension](https://chromewebstore.google.com/detail/pr-agent-chrome-extension/ephlnjeghhogofkifjloamocljapahnl)

## Pre-requisites

The PR-Agent Chrome extension will work on any repo where you have previously [installed PR-Agent](https://pr-agent-docs.codium.ai/installation/).

## Data privacy and security

The PR-Agent Chrome extension only modifies the visual appearance of a GitHub PR screen. It does not transmit any user's repo or pull request code. Code is only sent for processing when a user submits a GitHub comment that activates a PR-Agent tool, in accordance with the standard privacy policy of PR-Agent.
