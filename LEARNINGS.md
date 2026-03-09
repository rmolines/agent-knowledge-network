# LEARNINGS.md — Technical learnings

Gotchas, limitations, and non-obvious behaviors discovered while working on this project.

---

## GitHub Actions

### `bootstrap.yml`: `run_number == 1` guard

`github.run_number` starts at 1 for the first run of any workflow in a repo. Using this as a
guard ensures branch protection is only applied once. **Do not re-run this workflow manually** —
it will attempt to apply protection again (which is usually fine but clutters logs).

### `template-sync.yml`: must guard with `!is_template`

Without the `!github.event.repository.is_template` guard, the sync workflow would run on the
template repo itself and open PRs against its own `main`. The guard makes it a no-op on the
template and active only on forks.

### Action SHA pinning

Always pin to full commit SHA, not tag:
```yaml
# Good
uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
# Bad (tag can be hijacked)
uses: actions/checkout@v4
```

---

## Claude Code hooks (CVE-2025-59536)

Hooks in `.claude/settings.json` execute shell commands **without user confirmation**.
This was documented in CVE-2025-59536. Mitigation: keep hook logic in external scripts
(`.claude/hooks/`) so they're visible, auditable, and can be reviewed in PRs.

---

## markdownlint

- Use `npx --yes markdownlint-cli2` to avoid requiring global install
- `MD013` (line length) needs `tables: false` and `code_blocks: false` to avoid false positives
- `MD024` (duplicate headings) should be disabled for `HANDOVER.md` — entries often have similar structure
- `MD041` (first heading must be h1) breaks templates with frontmatter or `<!-- TODO -->` comments

---

## 2026-03-08 — alembic.ini: ConfigParser silently lowercases option keys

`sqlalchemy.url = %(DATABASE_URL)s` fails at runtime with `InterpolationMissingOptionError` because
ConfigParser normalises all option keys to lowercase before interpolation — `%(DATABASE_URL)s` becomes
`%(database_url)s`, which doesn't exist. Fix: use a literal placeholder in `alembic.ini` and read the
real URL from the environment inside `migrations/env.py` using `os.environ` or the app's settings object.

## 2026-03-08 — Poetry 1.8+ in package-mode with PEP 621 pyproject.toml

Poetry 1.8.0 defaults to package mode and expects `[tool.poetry]` with `name`, `version`, and `authors`.
Projects that use only `[project]` (PEP 621 / uv style) will fail at `poetry install`. Fix: add
`[tool.poetry]` with `package-mode = false` — this disables packaging behaviour and lets Poetry act
purely as a dependency manager without requiring the full package metadata.

## 2026-03-08 — fastapi-users pins python-multipart to an exact version

`fastapi-users 13.x` depends on `python-multipart==0.0.9` (exact). If `pyproject.toml` also pins
`python-multipart` (e.g. `^0.0.20`), Poetry raises a dependency conflict. Fix: remove the explicit
`python-multipart` entry from `pyproject.toml` and let `fastapi-users` own the constraint. The
pattern generalises: when a framework uses an exact pin on a transitive dep, don't re-declare it.

## 2026-03-08 — datetime.utcnow() returns naive datetimes; dangerous with expires_at

`datetime.utcnow()` is deprecated since Python 3.12 and returns a naive datetime (no tzinfo).
Comparing it against a timezone-aware `expires_at` stored in the DB raises a TypeError at runtime.
Fix: `datetime.now(tz=timezone.utc)` everywhere — returns an aware datetime and is future-proof.

## 2026-03-08 — Canonical config must have one source of truth; migrations/env.py is a common offender

`migrations/env.py` often reads `os.environ["DATABASE_URL"]` directly, bypassing the app's
`api/config.py` (which handles `.env` loading via python-dotenv). This means migrations work in
production (where the var is injected) but silently break in local dev (where only `.env` exists).
Fix: import `settings` from `api/config.py` in `env.py` and read `settings.database_url`.

## 2026-03-08 — CORS: allow_origins=["*"] silently blocks HttpOnly cookies cross-origin

`CORSMiddleware(allow_origins=["*"])` causes browsers to strip `Set-Cookie` headers on
cross-origin responses. There is no browser error — cookies simply never arrive. Fix requires two
changes together: replace `"*"` with an explicit list of allowed origins AND set
`allow_credentials=True`. Either change alone is insufficient.

## 2026-03-08 — Deleting a remote branch before gh pr merge closes the PR

`gh pr merge` looks up the PR by its head branch. If the remote branch is deleted first (e.g.
via `git push origin --delete feat/...`), GitHub marks the PR as closed (not merged). Always run
`gh pr merge` before deleting the remote branch, or let the merge itself handle branch deletion
via the `--delete-branch` flag.

