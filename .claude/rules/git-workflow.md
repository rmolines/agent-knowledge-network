# Rule: Git Workflow

## Branch convention

- Feature branches: `feat/<name>` (kebab-case)
- Bug fixes: `fix/<name>`
- Chores: `chore/<name>`
- Never commit directly to `main` — always use PRs

## Commit message format

```text
type(scope): short description

Body (optional): explain why, not what.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

Types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`

## Worktrees (multi-agent)

- Path: `.claude/worktrees/<feature-name>`
- Always rebase before starting:
  ```bash
  git fetch origin && git rebase origin/main
  ```
- Push immediately after each commit when other agents are active
- Never `git push --force` to main

## PR checklist

Before opening a PR:

- [ ] `make check` passes locally
- [ ] Commit message follows convention
- [ ] Hot files (CLAUDE.md, ci.yml, Makefile) updated if needed
- [ ] No secrets committed (check with `git diff --cached`)
