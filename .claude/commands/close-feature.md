# /close-feature

Você é um assistente de desenvolvimento executando o skill `/close-feature`.

Este skill fecha uma feature após ela já ter sido validada em produção via `/ship-feature`.
Cuida apenas de **documentação e cleanup** — não faz commit, push, PR nem deploy.

Se a feature ainda não foi validada em produção, rode `/ship-feature` primeiro.

---

## Passos

### 0. Ler o plano da feature (se existir)

Perguntar o nome da feature se não foi informado.

Verificar se `.claude/feature-plans/<nome>/plan.md` existe.
Se sim: ler integralmente para entender o que foi feito (contexto para a documentação).

### 0.5 — Detectar PR mergeado

```bash
BRANCH=$(git branch --show-current 2>/dev/null || git -C "$WORKTREE_PATH" branch --show-current)
PR_DATA=$(gh pr list --head "$BRANCH" --state merged --json number,mergedAt --limit 1 2>/dev/null || echo "[]")
PR_NUMBER=$(echo "$PR_DATA" | python3 -c "import json,sys; data=json.load(sys.stdin); print(data[0]['number'] if data else '')" 2>/dev/null)
```

Se `PR_NUMBER` encontrado: usar nos passos 1b (CHANGELOG) e 1f (backlog.json).
Se não encontrado: perguntar ao usuário o número ou pular o update de backlog.json.

### 1. Atualizar documentação

**ASSERT antes de prosseguir:** confirmar REPO_ROOT antes de qualquer write de documentação.
Executar este bloco primeiro e parar se falhar:

```bash
REPO_ROOT=$(git worktree list | head -1 | awk '{print $1}')
if [ -z "$REPO_ROOT" ] || [ ! -d "$REPO_ROOT" ]; then
  echo "ERRO: nao foi possivel determinar REPO_ROOT. Abortando."
  exit 1
fi
echo "REPO_ROOT confirmado: $REPO_ROOT"
```

**Se REPO_ROOT falhar: PARAR e reportar ao usuario antes de qualquer write.**

Usar `$REPO_ROOT/` como prefixo em todos os paths de documentacao dos passos abaixo.

#### 1a–1e. Docs em paralelo (AI-native)

> **Design:** HANDOVER, CHANGELOG, LEARNINGS e CLAUDE.md são documentos independentes.
> Disparar como 4 subagentes simultâneos; fazer único commit ao final com todos os artefatos.

Coletar contexto antes de disparar os subagentes:
- SHA do commit mergeado: `git log --oneline -5`
- PR number: usar `PR_NUMBER` do Passo 0.5
- URL do repo: `git remote get-url origin` (converter SSH → HTTPS)

Disparar os 4 subagentes com `Task tool` (`run_in_background=true`):

---

**Subagente A — HANDOVER.md:**
> Leia `.claude/feature-plans/<nome>/plan.md` (se existir).
> Gere uma entrada de HANDOVER com: data atual, o que foi feito, decisões tomadas, armadilhas encontradas, próximos passos, arquivos-chave.
> Faça append em `$REPO_ROOT/HANDOVER.md` (criar se não existir).

---

**Subagente B — CHANGELOG.md (git pointer):**
> Formato AI-native: git history é a fonte de verdade — escreva um pointer, não prose redundante.
>
> Coletar: SHA do commit mergeado, número do PR, URL do repo, tipo (feat/fix/improvement).
>
> **Formato para qualquer tipo:**
> ```markdown
> ## <nome-feature> — PR #N — YYYY-MM-DD
>
> **Tipo:** <feat|fix|improvement>
> **Commit:** `git show <SHA>` para diff completo
> **Decisões e armadilhas:** ver LEARNINGS.md#<nome-feature>
>
> ---
> ```
>
> Inserir logo após a linha `# Changelog` (antes da primeira entrada `##`).
> Usar Edit tool: `old_string` = primeira linha após o cabeçalho, `new_string` = nova entrada + essa mesma linha.
> Criar o arquivo se não existir.

---

**Subagente C — LEARNINGS.md:**
> Avalie se algo desta sessão vale registrar — você decide, não pergunte.
> Critério: algo não documentado que causou surpresa, ou que seria útil em situações futuras.
> Se sim: propor o aprendizado ao usuário e, com aprovação, adicionar:
> ```markdown
> ## <data> — <título curto>
> <aprendizado>
> ```
> Se não houver nada novo: retornar "nada novo para registrar".

---

**Subagente D — CLAUDE.md pitfalls:**
> Avalie se houve armadilha nova — você decide, não pergunte.
> Critério: problema não-óbvio que outro agente cometeria no mesmo contexto.
> Se sim: propor ao usuário e, com aprovação, adicionar à tabela de armadilhas em `$REPO_ROOT/CLAUDE.md`.
> Se não houver nada novo: retornar "sem novas armadilhas".

---