## 2026-03-08 — Two separate httpx.AsyncClient() contexts waste a TLS handshake per call

Opening a new `async with httpx.AsyncClient() as client:` for each sequential GitHub API call
creates a new TCP+TLS connection every time. Merge sequential calls into a single client context
so the connection is reused. This matters most when chaining two or three calls in the same
request handler (e.g. exchange code → fetch user info).

## 2026-03-08 — db.refresh(session) after commit is a no-op when expire_on_commit=False

With `expire_on_commit=False` (common in async SQLAlchemy setups), SQLModel/SQLAlchemy does not
expire attributes after `session.commit()`. A subsequent `await session.refresh(obj)` issues a
SELECT but the result is identical to what's already in memory — it's dead code. Only call
`refresh` when you genuinely need server-side defaults (e.g. `created_at`, auto-incremented id)
and only if `expire_on_commit` is True (the default).

## 2026-03-08 — SQLAlchemy async engine is created at module import time, breaking unit tests

`api/db.py` typically creates the async engine at module level (e.g. `engine = create_async_engine(...)`).
Any module that imports from `api.db` — even indirectly — will trigger this at import time, which requires
`asyncpg` to be installed. In unit tests that mock the DB, add `sys.modules["api.db"] = MagicMock()` before
importing the module under test, or use `importlib.import_module` after patching, to avoid the eager engine creation.

## 2026-03-08 — Redis GETDEL for atomic one-time-use token validation (available since Redis 6.2)

For OAuth CSRF state tokens, a GET followed by DEL has a race window where two concurrent
requests can both read the value before either deletes it. `GETDEL` (Redis 6.2+) retrieves and
deletes the key atomically, making one-time-use validation safe without a Lua script or WATCH/MULTI.
Railway's managed Redis runs 7.x, so this is safe to use.

## 2026-03-09 — pg_insert on_conflict_do_update: use `__table__.c` for server-side column references

When using SQLAlchemy's `insert().on_conflict_do_update(set_=...)` with `postgresql.insert` (pg_insert),
column references inside `set_` must be explicit table-level references, not model attributes:

```python
# Wrong — resolves to a Python-side value, not a server-side reference
set_={"session_count": GapSignal.session_count + 1}

# Correct — server-side column expression evaluated by Postgres
set_={"session_count": GapSignal.__table__.c.session_count + 1}
```

Using the model attribute produces a client-evaluated expression (often `None + 1`) rather than the
incrementing SQL expression `session_count = session_count + 1`. This silently resets the column
instead of incrementing it.

## 2026-03-09 — Never call db.commit() inside a helper that receives an injected session

Calling `session.commit()` inside a helper that receives a FastAPI-injected `AsyncSession` (via
`get_db` dependency) prematurely finalises the transaction. The `get_db` context manager owns the
session lifecycle: it commits on clean exit and rolls back on exception. An explicit commit inside
the helper breaks this contract — subsequent operations in the same request see a new implicit
transaction, and any exception after the premature commit cannot be rolled back.

Rule: only call `commit()` at the boundary that owns the session (the dependency or a top-level
service that creates its own session). Helpers that receive an injected session must only call
`session.add()`, `session.exec()`, `session.flush()` (if needed for IDs), or `session.rollback()`.

## 2026-03-09 — SQLModel AsyncSession vs plain SQLAlchemy AsyncSession: exec() only on SQLModel

`SQLModel`'s `AsyncSession` (from `sqlmodel.ext.asyncio.session`) adds the `.exec()` method that
accepts `SQLModel` select statements and returns typed results. Plain SQLAlchemy's `AsyncSession`
(from `sqlalchemy.ext.asyncio`) does not have `.exec()` — calling it raises `AttributeError`.

If `api/db.py` uses `sqlalchemy.ext.asyncio.async_sessionmaker`, the sessions it creates are plain
SQLAlchemy sessions. To use `.exec()` in route handlers or services, either:

1. Wrap the session with SQLModel's `AsyncSession` at the dependency boundary, or
2. Switch the sessionmaker to use `sqlmodel.ext.asyncio.session.AsyncSession` as the `class_` argument.

Mixing the two silently works as long as only `.execute()` is used; the breakage only appears when
`.exec()` is called with a SQLModel statement.

## 2026-03-09 — Action SHA pinning: one wrong character causes a silent CI failure

SHA pins are checked byte-for-byte by GitHub. A single-character typo (e.g. `...90a2f` instead
of `...90a2b`) causes the workflow to fail with a cryptic "Can't find action" or checkout error,
not a helpful "SHA mismatch" message. The diff between the wrong and correct SHA is invisible
at a glance. When a new SHA is introduced (or copied from another workflow), verify it against
`https://github.com/<owner>/<repo>/commit/<sha>` before committing.

