<div align="center">

<a href="https://www.quorumtech.ch">
  <img src="./assets/quorum-logo.svg" alt="Quorum Technologies" width="190" />
</a>

<br /><br />

# Polyglot PR Bot

### Contribute in the language you love. We'll help with the rest.

An open-source GitHub bot that helps people contribute across programming languages, without expecting everyone to know them all.

[![MIT License](https://img.shields.io/badge/License-MIT-18314E.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-View_project-18314E?logo=github)](https://github.com/vihanga-w/polyglot-pr-bot)

**Built by [Quorum Technologies](https://www.quorumtech.ch). Open to everyone.**

</div>

---

## Good ideas shouldn't depend on which language you know.

Imagine you spot a bug in a Rust library, but you only know Python. You understand the problem. You know how to fix it. The language just gets in the way.

**We want to change that.**

Polyglot PR Bot aims to let you express a change in the language you're comfortable with, then help translate, test, and review it for the language the project actually uses. For projects with several language implementations, it can help carry the same behaviour across every copy.

You bring the idea and the code you know how to write. The bot handles the repetitive cross-language work and explains what it changed. Maintainers still decide what gets merged.

> **Example:** A contributor writes a Python test and reference fix for a bug in a C library. The bot uses that as a behavioural guide, proposes a native C patch, checks it against the project's tests and conventions, and sends it for human review. The final contribution is C, even though the contributor started in Python.

## Two ways to contribute

| If you're working on... | We'd like you to be able to... |
| --- | --- |
| **A project implemented in several languages** | Fix the version you know, then let the bot find and propose corresponding changes in the others. |
| **A project written in a language you don't know** | Submit a small reference implementation or test in a familiar language, then review the proposed native-language patch. |

The second workflow is a goal, not magic automatic translation. Some changes depend on memory models, operating systems, concurrency, performance, or platform APIs. In those cases, the bot should explain the tradeoffs and ask for help rather than pretend the languages are interchangeable.

## How a contribution moves forward

1. **Start where you're comfortable.** Open a PR in a supported language, or provide a reference example for the behaviour you want.
2. **Find the affected code.** The bot identifies related implementations, APIs, and tests, including code the PR didn't touch.
3. **Propose the missing work.** It prepares idiomatic changes for the other languages, with an explanation of what must stay equivalent.
4. **Check the result.** Builds, shared conformance tests, and language-specific tests run wherever possible. Differences are documented, not hidden.
5. **Run an independent final review.** A separate, stronger reviewer, configurable to use models such as Fable or Astra where available, checks correctness, regressions, security risks, and whether the change introduces new vulnerabilities.
6. **Hand it to a person.** The bot recommends merging only when the required checks pass and it has enough evidence. Maintainers review the actual changes and make the final call.

**An AI review is not a security guarantee.** A clean verdict means the bot found no blocking issue under the checks it performed, not that the code is proven vulnerability-free. If parity or safety cannot be established, the verdict should say **Unverified**, not **Approved**.

## Ask the bot what happened

No need to read every generated diff to understand what the bot is proposing. Ask it directly on a PR:

```text
/explain
```

Get a plain-English overview of the contributor's change, what the bot changed in other languages, why it did so, which tests passed, and what still needs attention.

```text
/explain Why does the Rust version return a Result instead of throwing?
```

Ask a specific question and get an answer grounded in the PR, its generated changes, and test results. If the available evidence doesn't answer the question, the bot should say so.

Other planned commands:

```text
/parity           # Compare implementations and report gaps
/parity --fix     # Propose missing cross-language changes
```

These commands describe the intended interface and are **not yet implemented**.

## What we're building

| Capability | Status |
| --- | --- |
| General AI PR review and improvement suggestions | Inherited from PR-Agent |
| Configurable models, CLI, and self-hosting options | Inherited from PR-Agent |
| Finding corresponding code across languages | Planned |
| Contributing via a familiar-language reference | Planned |
| Generating native-language change proposals | Planned |
| Shared behavioural and conformance checks | Planned |
| Independent high-assurance security and regression review | Planned |
| `/explain` and conversational PR questions about parity work | Planned |
| Evidence-based merge recommendations | Planned |

We're building in public. This repository began as a fork of the open-source PR-Agent project; the cross-language features above are the direction we're working toward, not features we're claiming are already shipped.

## Try the current review engine

The inherited PR-Agent CLI still uses its original command name while we build the new workflow.

```bash
git clone https://github.com/vihanga-w/polyglot-pr-bot.git
cd polyglot-pr-bot

python -m pip install -e '.[github]'
export OPENAI_KEY='your-api-key'

pr-agent --pr_url https://github.com/owner/repo/pull/123 review
```

Replace the example PR URL and configure the AI provider and repository access you intend to use. For existing PR-Agent commands and setup options, see the [upstream documentation](https://docs.pr-agent.ai/). It may refer to upstream packages rather than this fork.

## We'd love your help

You don't need to speak every programming language to contribute here either.

Whether you're experienced with compilers and static analysis, enjoy writing good tests, or just have a frustrating cross-language bug to share, there's room for you. We especially welcome real examples of two implementations that *look* alike but behave differently.

Our guiding rule is simple: **make contributions easier without making reviews less trustworthy.** No silent code changes, no mystery approvals, and no expectation that an AI-generated patch must be accepted.

Take a look at [CONTRIBUTING.md](CONTRIBUTING.md), open an issue, or start a conversation in a PR.

## Security and privacy

Run untrusted PR code in isolated environments without deployment credentials. Keep permissions narrow, require review for generated changes, and never treat a model's opinion as a substitute for security tests. Self-hosting is supported by the inherited engine; code sent to a configured model provider is subject to that provider's data-handling terms.

## License

MIT. See [LICENSE](LICENSE) for the full terms. Keep all applicable upstream copyright and license notices when redistributing this project.

---

<sub>

**From Quorum, with thanks.** Polyglot PR Bot is an open-source project by [Quorum Technologies](https://www.quorumtech.ch), built on [PR-Agent](https://github.com/The-PR-Agent/pr-agent), the community-maintained AI pull request reviewer originally developed by Qodo. We are grateful to its authors and contributors for making this work possible. The upstream project is MIT-licensed; its required attribution and license notices must be preserved. Polyglot PR Bot is independent of, and not endorsed by, Qodo or the PR-Agent maintainers.

</sub>