# /start-feature

Você é um assistente de desenvolvimento executando o skill `/start-feature`.

O argumento passado é o nome ou descrição da feature: $ARGUMENTS

---

## Detecção de fase

### 1. Identificar nome e flag

Parsear `$ARGUMENTS`:
- `--discover [<nome>]` → flag discover
- `--deep [<nome>]` → flag deep
- `--novel [<nome>]` → flag novel (pode combinar: `--discover --novel`, `--deep --novel`)
- `--fast [<nome>]` → alias silencioso de default (sem flag)
- `<nome>` simples → sem flag
- vazio → perguntar nome (ver abaixo)

**Se sem nome:**

1. Verificar `.claude/backlog.json`:
   - Se existir: ler e identificar a primeira feature com `"status": "pending"` que não tenha worktree criada (`git branch -a | grep feature/<slug>`)
   - Se não existir: procurar `sprint.md` em `.claude/feature-plans/*/<milestone>/sprint.md` e identificar primeiro `- [ ]` sem worktree
   - Apresentar sugestão e aguardar confirmação antes de continuar
2. Se nem backlog.json nem sprint.md existirem: perguntar o nome curto (kebab-case)

### 2. Detectar fase pelo estado de arquivos

Verificar `.claude/feature-plans/<nome>/`:

| Condição | Fase |
|---|---|
| `plan.md` existe | Fase C — Execução |
| `research.md` existe, `plan.md` não | Fase B — Planejamento |
| `discovery.md` existe, `research.md` não | Fase A — Pesquisa |
| Nenhum arquivo existe + flag `--discover` | Fase 0 — Discovery |
| Nenhum arquivo existe + flag `--deep` | Fase A — Pesquisa (full workflow) |
| Nenhum arquivo existe + sem flag (default) | Fase C fast — Execução direta |

> **`--novel`** pode ser combinada com qualquer fase (`--discover --novel`, `--deep --novel`).
> Quando ativa: substitui subagentes de web search por analogia por raciocínio de primeira ordem.
> Sem ela: a skill detecta automaticamente se web search retorna pouco e avisa.

---

## FASE 0 — Discovery (pitch mode)

> Executada com `--discover`. Termina sem criar worktree.
> Objetivo: definir o problema real antes de qualquer pesquisa técnica.

### Passo 0.1 — Pesquisa paralela (3 subagentes)

Lance os 3 subagentes simultaneamente com Task tool (`run_in_background=true`).

**Subagente A — Codebase:**
> Leia o CLAUDE.md do projeto para entender stack e convenções.
> Leia os hot files listados no CLAUDE.md + arquivo de configuração central.
> Identifique o módulo mais próximo ao problema descrito em: `<feature descrita>`.
> Retorne: o que já existe no projeto que resolve parcialmente o problema, pontos de extensão naturais, dependências internas relevantes.

**Subagente B — Web / First-principles:**

Se `--novel` está ativo **ou** se o web search anterior não encontrou precedentes relevantes:
> Você é um raciocinádor de primeira ordem. NÃO faça web search por produtos similares.
> Execute este chain of thought para `<feature descrita>`:
>
> **Etapa 1 — Desconstrução em primitivos**
> Reduza o objetivo a pré/pós-condições em linguagem não-técnica, sem mencionar soluções.
> "Para que este problema esteja resolvido, o que precisa ser verdade?"
>
> **Etapa 2 — Suposições implícitas**
> Liste 5+ suposições implícitas sobre como resolver isso.
> Para cada uma: "Suposição: [X]. Precisa ser verdade? [Sim/Não/Talvez — porque...]"
>
> **Etapa 3 — Restrições reais vs. convencionais**
> Separe: (a) restrições físicas/lógicas — impossível contornar; (b) restrições convencionais — candidatas a desafiar.
>
> **Etapa 4 — Construção ascendente**
> A partir das pós-condições (Etapa 1) e restrições reais (Etapa 3), derive a solução de baixo para cima.
> Sem citar produtos ou implementações existentes.
>
> **Etapa 5 — Análogos estruturais (domínios não-tech)**
> Identifique problemas em física, biologia, design, economia com a mesma estrutura lógica.
> Para cada análogo: "O que transfere para nossa solução?"
>
> Retorne: síntese das 5 etapas + 2-3 abordagens derivadas do raciocínio.