## 2026-03-09 — Importing api.main in tests pulls in redis, arq, and qdrant_client transitively

`api/main.py` wires the FastAPI lifespan which imports `arq`, and routers that import `redis.asyncio`
and `qdrant_client`. Any test file that does `from api.main import app` will trigger all three
imports at collection time, even if the test itself never touches those services.

Tests that previously only imported individual routers or services were immune because those modules
don't import `api.main`. Once a test needs the full `app` (e.g. for `TestClient` or `AsyncClient`),
add the following mocks to `tests/conftest.py` **before** any `api.*` import:

```python
sys.modules.setdefault("redis.asyncio", MagicMock())
sys.modules.setdefault("arq", MagicMock())
sys.modules.setdefault("qdrant_client", MagicMock())
sys.modules.setdefault("qdrant_client.models", MagicMock())
```

## 2026-03-09 — arq mock for lifespan teardown requires AsyncMock with AsyncMock close()

When mocking `arq` in tests, the lifespan calls `await arq.create_pool(...)` and then
`await pool.close()` on shutdown. Both must be async-awaitable:

```python
mock_pool = MagicMock()
mock_pool.close = AsyncMock()
arq_mock = MagicMock()
arq_mock.create_pool = AsyncMock(return_value=mock_pool)
sys.modules["arq"] = arq_mock
```

If `create_pool` is a plain `MagicMock`, `await create_pool(...)` raises `TypeError: object
MagicMock can't be used in 'await' expression`. If `close` is a plain `MagicMock`, the teardown
coroutine hangs. Both must be `AsyncMock`.

## infra-deploy — 2026-03-08

### ARQ worker deve ser um serviço separado no docker-compose e no Railway

O worker ARQ não deve rodar no mesmo processo que o servidor web. Em docker-compose,
adicionar um segundo serviço usando a mesma imagem mas com command override:

```yaml
worker:
  build: .
  command: arq api.workers.arq_worker.WorkerSettings
  # mesmas env vars e depends_on que o serviço api
```

No Railway, criar um segundo serviço apontando para o mesmo repo com
`startCommand = "arq api.workers.arq_worker.WorkerSettings"` configurado via UI.

### Migrations no startup do api eliminam etapa manual em `make dev`

Adicionar `alembic upgrade head &&` antes do uvicorn no `command` do serviço `api`
em docker-compose garante que o schema está sempre atualizado após `docker-compose up`.
O worker não deve rodar migrations — apenas o serviço api é responsável por isso.

### Qdrant: nunca publicar porta 6333 no host em docker-compose

O mapeamento `ports: ["6333:6333"]` expõe o Qdrant na interface de rede do host.
Para o stack local, a comunicação interna via Docker network é suficiente.
Remover o bloco `ports` do serviço qdrant — outros contêineres acessam via
`http://qdrant:6333` sem publicação externa.

---

## 2026-03-09 — get_db must be explicitly overridden per-endpoint in unit tests

Mocking `api.db` via `sys.modules` prevents the engine from being created at import time, but it does not register a valid async-generator override for FastAPI's `get_db` dependency. Endpoints that declare `db: AsyncSession = Depends(get_db)` directly will return 422 or fail with dependency injection errors in tests even when `api.db` is mocked globally.

Fix: in the test client fixture, add `app.dependency_overrides[get_db] = lambda: MagicMock()` explicitly. Endpoints that only use `get_db` indirectly (e.g. via a custom dependency that is itself overridden) do not need this.

## 2026-03-09 — Postgres FTS: language config must match between indexing and querying

`to_tsvector('simple', text)` and `websearch_to_tsquery('simple', query)` must use the same language configuration. Using `'english'` at query time against a `'simple'` tsvector (or vice versa) silently returns zero results — Postgres does not raise an error, it just finds no matches because stemming is applied inconsistently. Always use the same language string in both the index expression and the query function.

## 2026-03-09 — Mock qdrant_client em tests unitários

`api/workers/indexer.py` importa `api/services/qdrant.py` no nível do módulo, que por sua vez importa `qdrant_client`.
Mesmo que o teste só exercite `parse_post_markdown` (função pura, sem Qdrant), o import falha com `ModuleNotFoundError: No module named 'qdrant_client'`.

Fix: adicionar ao `tests/conftest.py`:

```python
sys.modules.setdefault("qdrant_client", MagicMock())
sys.modules.setdefault("qdrant_client.models", MagicMock())
```

Mesmo padrão já usado para `api.db` / `asyncpg`.
