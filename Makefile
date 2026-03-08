.PHONY: help check lint validate sync-skills clean setup

# Default target
help: ## Show this help
	@echo "claude-kickstart — available targets:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Quick start: make check"

check: lint validate ## Run all checks (lint + validate)

lint: ## Lint all Markdown files
	@echo "→ Linting Markdown..."
	@npx --yes markdownlint-cli2 "**/*.md" "!.claude/feature-plans/**" --config .markdownlint.yaml \
		&& echo "✅ Markdown lint passed" \
		|| (echo "❌ Markdown lint failed" && exit 1)

validate: ## Validate JSON files and project structure
	@echo "→ Validating JSON..."
	@find .claude -name "*.json" | while read -r f; do \
		python3 -m json.tool "$$f" > /dev/null \
			&& echo "  ✅ $$f" \
			|| (echo "  ❌ $$f" && exit 1); \
	done
	@echo "→ Validating structure..."
	@bash .claude/scripts/validate-structure.sh

sync-skills: ## Pull latest skills from upstream template
	@echo "→ Syncing skills from upstream..."
	@git remote add upstream https://github.com/rmolines/claude-kickstart.git 2>/dev/null || true
	@git fetch upstream main --quiet
	@CURRENT=$$(cat .claude/commands/SYNC_VERSION 2>/dev/null || echo "none"); \
	UPSTREAM=$$(git rev-parse upstream/main); \
	if [ "$$CURRENT" = "$$UPSTREAM" ]; then \
		echo "✅ Already up to date ($$UPSTREAM)"; \
	else \
		git checkout upstream/main -- .claude/commands/; \
		echo "$$UPSTREAM" > .claude/commands/SYNC_VERSION; \
		echo "✅ Updated to $$UPSTREAM"; \
		echo "   Review changes with: git diff HEAD .claude/commands/"; \
		echo "   Commit when ready:   git add .claude/commands/ && git commit -m 'chore: sync skills'"; \
	fi

clean: ## Remove generated files (worktrees, cache)
	@echo "→ Cleaning..."
	@if [ -d ".claude/worktrees" ]; then \
		echo "  Removing .claude/worktrees/..."; \
		rm -rf .claude/worktrees; \
	fi
	@if [ -d ".claude/cache" ]; then \
		echo "  Removing .claude/cache/..."; \
		rm -rf .claude/cache; \
	fi
	@echo "✅ Clean done"

setup: ## One-time setup: install local dev tools (markdownlint)
	@echo "→ Setting up dev tools..."
	@command -v node > /dev/null || (echo "❌ Node.js required for markdownlint — install from https://nodejs.org" && exit 1)
	@npx --yes markdownlint-cli2 --version > /dev/null && echo "✅ markdownlint-cli2 available via npx"
	@command -v python3 > /dev/null && echo "✅ python3 available" || echo "⚠️  python3 not found — JSON validation will fail"
	@echo "✅ Setup complete. Run 'make check' to validate."
