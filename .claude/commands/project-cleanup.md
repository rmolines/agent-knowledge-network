# /project-cleanup

Você é um assistente de desenvolvimento executando o skill `/project-cleanup`.

Este skill audita e limpa acúmulo cross-feature no repo: worktrees orfãs, branches antigas,
feature-plans não-arquivados, e entradas stale em docs.

Absorve a função de `commit-commands:clean_gone` — não é necessário rodar separadamente.

---

## Fase 1 — Audit (3 subagentes paralelos, read-only)

**ASSERT antes de começar:** confirmar REPO_ROOT.

```bash
REPO_ROOT=$(git worktree list | head -1 | awk '{print $1}')
if [ -z "$REPO_ROOT" ] || [ ! -d "$REPO_ROOT" ]; then
  echo "ERRO: nao foi possivel determinar REPO_ROOT. Abortando."
  exit 1
fi
echo "REPO_ROOT: $REPO_ROOT"
```

Disparar 3 subagentes com `Task tool` (`run_in_background=true`):

---

**Subagente A — Git/GitHub:**

Executar os comandos abaixo e reportar findings (apenas listar — não deletar nada):

```bash
# 1. Worktrees orfãs em disco (dirs em .claude/worktrees/ não no git worktree list)
REGISTERED=$(git worktree list | awk '{print $1}')
for dir in "$REPO_ROOT/.claude/worktrees/"/*/; do
  [ -d "$dir" ] || continue
  name=$(basename "$dir")
  echo "$REGISTERED" | grep -q "$dir" || echo "ORFÃO: $dir"
done

# 2. Branches locais [gone] (remote deletada)
git branch -vv | grep '\[gone\]'

# 3. Branches locais merged em origin/main
git branch --merged origin/main | grep -v '^\*' | grep -v 'main'

# 4. Remote branches worktree-* com PR merged
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)
for branch in $(git branch -r | grep 'origin/worktree-' | sed 's|origin/||' | tr -d ' '); do
  PR=$(gh pr list --head "$branch" --state merged --json number,title --limit 1 2>/dev/null)
  [ -n "$PR" ] && echo "MERGED_PR: $branch → $PR"
done

# 5. PRs abertos com branch worktree-* (requerem atenção humana)
gh pr list --state open --json number,title,headRefName | python3 -c "
import json,sys
prs = json.load(sys.stdin)
for pr in prs:
  if 'worktree-' in pr.get('headRefName',''):
    print(f'PR_ABERTO: #{pr[\"number\"]} {pr[\"title\"]} ({pr[\"headRefName\"]})')
"
```

Retornar listas separadas por categoria.

---

**Subagente B — Feature-plans:**

```bash
# 1. Pastas em root (não archived) cujo PR foi merged
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)
for dir in "$REPO_ROOT/.claude/feature-plans/"/*/; do
  [ -d "$dir" ] || continue
  slug=$(basename "$dir")
  [ "$slug" = "archived" ] && continue
  PR=$(gh pr list --search "head:worktree-$slug OR head:feat/$slug" --state merged --json number --limit 1 2>/dev/null)
  [ -n "$PR" ] && [ "$PR" != "[]" ] && echo "PR_MERGED: $slug"
done

# 2. Pastas vazias (sem nenhum .md)
for dir in "$REPO_ROOT/.claude/feature-plans/"/*/; do
  [ -d "$dir" ] || continue
  slug=$(basename "$dir")
  [ "$slug" = "archived" ] && continue
  count=$(find "$dir" -name "*.md" | wc -l | tr -d ' ')
  [ "$count" = "0" ] && echo "VAZIO: $slug"
done

# 3. Duplicatas (aparece em root E em archived)
for dir in "$REPO_ROOT/.claude/feature-plans/archived/"/*/; do
  [ -d "$dir" ] || continue
  slug=$(basename "$dir")
  [ -d "$REPO_ROOT/.claude/feature-plans/$slug" ] && echo "DUPLICATA: $slug"
done

# 4. Uncommitted changes em feature-plans
git -C "$REPO_ROOT" status --short | grep "feature-plans"
```

Retornar listas separadas por categoria.

---

**Subagente C — Docs:**

```bash
# 1. HANDOVER.md: entradas com feature-slug que está em archived/
# (busca por padrões "## <slug>" no HANDOVER onde slug existe em archived/)
```

Ler `$REPO_ROOT/HANDOVER.md` e `$REPO_ROOT/LEARNINGS.md`.
Ler `$REPO_ROOT/CLAUDE.md` (seção de pitfalls/armadilhas).
Listar slugs de features arquivadas presentes em `.claude/feature-plans/archived/`.

Para cada entrada `## <slug>` no HANDOVER.md: verificar se o slug tem pasta em `archived/` →
se sim, marcar como candidata a remover.

Para cada entrada `## <data> — <título>` no LEARNINGS.md: verificar se há pitfall com
keywords similares no CLAUDE.md → se sim, marcar como candidata (overlap).

Retornar listas separadas por categoria.

---

Aguardar todos os 3 subagentes com `TaskOutput`.

---

## Fase 2 — Relatório

Consolidar os findings dos 3 subagentes e apresentar:

