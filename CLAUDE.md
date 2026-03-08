# CLAUDE.md — Instructions for Claude Code
<!-- TODO: Replace this file with your project's specific instructions after forking -->

## Project overview
<!-- TODO: 2-3 sentences about what this project does and why it exists -->

## Critical rules — NEVER do without explicit approval

- Never commit tokens, keys, or passwords — use environment variables or secret managers
- Never force-push to main — always use PRs with CI passing
- Never skip pre-commit hooks (--no-verify) — fix the underlying issue
- Never delete data without a dry-run step first

## Feature workflow — complete cycle

Use the skills below for any non-trivial feature (>2-3 files or with architectural decisions):

1. `/start-milestone` — decompose milestone from roadmap.md into scoped features → generates `sprint.md`
2. `/start-feature` — intake + research (Phase A) → `/clear` → planning (Phase B) → `/clear` → worktree + execution (Phase C)
3. Build and iterate in the worktree
4. `/validate` — direction check: verify implementation still solves the original problem
5. `/ship-feature` — simplify automático + commit + rebase + PR + CI + smoke test
6. `/close-feature` — documentation (HANDOVER, MEMORY, LEARNINGS, CLAUDE.md) + cleanup

**Orientation (any time):** `/project-compass` — "where are we?", "what's left?", "next feature?"

**Why the `/clear` between phases?**
Clean context = less hallucination. Each phase saves output to `.claude/feature-plans/<name>/`
so the next phase can read it without relying on conversation memory.

## Hot files — always read before editing

These files are modified by almost every feature — coordinate with other agents:

- `CLAUDE.md`
- `.github/workflows/ci.yml`
- `.claude/commands/*.md`
- `README.md`
- `Makefile`

## Known pitfalls

| Component | Pitfall | Fix |
|---|---|---|
| template-sync.yml | Runs on template repo itself → no-op | Guard: `!github.event.repository.is_template` |
| bootstrap.yml | Only fires on first push (run_number == 1) | Don't re-run manually — it will apply protection twice |
| Hooks | Run in non-interactive shells; `~/.zshrc` with unconditional `echo` breaks JSON | Use `#!/bin/bash` with `set -euo pipefail`; no shell rc sourcing |
| settings.json | Hooks execute shell without confirmation (CVE-2025-59536) | Comment warns users; hooks in `.claude/hooks/` are auditable |
| SYNC_VERSION | SHA must match upstream main HEAD | Update with `git rev-parse upstream/main` after sync |

## Worktree convention

- Path: `.claude/worktrees/<feature-name>`
- Branch: `feature/<feature-name>` (kebab-case)
- Always rebase before starting: `git fetch origin && git rebase origin/main`

## Daily commands

```bash
make help            # List all available commands
make check           # Run lint + validate
make lint            # Lint Markdown files
make validate        # Validate JSON + structure
make sync-skills     # Pull latest skills from upstream template
make clean           # Remove generated files (.claude/worktrees/, .claude/cache/)
```

## Secrets

None required — this template has no backend. Add secrets in `.env` (never commit) when
your project needs them. Document them here and in `.env.example`.
