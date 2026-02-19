---
name: git
description: Git commit and branch creation using Conventional Commits format, and GitHub operations via gh CLI. Use when creating commits, staging changes, writing commit messages, creating branches, creating PRs, or checking CI. Triggers include: "commit these changes", "create a commit", "make a branch", "stage and commit", "create a PR", "check CI".
allowed-tools: Bash(git add:*), Bash(git branch:*), Bash(git checkout -b:*), Bash(git commit:*), Bash(git diff:*), Bash(git log:*), Bash(git status:*)
---

# Git Commit Guidelines

## Commit Message Format

Use Conventional Commits format:

```
<type>[optional scope]: <description>

[optional body]
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

**Subject line rules:**

- Start with a type prefix
- Description in imperative present tense
- Keep short and concise
- Lowercase after the colon

**Examples:**

- `feat: add user authentication`
- `fix: resolve validation bug in login form`
- `docs: update database schema documentation`
- `chore: remove deprecated API endpoints`
- `refactor: simplify user service`

**Body (optional):**

- Add details only when subject line insufficient
- Explain why, not what (code shows what)

## Branch Naming

- Derive from goal
- Keep short
- Use lowercase with hyphens

**Examples:**

- `user-auth`
- `fix-validation`
- `update-schema`
- `api-cleanup`

## GitHub CLI

Use `gh` for all GitHub operations. Never use WebFetch or WebSearch to inspect GitHub URLs — always use `gh` instead.

```shell
gh pr create --title "..." --body "..."  # Create a pull request
gh pr view                               # View current branch's PR
gh run list --branch <branch>            # List CI runs for a branch
gh run view <run-id> --log-failed        # Show logs for failed CI jobs
```

When a GHA workflow fails, always use `gh run view <run-id> --log-failed` to diagnose it.
