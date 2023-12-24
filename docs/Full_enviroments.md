## Overview
`PR-Agent` offers extensive pull request functionalities across various git providers:
|       |                                             | GitHub | Gitlab | Bitbucket | CodeCommit | Azure DevOps | Gerrit |
|-------|---------------------------------------------|:------:|:------:|:---------:|:----------:|:----------:|:----------:|
| TOOLS | Review                                      |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:       |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:    |
|       | ⮑ Incremental                              |   :white_check_mark:    |       |           |       |          |     |
|       | Ask                                         |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:          |   :white_check_mark:          | :white_check_mark: |  :white_check_mark:    |
|       | Auto-Description                            |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:        |   :white_check_mark:    |   :white_check_mark:    | :white_check_mark:    |
|       | Improve Code                                |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:        |   :white_check_mark:    |          |    :white_check_mark:    |
|       | ⮑ Extended                             |   :white_check_mark:    |   :white_check_mark:    |        :white_check_mark:   |   :white_check_mark:    |          | :white_check_mark:    |
|       | Reflect and Review                          |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:        |          |   :white_check_mark:    |    :white_check_mark:    |
|       | Update CHANGELOG.md                         |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:        |   :white_check_mark:    |          |       |
|       | Find similar issue                          |   :white_check_mark:    |                         |                             |          |          |       |
|       | Add Documentation                           |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:        |   :white_check_mark:    |          |    :white_check_mark:    |
|       | Generate Custom Labels 💎                   |   :white_check_mark:    |   :white_check_mark:    |         |     |          |      |
|       |                                             |        |        |      |      |      |
| USAGE | CLI                                         |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:       |   :white_check_mark:    |   :white_check_mark:    |
|       | App / webhook                               |   :white_check_mark:    |   :white_check_mark:    |           |          |          |
|       | Tagging bot                                 |   :white_check_mark:    |        |           |          |          |
|       | Actions                                     |   :white_check_mark:    |        |           |          |          |
|       | Web server                                  |       |        |           |          |          |  :white_check_mark:   |
|       |                                             |        |        |      |      |      |
| CORE  | PR compression                              |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:       | :white_check_mark: |   :white_check_mark:       | :white_check_mark:       |
|       | Repo language prioritization                |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:       | :white_check_mark: |   :white_check_mark:       | :white_check_mark:       |
|       | Adaptive and token-aware<br />file patch fitting |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:       | :white_check_mark: |   :white_check_mark:       | :white_check_mark:       |
|       | Multiple models support |   :white_check_mark:    |   :white_check_mark:    |   :white_check_mark:       | :white_check_mark: |   :white_check_mark:       | :white_check_mark:       |
|       | Incremental PR Review |   :white_check_mark:    |      |      |      |      |      |