Se `--novel` **não** está ativo:
> Pesquise como produtos similares resolvem: `<feature descrita>`.
> Foco: padrões de UX estabelecidos, alternativas, trade-offs documentados em 2025-2026.
> Retorne: 2-3 abordagens com prós e contras.
> **Se não encontrar nada relevante** (feature parece inédita): retorne `SEM_PRECEDENTES` + o que tentou buscar.

**Subagente C — Tech estimate:**
> Com base em `<feature descrita>` e no stack (leia CLAUDE.md):
> Estime complexidade (P/M/G), riscos técnicos principais, dependências não óbvias, decisões que criam dívida técnica.

Aguardar com `TaskOutput`. Sintetizar antes de continuar.

### Passo 0.2 — Síntese inicial

Se o Subagente B retornou `SEM_PRECEDENTES` e `--novel` **não** estava ativo:

```text
⚠️  Web search não encontrou precedentes relevantes para "<feature>".
Esta pode ser uma feature inédita. Sugestão: rode /start-feature --discover --novel <nome>
para ativar raciocínio de primeira ordem em vez de busca por analogias.

Continuar mesmo assim? (sim = prosseguir com o que foi encontrado; não = encerrar)
```

Aguardar resposta antes de continuar.

Caso contrário, apresentar:

```text
## Entendimento atual

<síntese dos 3 subagentes>

## Suposições que podem estar erradas

1. <suposição A>
2. <suposição B>
3. <suposição C — se houver>
```

### Passos 0.3–0.5 — Rodadas de perguntas

> **Regra de intake:** Uma pergunta por vez. Prefira múltipla escolha quando possível.
> Aguardar resposta antes de fazer a próxima.

Fazer **no máximo 3 perguntas por rodada**, aguardar resposta antes de continuar.

- **0.3 Problema:** o que existe no codebase/produto que toca isso; o que está faltando; para quem
- **0.4 Alternativas:** tentativas anteriores que não funcionaram; restrições; trade-offs preferidos
- **0.5 Escopo:** limites explícitos; critério de sucesso mensurável; prazo ou dependências externas

### Passo 0.6 — Gerar discovery.md

Salvar em `.claude/feature-plans/<nome>/discovery.md`:

````markdown
# Discovery: <nome>
_Gerado em: <data>_

## Problema real
[descrição precisa — não a solução]

## Usuário / contexto
[quem sente a dor, em qual situação]

## Alternativas consideradas
| Opção | Por que não basta |
|---|---|
| | |

## Por que agora
[motivação: o que muda se não fizer]

## Escopo da feature
### Dentro
- [item]

### Fora (explícito)
- [item — tão importante quanto o dentro]

## Critério de sucesso
- [métrica ou comportamento observável]

## Riscos identificados
[da pesquisa dos subagentes — Passo 0.1]

## Handoff

next_skill: /start-feature --deep <nome>

carry_forward:
- [problema real]: <uma frase — minimal sufficient statistic do problema>
- [escopo dentro]: <itens principais que estão no escopo>
- [escopo fora]: <exclusões explícitas>
- [critério de sucesso]: <comportamento observável>
- [decisões já tomadas]: <o que não precisa ser re-pesquisado na próxima fase>

excluded:
- [alternativas descartadas e por quê — previne re-descoberta]

invalidated:
- [o que ficaria stale se task_definition mudar substancialmente]

gate: não
<!-- gate: sim = pre-bet decision permanece humano; não = próxima skill lê ## Handoff automaticamente por path convention -->
````

Ao final:

```text
discovery.md salvo em .claude/feature-plans/<nome>/

Próximo passo: Fase A (Pesquisa técnica)
Recomendo /clear antes de continuar — rode /start-feature --deep <nome> para pesquisa completa,
ou /start-feature <nome> para execução direta com o discovery como contexto.

────────────────────────────────────────────────
Cole na nova sessão após /clear:

Feature "<nome>" — Discovery concluído.
Contexto salvo em: .claude/feature-plans/<nome>/discovery.md
Próximo comando: /start-feature --deep <nome>
────────────────────────────────────────────────
```

---

## FASE A — Pesquisa (`--deep`)

### Passo A.1 — Coletar contexto

Se `discovery.md` existir: ler o `## Handoff` section.
Se `## Handoff` não existir: ler o arquivo inteiro e emitir `⚠️ discovery.md sem Handoff block — lendo artefato completo`.
Os campos `carry_forward` do Handoff block suprimem as perguntas padrão.

