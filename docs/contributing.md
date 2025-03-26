# Contributing Guidelines

We welcome contributions from the community! This guide will help you understand our contribution process and requirements.

## Development guidelines

1. Small PRs ([blogpost](https://testing.googleblog.com/2024/07/in-praise-of-small-pull-requests.html))
1. When fixing a bug, include a test that reproduces the issue in the same pull request (the test should fail without your changes)
1. If you are refactoring, ensure adequate test coverage exists for the target area. If coverage is insufficient, create tests in a separate pull request first. This approach provides a safety net for validating current behavior and simplifies code reviews.

## Build and Test

Prerequisites:

- Poetry 1.5.1. [Installation guide](https://python-poetry.org/docs/#installing-with-the-official-installer)

Build a new local version:

```bash
poetry build
```

### Unit tests

```bash
poetry run pytest tests/unit
```

### Linting and Type-checking

`ucc-gen` uses the [`pre-commit`](https://pre-commit.com) framework for linting and type-checking.
Consult with `pre-commit` documentation about what is the best way to install the software.

To run it locally:

```bash
poetry run pre-commit run --all-files
```
<!--
## Testing TA with the Local Version of AUT

AUT is a testing tool for Technology Add-ons (TAs), so it's important to use the tool for TA tests while developing AUT locally.

...
-->

## Documentation changes

Documentation changes are also welcome!

To verify changes locally:

```bash
poetry run mkdocs serve -a localhost:8001
```

## Issues and bug reports

If you're seeing some unexpected behavior with AUT, create an [issue](https://github.com/splunk/addonfactory-ucc-test/issues) on GitHub. You can click on "New Issue" and use the template provided.

## Pull requests

We love to see pull requests!

### PR Title

We follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) for PR titles. The title format is crucial as we squash commits during merge, and this PR title will be used in the release notes (for feat and fix types).
Here's a short TL;DR of the format:

```
<type>(<scope>): <description>

Types:
- feat: New feature (user facing)
- fix: Bug fix (user facing)
- docs: Documentation changes (user facing)
- style: Code style changes (formatting, etc.)
- refactor: Code changes that neither fix bugs nor add features
- perf: Performance improvements
- test: Adding or updating tests
- chore: Maintenance tasks
```

Example: `feat(ui): add new input validation for text fields`

### PR Description

Includes:

- Motivation behind the changes (any reference to issues or user stories)
- High level description of code changes
- Description of changes in user experience if applicable.
- Steps to reproduce the issue or test the new feature, if possible. This will speed up the review process.

After submitting your PR, GitHub will automatically add relevant reviewers, and CI checks will run automatically.

> Note: `semgrep` and `fossa` checks might fail for external contributors. This is expected and will be handled by maintainers.


## Release flow

The instructions below utilize the [GitHub CLI tool](https://cli.github.com/), which you can install via HomeBrew:

```bash
brew install gh
gh auth login
```

- The default development branch is `develop`. Use this branch for creating pull requests (PRs) for your features, fixes, documentation updates, etc. PRs to the `develop` branch should be merged using the squash option on GitHub.
- When it's time for a release (handled by the UCC team), create a PR from `develop` to `main` using the following commands:

```bash
gh pr create --title "chore: merge develop into main" --body "" --head develop --base main
# set automerge with merge commit to avoid accidentally squashing PR
gh pr merge develop --auto --merge
```

- Ensure CI passes and await team review.
- PR should be merged using **merge commit** option in GitHub (already included in the command)
- Releases are made automatically (both on GitHub and PyPI), and a bot will push a commit to `main` with all necessary changes
- If necessary, update release notes and CHANGELOG.md accordingly to the content of the release.
- If any issue was solved by this release, remove **waiting-for-release** label from it and then close the issue.
- After the release, backport the bot's changes to the `develop` branch:

```bash
gh pr create --title "chore: merge main into develop" --body "" --head main --base develop
# set automerge with merge commit to avoid accidentally squashing PR
gh pr merge main --auto --merge
```

- If a release encounters issues requiring a quick bug fix (handled by the AUT team):
    + Create a PR to the main branch with the fix, including tests that reproduce and then fix the issue.
    + Ensure CI passes and await team review.
    + Merge the PR using the merge commit option on GitHub.
    + Backport the bug fix PR to the develop branch.

<!--
- After release is done, announce it to community on slack channels:
    + [Internal UCC channel](https://splunk.enterprise.slack.com/archives/C03T8QCHBTJ)
    + [Splunk Usergroup UCC channel](https://splunk-usergroups.slack.com/archives/C03SG3ZL4S1)
-->
