# .claude/settings.json — Why each setting exists

## Security warning (CVE-2025-59536)

Hooks in `settings.json` execute shell commands **without user confirmation**.
Always audit this file before accepting PRs that modify it.
Scripts live in `.claude/hooks/` to keep them visible and reviewable.

## PreToolUse: Write|Edit → pre-tool-use.sh

**Why:** Lint Markdown before any file write to catch formatting errors early.
Without this hook, you'd discover lint failures only at CI time (after pushing).

**What it does:**
- If the file being written/edited is a `.md` file, runs `markdownlint-cli2` on it
- If markdownlint is not installed, skips silently (non-blocking for non-md files)
- Uses `npx markdownlint-cli2` to avoid requiring a global install

**To disable temporarily:**
Remove or comment out the hook entry in `settings.json`.
Do not use `--no-verify` equivalents — fix the underlying lint issue.
