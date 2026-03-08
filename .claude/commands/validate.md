# /validate

Checkpoint de direção durante implementação: verifica se o código atual ainda resolve o problema original e cobre o plano aprovado. Invocar antes do `/ship-feature`, a qualquer ponto da Fase C.

<!-- Contexto de uso: agentes driftam silenciosamente do plano. Este comando conecta o código
ao problema definido na Fase A, antes de criar o PR. Não é substituto de testes técnicos —
essa responsabilidade é do /ship-feature. -->

**Argumento recebido:** $ARGUMENTS

---

## Antes de começar

**1. Detectar o nome da feature:**

- Se `$ARGUMENTS` for fornecido, usá-lo como nome da feature
- Senão, inferir do branch atual:
  ```bash
  git branch --show-current
  # Resultado esperado: "feature/<nome>" → nome = parte após "feature/"
  ```
- Se o branch não seguir o padrão `feature/<nome>`, pedir ao usuário que especifique:
  > "Não consegui inferir o nome da feature. Qual o nome? (ex: minha-feature)"

**2. Verificar existência do `plan.md`:**

- Procurar em `.claude/feature-plans/<nome>/plan.md`
- Se não existir: exibir este erro e parar:
  > "Nenhum `plan.md` encontrado em `.claude/feature-plans/<nome>/`. O `/validate` requer uma feature iniciada com `/start-feature`. Se a feature existe, especifique o nome manualmente: `/validate <nome>`"

---

## O que fazer

### Passo 1 — Carregar contexto (em paralelo)

- Ler `.claude/feature-plans/<nome>/plan.md` integralmente
- Ler `.claude/feature-plans/<nome>/research.md` integralmente (se existir — o problema original pode estar aqui)
- Executar `git diff origin/main...HEAD` para capturar todos os commits da branch
- Executar `git diff HEAD` para capturar mudanças não comitadas (trabalho em andamento)

Combinar os dois diffs como "diff total da feature". Se um deles estiver vazio, usar apenas o outro.

### Passo 2 — Analisar alinhamento com o problema

Localizar a definição do problema:
- Preferência 1: seção `## Problema` do `plan.md`
- Preferência 2: seção `## Descrição da feature` do `research.md`
- Preferência 3: qualquer seção de contexto/objetivo no `plan.md`

Comparar o diff com o problema e classificar cada mudança encontrada:

| Classificação | Critério |
|---------------|----------|
| ✅ Alinhado | Mudança implementa diretamente o que o problema descreve |
| ⚠️ Drift | Mudança resolve algo relacionado mas diferente do problema original |
| ➕ Extra-escopo | Mudança implementa algo não mencionado no problema (não necessariamente ruim) |
| ❌ Pendente | Algo que o problema requer, mas não encontrado no diff |

### Passo 3 — Analisar cobertura do plano

Mapear cada item/passo listado em `plan.md` (seção `## Passos de execução` ou equivalente) contra o diff:

| Classificação | Critério |
|---------------|----------|
| ✅ Feito | Item claramente implementado no diff |
| 🔄 Parcial | Item começou mas está incompleto — descrever o que falta |
| ❌ Faltando | Item não encontrado no diff |
| ➕ Não planejado | Mudança no diff que não corresponde a nenhum item do plano |

### Passo 4 — Gerar e salvar relatório

Produzir o relatório completo no formato abaixo. Ser específico: citar arquivos, funções, linhas onde possível. Evitar julgamentos vagos como "parece ok".

Salvar em `.claude/feature-plans/<nome>/validation-report.md` (sobrescrever se já existir).
Exibir também na conversa.

---

## Formato de saída

```text
## 🧭 Relatório de Validação — <nome-da-feature>

---

### 1. Alinhamento com o problema

**Problema original:** <1-2 frases resumindo o problema definido na Fase A>

| Status | O que foi implementado | Observação |
|--------|----------------------|------------|
| ✅ Alinhado | <mudança X> | <como resolve o problema> |
| ⚠️ Drift | <mudança Y> | <como difere do objetivo original> |
| ➕ Extra-escopo | <mudança Z> | <não estava no problema — avaliar se é necessário> |
| ❌ Pendente | <o que o problema requer> | <ainda não implementado> |

**Veredito:** [Alinhado / Drift leve / Drift significativo / Off-track]
<Justificativa em 1-2 frases.>

---

### 2. Cobertura do plano

| Item do plan.md | Status | Observação |
|-----------------|--------|------------|
| <passo 1> | ✅ Feito | |
| <passo 2> | 🔄 Parcial | <o que ainda falta> |
| <passo 3> | ❌ Faltando | |
| <mudança não planejada> | ➕ Não planejado | <avaliar se deve entrar no plano ou ser revertida> |

**Resumo:** X/Y itens do plano concluídos.
[Cobertura adequada / Faltam itens críticos / Itens extras significativos]

---

### Recomendação

[Continuar / Ajustar escopo / Parar e realinhar com o usuário]

<Próxima ação sugerida em 1-2 frases.>
```

---

## Quando NÃO usar

- Antes da Fase C do `/start-feature` — `plan.md` ainda não existe
- Como substituto do `/ship-feature` — validate não roda testes técnicos nem faz build
- Para validar infra/deploy — isso é escopo do `/ship-feature`
- Em branches que não seguem o workflow `/start-feature` (sem `plan.md`)

---

## Diferença entre /validate e /checkpoint

| | /checkpoint | /validate |
|---|---|---|
| Quando | Durante execução, entre deliverables | Após execução, antes do PR |
| O que verifica | Assunções do plan.md foram validadas? | Código implementado = problema do plan.md? |
| Gate | Obrigatório (definido no plan.md) | Recomendado (soft gate no /ship-feature) |
| Escopo | Deliverable atual | Feature inteira (diff vs origin/main) |

---

## Testes

| Cenário | Input | Output esperado |
|---------|-------|----------------|
| Feature alinhada | `/validate` em worktree com plan.md e código alinhado | Relatório com ✅ nas duas seções, veredito "Alinhado" |
| Feature com drift | `/validate` em worktree onde código divergiu do problema | ⚠️ Drift identificado com arquivo/função específica |
| Cobertura parcial | `/validate` com metade do plano implementada | 🔄 Parcial em vários itens, recomendação "Continuar" |
| Sem plan.md | `/validate` sem feature iniciada com start-feature | Erro claro indicando ausência do plan.md |
| Nome manual | `/validate minha-feature` | Usa `minha-feature` para localizar plan.md |
| Branch sem padrão | `/validate` em branch `main` ou `fix/xyz` | Pede nome da feature ao usuário |
