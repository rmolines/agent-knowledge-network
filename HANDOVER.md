# HANDOVER.md — Session history

Newest entries at the top.

---

## search-service — 2026-03-09

**PR:** #12 — feat(search-service): Postgres FTS replacing Qdrant + OpenAI embeddings
**Status:** merged

### O que foi feito

- `api/models.py` — adicionado modelo `Post` com coluna `search_vector: TSVECTOR` (nullable, computada pelo Postgres no insert)
- `migrations/versions/0003_create_posts_table.py` — migration Alembic que cria a tabela `posts` com índice GIN em `search_vector` e unique constraint `uq_posts_repo_file` para suportar upsert no re-index
- `api/routers/search.py` — reescrito `GET /search`: usa `websearch_to_tsquery` + `ts_rank`; resultados são XML-wrapped via `api/security/wrappers.py`
- `api/workers/indexer.py` — reescrito para fazer upsert no Postgres com `to_tsvector("simple", title + tl_dr + tags)` em vez de gerar embeddings OpenAI e indexar no Qdrant; usa `_session_factory()` diretamente (não o `get_db` do FastAPI) por rodar em background task ARQ
- `docker-compose.yml` — adicionado serviço `worker` para o ARQ rodando separado da API
- `docker-compose.test.yml` — atualizado para refletir remoção do Qdrant
- `api/services/qdrant.py` e `api/services/embeddings.py` — deletados
- `pyproject.toml` — removidos `qdrant-client` e `openai` (~200 MB de dependências mortas)
- `tests/unit/test_search.py` — adicionados 6 testes unitários para `GET /search`
- `CLAUDE.md`, `.env.example`, `sprint.md` — atualizados para refletir o novo stack

### Decisões

- FTS com configuração de linguagem `"simple"` usada tanto na indexação quanto na query — sem stemming específico de idioma, comportamento previsível multilíngue
- `search_vector` é NULLABLE porque é computada por função Postgres no insert (não pelo app)
- Unique constraint `uq_posts_repo_file` habilita upsert idempotente no re-index
- Worker ARQ roda como serviço separado (container separado) — não embutido no processo da API; mantém o mesmo padrão estabelecido em `infra-deploy`
- Indexer usa `_session_factory()` diretamente em vez do `get_db` do FastAPI — background tasks ARQ não têm acesso ao ciclo de vida de request do FastAPI

### Armadilhas

- `get_db` precisa ser overridden explicitamente no fixture de teste para endpoints que o usam diretamente (`GET /search`); o mock global de `api.db` no `conftest.py` não é suficiente — ver pitfall documentado no CLAUDE.md
- Mock do pool ARQ deve usar `AsyncMock()` para o método `.close()`, caso contrário o teardown do lifespan do FastAPI falha com `TypeError`
- Mock de `qdrant_client` removido do `conftest.py` — não é mais necessário após remoção do serviço

### Próximos passos

