# claude-kickstart

**The professional Claude Code setup you'd spend 3 months discovering on your own — working in 30 minutes.**

Fork → open Claude Code → run `/start-project "your idea"` → 30 minutes later you have:

- A structured project with multi-agent running in parallel
- Complete feature lifecycle (start → ship → close → repeat)
- Opinionated CLAUDE.md with best practices baked in
- CI/CD on GitHub Actions (lint + validation + branch protection)
- Institutional memory system (HANDOVER + LEARNINGS + MEMORY)

The `/start-project` research phase with 4 parallel agents is itself a demo of the multi-agent power — you see it work on the first interaction, without configuring anything.

---

## Quickstart

```bash
# 1. Fork this repo on GitHub ("Use this template" button)
# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/YOUR_PROJECT.git
cd YOUR_PROJECT

# 3. Open Claude Code and kick off your project
claude
```

Then in Claude Code:

```text
/start-project "your idea here"
```

That's it. Claude will research your market, validate assumptions, plan the architecture, and bootstrap the project — asking only what it can't infer.

---

## What's included

### Skills (`/commands`)

| Skill | What it does |
|---|---|
| `/start-project` | Discovery → research → plan → bootstrap (this skill) |
| `/start-feature` | Intake + research → plan → worktree + execution |
| `/ship-feature` | Commit + rebase + PR + CI + smoke test |
| `/close-feature` | Documentation (HANDOVER, MEMORY, LEARNINGS) + cleanup |
| `/handover` | Summarize session and prepend to HANDOVER.md |
| `/sync-skills` | Pull latest skills from upstream template |

### Infrastructure

- **`.claude/settings.json`** — Hooks: lint Markdown before every write
- **`.claude/rules/`** — Modular rules imported by CLAUDE.md (git, coding style, security)
- **`.github/workflows/ci.yml`** — Lint + JSON validation + structure check on every PR
- **`.github/workflows/bootstrap.yml`** — Auto-applies branch protection on first push (fork only)
- **`.github/workflows/template-sync.yml`** — Weekly PRs with upstream skill updates
- **`Makefile`** — `make check`, `make lint`, `make validate`, `make sync-skills`, `make clean`

### Memory system

- **`memory/MEMORY.md`** — Persistent context loaded each session (architectural decisions, key files)
- **`HANDOVER.md`** — Session history (newest at top)
- **`LEARNINGS.md`** — Technical gotchas and non-obvious behaviors

---

## After forking

1. **Fill in `CLAUDE.md`** — replace the `<!-- TODO -->` sections with your project specifics
2. **Update `CODEOWNERS`** — replace `@rmolines` with your GitHub username
3. **Set GitHub secrets** — add any secrets your project needs (document in `.env.example`)
4. **Run `make check`** — validate that everything is wired up correctly

---

## Feature workflow

```text
/start-feature "feature name"     # Research + plan
  → /clear                        # Clean context
  → /start-feature "feature name" # Execute in worktree

/ship-feature                     # PR + CI + merge
/close-feature                    # Docs + cleanup
```

Each `/clear` between phases prevents hallucination — outputs are saved to
`.claude/feature-plans/<name>/` so phases can read them without conversation memory.

---

## Keeping skills up to date

Your fork gets weekly PRs from this template via `template-sync.yml`.
Review and merge to stay current. Or run manually:

```bash
make sync-skills
```

---

## Philosophy

- **Zero deps in core** — no CLI to install, no runtime to maintain
- **Fork-native** — "Use this template" is the install command
- **The skills are the product** — everything else is scaffolding
- **Opinionated but not prescriptive** — the template suggests, your CLAUDE.md decides

---

## Contributing

Found a better pattern? Discovered a pitfall we should document? PRs welcome.

See `LEARNINGS.md` for the kind of content that belongs in this project.

---

## License

MIT — fork freely, ship fast.