Aguardar todos os 4 subagentes com `TaskOutput`.

**Commit único ao final** (após todos os subagentes concluírem):

```bash
git -C "$REPO_ROOT" add HANDOVER.md CHANGELOG.md LEARNINGS.md CLAUDE.md
git -C "$REPO_ROOT" commit -m "docs(<nome>): HANDOVER, CHANGELOG, LEARNINGS, CLAUDE.md pitfalls

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
git -C "$REPO_ROOT" push origin main
```

#### 1c. MEMORY.md coordinator — commit direto em main (se existir)

Verificar se `.claude/agent-memory/coordinator/MEMORY.md` existe.

**Se existir:**

```bash
REPO_ROOT=$(git worktree list | head -1 | awk '{print $1}')
MEMORY_FILE="$REPO_ROOT/.claude/agent-memory/coordinator/MEMORY.md"

git -C "$REPO_ROOT" pull --rebase origin main
```

Editar MEMORY_FILE com Edit tool (path absoluto):
- Remover a linha da tabela `## Worktrees ativas` onde Worktree = `<nome>`
- Remover TODAS as linhas da tabela `## Hot file claims (ativo)` onde Worktree = `<nome>`

```bash
git -C "$REPO_ROOT" add .claude/agent-memory/coordinator/MEMORY.md
git -C "$REPO_ROOT" commit -m "chore(coordinator): unregister worktree <nome>"
git -C "$REPO_ROOT" push origin main
```

**Se não existir:** pular este passo.

#### 1f. backlog.json (se existir)

```bash
command -v jq >/dev/null || { echo "jq não encontrado — pular update de backlog.json (brew install jq para habilitar)"; }
BACKLOG="$REPO_ROOT/.claude/backlog.json"
if [ -f "$BACKLOG" ] && command -v jq >/dev/null; then
  TODAY=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  jq --arg id "<nome>" \
     --arg pr "<pr_number>" \
     --arg date "$TODAY" \
     '(.features[] | select(.id == $id)) |= . + {status: "done", completedAt: $date, prNumber: ($pr | tonumber? // null)}' \
     "$BACKLOG" > "$BACKLOG.tmp" && mv "$BACKLOG.tmp" "$BACKLOG"
  echo "backlog.json atualizado: <nome> → done"
fi
```

Substituir `<nome>` pelo slug da feature e `<pr_number>` pelo PR detectado no Passo 0.5 (ou `""` se não encontrado).

#### 1g. Propagação ao kickstart (se houver skills novos/modificados)

Verificar se algum arquivo em `.claude/commands/` foi criado ou modificado nesta feature:

```bash
git diff origin/main...HEAD --name-only | grep "^\.claude/commands/"
```

Se **nenhum skill foi tocado**: pular sem mensagem.

Se **há skills novos ou modificados**, verificar primeiro que o kickstart está limpo:

```bash
KICKSTART={{KICKSTART_PATH}}
DIRTY=$(git -C "$KICKSTART" status --porcelain 2>/dev/null)
if [ -n "$DIRTY" ]; then
  echo "⚠️  kickstart tem mudanças locais não-commitadas:"
  echo "$DIRTY"
  echo ""
  echo "Resolver antes de prosseguir:"
  echo "  a) git -C $KICKSTART stash"
  echo "  b) git -C $KICKSTART add . && git -C $KICKSTART commit -m 'chore: wip'"
  echo "  c) Abortar e resolver manualmente"
  exit 1
fi
```

**Se kickstart estiver sujo: PARAR e reportar ao usuário antes de qualquer operação de propagação.**

Avaliar cada skill:

**Você** decide se o skill tem lógica genérica o suficiente para outros projetos — não pergunte ao usuário.
Critério: o skill resolve um problema que qualquer projeto com esse workflow teria, e a lógica
pode ser expressa com `{{PLACEHOLDERS}}` sem perder utilidade.

Exemplos que **devem** propagar: skills de revisão, checkpoints de qualidade, workflows de design.
Exemplos que **não devem**: skills com paths, comandos ou contexto exclusivos deste projeto.

Para cada skill candidato, apresentar:

```text
📤 "<nome>" foi criado/modificado nesta feature.
   Lógica parece genérica o suficiente para o kickstart.
   Confirmar propagação? (sim = crio versão template e faço PR no kickstart; não = fica só aqui)
```

Com confirmação, criar a versão template:

1. Ler o skill atual e identificar elementos projeto-específicos
2. Substituir por `{{PLACEHOLDER}}` — ex: paths hardcoded, nomes de ferramentas, constraints específicas
3. Adicionar seções `## Quando NÃO usar` e `## Testes` se ausentes (padrão kickstart)
4. Escrever em `{{KICKSTART_PATH}}/.claude/commands/<nome>.md`
5. Fazer commit e PR no kickstart:

