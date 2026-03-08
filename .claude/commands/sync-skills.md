# /sync-skills

Pull the latest skills from the upstream `claude-kickstart` template into this project.

## What this does

Updates `.claude/commands/` from `https://github.com/rmolines/claude-kickstart` (upstream).
Your customizations in `.claude/local-commands/` are NOT affected (if you use that convention).

## When to use

- When upstream has new skills or improvements you want
- After seeing a "sync-skills" PR from the automated `template-sync.yml` workflow
- Before starting a major feature, to ensure you're on current best practices

## Execution

```bash
# Add upstream remote (once)
git remote add upstream https://github.com/rmolines/claude-kickstart.git 2>/dev/null || true

# Fetch latest
git fetch upstream main

# Check current vs upstream
CURRENT=$(cat .claude/commands/SYNC_VERSION 2>/dev/null || echo "none")
UPSTREAM=$(git rev-parse upstream/main)
echo "Current: $CURRENT"
echo "Upstream: $UPSTREAM"

if [ "$CURRENT" = "$UPSTREAM" ]; then
  echo "✅ Already up to date."
else
  # Check for local uncommitted changes before applying (would be overwritten)
  DIRTY_LOCAL=$(git status --porcelain .claude/commands/ 2>/dev/null)
  if [ -n "$DIRTY_LOCAL" ]; then
    echo "⚠️  .claude/commands/ tem mudanças locais não-commitadas:"
    echo "$DIRTY_LOCAL"
    echo ""
    echo "Commitar ou stash antes de sync para evitar perda de mudanças."
    exit 1
  fi

  # Show what would change
  git diff HEAD upstream/main -- .claude/commands/

  # Apply (confirm with user first)
  git checkout upstream/main -- .claude/commands/
  echo "$UPSTREAM" > .claude/commands/SYNC_VERSION

  # Commit
  git add .claude/commands/
  git commit -m "chore: sync skills from upstream template ($(echo $UPSTREAM | cut -c1-7))"
  echo "✅ Skills updated. Review the diff and push when ready."
fi
```

## After syncing

- Review the diff: `git show HEAD`
- Run `make check` to ensure nothing broke
- Push to your remote: `git push origin main` (or open a PR)
