# Sprint M1 — Funciona para o fundador

<!-- Gerado em: 2026-03-08 -->

> Status ao vivo: use /project-compass. Este arquivo é readonly após criação.

## Milestone

**Objetivo:** Loop completo post→index→busca→resultado funcional sem intervenção manual, com rede não-vazia para M2.

**Critério de done:** Fundador completa o loop (instala skill → `post` → indexado → `busca query` → resultado com @handle citado)
sem intervenção manual. 20–30 posts do seeding indexados e buscáveis. `make check` passa. Deploy no Railway ativo.

## Features (ordem de execução)

| # | Feature | Slug | Deps | Esforço | Status |
|---|---------|------|------|---------|--------|
| 1 | Models Handle + Session + migration Alembic | `auth-session-model` | — | baixo | done (PR #2) |
| 2 | Filtros anti-injection (sanitizer) + XML wrapper para conteúdo recuperado | `content-security` | — | médio | done (PR #6) |
| 3 | Gap board: registrar queries vazias anonimizadas + `GET /gaps` (k≥3) | `gap-board` | — | baixo | done (PR #7) |
| 4 | Verificar/completar docker-compose + Railway deploy + smoke test | `infra-deploy` | — | baixo | pending |
| 5 | Fluxo OAuth completo: `/auth/login` → GitHub → callback → cookie HttpOnly + Redis CSRF one-time-use | `auth-oauth-flow` | `auth-session-model` | alto | done (PR #4) |
| 6 | Middleware FastAPI `get_current_user` + handle @username associado a posts + `GET /handles/@username` | `auth-middleware-handle` | `auth-oauth-flow` | baixo | done (PR #5) |
| 7 | `POST /posts` (202 + ARQ), parse frontmatter, embed 256d, upsert Qdrant | `post-ingest-endpoint` | `content-security`, `auth-middleware-handle` | médio | pending |
| 8 | Hybrid search endpoint: dense + BM25, alpha=0.5, XML-wrapped, retorna TL;DR + handle + link | `search-service` | `content-security` | médio | pending |
| 9 | Skills `busca.md` + `post.md` end-to-end com seus endpoints | `skills-e2e` | `post-ingest-endpoint`, `search-service` | baixo | pending |
| 10 | Quarentena 48h/24h para contas novas + rate limit 10 posts/hora por conta | `ingest-guardrails` | `auth-session-model`, `post-ingest-endpoint` | baixo | pending |
| 11 | Serviço: dado GitHub token, lista repos com `.claude/` presente | `repo-analyzer-service` | `auth-oauth-flow` | médio | pending |
| 12 | Integrar repo-analyzer no callback OAuth; retorna repos candidatos a post | `analyze-on-connect` | `repo-analyzer-service`, `auth-middleware-handle` | baixo | pending |
| 13 | Script de crawl: lista de repos → baixa CLAUDE.md/skills → converte para post format + indexa | `seeding-crawler` | `post-ingest-endpoint` | médio | pending |
| 14 | Execução curada do crawler: 20–30 posts indexados e buscáveis via `busca-skill` | `seeding-run` | `seeding-crawler`, `skills-e2e` | médio | pending |

## Grafo de dependências

```text
auth-session-model → auth-oauth-flow → auth-middleware-handle
                                     → repo-analyzer-service → analyze-on-connect
auth-middleware-handle → post-ingest-endpoint → skills-e2e
                       → analyze-on-connect    → ingest-guardrails
                                               → seeding-crawler → seeding-run
content-security → post-ingest-endpoint
                → search-service → skills-e2e → seeding-run

Independentes (sem deps, podem começar agora):
  auth-session-model, content-security, gap-board, infra-deploy
```

## Fusões aplicadas

- `auth-middleware` + `handle-registry` → **`auth-middleware-handle`** (ambos pequenos, mesma camada)
- `post-skill` + `busca-skill` → **`skills-e2e`** (polish final, feitos juntos no fim)

## Critério de granularidade

Uma feature está bem-scoped quando:
- Toca 1–3 arquivos principais
- Tem um "demonstrável" claro (teste que passa, endpoint que responde, skill que funciona end-to-end)
- Pode ser implementada em 1 sessão de Claude Code sem `/clear` intermediário
- Nome kebab-case descreve o QUÊ, não o PORQUÊ

## Próximo passo

/start-feature auth-session-model
