# /start-milestone

Decompõe um milestone do roadmap em features implementáveis com escopo fechado, gera um `sprint.md` ordenado por dependências,
e prepara o terreno para o `/start-feature` saber exatamente o que executar em seguida.

**Argumento:** `$ARGUMENTS` — nome do milestone (ex: `M1`, `M2`) e opcionalmente o slug do projeto (ex: `M2 claude-terminal`). Se não fornecido, será detectado automaticamente.

---

## Fase 0 — Detecção

**1. Nome do projeto:**
- Se `$ARGUMENTS` contém dois tokens (ex: `M2 claude-terminal`), o segundo é o slug do projeto.
- Caso contrário, liste os diretórios em `.claude/feature-plans/` — se houver exatamente um, use-o.
- Se houver ambiguidade (múltiplos diretórios), pergunte ao usuário.

**2. Nome do milestone:**
- Extraia do primeiro token de `$ARGUMENTS` (ex: `M2`).
- Se `$ARGUMENTS` estiver vazio, liste os milestones pendentes do `roadmap.md` e pergunte qual executar.

**3. Verifique se `sprint.md` já existe** em `.claude/feature-plans/<projeto>/<milestone>/sprint.md`:
- **Se existe** → entre em **modo revisão**: mostre o sprint atual, pergunte o que mudou, e siga para a Fase 3 incorporando o feedback.
- **Se não existe** → execute o fluxo completo a partir da Fase 1.

**4. Carregue o roadmap:**
Leia `.claude/feature-plans/<projeto>/roadmap.md`. Se não existir:

- Verificar se `.claude/backlog.json` existe:
  - Se sim: ler e listar milestones com `"status": "pending"` ou `"status": "active"` como alternativa ao roadmap
  - Informar ao usuário e perguntar se quer prosseguir com backlog.json ou primeiro criar o roadmap
- Se também não existir backlog.json: informar:
  ```text
  roadmap.md não encontrado. Rode /plan-roadmap antes de /start-milestone.
  ```

---

## Fase 1 — Decomposição em features

Leia a seção do milestone especificado no roadmap.md. Para cada item (`- [ ]`), decomponha em **2–4 features implementáveis** seguindo a régua abaixo.

**Régua de granularidade — uma feature está bem-scoped quando:**
- Toca **1–3 arquivos principais**
- Tem um **"demonstrável" claro**: tela que aparece, teste que passa, endpoint que responde, comando que funciona
- Pode ser implementada em **1 sessão de Claude Code** sem `/clear` intermediário
- **Nome kebab-case** descreve o QUÊ (noun+verb ou domain+noun), não o PORQUÊ

**Como decompor:**
- Um item de roadmap com impacto alto/esforço baixo → geralmente 1–2 features
- Um item com esforço médio → 2–3 features (separar model/service de view/UI)
- Um item com esforço alto → 3–4 features (separar por camada ou por fase do fluxo)
- Se o item toca model/service + UI → separar sempre (model vem antes)
- Se o item toca múltiplos fluxos de usuário → separar por fluxo

**Dependências:** uma feature B depende de A quando B usa um model, service ou protocolo definido em A. Se A não existir, B não compila ou não funciona.

**Ordem de execução:** esforço menor e menos dependências vêm primeiro. Features independentes podem ser listadas em qualquer ordem entre si.

---

## Fase 2 — Apresentação e validação

Apresente a decomposição ao usuário **antes de escrever qualquer arquivo**:

````text
## Decomposição — <Milestone>: <nome>

**Critério de done do milestone:** <critério do roadmap.md>

| # | Feature | Slug | Deps | Esforço |
|---|---------|------|------|---------|
| 1 | <descrição 1 linha> | `<slug>` | — | baixo |
| 2 | <descrição 1 linha> | `<slug>` | `<slug-dep>` | baixo |
| 3 | <descrição 1 linha> | `<slug>` | `<slug-dep>` | médio |
...

**Grafo de dependências:**
```
<slug-a> → <slug-b>
<slug-a>, <slug-c> → <slug-d>
```

**Primeira feature a executar:** `/start-feature <slug-1>`

Confirma essa decomposição? (ou me diga o que ajustar — posso fundir, dividir ou reordenar features)
````

Aguarde confirmação antes de continuar. Se o usuário pedir ajustes, incorpore e apresente novamente antes de escrever.

