# /ship-feature

Você é um assistente de desenvolvimento executando o skill `/ship-feature`.

Este skill entrega a feature em produção e valida que está funcionando.
Pode ser rodado múltiplas vezes durante o ciclo de uma feature — uma por iteração.

Após validação bem-sucedida, use `/close-feature` para documentação e cleanup.

---

## Configuração do projeto

Comandos fixos deste projeto (não precisam ser extraídos do CLAUDE.md):

- **BUILD_CMD:** `docker-compose build` (ou `pip install -e .` para testes unitários sem Docker)
- **TEST_CMD:** `pytest tests/unit/`
- **INTEGRATION_TEST_CMD:** `pytest tests/integration/` (requer `docker-compose up` rodando)
- **SMOKE_TEST:**
  ```bash
  curl http://localhost:8000/search?q=test
  # Esperado: {"results": [], "total": 0}

  curl http://localhost:8000/gaps
  # Esperado: {"gaps": []}
  ```
- **CI workflows:** `.github/workflows/ci.yml` e `.github/workflows/deploy.yml`
- **Deploy:** via tag git — `git tag v<version> && git push origin v<version>` (não há deploy manual)
- **Hot files do projeto:**
  - `api/security/sanitizer.py` — filtro anti-injection; qualquer mudança tem implicação de segurança
  - `api/security/wrappers.py` — XML wrapper para conteúdo recuperado; crítico para prompt injection
  - `skills/busca.md` — skill distribuída para usuários; mudanças afetam todos os agentes instalados
  - `skills/post.md` — skill de publicação; formato do frontmatter afeta o indexer
  - `api/services/qdrant.py` — hybrid search; dimensão do embedding hardcoded aqui (256d)
  - `api/workers/indexer.py` — pipeline de ingest; quarentena e sanitização acontecem aqui
  - `migrations/` — Alembic; coordenar mudanças de schema
  - `.github/workflows/ci.yml`
  - `.github/workflows/deploy.yml`
  - `CLAUDE.md`

---

## Detecção de caminho (fast vs standard)

Hot files já definidos acima. Detectar o caminho antes de qualquer outro passo:

```bash
# Linhas alteradas vs. main
LINES_CHANGED=$(git diff origin/main...HEAD --stat | tail -1 | grep -oE '[0-9]+ (insertion|deletion)' | awk '{sum+=$1} END {print sum+0}')

# Hot files tocados pela branch
HOT_FILES_TOUCHED=$(git diff origin/main...HEAD --name-only | grep -F "$(echo "$HOT_FILES" | tr ' ' '\n')" | wc -l | tr -d ' ')
```

| Condição | Caminho |
|----------|---------|
| `LINES_CHANGED < 150` **e** `HOT_FILES_TOUCHED == 0` **e** sem flag `--review` | **Fast** — local verification + merge direto |
| `HOT_FILES_TOUCHED > 0` **ou** `LINES_CHANGED >= 150` **ou** flag `--review` | **Standard** — PR + CI como rastreabilidade |

Anunciar o caminho escolhido em uma linha antes de prosseguir:
```text
🚀 Caminho: fast (N linhas, sem hot files)   — ou —   📋 Caminho: standard (hot files tocados / N≥150 linhas)
```

---

## Modo fast — local-first

> Ativado quando: <150 linhas alteradas, sem hot files, sem `--review`.
> Objetivo: local verification → commit → PR → merge em ~2 min.

### F1. Simplify + build + test (HARD GATE)

Rodar o skill `simplify` sem confirmação, depois:

```bash
docker-compose build
pytest tests/unit/
```

Se qualquer um falhar: **parar**. Não avançar com verificação local quebrada.

### F2. Commit

Mesmo fluxo do Modo standard passo 1 — sem confirmação.

### F3. Rebase + push

```bash
git fetch origin
git rebase origin/main
git push -u origin <branch-atual>
```

### F4. PR + merge imediato

```bash
gh pr create --title "<título>" --body "$(cat <<'EOF'
## O que foi feito
- <bullet list>

## Arquivos modificados
- `path/to/file` — descrição

> Fast path: verificação local passou. CI roda como rastreabilidade.
EOF
)"
```