Se não existir ou faltar contexto:
- O que a feature faz?
- Alguma restrição técnica conhecida?

### Passo A.2 — Subagentes em paralelo

Lance os 3 subagentes simultaneamente com Task tool (`run_in_background=true`).

**Subagente A — Codebase reader:**
> Leia CLAUDE.md + hot files + CI workflow principal + arquivo de configuração central.
> Leia o módulo mais próximo da feature.
> Se existir `discovery.md`: use "Problema real" e "Escopo" para focar nos arquivos mais relevantes.
> Retorne: arquivos relevantes, padrões a seguir, dependências externas necessárias, armadilhas do CLAUDE.md aplicáveis.

**Subagente B — Conflict checker:**
> Verifique se `.claude/agent-memory/coordinator/MEMORY.md` existe.
> Se existir: identifique hot files com claim ativo, worktrees com sobreposição, ordem de merge recomendada.
> Se não existir: retorne "Sem coordenador ativo — sem conflitos a reportar".

**Subagente C — Web researcher / First-principles** (somente se a feature usa libs/APIs externas ou `--novel` está ativo):

Se `--novel` está ativo:
> Você é um raciocinádor de primeira ordem. Execute o chain of thought abaixo para `<feature descrita>`.
> Foco: arquitetura técnica — não UX/produto. Parta dos primitivos do stack (leia CLAUDE.md).
>
> **Etapa 1 — Primitivos técnicos**
> Quais operações fundamentais (I/O, transformação, sincronização, armazenamento) compõem o núcleo desta feature?
> Liste em termos de primitivos do sistema, sem citar bibliotecas.
>
> **Etapa 2 — Suposições de implementação**
> Liste 5+ suposições sobre como implementar isso.
> "Suposição: [X]. Precisa ser verdade dado o stack? [Sim/Não — porque...]"
>
> **Etapa 3 — Restrições do stack**
> Dado o stack declarado no CLAUDE.md: quais restrições são impostas pela plataforma/linguagem? Quais são apenas convenções?
>
> **Etapa 4 — Construção a partir do stack**
> Derive a abordagem de implementação usando apenas os primitivos do stack identificados.
>
> **Etapa 5 — Onde libs externas ajudam vs. atrapalham**
> Para cada componente da Etapa 4: "Há uma lib que resolve exatamente isso sem overfit? Ou a construção própria é mais limpa?"
>
> Retorne: arquitetura derivada + lista comentada de libs (usar / não usar / construir próprio).

Se `--novel` **não** está ativo (comportamento padrão):
> Pesquise boas práticas para `<tecnologia/API relevante>`.
> Foco: padrões de integração 2025-2026, armadilhas, versões estáveis.
> **Se não encontrar nada relevante** (feature parece inédita): retorne `SEM_PRECEDENTES_TECH` + o que tentou buscar.

Aguardar com `TaskOutput`. Sintetizar resultados.

### Passo A.3 — Identificar hot files

Marcar com ⚠️ arquivos que a feature vai tocar e que são hot files (do CLAUDE.md). Cruzar com Subagente B.

### Passo A.4 — Salvar research.md

Criar `.claude/feature-plans/<nome>/research.md`:

````markdown
# Research: <nome>

## Descrição da feature
<o que faz, por que, contexto>

## Arquivos existentes relevantes
- `path/to/file` — <por que é relevante>

## Padrões identificados
<convenções do projeto que a feature deve seguir>

## Dependências externas
<libs, APIs, secrets necessários — ou "nenhuma">

## Hot files que serão tocados
- `arquivo` — <motivo> [⚠️ CONFLITO POTENCIAL se outro agente já toca]

## Riscos e restrições
<armadilhas identificadas, limitações, pontos de atenção>

## Fontes consultadas
<URLs do WebSearch, se usadas>

## Handoff

next_skill: /start-feature <nome>

carry_forward:
- [arquitetura decidida]: <abordagem escolhida e por quê>
- [hot files]: <arquivos que serão tocados>
- [constraints técnicos]: <o que é irredutível — não pode mudar>
- [decisão arquitetural principal]: <a escolha mais importante desta fase>

excluded:
- [abordagens técnicas pesquisadas mas descartadas — previne re-pesquisa]

invalidated:
- [o que ficaria stale se o escopo ou stack mudar]
````

