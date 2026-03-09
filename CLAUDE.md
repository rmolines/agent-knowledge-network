# CLAUDE.md — Instructions for Claude Code

## Project overview

Agent Knowledge Network é uma rede social open-source onde pares humano+agente Claude
compartilham conhecimento em formato markdown skill-like. Pares têm handles (@username),
publicam posts com progressive disclosure (TL;DR → Contexto → Detalhe), e o agente
busca automaticamente via skill `busca`. O gap board expõe demanda não atendida para
guiar contribuição. Alternativa confiável ao web search para conhecimento da comunidade AI.

## Critical rules — NEVER do without explicit approval

- Never commit tokens, keys, or passwords — use environment variables or secret managers
- Never force-push to main — always use PRs with CI passing
- Never skip pre-commit hooks (--no-verify) — fix the underlying issue
- Never delete data without a dry-run step first
- Never expose Qdrant port 6333 publicly — internal network only
- Never hard-delete posts — use soft-delete + versioning

## Sprint atual

`.claude/sprint.md` — M1 features, status e ordem de execução. **Leia sempre antes de iniciar qualquer feature.**

## Feature workflow — complete cycle

Use the skills below for any non-trivial feature (>2-3 files or with architectural decisions):

1. `/start-milestone` — decompose milestone from roadmap.md into scoped features → generates `sprint.md`
2. `/start-feature` — intake + research (Phase A) → `/clear` → planning (Phase B) → `/clear` → worktree + execution (Phase C)
3. Build and iterate in the worktree
4. `/validate` — direction check: verify implementation still solves the original problem
5. `/ship-feature` — simplify automático + commit + rebase + PR + CI + smoke test
6. `/close-feature` — documentation (HANDOVER, MEMORY, LEARNINGS, CLAUDE.md) + cleanup

**Orientation (any time):** `/project-compass` — "where are we?", "what's left?", "next feature?"

## Hot files — always read before editing

- `CLAUDE.md`
- `api/security/sanitizer.py` — filtro anti-injection; qualquer mudança tem implicação de segurança
- `api/security/wrappers.py` — XML wrapper para conteúdo recuperado; crítico para prompt injection
- `skills/busca.md` — skill distribuída para usuários; mudanças afetam todos os agentes instalados
- `skills/post.md` — skill de publicação; formato do frontmatter afeta o indexer
- `api/services/qdrant.py` — hybrid search; dimensão do embedding hardcoded aqui (256d)
- `api/workers/indexer.py` — pipeline de ingest; quarentena e sanitização acontecem aqui
- `migrations/` — Alembic; coordenar mudanças de schema
- `.github/workflows/ci.yml`
- `.github/workflows/deploy.yml`

## Known pitfalls

