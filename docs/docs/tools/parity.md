---
title: "Parity"
sidebar_position: 12
---

## Overview

The `parity` tool is for repositories that keep the same behaviour implemented in several
languages side by side:

```
src/
  shared/      # code and specs every implementation consumes
  typescript/
  rust/
  golang/
  python/
```

For a pull request it works out which implementations were changed and which were not, finds the
files in each untouched implementation where the equivalent change belongs, and asks the model to
confirm whether the change is needed there (`needs change`, `not applicable` or `unverified`) and
what it should look like. It also reports performance opportunities in the changed code and whether
the work could be spread across several servers.

Invoke it by commenting on a PR:

```
/parity
```

or from the CLI:

```bash
python -m pr_agent.cli --pr_url=<PR_URL> parity
```

## What the comment contains

- A table with one row per implementation: changed, needs change (with the target file and the
  function or region), not applicable, or unverified.
- Per-language details for every `needs change` row: the file, the location, and a short description
  of the equivalent change in that language's idioms.
- A note when files under `shared_dir` changed, since every implementation consumes them.
- **Performance**: clearly faster algorithms or data structures, sequential work that can run in
  parallel, and hot paths that would be much faster in another implementation in the repository.
- **Distribution**: whether the work the change adds could be split across several servers and the
  partial results combined, with the split key, combine step and coordination costs.

Without a model (`use_llm = false`, or when the model call fails) the tool still posts a heuristic
report: which implementations were not changed and the best-matching candidate files, ranked by
relative path, file name, path words and identifiers from the diff found in the file.

PRs that touch nothing under `root` post nothing unless `publish_when_nothing_to_report` is on.

## Configuration options

All options live under the flat `[pr_parity]` section of the
[configuration file](https://github.com/vihanga-w/polyglot-pr-bot/blob/main/pr_agent/settings/configuration.toml)
and can be overridden per repository in `.pr_agent.toml`. Keys are plain strings, booleans, integers
or string lists, so an external dashboard can write them verbatim.

| Key | Default | Meaning |
| --- | --- | --- |
| `enabled` | `true` | Turn the tool off entirely. |
| `root` | `"src"` | Directory holding one sub-directory per implementation. |
| `languages` | `["typescript", "rust", "golang", "python"]` | Implementations, in report order. |
| `auto_detect_languages` | `true` | Also treat any other source-bearing directory under `root` as an implementation. |
| `shared_dir` | `"src/shared"` | Code shared by all implementations; changes are reported, not mirrored. |
| `max_candidates_per_language` | `5` | Candidate files shown per untouched implementation. |
| `max_candidate_content_fetches` | `3` | Files per implementation read to score identifier overlap. |
| `ignore_path_segments` | `["node_modules", "target", "dist", ...]` | Path segments never considered as candidates. |
| `use_llm` | `true` | `false` posts the heuristic report without a model call. |
| `check_performance` | `true` | Flag clearly faster approaches for the changed code. |
| `check_parallelism` | `true` | Flag sequential work that could run concurrently or in parallel. |
| `check_language_fit` | `true` | Flag hot paths better suited to another implementation in the repo. |
| `check_distribution` | `true` | Assess splitting the work across servers and combining results. |
| `service_dir_patterns` | `["services/*", "apps/*", "cmd/*", ...]` | Glob patterns that identify deployable services in a monorepo. |
| `publish_when_nothing_to_report` | `false` | Post a short note even when the PR is outside the layout. |
| `persistent_comment` | `true` | Update one comment per PR instead of adding a new one each run. |
| `extra_instructions` | `""` | Free-text instructions appended to the prompt. |

Example `.pr_agent.toml`:

```toml
[pr_parity]
root = "packages"
languages = ["typescript", "rust"]
shared_dir = "packages/common"
check_distribution = false
```

To run it automatically on every new PR, add `"/parity"` to `pr_commands` in the relevant
`[github_app]`, `[gitlab]` or `[bitbucket_app]` section.