Ao final:

```text
research.md salvo em .claude/feature-plans/<nome>/

Próximo passo: Fase B (Planejamento)
Recomendo /clear antes de continuar — rode /start-feature <nome> novamente.

────────────────────────────────────────────────
Cole na nova sessão após /clear:

Feature "<nome>" — Research concluído.
Contexto salvo em: .claude/feature-plans/<nome>/research.md
Próximo comando: /start-feature <nome>
────────────────────────────────────────────────
```

---

## FASE B — Planejamento

### Passo B.1 — Ler a pesquisa

Ler `.claude/feature-plans/<nome>/research.md` integralmente.

### Passo B.2 — Montar plano de execução

Para cada mudança: arquivo exato, o que fazer (específico), ordem de execução, como reverter.

### Passo B.3 — Checklist de infraestrutura

- [ ] Novo Secret: <não / qual>
- [ ] Script de setup: <não / o que faz>
- [ ] CI/CD: <não muda / o que muda>
- [ ] Config principal: <não muda / o que muda>
- [ ] Novas dependências: <não / quais>

### Passo B.4 — Validar contra LEARNINGS.md (se existir)

Se `LEARNINGS.md` existir: lançar subagente `Explore` para ler e identificar learnings com impacto no plano. Incorporar ajustes e adicionar seção `## Learnings aplicados` no plan.md.

### Passo B.5 — Salvar plan.md e perguntar

Salvar em `.claude/feature-plans/<nome>/plan.md`:

````markdown
# Plan: <nome>

## Problema
<Descrição do problema — usada pelo /validate para verificar alinhamento.>

## Assunções
<!-- status: [assumed] = não verificada | [verified] = confirmada | [invalidated] = refutada -->
<!-- risco:   [blocking] = falsa bloqueia a implementação | [background] = emerge naturalmente -->
- [assumed][blocking] <assunção crítica — ex: "o endpoint X retorna o campo Y que precisamos">
- [assumed][background] <assunção menor — ex: "SwiftData suporta query por este tipo de predicado">

<!-- opcional para features simples: remover se não houver assunções relevantes -->

## Questões abertas
<!-- Triple-bucket RFC-style. Remover buckets vazios. -->

**Resolver antes de começar (human gate now):**
- <questão que bloqueia o passo 1 se não respondida>

**A implementação vai responder (monitorar):**
- <questão que o código em si vai validar ou refutar>

**Explicitamente fora do escopo (evitar scope creep):**
- <o que não vai ser feito nesta feature>

<!-- opcional para features simples: omitir esta seção inteira se não houver questões abertas -->

## Deliverables

### Deliverable 1 — Walking Skeleton
**O que faz:** <integração ponta-a-ponta mínima — o menor pedaço que conecta todas as camadas>
**Critério de done:** <comportamento observável concreto — o que o usuário/dev consegue ver/testar>
**Valida:** <assunção 1>, <assunção 2>
**Resolve:** <questão aberta que este deliverable fecha>
**Deixa aberto:** <questão que só o Deliverable 2 vai responder>

**⚠️ Execute `/checkpoint` antes de continuar para o Deliverable 2.**

### Deliverable 2 — <nome>
**O que faz:** <funcionalidade completa deste incremento>
**Critério de done:** <comportamento observável>
**Valida:** <assunção N>
**Resolve:** <questão aberta que este deliverable fecha>
**Deixa aberto:** <questão que só o próximo deliverable vai responder — ou "nada">

**⚠️ Execute `/checkpoint` antes de continuar para o Deliverable 3.**

<!-- Adicionar mais deliverables se necessário. Remover a linha ⚠️ e "Deixa aberto" do último deliverable. -->
<!-- opcional para features simples: usar apenas Deliverable 1 sem /checkpoint -->

## Arquivos a modificar
- `path/to/file` — <o que fazer exatamente>

## Passos de execução
<!-- Referenciar os deliverables em ordem. Cada bloco termina com /checkpoint (exceto o último). -->
1. <Passo 1 — arquivo exato, função, o que criar/editar> [Deliverable 1]
2. <Passo 2 — idem> [Deliverable 1]
3. ⚠️ Execute `/checkpoint` — Deliverable 1 concluído
4. <Passo 4 — arquivo exato, função, o que criar/editar> [Deliverable 2]
5. <Passo 5 — idem> [Deliverable 2]

