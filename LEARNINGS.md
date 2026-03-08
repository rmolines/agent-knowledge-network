# LEARNINGS.md — Technical learnings

Gotchas, limitations, and non-obvious behaviors discovered while working on this project.

---

## GitHub Actions

### `bootstrap.yml`: `run_number == 1` guard

`github.run_number` starts at 1 for the first run of any workflow in a repo. Using this as a
guard ensures branch protection is only applied once. **Do not re-run this workflow manually** —
it will attempt to apply protection again (which is usually fine but clutters logs).

### `template-sync.yml`: must guard with `!is_template`

Without the `!github.event.repository.is_template` guard, the sync workflow would run on the
template repo itself and open PRs against its own `main`. The guard makes it a no-op on the
template and active only on forks.

### Action SHA pinning

Always pin to full commit SHA, not tag:
```yaml
# Good
uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
# Bad (tag can be hijacked)
uses: actions/checkout@v4
```

---

## Claude Code hooks (CVE-2025-59536)

Hooks in `.claude/settings.json` execute shell commands **without user confirmation**.
This was documented in CVE-2025-59536. Mitigation: keep hook logic in external scripts
(`.claude/hooks/`) so they're visible, auditable, and can be reviewed in PRs.

---

## markdownlint

- Use `npx --yes markdownlint-cli2` to avoid requiring global install
- `MD013` (line length) needs `tables: false` and `code_blocks: false` to avoid false positives
- `MD024` (duplicate headings) should be disabled for `HANDOVER.md` — entries often have similar structure
- `MD041` (first heading must be h1) breaks templates with frontmatter or `<!-- TODO -->` comments

---

## 2026-03-08 — alembic.ini: ConfigParser silently lowercases option keys

`sqlalchemy.url = %(DATABASE_URL)s` fails at runtime with `InterpolationMissingOptionError` because
ConfigParser normalises all option keys to lowercase before interpolation — `%(DATABASE_URL)s` becomes
`%(database_url)s`, which doesn't exist. Fix: use a literal placeholder in `alembic.ini` and read the
real URL from the environment inside `migrations/env.py` using `os.environ` or the app's settings object.

## 2026-03-08 — Poetry 1.8+ in package-mode with PEP 621 pyproject.toml

Poetry 1.8.0 defaults to package mode and expects `[tool.poetry]` with `name`, `version`, and `authors`.
Projects that use only `[project]` (PEP 621 / uv style) will fail at `poetry install`. Fix: add
`[tool.poetry]` with `package-mode = false` — this disables packaging behaviour and lets Poetry act
purely as a dependency manager without requiring the full package metadata.

## 2026-03-08 — fastapi-users pins python-multipart to an exact version

`fastapi-users 13.x` depends on `python-multipart==0.0.9` (exact). If `pyproject.toml` also pins
`python-multipart` (e.g. `^0.0.20`), Poetry raises a dependency conflict. Fix: remove the explicit
`python-multipart` entry from `pyproject.toml` and let `fastapi-users` own the constraint. The
pattern generalises: when a framework uses an exact pin on a transitive dep, don't re-declare it.

## 2026-03-08 — datetime.utcnow() returns naive datetimes; dangerous with expires_at

`datetime.utcnow()` is deprecated since Python 3.12 and returns a naive datetime (no tzinfo).
Comparing it against a timezone-aware `expires_at` stored in the DB raises a TypeError at runtime.
Fix: `datetime.now(tz=timezone.utc)` everywhere — returns an aware datetime and is future-proof.

## 2026-03-08 — Canonical config must have one source of truth; migrations/env.py is a common offender

`migrations/env.py` often reads `os.environ["DATABASE_URL"]` directly, bypassing the app's
`api/config.py` (which handles `.env` loading via python-dotenv). This means migrations work in
production (where the var is injected) but silently break in local dev (where only `.env` exists).
Fix: import `settings` from `api/config.py` in `env.py` and read `settings.database_url`.
