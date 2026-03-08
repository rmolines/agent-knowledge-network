#!/bin/bash
# pre-tool-use.sh — Lint Markdown before Write/Edit
# Called by .claude/settings.json PreToolUse hook
# Runs in non-interactive shell: no .zshrc/.bashrc sourcing

set -euo pipefail

# Read the tool input from stdin (Claude Code passes JSON)
INPUT=$(cat)

# Extract the file path from tool input
# Works for both Write (file_path) and Edit (file_path)
FILE_PATH=$(echo "$INPUT" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get('file_path', ''))
except Exception:
    print('')
" 2>/dev/null || echo "")

# Only lint Markdown files
if [[ "$FILE_PATH" != *.md ]]; then
  exit 0
fi

# Skip if file doesn't exist yet (Write tool creating new file — lint after write)
if [[ ! -f "$FILE_PATH" ]]; then
  exit 0
fi

# Run markdownlint if available
if command -v npx &>/dev/null; then
  npx --yes markdownlint-cli2 "$FILE_PATH" 2>&1 || {
    echo "⚠️  markdownlint found issues in $FILE_PATH"
    echo "Fix the issues above or update .markdownlint.yaml to suppress false positives."
    exit 1
  }
fi

exit 0
