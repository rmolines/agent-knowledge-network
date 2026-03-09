# HANDOVER.md — Session history

Newest entries at the top.

---

## content-security — 2026-03-09

**PR:** #6 — test(security): unit tests for wrappers and indexer
**Arquivos tocados:** `tests/unit/test_wrappers.py`, `tests/unit/test_indexer.py`, `tests/conftest.py`

**O que foi feito:**
Os módulos de segurança (`api/security/sanitizer.py`, `api/security/wrappers.py`, `api/workers/indexer.py`)
já estavam implementados. Esta feature adicionou os testes unitários que estavam faltando:

- `tests/unit/test_wrappers.py` — 15 testes cobrindo `wrap_tl_dr`, `wrap_with_context`, `wrap_full`,
  `BUSCA_SYSTEM_PROMPT_FRAGMENT`, campos `None` e formato XML
- `tests/unit/test_indexer.py` — 11 testes cobrindo `parse_post_markdown`: post válido, post mínimo,
  frontmatter ausente, TL;DR ausente, fallback de data
- `tests/conftest.py` — adicionado mock de `qdrant_client` para que os testes unitários rodem sem
  o pacote instalado

**Decisões:**
- `qdrant_client` precisa ser mockado no `conftest.py` (mesmo padrão de `api.db`) porque `parse_post_markdown`
  é uma função pura, mas a cadeia de imports no nível de módulo puxa `qdrant_client` antes de qualquer
  execução de código
- Nenhum bug encontrado no pipeline de segurança: a lógica de quarentena está correta — posts em
  quarentena são armazenados com `quarantined=True` e `hybrid_search` os filtra por padrão
  (`exclude_quarantined=True`)

**Armadilhas encontradas:**
- A chain de imports do `indexer.py` puxa `qdrant_client` indiretamente mesmo ao testar funções puras;
  é necessário mockar o pacote via `sys.modules` no `conftest.py` antes de qualquer import dos módulos
  de produção — mesmo padrão do `api.db` descoberto na feature `auth-middleware`

**Próximos passos:**
- Adicionar testes de integração para o pipeline completo de ingest (quarentena → sanitização → indexação)
  quando o ambiente Docker estiver disponível no CI
- Considerar testes para `api/security/sanitizer.py` (injeção de prompt, PoisonedRAG) se o escopo de
  cobertura for ampliado

---

## auth-oauth-flow — 2026-03-08

**PR:** #4 — feat(auth): GitHub OAuth flow with HttpOnly session cookie
**Merged commit:** 0d9f805 (squash of bef5620, 630bcbe)
**Arquivos principais:** `api/routers/auth.py`, `api/services/redis.py`, `api/services/jwt.py`, `api/db.py`, `api/main.py`, `api/config.py`

**O que foi feito:**
Implementou o fluxo OAuth completo com GitHub. `/auth/login` armazena um state CSRF de uso único no Redis;
`/auth/callback` valida o state (GETDEL atômico), troca o code pelo token GitHub, faz upsert de `Handle` + `Session`
no banco e emite um JWT como cookie HttpOnly. `/auth/logout` limpa o cookie.

Novos módulos criados: `api/db.py` (async session factory), `api/services/redis.py`, `api/services/jwt.py`.

Correções adicionais: CORS `allow_origins=["*"]` substituído por `settings.allowed_origins` + `allow_credentials=True`;
dois `httpx.AsyncClient()` consolidados em um (keep-alive); params OAuth via `httpx.URL.copy_merge_params`;
`db.refresh(session)` redundante removido (`expire_on_commit=False` torna-o no-op).

**Decisões tomadas:**
- JWT via `python-jose[cryptography]` (HS256, TTL 30 dias)
- Cookie: `HttpOnly` + `Secure` + `SameSite=Lax`
- Redis GETDEL para validação atômica de state one-time-use
- NullPool para DB (compatível com Railway/PgBouncer)
- Headers GitHub reutilizados de `api/services/github.py`

**Armadilhas encontradas:**
- `allow_origins=["*"]` quebra cookies cross-origin silenciosamente — requer `allowed_origins` explícito + `allow_credentials=True`
- Deletar branch remota antes de `gh pr merge` fecha o PR; foi necessário re-push e recriar o PR
- Branch protection exige CI passando antes do merge; auto-merge estava desativado no repo

**Próximos passos:**
- Implementar middleware de validação de sessão (ler cookie, decodificar JWT, injetar usuário atual)
- Adicionar checagem de expiração em `/auth/callback` contra `Session.expires_at`
- Rate limiting em `/auth/login` e `/auth/callback`

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

---

## auth-middleware — 2026-03-08

**PR:** #5 — feat(auth): authentication middleware — get_current_handle dependency
**Merged commit:** 65daf0f
**Key files:** `api/deps.py`, `api/routers/posts.py`, `tests/conftest.py`, `tests/unit/test_deps.py`

**O que foi feito:**
Criado `api/deps.py` com a dependency `get_current_handle` — lê o cookie HttpOnly `session`,
decodifica o JWT HS256 (claims `sub=handle_id`, `sid=session_id`), valida a Session no DB
(existência + expiração) e retorna o `Handle` autenticado. Retorna 401 para cookie ausente,
JWT inválido, claims faltando, session não encontrada, session expirada ou handle não encontrado.
Aplicado em `POST /posts` (resolve TODO existente). Adicionados 7 testes unitários cobrindo
todos os caminhos de erro e o happy path.

**Decisões tomadas:**
- `import datetime` dentro do corpo da função para evitar problemas de import circular
- Mock de `api.db` via `sys.modules` no conftest — engine é criado no import, não sob demanda

**Armadilhas encontradas:**
- `api.db` cria `_engine` no import; testes falham sem asyncpg instalado. Fix: mock via `sys.modules`
  antes de qualquer import de `api.deps` no conftest.
- Linhas longas em HANDOVER.md quebraram o CI (MD013 — máx 200 chars). Sempre quebrar linhas
  longas em arquivos `.md`.

**Próximos passos:**
- Aplicar `get_current_handle` em rotas futuras que exijam autenticação
- Considerar variante `get_optional_handle` para rotas que funcionam com ou sem auth
