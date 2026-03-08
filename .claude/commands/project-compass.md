# /project-compass

Deriva o estado atual do projeto a partir de git e sprint.md — sem armazenar estado em nenhum arquivo.
Use a qualquer momento que você quiser saber: "onde estamos?", "o que falta?", "qual a próxima feature?".

**Argumento opcional:** `$ARGUMENTS` — nome do projeto. Se omitido, detecta automaticamente.

---

## Fase 0 — Identificar projeto

Se `$ARGUMENTS` foi fornecido, use como nome do projeto.

Senão, detectar automaticamente:

```bash
# Listar projetos disponíveis (excluindo 'archived')
ls .claude/feature-plans/ | grep -v archived
```

Se houver exatamente um diretório, usar esse.
Se houver mais de um, listar e pedir ao usuário que especifique:

> "Encontrei múltiplos projetos: [lista]. Qual devo analisar?"

---

## Fase 1 — Carregar contexto (em paralelo)

Execute todas as leituras simultaneamente:

### 1a. Documentos do projeto

```bash
cat .claude/feature-plans/<projeto>/roadmap.md 2>/dev/null || echo "(sem roadmap)"
```

Extrair: nome dos milestones, objetivos, critérios de done.

### 1b. Sprint files de todos os milestones

```bash
cat .claude/feature-plans/<projeto>/M*/sprint.md 2>/dev/null || echo "(sem sprint files)"
```

Para cada sprint.md encontrado, extrair:
- Nome do milestone (ex: `M1 — MVP`)
- Objetivo e critério de done
- Features e respectivos status (`✅ done`, `pending`, `in_progress` ou checkboxes `- [ ]` / `- [x]`)

### 1c. Backlog JSON

```bash
cat .claude/backlog.json 2>/dev/null || echo "(sem backlog.json)"
```

Se existir: extrair milestones com status, features por milestone com status e path, pitches pendentes, e `chores[]` com data, prNumber, itens e status de cada sessao de polish.

### 1d. PRs merged (features entregues)

```bash
gh pr list --state merged --json number,title,headRefName,mergedAt --limit 50
```

Filtrar onde `headRefName` começa com `feature/`. Extrair slugs e datas.
Se `gh` não estiver autenticado, pular e anotar no relatório: "(PRs merged não verificados — `gh` não autenticado)"

### 1e. Branches de feature ativos (em andamento)

```bash
git branch -a | grep "feature/"
```

Extrair slugs das branches locais e remotas.

---

## Fase 2 — Cruzar dados

Construir visão por milestone:

**Fonte de status (prioridade):**
1. Se `backlog.json` existe: usar como fonte primária de status das features
   - `status=in-progress` → em andamento
   - `status=done` → done
   - `status=pending` → pendente
   - sprint.md complementa com detalhes de decomposição
2. Se não existe backlog.json: inferir pelo cruzamento de sprint.md + PRs merged + branches

Para cada milestone (M1, M2, M3, ...):
1. Listar features (de backlog.json ou sprint.md)
2. Marcar como **done** se: `status=done` no backlog, OU `✅ done` / `- [x]` no sprint.md, OU PR merged com slug correspondente
3. Marcar como **em andamento** se: `status=in-progress` no backlog, OU branch `feature/<slug>` existe E não merged
4. Marcar como **pendente** se: nenhuma das condições acima

**Milestone atual** = primeiro milestone com status `active` no backlog, ou primeiro com features pendentes/em andamento.

Se todos os milestones estão 100% done: reportar conclusão do projeto.

---

## Fase 3 — Gerar relatório

```text
## 🧭 Project Compass — <projeto>
_<data e hora atual>_

---

### 📍 Onde estamos

**Milestone atual:** <nome e número> — <objetivo em 1 frase>

Progresso: <N>/<M> features concluídas

| Feature | Status |
|---------|--------|
| <slug> | ✅ done |
| <slug> | 🔄 em andamento (branch: feature/<slug>) |
| <slug> | ⏳ pendente |

**Critério de done deste milestone:** <texto do sprint.md>

---

### ✅ O que foi construído

Features entregues (todos os milestones):

| Milestone | Feature | PR | Data |
|-----------|---------|-----|------|
| M1 | <slug> | #<n> | <data> |
| M2 | <slug> | #<n> | <data> |

---

### ⏳ O que fazer agora

**Próxima feature:** `<slug>` — <descrição do sprint.md>

Dependências: <deps do sprint.md, ou "nenhuma">

Bloqueios abertos: <PRs abertos em review, ou "nenhum">

---

### 💡 Pitches (se houver no backlog.json)

| Pitch | Problema | Status |
|-------|---------|--------|
| <título> | <problema curto> | awaiting-bet |

_(Omitir esta seção se não houver pitches no backlog.json)_

---

### 🧹 Chores recentes (se houver no backlog.json)

| Data | PR | Itens | Status |
|------|-----|-------|--------|
| <YYYY-MM-DD> | #N | K itens | merged / open |

_(Omitir esta seção se `chores[]` estiver vazio ou ausente no backlog.json)_

---

### ▶ Próxima ação

/start-feature <slug>

<Contexto adicional em 1-2 frases, se relevante.>
```

---

## Quando usar

Rode `/project-compass` quando:

- Começar uma nova sessão de trabalho e quiser saber por onde continuar
- Sentir que está driftando do plano original
- Quiser confirmar que o milestone está progredindo bem
- Após um `/close-feature`, para ver o estado atualizado
- Quando alguém perguntar "o que falta para este milestone?"

**Frases-gatilho:** "onde estamos", "o que falta", "próxima feature", "estou driftando", "status do projeto"

---

## Notas de implementação

- **Nunca escrever em nenhum arquivo** — o estado é sempre derivado, nunca armazenado
- Se um sprint.md não tiver coluna `Status`, inferir pelo cruzamento com PRs merged e branches ativas
- Se não houver sprint.md para um milestone, reportar como "sem sprint planejado"
- Datas de PRs merged devem ser exibidas no formato `YYYY-MM-DD`
