---
name: git
description: Git commit and branch creation using Conventional Commits format. Use when creating commits, staging changes, writing commit messages, or creating branches. Triggers include: "commit these changes", "create a commit", "make a branch", "stage and commit".
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
