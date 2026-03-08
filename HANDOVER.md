# HANDOVER.md — Session history

Newest entries at the top.

---

## auth-session-model — 2026-03-08

**PR:** #2 — feat(auth): Handle e Session SQLModel models com Alembic migration
**Arquivos principais:** `api/models.py`, `migrations/env.py`, `migrations/versions/0001_create_handle_and_session_tables.py`, `alembic.ini`, `pyproject.toml`

**O que foi feito:**
Criou a camada de persistência para o fluxo OAuth. Adicionou `api/models.py` com dois modelos SQLModel (`Handle` e `Session`).
Inicializou `migrations/` com Alembic async-compatible e criou a migration `0001` que gera as tabelas `handles` e `sessions`.

**Decisões tomadas:**
- SQLModel sobre SQLAlchemy puro — compatibilidade nativa com FastAPI e Pydantic v2
- Alembic async via `AsyncEngine` + `run_sync` em `env.py` — necessário para stack async do projeto
- `datetime.now(tz=timezone.utc)` em vez de `datetime.utcnow()` — deprecated no Python 3.12+
- `DateTime(timezone=True)` nas colunas de timestamp — garante armazenamento correto com fuso
- `settings.database_url` em vez de `os.environ` direto — centraliza configuração e evita KeyError em runtime

**Armadilhas encontradas:**
- `pyproject.toml` sem seção `[tool.poetry]` quebrava Poetry 1.8.0 — adicionado o bloco obrigatório
- `alembic.ini` usava interpolação `%(DATABASE_URL)s` que `configparser` não resolve — substituído por leitura via `settings` no `env.py`
- `fastapi-users 13.0.0` conflita com `python-multipart ^0.0.20` — fixado para versão compatível
- `connectable.dispose()` redundante no `env.py` gerava warning — removido

**Próximos passos:**
- `auth-oauth-flow` pode agora usar `Handle` e `Session` importando de `api.models`
- Lembrar de rodar `alembic upgrade head` no deploy

---

## 2026-02-27 — Bootstrap via /start-project

**What was done:**

- Executed Fase 3 (Bootstrap) of `/start-project` for the `claude-kickstart` template repository
- Created GitHub repo `rmolines/claude-kickstart` (public)
- Wrote all project files: CLAUDE.md, Makefile, CI workflows, skills, hooks, rules, memory files

**Architectural decisions:**

- GitHub Template Repository format (not CLI) — zero friction
- Hooks in `.claude/hooks/` external scripts (not inline `settings.json`) — auditable, CVE-2025-59536 compliant
- Static CI only (lint + JSON + structure) — no runtime to test
- `bootstrap.yml` with `run_number == 1` guard — auto-applies branch protection on first fork push

**Files created:**

- `CLAUDE.md`, `README.md`, `LEARNINGS.md`, `HANDOVER.md`, `Makefile`
- `.claude/settings.json`, `.claude/settings.md`
- `.claude/hooks/pre-tool-use.sh`
- `.claude/scripts/validate-structure.sh`
- `.claude/rules/git-workflow.md`, `coding-style.md`, `security.md`
- `.claude/commands/start-feature.md`, `ship-feature.md`, `close-feature.md`, `handover.md`, `sync-skills.md`
- `.claude/commands/SYNC_VERSION`
- `.github/workflows/ci.yml`, `bootstrap.yml`, `template-sync.yml`
- `.github/dependabot.yml`, `CODEOWNERS`, `SECURITY.md`
- `memory/MEMORY.md`

**Open threads:**

- Demo GIF/video for README (identified as high-risk if not done before launch)
- CONTRIBUTING.md for community contributors
- Mark repo as Template in GitHub Settings (done via API in bootstrap sequence)