Sem aguardar CI — mergear imediatamente após criar o PR:

```bash
gh pr merge --squash
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
BRANCH=$(git branch --show-current)
gh api -X DELETE "repos/$REPO/git/refs/heads/$BRANCH" 2>/dev/null || true
```

### F5. Resultado

```text
✅ Feature entregue (fast path)!

PR: <url> — merged
Verificação local: ✅ build + test passaram
CI: rodando como rastreabilidade (não bloqueante)

Rode /close-feature para documentação e cleanup.
```

---

## Detecção de modo

1. Perguntar o nome da feature se não foi informado
2. Detectar flag `--review`: se o argumento contém `--review`, forçar standard path com CI blocking gate (ignorar detecção automática de caminho)
3. Obter branch atual: `git branch --show-current`
4. Verificar se a branch existe no remote:
   ```bash
   git ls-remote --heads origin <branch>
   ```
   - **Retornou output** → **Modo PR** (primeira execução ou iteração antes do merge)
   - **Retornou vazio** → **Modo direto** (branch já foi mergeada; esta é uma iteração)

5. Verificar se há algo para entregar:
   ```bash
   git status --short
   git log origin/main..HEAD --oneline
   ```
   - Se limpo e sem commits à frente → perguntar se quer rodar o smoke test mesmo assim ou encerrar

---

## Modo PR — primeira execução

### 0. Ler o plano da feature

Se `.claude/feature-plans/<nome>/plan.md` existe: ler integralmente e extrair:
- Checklist de infraestrutura (secrets, configurações, scripts de setup)
- Smoke test recomendado

Se `plan.md` não existir:

```text
⚠️ Nenhum plan.md encontrado para esta feature.
O checklist de infra (secrets, scripts de setup) não será verificado.
Continuando com base apenas no CLAUDE.md.
```

### 0.4. Simplify automático

Rodar o skill `simplify` agora — sem pedir confirmação ao usuário.

O simplify revisa o diff atual para reuse, qualidade e eficiência, e corrige problemas encontrados diretamente.
Aguardar a conclusão antes de avançar. Se não houver problemas, continuar normalmente.

Após o simplify, verificar se o diff toca código Swift:

```bash
git diff origin/main...HEAD --name-only | grep "\.swift$"
```

- Se há arquivos `.swift` com views (nome termina em `View.swift` ou diff contém `some View`) → invocar `swiftui-expert-skill` para um review pass
  [porque a skill detecta anti-patterns de SwiftUI que o simplify genérico não cobre]
- Se há arquivos `.swift` com código concorrente (diff contém `actor`, `async`, `@MainActor`, `Task {`) → invocar `swift-concurrency` para um review pass
  [porque data races e isolamento incorreto não aparecem em build — só em runtime]

Se nenhuma condição se aplicar: continuar normalmente.

### 0.5. Verificação local (HARD GATE)

Antes de qualquer commit ou push, rodar:

```bash
docker-compose build
pytest tests/unit/
```

Se qualquer um falhar: **parar aqui**. Não criar PR com build quebrado.

Mostrar output completo — não resumir. Só avançar com ambos passando.

### 1. Commit (se houver mudanças pendentes)

1. Identificar todos os arquivos modificados/novos
2. **Não adicionar arquivos com secrets** (`.env`, tokens hardcoded)
3. Compor mensagem de commit no formato:
   ```text
   feat|fix|chore: <descrição concisa>

   - <detalhe 1>
   - <detalhe 2>

   Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
   ```
4. Usar o sub-skill `commit-commands:commit` para criar o commit (ou executar `git add <arquivos específicos>` + `git commit` diretamente) **sem pedir confirmação da mensagem**

### 1.5. Preflight de hot files

Detectar sobreposição com `origin/main` antes do rebase:

```bash
git fetch origin
MERGE_BASE=$(git merge-base HEAD origin/main)
git diff --name-only $MERGE_BASE origin/main > /tmp/main_changed
git diff --name-only $MERGE_BASE HEAD       > /tmp/branch_changed
OVERLAP=$(comm -12 <(sort /tmp/main_changed) <(sort /tmp/branch_changed))
```

