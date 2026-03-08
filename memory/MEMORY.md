# MEMORY.md — Persistent project memory

This file is loaded into Claude Code's context at the start of each session.
Keep it concise (under 200 lines) — detailed notes go in separate topic files.

## Project: claude-kickstart

GitHub Template Repository for professional Claude Code setups.

**Core value prop:** The setup that takes 3 months to discover on your own — working in 30 minutes.

**Distribution:** Fork → `/start-project "your idea"` → structured project in 30 min.

## Architecture decisions (permanent)

- **Template format**: GitHub Template Repository (not CLI) — zero friction for users
- **Skills sync**: `git fetch upstream` — zero deps, works without installing anything
- **Memory**: Markdown files — legible by humans and agents without special tooling
- **Hooks**: External scripts in `.claude/hooks/` — auditable, never inline in `settings.json`
- **CI**: Static validation only (lint + JSON + structure) — template has no runtime

## Key files

- `CLAUDE.md` — project instructions (hot file, read before every feature)
- `.claude/commands/` — the skills (they ARE the product)
- `.claude/commands/SYNC_VERSION` — SHA of upstream main used in this version
- `.claude/scripts/validate-structure.sh` — CI structure check; adding required files here means adding to repo too
- `.github/workflows/bootstrap.yml` — runs ONCE on first fork push; applies branch protection
- `.github/workflows/template-sync.yml` — weekly PRs with upstream skill updates

## Pitfalls discovered

- `bootstrap.yml` only fires when `run_number == 1` — don't re-run manually
- `template-sync.yml` must guard with `!is_template` or it'll open PRs on the template repo itself
- Hook scripts run in non-interactive shell — never source `~/.zshrc` or `~/.bashrc`
- `settings.json` hooks run without user confirmation (CVE-2025-59536) — always use scripts in `.claude/hooks/`

## TODO: replace on fork

After forking, update:
1. `CLAUDE.md` — fill in project overview section
2. `.github/CODEOWNERS` — replace `@rmolines` with your username
3. `.github/workflows/template-sync.yml` — update upstream URL if you create your own variant
4. `README.md` — replace with your project's README
