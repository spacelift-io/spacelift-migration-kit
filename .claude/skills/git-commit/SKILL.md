---
name: git-commit
description: Git commit and branch creation guidelines. Use when creating commits, committing code changes, or creating new branches.
allowed-tools: Bash(git add:*), Bash(git branch:*), Bash(git checkout -b:*), Bash(git commit:*), Bash(git diff:*), Bash(git log:*), Bash(git status:*)
---

# Git Commit Guidelines

## Commit Message Format

**Subject line:**

- Start with imperative verb in present tense (add, fix, update, remove, refactor)
- Keep short and concise
- No conventional commit prefixes (no "feat:", "fix:", etc.)

**Examples:**

- `Add user authentication`
- `Fix validation bug in login form`
- `Update database schema for events`
- `Remove deprecated API endpoints`
- `Refactor user service`

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

## What NOT to Include

- No AI co-authoring information
- No conventional commit prefixes
- No ticket numbers (unless explicitly requested)