---

## Fase 3 — Geração do sprint.md

Após confirmação, crie o diretório `.claude/feature-plans/<projeto>/<milestone>/` se não existir, e salve o `sprint.md`:

````markdown
# Sprint <Milestone> — <nome do milestone>
_Gerado em: <data>_

> Status ao vivo: use /project-compass. Este arquivo é readonly após criação.

## Milestone

**Objetivo:** <meta/critério do roadmap.md>
**Critério de done:** <critério concreto do roadmap.md>

## Features (ordem de execução)

| # | Feature | Slug | Deps | Esforço | Status |
|---|---------|------|------|---------|--------|
| 1 | <descrição> | `<slug>` | — | baixo | pending |
| 2 | <descrição> | `<slug>` | `<dep>` | baixo | pending |
| 3 | <descrição> | `<slug>` | `<dep>` | médio | pending |
...

## Grafo de dependências

```
<slug-a> → <slug-b>
<slug-b>, <slug-c> → <slug-d>
```

## Critério de granularidade

Uma feature está bem-scoped quando:
- Toca 1–3 arquivos principais
- Tem um "demonstrável" claro (tela que aparece, teste que passa, endpoint que responde)
- Pode ser implementada em 1 sessão de Claude Code sem `/clear` intermediário
- Nome kebab-case descreve o QUÊ, não o PORQUÊ

## Próximo passo

/start-feature <slug-da-feature-1>
````

### Atualizar backlog.json (se existir)

Se `.claude/backlog.json` existir:

1. Verificar se o milestone já está no array `milestones`:
   - Se não: adicionar `{"id": "<m-id>", "name": "<nome>", "objective": "<objetivo>", "status": "active", "completedAt": null}`
   - Se sim: atualizar `"status": "active"` se ainda não estiver
2. Para cada feature confirmada na decomposição:
   - Verificar se já existe no array `features` (por `id`)
   - Se não: adicionar `{"id": "<slug>", "title": "<descrição>", "status": "pending", "milestone": "<m-id>",`
     `"path": null, "dependencies": [<deps>], "branch": null, "prNumber": null, "startedAt": null, "completedAt": null, "createdAt": "<ISO-8601>"}`
3. Validar: `python3 -m json.tool .claude/backlog.json > /dev/null`

Se backlog.json não existir: pular (não criar automaticamente).

> **Nota de arquitetura:**
> `sprint.md` é um artefato de **planejamento** — define a decomposição e ordem de execução.
> Não é atualizado durante a execução. Não use os checkboxes do sprint.md para tracking.
>
> `backlog.json` é a **fonte de verdade de status** — atualizado por /start-feature (in-progress)
> e /close-feature (done). Use /project-compass para ver o estado real.

---

## Fase 4 — Confirmação

Após salvar, exiba:

```text
sprint.md salvo em .claude/feature-plans/<projeto>/<milestone>/

<Milestone> — <N> features mapeadas:
  1. `<slug-1>` — <descrição curta>
  2. `<slug-2>` — <descrição curta> (após <slug-1>)
  ...

Próximo passo: /start-feature <slug-1>
```

---

## Quando NÃO usar

- **Antes de `/plan-roadmap`** — sprint.md pressupõe roadmap.md com milestones definidos
- **Para features avulsas** fora de um milestone — use `/start-feature <nome>` diretamente
- **Para replanejar o produto inteiro** — use `/plan-roadmap` (revisão de roadmap)
- **Para um milestone já 100% done** — não há o que decompor

---

## Testes

| Cenário | Input | Output esperado |
|---------|-------|-----------------|
| Fluxo normal | `/start-milestone M2` | Decomposição apresentada → confirmação → sprint.md criado |
| Com slug explícito | `/start-milestone M2 claude-terminal` | Mesma coisa, sem perguntar nome do projeto |
| Sem argumento | `/start-milestone` | Lista milestones pendentes do roadmap e pergunta qual |
| sprint.md existe | `/start-milestone M2` | Modo revisão: mostra sprint atual e pergunta o que mudou |
| roadmap.md ausente | `/start-milestone M1` | Erro claro: rode /plan-roadmap primeiro |
| Negativo: feature avulsa | `/start-milestone login-feature` | Identifica que não é milestone → avisa e pergunta se quer `/start-feature login-feature` |