```
## Relatório de limpeza

### Git/GitHub
- Worktrees orfãs em disco: N
  <lista>
- Branches locais [gone] ou merged: N
  <lista>
- Remote branches worktree-* com PR merged: N
  <lista>
- PRs abertos (requerem atenção humana): N
  <lista>

### Feature-plans
- Não-arquivados com PR merged: N
  <lista>
- Pastas vazias (sem artefatos): N
  <lista>
- Duplicatas (root + archived): N
  <lista>
- Uncommitted changes: N
  <lista>

### Docs
- Entradas HANDOVER de features arquivadas: N
  <lista>
- Learnings com possível overlap com CLAUDE.md: N
  <lista — requer revisão humana>

### Total auto-limpável: N itens
### Total requer revisão humana: N itens
```

---

## Fase 3 — Cleanup por seção (confirmação por seção)

### 3a. Git/GitHub

Mostrar ao usuário:

```
Limpar Git? (sim/não)
  ✓ Deletar N dirs orfãs de .claude/worktrees/
  ✓ Deletar N branches locais merged/[gone]
  ✓ Deletar N remote branches worktree-* com PR merged
    (PRs abertos são ignorados — requerem ação manual)
```

Se sim:

```bash
# 1. Dirs orfãs em disco
# NOTA: worktree atual nunca é deletada (seria suicídio)
CURRENT_DIR=$(pwd)
REGISTERED=$(git -C "$REPO_ROOT" worktree list | awk '{print $1}')
for dir in "$REPO_ROOT/.claude/worktrees/"/*/; do
  [ -d "$dir" ] || continue
  # Nunca deletar a worktree em que o agente atual está rodando
  [[ "$CURRENT_DIR" == "$dir"* ]] && echo "SKIP (worktree ativa): $dir" && continue
  echo "$REGISTERED" | grep -q "$dir" || rm -rf "$dir" && echo "Removido: $dir"
done

# 2. Branches locais [gone]
git -C "$REPO_ROOT" branch -vv | grep '\[gone\]' | awk '{print $1}' | xargs -r git -C "$REPO_ROOT" branch -D

# 3. Branches locais merged
git -C "$REPO_ROOT" branch --merged origin/main | grep -v '^\*' | grep -v 'main' | xargs -r git -C "$REPO_ROOT" branch -d

# 4. Remote branches worktree-* com PR merged (lista gerada pelo Subagente A)
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
# Para cada branch na lista do Subagente A:
# gh api -X DELETE "repos/$REPO/git/refs/heads/<branch>"
```

Executar item por item e reportar o que foi removido.

### 3b. Feature-plans

Mostrar ao usuário:

```
Arquivar feature-plans não-arquivados? (sim/não)
  ✓ Mover N pastas para .claude/feature-plans/archived/
  ✓ Remover N duplicatas de root (já existem em archived/)
  ✓ Remover N pastas vazias
```

Se sim:

```bash
# Arquivar pastas com PR merged
mv "$REPO_ROOT/.claude/feature-plans/<slug>" "$REPO_ROOT/.claude/feature-plans/archived/<slug>"

# Remover duplicatas de root (archived já tem a versão)
rm -rf "$REPO_ROOT/.claude/feature-plans/<slug>"

# Commitar tudo junto
git -C "$REPO_ROOT" add .claude/feature-plans/
git -C "$REPO_ROOT" commit -m "chore(cleanup): archive stale feature-plans

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

Se houver uncommitted changes identificados pelo Subagente B, incluir no mesmo commit.

### 3c. Docs (revisão humana)

**HANDOVER.md — entradas de features arquivadas:**

Mostrar as entradas candidatas a remover (máx 5 linhas por entrada para preview).
Pergunta: "Remover estas entradas do HANDOVER.md? (sim/não)"

Se sim: usar Edit tool para remover cada entrada (da linha `## <slug>` até o próximo `## ` ou fim do arquivo).

**LEARNINGS.md — learnings com overlap:**

Mostrar pares: `<título do learning>` → `<pitfall similar no CLAUDE.md>`.
Pergunta: "Estes learnings já estão cobertos pelo CLAUDE.md. Remover? (sim/não)"

Se sim: usar Edit tool para remover cada entrada do LEARNINGS.md.

**NÃO fazer automaticamente:**
- Deletar PRs abertos
- Modificar CLAUDE.md
- Push para main sem os docs commitados

---

## Fase 4 — Commit docs + push

Se HANDOVER.md ou LEARNINGS.md foram modificados:

```bash
git -C "$REPO_ROOT" add HANDOVER.md LEARNINGS.md
git -C "$REPO_ROOT" commit -m "chore(cleanup): remove stale doc entries

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
git -C "$REPO_ROOT" push origin main
```

---

## Fase 5 — Resumo final

```
✅ Cleanup concluído!

Git:  N worktrees removidas · N branches locais · N remote branches
Plans: N arquivados · N uncommitted changes commitados
Docs: N entradas removidas do HANDOVER · N learnings removidos

Itens ignorados (requerem ação manual):
- <lista de PRs abertos, se houver>
- <qualquer item que o usuário escolheu não limpar>
```

---

## Regras

- Subagentes são read-only na Fase 1 — nenhum delete antes do relatório
- PRs abertos nunca são auto-fechados — sempre requerem ação manual
- CLAUDE.md nunca é modificado por este skill
- Nunca fazer push para main sem confirmar que docs foram revisados (Fase 3c)
- Se REPO_ROOT falhar no assert inicial: parar e reportar antes de qualquer operação
- Confirmar por seção — nunca fazer tudo de uma vez sem perguntar