## Checklist de infraestrutura
- [ ] Novo Secret: <não / qual>
- [ ] Script de setup: <não / o que faz>
- [ ] CI/CD: <não muda / o que muda>
- [ ] Config principal: <não muda / o que muda>
- [ ] Novas dependências: <não / quais>

## Rollback
<Como reverter — comandos concretos>

## Learnings aplicados
<Lista de learnings relevantes — ou "nenhum impacto identificado">
````

Apresentar e aguardar:

```text
plan.md salvo em .claude/feature-plans/<nome>/

Executar agora ou /clear primeiro?
- Executar agora — contexto ainda é válido
- /clear — recomendado se a sessão está longa (rode /start-feature <nome> para retomar na Fase C)

────────────────────────────────────────────────
Cole na nova sessão após /clear (se optar por limpar):

Feature "<nome>" — Plan pronto.
Contexto salvo em: .claude/feature-plans/<nome>/plan.md
Próximo comando: /start-feature <nome>
────────────────────────────────────────────────
```

---

## FASE C — Execução

### Passo C.1 — Ler o plano

Ler `.claude/feature-plans/<nome>/plan.md` integralmente.

**Se não existir plan.md (Fase C fast):**
1. Ler CLAUDE.md + arquivos mais relevantes (sem subagentes — leitura direta)
2. Fazer 1-2 perguntas: "o que a feature deve fazer?" + "quais arquivos serão tocados?"
3. Gerar mini plan.md (problema + assunções principais + deliverables simplificados + passos concretos + rollback mínimo)
4. Mostrar ao usuário para confirmação rápida
5. Prosseguir para C.2

### Passo C.2 — Verificar coordinator (se existir)

Se `.claude/agent-memory/coordinator/MEMORY.md` existir:

```bash
REPO_ROOT=$(git worktree list | head -1 | awk '{print $1}')
MEMORY_FILE="$REPO_ROOT/.claude/agent-memory/coordinator/MEMORY.md"
git -C "$REPO_ROOT" pull --rebase origin main
```

Verificar hot file claims. Se conflito: alertar com opções (aguardar / reduzir escopo / prosseguir).

Editar MEMORY_FILE e commitar imediatamente:

```bash
git -C "$REPO_ROOT" add .claude/agent-memory/coordinator/MEMORY.md
git -C "$REPO_ROOT" commit -m "chore(coordinator): register worktree <nome> + claim hot files"
git -C "$REPO_ROOT" push origin main || (git -C "$REPO_ROOT" pull --rebase origin main && git -C "$REPO_ROOT" push origin main)
```

### Passo C.3 — Criar worktree

Verificar worktrees abertas:

```bash
git worktree list | tail -n +2 | wc -l
```

Se ≥ 5: emitir aviso e aguardar confirmação do usuário antes de prosseguir.

**ASSERT antes de prosseguir:** confirmar que a branch não existe no remote antes de criar a worktree.

```bash
git ls-remote --heads origin worktree-<nome>
```

- Se retornar output (branch já existe no remote): **PARAR** e perguntar ao usuário — pode ser uma worktree de sessão anterior. Opções: retomar a branch existente ou criar com nome diferente.
- Se retornar vazio: prosseguir normalmente.

**Se a branch ja existir no remote: PARAR e reportar ao usuario.**

Criar: `EnterWorktree name=<nome>`

### Passo C.4 — Atualizar backlog.json

Se `.claude/backlog.json` existir e `command -v jq` disponível:

```bash
TODAY=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
BRANCH=$(git branch --show-current)
jq --arg id "<nome>" \
   --arg date "$TODAY" \
   --arg branch "$BRANCH" \
   '(.features[] | select(.id == $id)) |= . + {status: "in-progress", startedAt: $date, branch: $branch}' \
   .claude/backlog.json > .claude/backlog.json.tmp && mv .claude/backlog.json.tmp .claude/backlog.json
```

Se jq não disponível: pular silenciosamente (não bloquear).

### Passo C.5 — Executar o plano

Mostrar apenas um resumo de uma linha e começar o passo 1.

