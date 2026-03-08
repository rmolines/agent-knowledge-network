# Rule: Security

## Secrets

- Never commit tokens, keys, API secrets, or passwords
- All secrets go in `.env` (gitignored) or GitHub Secrets
- Document all required env vars in `.env.example` with placeholder values
- Before any commit: `git diff --cached | grep -i "key\|token\|secret\|password"` (eyeball check)

## Hooks and automation (CVE-2025-59536)

Hooks in `.claude/settings.json` execute shell commands **without user confirmation**.

Rules:
- All hook scripts must live in `.claude/hooks/` — never inline shell in `settings.json`
- Review every PR that modifies `.claude/settings.json` or `.claude/hooks/` files
- Use `set -euo pipefail` in all hook scripts
- Never source shell rc files in hooks (non-interactive shell, can break hook JSON output)

## GitHub Actions

- Pin actions to full commit SHAs (not tags like `v4`):
  ```yaml
  # Good
  uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
  # Bad
  uses: actions/checkout@v4
  ```
- Use `permissions: contents: read` (minimal) unless write is required
- Never print secrets in logs (`echo $SECRET` in run steps)
- Use `github.event.repository.is_template` guard to prevent workflows from running on the template repo itself

## Dependencies

- Use `dependabot.yml` for automatic security updates
- Pin direct dependencies; review dependabot PRs before merging

## Data

- Never delete data without a dry-run step first
- No `rm -rf` without a confirm prompt in interactive scripts