```bash
KICKSTART={{KICKSTART_PATH}}
git -C "$KICKSTART" add .claude/commands/<nome>.md
git -C "$KICKSTART" commit -m "feat(skills): add /<nome> — propagated from <projeto>"
# Usar gh api diretamente (gh pr create pode detectar repo errado em worktrees):
BRANCH=$(git -C "$KICKSTART" branch --show-current)
git -C "$KICKSTART" push origin "$BRANCH"
gh api repos/rmolines/claude-kickstart/pulls \
  --method POST \
  -f title="feat(skills): add /<nome>" \
  -f head="$BRANCH" \
  -f base="main" \
  -f body="Propagado de <projeto> após uso real na feature <nome-feature>."
```

Exibir URL do PR e aguardar confirmação de merge antes de continuar.

Após merge confirmado, sincronizar a versão genérica de volta ao projeto:

```bash
# Garantir que local main está em cima do squash-merge antes de sync.
# Sem isso, o push falha com conflito em .claude/commands/ quando o PR
# que acabou de mergear tocou skills (mesma causa: squash-merge já está
# em origin/main, local main pode estar desatualizado).
git -C "$REPO_ROOT" pull --rebase origin main
make sync-skills
```

Se `make sync-skills` não existir: avisar e sugerir verificar o Makefile.

### 2. Remover worktree e branch local

**ASSERT antes de prosseguir:** confirmar que a sessao atual nao esta dentro da worktree a ser removida.

```bash
REPO_ROOT=$(git worktree list | head -1 | awk '{print $1}')
WORKTREE_PATH="$REPO_ROOT/.claude/worktrees/<nome>"
CURRENT_DIR=$(pwd)
if [[ "$CURRENT_DIR" == "$WORKTREE_PATH"* ]]; then
  echo "ERRO: sessao atual esta dentro da worktree a ser removida. Saia da worktree antes de continuar."
  exit 1
fi
```

**Se CWD estiver dentro da worktree: PARAR e reportar ao usuario.**

Verificar se a worktree existe:
```bash
git -C "$REPO_ROOT" worktree list | grep "<nome>"
```

- Se existir e o agente atual estiver **dentro** dela: avisar que precisa sair primeiro (a worktree não pode remover a si mesma)
- Se existir e o agente estiver **fora** dela:
  ```bash
  git -C "$REPO_ROOT" worktree remove --force "$WORKTREE_PATH" 2>/dev/null || true
  git -C "$REPO_ROOT" worktree prune
  git -C "$REPO_ROOT" branch -D worktree-<nome> 2>/dev/null || true
  # Limpar remote branch se ship-feature não deletou (falha silenciosa em worktree)
  REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
  gh api -X DELETE "repos/$REPO/git/refs/heads/worktree-<nome>" 2>/dev/null || true
  ```
- Se não existir no `git worktree list` mas o diretório ainda estiver em disco:
  ```bash
  rm -rf "$WORKTREE_PATH"
  ```
- Se não existir em nenhum dos dois: pular sem mensagem

### 3. Limpar feature-plans

- Verificar se existe `.claude/feature-plans/<nome>/`
- **Sempre arquivar automaticamente** → mover para `.claude/feature-plans/archived/<nome>/` sem perguntar

### 4. Resumo final

**Antes de apresentar o resumo:** se `plan.md` foi lido no Passo 0, usar o campo `## Problema` e os `## Deliverables` para compor o bloco abaixo.
Se não foi lido, usar o título do PR (Passo 0.5) e o CHANGELOG gerado (Passo 1b) como fonte.

```text
## O que foi entregue

Feature: <nome>
PR: #N — <título do PR>
Data: YYYY-MM-DD

Resumo: <1-2 frases do Problema do plan.md ou do título do PR, em linguagem simples>

O que mudou:
- <Deliverable 1 concluído — o que o usuário/dev consegue fazer agora>
- <Deliverable 2 se houver>

Arquivos principais:
- path/to/file — <o que mudou>
```

---

```text
✅ Feature encerrada!

Documentação:
- HANDOVER.md ✅
- CHANGELOG.md ✅
- MEMORY.md coordinator <✅ ou ⏭️ sem coordinator>
- LEARNINGS.md <✅ ou ⏭️ pulado>
- CLAUDE.md armadilhas <✅ ou ⏭️ pulado>
- Kickstart propagation <✅ PR aberto | ⏭️ sem skills candidatos | ⏭️ não confirmado pelo dev>

Worktree: <removida | já não existia | aguardando saída manual>
feature-plans: arquivado

Próximos passos:
- <qualquer item pendente, ou "nenhum">
```

---

## Regras

- Nunca commitar código da feature em main — commits de documentação (HANDOVER.md, CHANGELOG.md, MEMORY.md coordinator) e sync de skills em main são esperados e permitidos
- Se chamado sem feature validada em produção: lembrar de rodar `/ship-feature` primeiro