Para cada arquivo em `OVERLAP`:
- Se é hot file do projeto → **⛔ ALERTA**: "origin/main alterou `<arquivo>` desde que você branchou. O rebase vai colidir. Verifique o diff antes de continuar."
  - Perguntar: "Deseja prosseguir com o rebase mesmo assim?"
  - Sim → prosseguir (haverá conflito manual)
  - Não → encerrar
- Se não é hot file → **⚠️ aviso leve**: "origin/main também modificou `<arquivo>`. Rebase pode ter conflito."

Se `OVERLAP` vazio → prosseguir sem mensagem.

### 2. Rebase em cima do main

```bash
git rebase origin/main
```

Se houver conflitos: listar e pedir orientação ao usuário antes de tentar resolver.

### 3. Push

```bash
git push -u origin <branch-atual>
```

### 4. Criar Pull Request

```bash
gh pr create --title "<título>" --body "$(cat <<'EOF'
## O que foi feito
- <bullet list das mudanças>

## Como testar
- <passos para verificar que funciona>

## Impacto em produção
- Restart/redeploy necessário: sim/não
- Novo secret de ambiente: <nome> ou nenhum
- Script de setup necessário: <descrição> ou nenhum
- Mudança em configuração crítica: sim/não

## Arquivos modificados
- `path/to/file` — <descrição>
EOF
)"
```

Criar diretamente **sem pedir confirmação** — exibir a URL do PR após criar.

### 5. Checklist pré-merge

Com base no `plan.md` (passo 0), verificar cada item antes de mergear:

**Novos secrets de ambiente?**
- Se sim: ⚠️ lembrar o usuário de configurá-los no ambiente (GitHub Secrets, Vercel, Railway, etc.) ANTES do merge
- O deploy vai falhar silenciosamente se o secret não existir no CI
- 🔴 Aguardar confirmação antes de continuar

**Script de setup/migração necessário?**
- Se sim: anotar — será executado no passo 6b

**Mudança em arquivo de configuração que requer restart?**
- Se sim: anotar — restart será necessário após o deploy

**Commits inesperados na branch?**
- `git log origin/main..HEAD --oneline` — garantir que só os commits desta feature estão
- Se aparecer algo inesperado, investigar antes de mergear

### 6. CI — rastreabilidade e merge

> **Design AI-native:** verificação local (passo 0.5) é o hard gate. CI é rastreabilidade — roda, mas não bloqueia o merge.
> Exceção: flag `--review` ativa o CI blocking gate do modo legado (ver abaixo).

**Com flag `--review` (opt-in para revisão humana):**

```bash
gh pr checks <pr_number> --watch
```

- Se todos passarem: prosseguir para o merge
- Se algum falhar: exibir erro detalhado e **PARAR** — corrigir e rodar `/ship-feature` novamente

> **Atenção após re-push de fix de CI:** `gh pr checks --watch` pode exibir resultado do run *anterior*.
> Nesse caso, obter o run ID explicitamente:
> ```bash
> sleep 5
> BRANCH=$(git branch --show-current)
> LATEST_RUN=$(gh run list --branch "$BRANCH" --limit 1 --json databaseId -q '.[0].databaseId')
> gh run watch "$LATEST_RUN" --exit-status
> ```

**Sem `--review` (default — standard path):**

```bash
# Mostrar status atual do CI (informacional — não blocking)
gh pr checks <pr_number> 2>/dev/null | head -20 || true
```

Exibir resultado e continuar independentemente — o merge não aguarda CI verde.

Mergear diretamente **sem pedir confirmação**:

```bash
BRANCH=$(git branch --show-current)
gh pr merge --squash
# --delete-branch falha silenciosamente em worktree (main já checked out no repo pai)
# Deletar remote branch explicitamente:
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
gh api -X DELETE "repos/$REPO/git/refs/heads/$BRANCH" 2>/dev/null \
  || echo "⚠️  Remote branch não deletada automaticamente — limpar com: gh api -X DELETE repos/$REPO/git/refs/heads/$BRANCH"
```