- Rodar `make migrate` após deploy no Railway para aplicar `0003_create_posts_table`
- Desprovisionar Qdrant no Railway após deploy bem-sucedido (serviço e volume)
- Feature `skills-e2e` (#13) depende deste serviço estar em produção

### Arquivos-chave

- `api/models.py` — modelo `Post` com `TSVECTOR`
- `api/routers/search.py` — endpoint FTS
- `api/workers/indexer.py` — pipeline de ingest em background
- `migrations/versions/0003_create_posts_table.py` — migration Alembic

---

## infra-deploy — 2026-03-08

**PR:** TBD
**Arquivos-chave:** `docker-compose.yml`, `Makefile`, `railway.toml`

**O que foi feito:**

- `docker-compose.yml` — adicionado serviço `worker` que roda `arq api.workers.arq_worker.WorkerSettings`
  com mesmas variáveis de ambiente e dependências que o `api`; serviço `api` agora executa
  `alembic upgrade head` antes do uvicorn; porta 6333 do Qdrant removida do mapeamento de host
  (interna ao Docker network apenas — regra de segurança)
- `Makefile` — adicionado target `make migrate` (roda migrations via `docker exec` no container api)
  e `make smoke-test` (curl nos 3 endpoints `/health`, `/search?q=test`, `/gaps` com saída legível)
- `railway.toml` — adicionado comentário documentando que o worker precisa de um segundo serviço Railway
  apontando para o mesmo repo com `startCommand = "arq api.workers.arq_worker.WorkerSettings"`

**Decisões tomadas:**

- Worker como serviço separado em docker-compose (não process dentro do container da API) — ARQ workers
  são stateful (poll Redis); misturar com o processo web cria acoplamento desnecessário e dificulta
  escalar cada camada independentemente
- Migrations no startup do `api` via `command` override — garante que `make dev` sempre sobe com schema
  atualizado sem etapa manual separada; o worker não roda migrations (evita conflitos se os dois subirem
  exatamente ao mesmo tempo)
- Qdrant sem port publish no docker-compose — comunicação via Docker internal network é suficiente para
  o stack local; expor 6333 no host violaria a regra de segurança do projeto

**Próximos passos:**

- Criar PR e atualizar sprint.md com número do PR
- Criar segundo serviço Railway para o worker (UI do Railway → New Service → Same Repo → override start command)
- Smoke test manual após `make dev`: `make smoke-test`

---

## post-ingest-endpoint — 2026-03-09

**PR:** #9 — feat(arq): wire ARQ job queue into POST /posts endpoint
**Commits:** `86501e8` (fix(ci): SHA typo em actions/setup-python), `6fe5903` (feat(arq): wire ARQ pool + enqueue_job)
**Arquivos-chave:** `api/workers/arq_worker.py`, `api/main.py`, `api/deps.py`, `api/routers/posts.py`,
`tests/conftest.py`, `tests/unit/test_posts.py`

**O que foi feito:**

- `api/workers/arq_worker.py` — criado `WorkerSettings` com configuração do ARQ job queue;
  `index_post` registrado como job function; aceita `github_token` para autenticar chamadas à API GitHub
- `api/main.py` — pool ARQ criado no lifespan (`on_startup`/`on_shutdown`) e exposto em `app.state.arq_pool`
- `api/deps.py` — adicionado helper interno `_validate_session` (elimina duplicação entre `get_current_handle`
  e futuros deps); novos deps `get_arq_pool` (lê `app.state.arq_pool`) e `get_current_github_token`
  (extrai o token GitHub da Session autenticada)
- `api/routers/posts.py` — substituído `BackgroundTasks` por `arq.enqueue_job`; `github_token`
  agora passado como argumento para o job de indexação
- `tests/conftest.py` — adicionados mocks de `arq` e `redis.asyncio` para que testes unitários
  rodem sem as libs instaladas no ambiente CI
- `tests/unit/test_posts.py` — 3 novos testes: enqueue com sucesso, 401 sem sessão, 500 quando
  pool ARQ indisponível

**Decisões tomadas:**

- ARQ sobre `FastAPI BackgroundTasks` — `BackgroundTasks` não tem persistência: se o processo
  reiniciar o job é perdido silenciosamente; ARQ persiste jobs no Redis e reprocessa em falha
- Helper `_validate_session` extraído para evitar duplicação entre `get_current_handle` e
  `get_current_github_token` — ambos precisam ler o cookie, decodificar o JWT e validar a Session
- Token GitHub armazenado na Session (já existente do fluxo OAuth); recuperado via dep e passado
  explicitamente ao job — evita acoplamento direto entre o router e o modelo de persistência

**Armadilhas encontradas:**

- SHA de `actions/setup-python` no CI tinha um typo de 1 caractere (`...90a2f` → `...90a2b`);
  CI falhava silenciosamente na verificação de hash da action — conferir SHA completo no commit da action
- `arq` e `redis.asyncio` não estavam instalados no ambiente de testes unitários; mesma estratégia
  de mock via `sys.modules` em `tests/conftest.py` (padrão estabelecido nas features `auth-middleware`
  e `content-security`) — qualquer nova lib com import no nível de módulo precisa do mesmo tratamento

**Próximos passos:**

- `tests/integration/` ainda vazio — testes de integração do endpoint `POST /posts` (enqueue real
  no Redis + worker processando) podem ser adicionados quando o ambiente Docker estiver disponível no CI
- Worker ARQ (`arq run api.workers.arq_worker.WorkerSettings`) precisa estar rodando como processo
  separado em produção; configurar serviço dedicado no Railway para o worker
- Considerar dead-letter queue ou retries configuráveis em `WorkerSettings` para jobs de indexação falhos

---

## gap-board — 2026-03-09

**PR:** #7 — feat(gap-board): gap signal recording + public board endpoint
**Key files:** `api/models.py`, `api/workers/gap_tracker.py`, `api/routers/gaps.py`,
`api/routers/search.py`, `migrations/versions/0002_create_gap_signals_table.py`

**O que foi feito:**

- `api/models.py` — adicionado `GapSignal` SQLModel com PK composta `(query_hash, week_bucket, session_count)`
- `migrations/versions/0002_create_gap_signals_table.py` — migration Alembic que cria a tabela `gap_signals`
- `api/workers/gap_tracker.py` — `record_gap(query, db)`: upsert via `pg_insert` com `ON CONFLICT DO UPDATE`,
  incrementa `session_count` usando `GapSignal.__table__.c.session_count + 1` (server-side, sem ambiguidade ORM);
  lifecycle da sessão de DB pertence ao `get_db` — sem `db.commit()` explícito aqui
- `api/routers/gaps.py` — `list_gaps()`: retorna `gap_signals` com `session_count >= gap_min_sessions`
  (k=3 configurável em settings), ordenado por demanda decrescente
- `api/routers/search.py` — injeta `db: AsyncSession = Depends(get_db)` e passa para `record_gap`
  quando a busca retorna zero resultados
- 7 testes unitários para `gap_tracker` cobrindo `_week_bucket`, `_hash_query` e `record_gap`

**Decisões tomadas:**

- Queries armazenadas apenas como `sha256[:16]` — nunca texto cru (privacidade)
- k-anonimato: gaps só são expostos quando `session_count >= gap_min_sessions` (padrão=3, configurável)
- `GapItem.query_hint` expõe o hash da query — nome ligeiramente enganoso (deveria ser `query_hash`
  em uma limpeza futura)

**Armadilhas encontradas:**

- `db.commit()` dentro de `record_gap` estava errado — lifecycle da sessão pertence ao `get_db`
  dependency; removido após revisão de simplify
- `GapSignal.__table__.c.session_count + 1` é a forma correta de referenciar o valor existente
  no `set_` do upsert `pg_insert` — `GapSignal.session_count + 1` pode ser avaliado como expressão
  ORM de forma incorreta

**Próximos passos:**

- Rodar `alembic upgrade head` no Railway após deploy
- Considerar renomear `GapItem.query_hint` → `query_hash` para clareza da API
- Adicionar índice em `session_count` para performance do `list_gaps` em escala

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