| Component | Pitfall | Fix |
|---|---|---|
| Qdrant | Volume persistente obrigatório no Railway (path `/qdrant/storage`) | Configurar Railway volume antes de deploy |
| Qdrant | Porta 6333 nunca exposta publicamente | Network privada no Railway |
| Embedding | Dimensão hardcoded 256d — trocar model invalida TODOS os vetores | Só trocar model em migração planejada com re-embedding total |
| GitHub API | Cota 5k req/hora por token | Usar token OAuth do usuário para indexação do próprio repo |
| OAuth CSRF | State parameter deve ser one-time-use (deletar do Redis após callback) | Ver `api/routers/auth.py` |
| Posts maliciosos | PoisonedRAG: 5 docs crafted contaminam base | Quarentena 24h + sanitizer obrigatório antes de indexar |
| ARQ workers | Rodam em processo separado; não sourcear `~/.zshrc` | `set -euo pipefail` em scripts |
| Posts | Hard-delete quebra queries temporais | Sempre soft-delete + versioning |
| template-sync.yml | Runs on template repo itself → no-op | Guard: `!github.event.repository.is_template` |
| bootstrap.yml | Only fires on first push (run_number == 1) | Don't re-run manually |
| Poetry | Poetry 1.8+ requer `package-mode = false` em `[tool.poetry]` quando o projeto usa apenas `[project]` (PEP 621) — falha silenciosa no build | Adicionar `package-mode = false` ao `[tool.poetry]` em `pyproject.toml` |
| Alembic | `%(DATABASE_URL)s` em `alembic.ini` falha — ConfigParser normaliza option names para lowercase, quebrando interpolação | Usar placeholder fixo em `alembic.ini` e ler a URL via `os.environ` / `settings.database_url` em `env.py` |
| fastapi-users | `fastapi-users 13.0.0` exige `python-multipart==0.0.9` — conflita com pins explícitos de versões mais recentes | Não pinnar `python-multipart` diretamente; deixar `fastapi-users` resolver a dependência |
| Python 3.12 | `datetime.utcnow()` deprecated no Python 3.12+ — vira `DeprecationWarning` que CI trata como erro | Usar `datetime.now(tz=timezone.utc)` em todo o codebase |
| CORS + cookies | `allow_origins=["*"]` é incompatível com `allow_credentials=True` — browsers silenciosamente descartam cookies em requests cross-origin; OAuth com cookies parece funcionar em dev (same-origin) mas falha em produção | Usar origem explícita (`FRONTEND_URL`) em vez de wildcard quando credentials estão habilitados |
| `api.db` | `_engine` criado no import — testes que importam `api.deps` falham com `ModuleNotFoundError: asyncpg` sem driver instalado | Mockar `api.db` via `sys.modules` em `tests/conftest.py` antes de qualquer import |
| `qdrant_client` | Unit tests que importam módulos com `from api.services.qdrant import ...` falham com `ModuleNotFoundError: No module named 'qdrant_client'` mesmo sem usar Qdrant diretamente | Mockar `qdrant_client` e `qdrant_client.models` via `sys.modules` em `tests/conftest.py` — mesmo padrão do `api.db` |
| FastAPI session | Chamar `db.commit()` dentro de um helper que recebe a sessão injetada por `get_db` finaliza a transação prematuramente e impede rollback em erros subsequentes — `get_db`'s context manager é o dono da transação | Nunca chamar `db.commit()` em helpers; deixar o contexto de `get_db` (ou o router) fazer o commit ao final |
| SQLAlchemy upsert | Usar atributo ORM (`GapSignal.session_count + 1`) no `set_` de `on_conflict_do_update` é ambíguo e pode falhar em runtime | Usar referência de coluna de tabela explícita: `GapSignal.__table__.c.session_count + 1` |
| SQLModel AsyncSession | `db.exec()` (padrão usado em `deps.py` e nos routers) só existe em `sqlmodel.ext.asyncio.session.AsyncSession` — plain `sqlalchemy.ext.asyncio.AsyncSession` não tem esse método; sessions criadas via `async_sessionmaker` do SQLAlchemy puro não são compatíveis | Garantir que `async_sessionmaker` em `api/db.py` usa `class_=sqlmodel.ext.asyncio.session.AsyncSession` |
| `api.main` em testes | Importar `api.main` (ex: via `TestClient(app)`) puxa transitivamente todos os routers, incluindo `auth.py` → `redis.asyncio`, `arq`, e `qdrant_client` — testes falham com `ModuleNotFoundError` mesmo sem usar essas dependências | Mockar `redis`, `redis.asyncio`, `arq`, e `qdrant_client` (e submodules) via `sys.modules` em `conftest.py` antes de importar `api.main` — ou importar apenas os módulos necessários em vez do app completo |
| ARQ pool mock | O lifespan do FastAPI chama `await pool.close()` no teardown — se o mock do `create_pool` retornar um `MagicMock()` comum, o `await` falha com `TypeError: object MagicMock can't be used in 'await' expression` | O mock de `create_pool` deve retornar um objeto com `close=AsyncMock()`: `mock_pool = MagicMock(); mock_pool.close = AsyncMock()` |
| `get_db` em testes de endpoint | Endpoints que dependem diretamente de `get_db` (ex: `GET /search`) retornam 422 em testes unitários se `get_db` não for overridden explicitamente — o mock global de `api.db` em `conftest.py` não registra o callable como async generator válido para FastAPI | Adicionar `from api.db import get_db` + `app.dependency_overrides[get_db] = lambda: MagicMock()` no fixture do client; apenas endpoints que indiretamente usam `get_db` (via deps overridden, ex: `get_current_handle`) não precisam do override |

## Worktree convention

- Path: `.claude/worktrees/<feature-name>`
- Branch: `feat/<feature-name>` (kebab-case)
- Always rebase before starting: `git fetch origin && git rebase origin/main`

## Daily commands

```bash
make help            # List all available commands
make check           # Run lint + typecheck + tests
make lint            # Lint Markdown + Python (ruff)
make test            # Run unit tests
make test-integration # Run integration tests (requires docker-compose up)
make dev             # Start local stack (docker-compose up)
make sync-skills     # Pull latest skills from upstream template
make clean           # Remove generated files
```

## Smoke test

```bash
curl http://localhost:8000/search?q=test
# Expected: {"results": [], "total": 0}

curl http://localhost:8000/gaps
# Expected: {"gaps": []}
```

## Secrets

```bash
OPENAI_API_KEY=       # embeddings (text-embedding-3-small)
GITHUB_CLIENT_ID=     # OAuth app
GITHUB_CLIENT_SECRET= # OAuth app
DATABASE_URL=         # PostgreSQL (Railway provê automaticamente)
REDIS_URL=            # Redis (Railway provê automaticamente)
QDRANT_URL=           # URL interna do Railway
SECRET_KEY=           # JWT sessions — gerar com: python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Documentados em `.env.example`. Nunca commitar `.env`.
