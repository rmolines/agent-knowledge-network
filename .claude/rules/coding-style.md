# Rule: Coding Style

## Markdown

- Use ATX headings (`#`, `##`, etc.) — not Setext style (`===`, `---`)
- Blank line before and after headings, lists, and code blocks
- Use fenced code blocks with language tags (` ```bash `, ` ```json `, etc.)
- Line length: 200 chars max (see `.markdownlint.yaml`)
- Use `<!-- TODO: ... -->` for template placeholders that users should fill

## Shell scripts

- Always start with `#!/bin/bash`
- Use `set -euo pipefail`
- Quote all variables: `"$VAR"` not `$VAR`
- Use `command -v tool` to check if tools exist before using them
- No sourcing of `~/.zshrc` or `~/.bashrc` — hooks run in non-interactive shells

## JSON (settings, configs)

- Use 2-space indentation
- No trailing commas
- Validate with: `python3 -m json.tool file.json > /dev/null`

## Naming

- Files: `kebab-case.md`
- GitHub Actions workflows: `kebab-case.yml`
- Makefile targets: `kebab-case`
- Git branches: `feat/kebab-case`
- Skills/commands: `kebab-case.md`

## Secrets and environment

- Never hardcode secrets in any file
- Document all env vars in `.env.example`
- Never commit `.env` — it's in `.gitignore`