### 6a. Verificar que o deploy chegou ao ambiente

O deploy deste projeto é ativado via tag git — não há deploy automático ao mergear em main.

**Para disparar deploy:**
```bash
# Obter versão atual e incrementar (ex: v0.1.0 → v0.1.1)
git tag v<version>
git push origin v<version>
```

Acompanhar `.github/workflows/deploy.yml` via:
```bash
gh run list --workflow=deploy.yml --limit 3
```

Confirmar que o deploy concluiu com sucesso antes de rodar o smoke test.

**Não declarar deploy OK sem confirmar esta etapa — o Railway leva ~2 min após a tag.**

### 6b. Executar script de setup (se necessário)

Se o plano indicou setup necessário: executar agora e verificar que concluiu sem erro.

### 7. Smoke test

Executar os dois endpoints de validação:

```bash
curl http://localhost:8000/search?q=test
# Esperado: {"results": [], "total": 0}

curl http://localhost:8000/gaps
# Esperado: {"gaps": []}
```

Se falhar: investigar logs antes de escalar o problema.
**Não declarar sucesso com smoke test vermelho.**

### 8. Resultado

Se tudo passou:
```text
✅ Feature entregue (standard path)!

PR: <url> — merged
Verificação local: ✅ build + test passaram
CI: rodando como rastreabilidade

Se encontrar problemas, corrija na worktree e rode /ship-feature novamente.
Quando estiver satisfeito, rode /close-feature para documentação e cleanup.
```

Se algo falhou: reportar o erro e aguardar orientação — não encerrar.

---

## Modo direto — iteração pós-merge

Execute quando a branch remota não existe mais (foi deletada após merge anterior).

### 1. Commit (se houver mudanças pendentes)

Mesmo fluxo do Modo PR passo 1 — sem pedir confirmação.

### 1.5. Preflight de hot files

Mesmo procedimento do Modo PR passo 1.5.

### 2. Push direto para main

```bash
git fetch origin
git rebase origin/main
git push origin HEAD:main
```

Se houver conflitos no rebase: listar e pedir orientação. Nunca usar `--force`.

### 3. Acompanhar CI (informacional)

```bash
# Mostrar status — não blocking
gh run list --limit 3
```

CI corre como rastreabilidade. Não aguardar nem bloquear neste passo.

### 4. Verificar deploy e smoke test

Mesmo fluxo do Modo PR passos 6a, 6b e 7.

### 5. Resultado

```text
✅ Iteração entregue e validada!

Commit: <sha curto>
CI: ✅ passou em <duração>
Smoke test: ✅

Se precisar de mais iterações, corrija e rode /ship-feature novamente.
Quando estiver satisfeito, rode /close-feature para documentação e cleanup.
```

---

## Regras

- Nunca `git push --force` sem aprovação explícita do usuário
- Nunca commitar arquivos com secrets (`.env`, tokens hardcoded)
- Commit e PR criados autonomamente — sem aguardar confirmação da mensagem
- Se qualquer passo falhar: parar e reportar antes de continuar
- **Nunca criar PR sem antes rodar `docker-compose build` + `pytest tests/unit/` e mostrar output** (passo 0.5)
- **Nunca declarar "em produção" sem ter verificado deploy (passo 6a) e smoke test (passo 7)**
- **O smoke test usa os endpoints `/search?q=test` e `/gaps` definidos no CLAUDE.md**
- **Deploy é via tag git** — `git tag v<version> && git push origin v<version>` — nunca deploy manual direto
- **Qdrant porta 6333 nunca exposta publicamente** — verificar `.github/workflows/deploy.yml` se tocar networking
- **Sanitizer obrigatório antes de indexar** — qualquer feature de ingest deve passar por `api/security/sanitizer.py`
- **Soft-delete sempre** — nunca hard-delete de posts; verificar se a feature não introduz hard-delete acidentalmente
- **Embedding 256d hardcoded** — se a feature tocar `api/services/qdrant.py`, confirmar que a dimensão não mudou
