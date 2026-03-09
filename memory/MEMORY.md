# MEMORY.md — Agent Knowledge Network

<!-- Atualizado: 2026-03-08 -->

## O que é este projeto

Rede social open-source onde pares humano+agente Claude compartilham conhecimento em markdown.
Agentes buscam via skill `busca` sem depender de web search. Pares têm handles (`@username`),
publicam posts com progressive disclosure (TL;DR → Contexto → Detalhe).

## M1 — Status atual (7/14 features — 50%)

```text
✅  auth-session-model     PR #2   Handle + Session + Alembic
✅  auth-oauth-flow        PR #4   GitHub OAuth + HttpOnly cookie JWT
✅  auth-middleware        PR #5   get_current_handle + get_current_github_token
✅  content-security       PR #6   sanitizer + XML wrapper
✅  gap-board              PR #7   gap signals + GET /gaps (k≥3)
✅  post-ingest-endpoint   PR #9   POST /posts + ARQ queue
✅  infra-deploy           PR TBD  docker-compose worker + smoke-test + railway.toml

🔲  search-service         hybrid search (rota existe, precisa de wire)
🔲  skills-e2e             busca.md + post.md end-to-end
🔲  ingest-guardrails      quarantine 48h/24h + rate limit
🔲  repo-analyzer-service  lista repos com .claude/
🔲  analyze-on-connect     analyzer no callback OAuth
🔲  seeding-crawler        bulk CLAUDE.md/skills → post format
🔲  seeding-run            20–30 posts indexados e buscáveis
```

**Próxima feature:** `search-service` — Postgres FTS (PR #11 fechado, reescrever com tsvector).

## Arquitetura

- **Stack:** FastAPI + SQLModel + Alembic + ARQ + Redis + Postgres FTS (tsvector/BM25)
- **Search:** Postgres `pg_websearch_to_tsquery` — sem Qdrant, sem OpenAI embeddings. Queries de agentes são técnicas e precisas; controle do vocabulário via skills `post.md` + `busca.md` torna BM25 suficiente.
- **Auth:** GitHub OAuth → JWT HS256 → HttpOnly cookie (SameSite=Lax)
- **Workers:** ARQ (Redis-backed) — processo separado, não BackgroundTasks
- **Deploy:** Railway — API service + Worker service separados (mesmo repo, start commands diferentes)

## Arquivos críticos

- `CLAUDE.md` — leia sempre antes de editar qualquer coisa
- `api/security/sanitizer.py` + `wrappers.py` — anti-injection; qualquer mudança tem impacto de segurança
- `api/services/search.py` — Postgres FTS service (a criar em `search-service`)
- `api/workers/indexer.py` — pipeline de ingest completo
- `api/workers/arq_worker.py` — `WorkerSettings` + jobs registrados
- `migrations/` — Alembic; coordenar mudanças de schema
- `skills/busca.md` + `skills/post.md` — distribuídas para usuários finais

## Pitfalls recorrentes (resumo — detalhes em LEARNINGS.md)

- `db.commit()` em helpers: nunca — lifecycle pertence ao `get_db` dependency
- `datetime.utcnow()`: deprecated — usar `datetime.now(tz=timezone.utc)`
- Mocks em unit tests: `api.db`, `redis.asyncio`, `arq` devem ser mockados via `sys.modules` em `conftest.py`
- ARQ pool mock: `create_pool` e `pool.close` devem ser `AsyncMock`, não `MagicMock`
- `get_db` em testes de endpoint: endpoints que dependem diretamente de `get_db` precisam de `app.dependency_overrides[get_db] = lambda: MagicMock()`
- CORS + credentials: `allow_origins=["*"]` é incompatível com `allow_credentials=True`

## Convenções

- Branch: `feat/<kebab-case>`
- Worktree: `.claude/worktrees/<feature-name>`
- Commits: `type(scope): description` + `Co-Authored-By`
- Nunca commit direto em main — sempre PR com CI passando
