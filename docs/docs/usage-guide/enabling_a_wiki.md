`Supported Git Platforms: GitHub, GitLab, Bitbucket`


For optimal functionality of Qodo Merge, we recommend enabling a wiki for each repository where Qodo Merge is installed. The wiki serves several important purposes:

**Key Wiki Features: 💎**

- Storing a [configuration file](https://qodo-merge-docs.qodo.ai/usage-guide/configuration_options/#wiki-configuration-file)
- Defining a [`best_practices.md`](https://qodo-merge-docs.qodo.ai/tools/improve/#best-practices) file
- Track [accepted suggestions](https://qodo-merge-docs.qodo.ai/tools/improve/#suggestion-tracking)
- Facilitates learning over time by creating an [auto_best_practices.md](https://qodo-merge-docs.qodo.ai/core-abilities/auto_best_practices) file


**Setup Instructions (GitHub):**

To enable a wiki for your repository:

1. Navigate to your repository's main page on GitHub
2. Select "Settings" from the top navigation bar
3. Locate the "Features" section
4. Enable the "Wikis" option by checking the corresponding box
5. Return to your repository's main page
6. Look for the newly added "Wiki" tab in the top navigation
7. Initialize your wiki by clicking "Create the first page" and saving (this step is important - without creating an initial page, the wiki will not be fully functional)

### Why Wiki?

- Your code (and its derivatives, including accepted code suggestions) is yours. Qodo Merge will never store it on external servers.
- Repository changes typically require pull requests, which create overhead and are time-consuming. This process is too cumbersome for auto data aggregation, and is not very convenient even for managing frequently updated content like configuration files and best practices.
- A repository wiki page provides an ideal balance:
    - It lives within your repository, making it suitable for code-related documentation
    - It enables quick updates without the overhead of pull requests
    - It maintains full Git version control, allowing you to track changes over time.