Regras:
- Executar cada passo completamente antes do próximo
- Ler estado atual de cada arquivo antes de editar — nunca editar às cegas
- Confirmar cada passo com "✅ Passo N concluído" e continuar sem parar
- Se um passo falhar: diagnosticar, tentar corrigir; parar só após 2 tentativas sem sucesso
- Se há outros agentes ativos: fazer push imediatamente após cada commit
- **Não pedir confirmação entre passos — executar autonomamente**
- **Ao encontrar um passo `⚠️ Execute /checkpoint` no plan.md: invocar `/checkpoint` e PARAR até receber resposta humana — nunca pular ou auto-responder**
- Executar os passos na ordem dos Deliverables: concluir todos os passos de um deliverable antes de avançar para o próximo

### Passo C.6 — Build + testes automáticos

Lançar em background (`run_in_background=true`):

- Build (comando definido no CLAUDE.md — ex: `swift build`, `make check`, `npm run build`)
- Suite de testes automatizados se disponível (ex: `swift test`, `make test`, `npm test`)

Enquanto aguarda: exibir resumo (arquivos criados/editados, decisões tomadas).

Resultado:
- ✅: prosseguir para C.7
- ❌: exibir erro completo, corrigir, repetir C.6 — **nunca avançar para C.7 com build quebrado**

### Passo C.7 — Checklist de testes para o usuário

Classificar os comportamentos introduzidos ou modificados pela feature em duas categorias:

**Claude Code pode testar automaticamente:**
- Compilação e build
- Suite de testes unitários/integração existente
- Linters e checks estáticos (`make check`, etc.)
- Saída de CLI/scripts verificável no terminal

**Requer o usuário (Claude Code não consegue testar):**
- UI e visual — aparência, layout, animações
- Fluxos de interação — clicar, navegar, sequências encadeadas
- Diálogos e permissões do OS — alerts, autorizações, notificações
- Integrações com serviços externos ativos — APIs reais, sockets live
- Edge cases visuais — dark mode, tamanhos de janela, estados de erro visíveis

Gerar apenas os checks relevantes para **esta feature específica** — não uma lista genérica.

Formato obrigatório:

```text
## Testes automáticos — OK ✅
- Build: verde
- <suite de testes>: X/X passed

## Testes manuais — necessários antes do /ship-feature

Como rodar o app: <comando concreto ou "abrir no Xcode → Run target X">

- [ ] <ação concreta> → <resultado esperado>
- [ ] <ação concreta> → <resultado esperado>
- [ ] <ação concreta> → <resultado esperado>

Quando todos os checks estiverem marcados: rode /ship-feature
```

Aguardar confirmação do usuário ("OK", "testei", ou similar) antes de encerrar a sessão.
Não sugerir `/ship-feature` antes dessa confirmação.

---

## Quando usar sem roadmap

Se você está em um projeto existente e quer adicionar uma feature específica,
não precisa ter roadmap.md ou sprint.md. Rode diretamente:

```text
/start-feature <nome>
```

O skill detecta ausência de plan.md, faz 1-2 perguntas rápidas, gera um mini plan.md
e executa. Tudo na mesma sessão, sem /clear.

Use o fluxo completo (`--deep` ou `--discover`) quando houver incerteza técnica
ou o problema ainda não estiver bem definido.

---

## Flags — referência rápida

| Flag | Comportamento | Caso de uso típico |
|---|---|---|
| (nenhuma) | Fase C fast — execução direta com mini plan | Feature clara em projeto existente, sem roadmap necessário |
| `--deep` | Fase A → B → C — workflow completo | Feature complexa, múltiplos arquivos, incerteza técnica |
| `--discover` | Fase 0 — pitch, para antes da worktree | Ainda explorando o problema, sem bet |
| `--novel` | First-principles em vez de web search | Feature inédita, sem precedentes |
| `--fast` | Alias de (nenhuma) — depreciado | Substituído pelo default |

---

## Regras gerais

- Nunca criar worktree nas Fases 0, A ou B — worktree só na Fase C
- Se o nome não foi informado: perguntar antes de qualquer leitura de arquivo
- **Na Fase C: não parar entre passos pedindo confirmação — executar autonomamente**
- **MEMORY.md coordinator vai sempre para main via commit imediato — nunca deixar pendente**
- **`--fast` é depreciado** — comportamento agora é o default sem flag
- **`--novel` não é exclusivo de `--discover`** — funciona em qualquer fase que envolva pesquisa externa
- **Detecção automática de `SEM_PRECEDENTES`**: quando a skill detecta feature inédita sem `--novel`, sempre avisar e sugerir antes de prosseguir — nunca pular silenciosamente
