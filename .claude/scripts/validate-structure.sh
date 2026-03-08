#!/bin/bash
# validate-structure.sh — Check that required files exist in the repo
# Called by Makefile `make validate` and CI

set -euo pipefail

ERRORS=0

required_files=(
  "CLAUDE.md"
  "HANDOVER.md"
  "LEARNINGS.md"
  "README.md"
  "Makefile"
  ".markdownlint.yaml"
  ".claude/settings.json"
  ".claude/commands/start-feature.md"
  ".claude/commands/ship-feature.md"
  ".claude/commands/close-feature.md"
  ".claude/commands/handover.md"
  ".claude/commands/sync-skills.md"
  ".claude/commands/SYNC_VERSION"
  ".claude/hooks/pre-tool-use.sh"
  ".claude/rules/git-workflow.md"
  ".claude/rules/coding-style.md"
  ".claude/rules/security.md"
  ".github/workflows/ci.yml"
  ".github/dependabot.yml"
  "memory/MEMORY.md"
)

for f in "${required_files[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "❌ Missing: $f"
    ERRORS=$((ERRORS + 1))
  else
    echo "✅ $f"
  fi
done

if [[ $ERRORS -gt 0 ]]; then
  echo ""
  echo "Structure validation failed: $ERRORS file(s) missing."
  exit 1
fi

echo ""
echo "✅ Structure validation passed."
