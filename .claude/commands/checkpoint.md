# /checkpoint

Você é um assistente de desenvolvimento executando o skill `/checkpoint`.

Este skill é um alignment point mid-feature. Objetivo: superficializar assunções embutidas antes que acumulem.

**Invariante:** sem input humano, o checkpoint não fecha — o agente NUNCA pode auto-responder.

---

## Passo 1 — Localizar a feature atual

```bash
git branch --show-current
```

Extrair o nome da feature do branch:
- Branch `feature/<nome>` → nome = `<nome>`
- Se não estiver num branch `feature/`: exibir aviso e encerrar:

  ```text
  ⚠️  Você não está num branch feature/. /checkpoint só funciona dentro de uma feature em andamento.
  Branch atual: <branch>
  ```

## Passo 2 — Carregar plan.md

Ler `.claude/feature-plans/<nome>/plan.md` integralmente.

Se não existir:

```text
⚠️  plan.md não encontrado em .claude/feature-plans/<nome>/plan.md
/checkpoint requer um plan.md com seções ## Assunções e ## Deliverables.
```

Encerrar.

## Passo 3 — Detectar deliverable atual

Verificar se existe `.claude/feature-plans/<nome>/checkpoints.md`.

Se existir: ler a última entrada para saber qual foi o último deliverable fechado.
Se não existir: este é o checkpoint do Deliverable 1.

Identificar o deliverable atual (próximo após o último fechado, ou o primeiro se for o início).

## Passo 4 — Resumir o que foi construído

Determinar o ponto de partida do git log:
- Se há entrada em `checkpoints.md`: usar o timestamp da última entrada como referência
- Se não há: usar o commit de criação do branch (`git log --oneline origin/main..HEAD`)

```bash
git log --oneline origin/main..HEAD
```

Lançar subagente `Explore` com instrução:
> Leia os arquivos modificados nesta branch desde o último checkpoint.
> Retorne: lista dos arquivos mudados + descrição em 2-3 frases do que foi construído — focando no comportamento observável, não nos detalhes de implementação.

Aguardar resultado do subagente.

## Passo 5 — Exibir contexto e fazer a pergunta

Ao extrair assunções do plan.md, separar por tag de risco:
- Assunções com `[blocking]` → grupo "⚠️ Blocking" (exibir primeiro)
- Assunções com `[background]` → grupo "Background" (exibir depois)
- Assunções com `[assumed]` sem tag de risco (plan.md antigo) → exibir sem agrupamento, como antes

Exibir para o usuário:

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/checkpoint — <nome da feature> · Deliverable <N>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## O que foi construído
<resumo do subagente — comportamento observável>

## Assunções que este deliverable deveria validar

⚠️ Blocking
- <assunções [blocking] do plan.md que este deliverable toca — omitir grupo se vazio>

Background
- <assunções [background] do plan.md que este deliverable toca — omitir grupo se vazio>

## O que este deliverable deixa em aberto
<conteúdo de "Deixa aberto:" do deliverable atual no plan.md — omitir seção se vazio>

## Questões abertas (do plan.md)
<!-- omitir esta seção inteira se ## Questões abertas não existir no plan.md -->
Resolver antes de começar: <lista — ou "nenhuma pendente">
A implementação vai responder: <lista — ou "nenhuma">

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
O que foi construído avança o outcome original?
Qual assunção ficou embutida sem ser verificada?

(responda para fechar o checkpoint — o agente aguarda sua resposta)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**PARAR AQUI. Aguardar resposta humana. Não continuar até receber input.**

## Passo 6 — Processar resposta

Após receber a resposta do usuário:

### 6a — Atualizar plan.md

Para cada assunção que o usuário confirmou como verificada: alterar `[assumed]` → `[verified]` no `plan.md`.

Para novas assunções mencionadas pelo usuário que não constavam no plan.md: adicionar na seção `## Assunções` com status `[assumed]`.

Se o usuário identificou drift de escopo: adicionar nota na seção `## Problema` do plan.md com prefixo `<!-- checkpoint-N: ... -->`.

Se o usuário mencionar que uma questão aberta foi resolvida ou refutada: mover o item do bucket "Resolver antes de começar" ou
"A implementação vai responder" para um novo bucket `**Resolvidas neste checkpoint:**` na seção `## Questões abertas` do plan.md.
Não inferir resolução — só mover se o usuário mencionar explicitamente.

### 6b — Registrar em checkpoints.md

Appender a seguinte entrada em `.claude/feature-plans/<nome>/checkpoints.md` (criar se não existir):

````markdown
## Checkpoint <N> — Deliverable <N>
_<timestamp ISO 8601>_

### O que foi construído
<resumo do subagente>

### Assunções validadas
- [verified] <assunção 1> — <confirmação do usuário>

### Assunções ainda em aberto
- [assumed] <assunção 2> — <razão de não ter sido validada ainda>

### Novas assunções identificadas
- [assumed] <assunção nova> — <contexto da resposta do usuário>

### Resposta do usuário
> <transcrição literal da resposta>
````

## Passo 7 — Fechar checkpoint

```text
✅ Checkpoint <N> fechado.

Assunções atualizadas no plan.md:
- [verified]: <lista>
- [assumed] novos: <lista ou "nenhum">

checkpoints.md atualizado em .claude/feature-plans/<nome>/checkpoints.md

Próximo: Deliverable <N+1> — <nome do próximo deliverable, ou "feature concluída — rode /validate">
```

---

## Regras

- **Nunca auto-responder à pergunta do Passo 5** — o agente que chamou `/checkpoint` deve parar e esperar input humano
- Se `plan.md` não tem seção `## Assunções`: exibir aviso mas continuar com a pergunta (o usuário pode ter criado o plan.md manualmente)
- Se `plan.md` não tem seção `## Deliverables`: exibir aviso mas continuar
- O skill não bloqueia a execução além do Passo 5 — após receber resposta, fecha rapidamente e retorna controle ao agente
- Timestamps sempre em ISO 8601 UTC: `date -u +"%Y-%m-%dT%H:%M:%SZ"`
