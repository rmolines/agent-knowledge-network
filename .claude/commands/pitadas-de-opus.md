---
name: pitadas-de-opus
description: Use when facing high-stakes decisions where the cost of being wrong significantly exceeds the cost of Opus — any domain: architecture, product strategy, UX, business model, positioning, theoretical frameworks. Activates a deliberate calibration protocol: evaluate risk asymmetry to decide if Opus is warranted, structure the Opus session to surface paths Sonnet didn't explore, record delta for long-term calibration. Use /pitadas-de-opus for the activation decision, /pitadas-de-opus --log after a session to register outcome.
---

# /pitadas-de-opus

Protocolo de calibração deliberada para uso pontual e intencional do Opus em um workflow Sonnet-default.

**O que é:** Um gate de decisão com três funções: (1) avaliar se a tarefa justifica Opus via critério de assimetria de risco — em qualquer domínio;
(2) estruturar a sessão Opus para explorar caminhos que Sonnet não tomou;
(3) registrar o delta de forma acumulável — construindo evidência empírica de "quando Opus vale em cada tipo de problema".

**O que não é:** Não é routing automático. Não é comparação side-by-side de outputs. Não é "second opinion". A agência de decidir permanece humana — a skill estrutura a decisão, não a substitui.

**Argumento:** `$ARGUMENTS` — pode ser vazio (avaliação de ativação), descrição da tarefa, `--session` (estrutura sessão Opus diretamente), ou `--log` (registro de delta pós-sessão)

**Dispatch:**

| Argumento | Modo executado |
|---|---|
| (vazio ou descrição da tarefa) | Modo 1 — Decisão de ativação |
| `--session` | Modo 2 — Estrutura de sessão Opus |
| `--log` | Modo 3 — Registro de delta |

---

## Modo 1 — Decisão de ativação (default)

Executado quando a skill é invocada sem `--session` e sem `--log`.

### Passo 1.1 — Entender a tarefa

Se o argumento descreve a tarefa: usar como contexto.
Se vazio: fazer **uma** pergunta: "Qual é a tarefa ou decisão que você está enfrentando?"

Aguardar resposta antes de continuar.

### Passo 1.2 — Avaliar os 4 critérios de ativação

Apresentar a avaliação explícita para cada critério. Marcar com ✅ se aplica, ❌ se não aplica.

**Critério 1 — Fase de discovery ou exploração**
Opus tem delta documentado em tarefas abertas onde o espaço de busca ainda não foi mapeado —
em qualquer domínio: antes do bet de produto, definição de posicionamento, mapeamento de alternativas
técnicas, entendimento de um mercado desconhecido, exploração de um framework teórico novo.

✅ Se a tarefa é aberta (não há plano definido, alternativas não foram exploradas)
❌ Se a tarefa tem escopo fechado e direção já decidida

**Critério 2 — Decisão estruturante com múltiplas dimensões simultâneas**
Opus explora múltiplos caminhos antes de convergir. Sonnet tende a implementar o literal do prompt —
eficiente para execução, menos adequado quando há trade-offs não declarados entre dimensões diferentes:
tech vs. negócios, UX vs. viabilidade, velocidade de lançamento vs. qualidade de posicionamento,
coerência teórica vs. aplicabilidade prática.

✅ Se a decisão envolve trade-offs entre dimensões diferentes (e não é execução em uma única dimensão)
❌ Se é execução de algo já decidido

**Critério 3 — Custo de estar errado é alto e assimétrico**
A pergunta não é "qual modelo é melhor" — é "qual é o custo de errar aqui?".
Um posicionamento errado que afasta o cliente ideal é tão caro quanto uma decisão arquitetural que
bloqueia features futuras. O sinal de assimetria: o custo de corrigir depois é ordens de magnitude
maior do que o custo de explorar bem agora.

✅ Se uma decisão errada cria consequências difíceis de reverter — em qualquer dimensão:
dívida técnica, perda de oportunidade de mercado, desorientação de produto, expectativas erradas consolidadas
❌ Se o erro é facilmente corrigível na próxima iteração

**Critério 4 — Exploração adversarial necessária**
Tarefas onde a hipótese principal precisa ser ativamente contestada antes de executar — em qualquer domínio:
red team de um plano técnico, questionamento de suposições de mercado, contestação de premissas de UX,
geração de contra-exemplos para um framework teórico.

✅ Se você precisa que alguém questione ativamente as suposições do plano atual
❌ Se o plano já passou por revisão crítica ou a tarefa é de execução direta

### Passo 1.3 — Recomendação

Após avaliar os 4 critérios, apresentar:

```text
## Avaliação — pitadas de Opus

Critério 1 (discovery/exploração):              [✅ / ❌]
Critério 2 (decisão estruturante multi-dim.):   [✅ / ❌]
Critério 3 (custo de erro assimétrico):         [✅ / ❌]
Critério 4 (exploração adversarial):            [✅ / ❌]

Recomendação: [Opus justificado / Sonnet suficiente]

Justificativa: <1-2 frases — qual critério foi determinante e por quê>

Próximo passo: [/pitadas-de-opus --session ou continuar com Sonnet]
```

**Regra de recomendação:**

- 3-4 critérios ✅ → Opus claramente justificado
- 2 critérios ✅ → julgamento — apresentar raciocínio e deixar decisão com o usuário
- 0-1 critérios ✅ → Sonnet suficiente para esta tarefa

**PARAR AQUI.** Aguardar confirmação do usuário antes de prosseguir ou encerrar.

---

## Modo 2 — Estrutura de sessão Opus (`--session`)

Executado quando: (a) o usuário confirma uso do Opus no Modo 1, ou (b) `/pitadas-de-opus --session` é invocado diretamente.

Se invocado diretamente via `--session` sem contexto anterior: solicitar ao usuário em uma linha:
"Qual é a tarefa ou decisão que você quer explorar com Opus?" — aguardar resposta antes de continuar para 2.1.

Objetivo: maximizar o aproveitamento da sessão Opus estruturando-a para explorar caminhos que Sonnet não teria tomado.

### Passo 2.1 — Identificar o domínio

Identificar o domínio principal da tarefa para colorir o protocolo de sessão:

| Domínio | Exemplos |
|---|---|
| `tech` | arquitetura de sistema, decisão de stack, estrutura de dados, algoritmos |
| `produto` | escopo de feature, priorização, definição do problema, critérios de sucesso |
| `ux` | fluxos de interação, personas, hierarquia de informação, padrões de interface |
| `negócios` | modelo de negócio, pricing, canais, estratégia de crescimento |
| `marketing` | posicionamento, mensagem, segmentação, proposta de valor |
| `teoria` | frameworks conceituais, hipóteses de pesquisa, modelos explicativos |
| `outro` | qualquer combinação ou domínio não listado |

Se não estiver claro pelo contexto: perguntar em uma linha. "Qual é o domínio principal desta decisão?"

### Passo 2.2 — Definir escopo da sessão

Apresentar e confirmar com o usuário:

```text
## Escopo desta sessão Opus

Domínio: <domínio identificado>
Tarefa: <o que será explorado>

Dentro do escopo desta sessão:
- <o que Opus deve responder / explorar>

Fora do escopo (evitar scope creep):
- <o que não deve ser resolvido nesta sessão>

Critério de encerramento: <quando a sessão Opus pode ser considerada completa>
```

Aguardar confirmação antes de continuar.

### Passo 2.3 — Capturar baseline de custo

Antes de passar o protocolo ao usuário, instruir:

```text
Para medir o custo incremental desta sessão Opus, rode agora:

  /cost

Anote o valor de "Total cost" atual. Ao final da sessão Opus, rode /cost novamente —
a diferença é o custo desta pitada de Opus. Use /pitadas-de-opus --log para registrar.
```

Prosseguir diretamente para o Passo 2.4 — não bloquear aguardando confirmação.

### Passo 2.4 — Protocolo de sessão

Apresentar o protocolo para uso direto com Opus.
O protocolo é o mesmo para todos os domínios — o que muda é o contexto injetado.

```text
## Protocolo de sessão Opus — pitadas de opus

Cole este bloco no início da sua sessão Opus:

---
Você é uma instância de Opus ativada deliberadamente para explorar caminhos
que o fluxo padrão (Sonnet) provavelmente não tomaria.

Domínio: <domínio>
Tarefa: <tarefa definida no Passo 2.2>

Seu protocolo de exploração — execute nesta ordem:

**Etapa 1 — Perguntas que Sonnet não fez**
Liste 3-5 perguntas sobre esta tarefa que raramente aparecem em abordagens convencionais
para este domínio. Não responda ainda. Só liste.

**Etapa 2 — Suposições implícitas**
Identifique 3-5 suposições que estão sendo feitas sobre como resolver isso neste domínio.
Para cada uma: "Esta suposição precisa ser verdade? O que acontece se for falsa?"

**Etapa 3 — Caminhos não óbvios**
Derive 2-3 abordagens partindo das suposições questionadas na Etapa 2.
Pelo menos uma deve contradizer a abordagem mais óbvia.

**Etapa 4 — Síntese**
Qual é o insight mais valioso que provavelmente seria perdido em uma abordagem padrão?
Qual caminho você recomenda e por quê?
---
```

### Passo 2.5 — Gerar opus-session.md

Após a sessão Opus ser concluída, salvar o artefato em `.claude/feature-plans/<nome>/opus-session.md`:

```markdown
# Opus Session: <slug>
_Data: <data> · Domínio: <domínio>_

## Tarefa explorada
<descrição>

## Perguntas que Sonnet não fez (Etapa 1)
- <pergunta 1>
- <pergunta 2>

## Suposições contestadas (Etapa 2)
- <suposição>: <o que acontece se for falsa>

## Caminhos não óbvios (Etapa 3)
- <caminho 1>
- <caminho 2>

## Insight principal (Etapa 4)
<o insight mais valioso da sessão>

## Recomendação
<caminho recomendado e justificativa>

## Handoff

next_skill: /pitadas-de-opus --log

carry_forward:
- [tarefa]: <slug ou descrição curta>
- [dominio]: <domínio identificado>
- [insight principal]: <o insight mais valioso em uma frase>
- [recomendação]: <caminho recomendado>

excluded:
- [caminhos descartados na Etapa 3 — previne re-exploração]
```

Ao final: sugerir `/pitadas-de-opus --log` para registrar o delta.

---

## Modo 3 — Registro de delta (`--log`)

Executado com `/pitadas-de-opus --log`. Objetivo: converter a sessão Opus em evidência acumulável.

### Passo 3.1 — Coletar delta percebido

Fazer **uma** pergunta por vez. Aguardar resposta antes de continuar.

1. "Você rodou `/cost` antes e depois? Se sim, qual foi o custo incremental da sessão Opus? (cole o valor ou 'não medi')"
2. "O Opus gerou algo que o Sonnet provavelmente não geraria? Se sim, o que especificamente foi diferente? (1-2 frases. Se não, escreva 'não')"
3. "Nível de delta percebido: alto (mudou a direção) / médio (refinamento importante) / baixo (confirmou o que já sabia) / nenhum"

### Passo 3.2 — Appender ao OPUS_LOG.md

Criar ou appender ao `OPUS_LOG.md` na raiz do projeto. Cada entrada usa o formato:

```markdown
## <data> — <slug>

- **Domínio:** tech | produto | ux | negócios | marketing | teoria | outro
- **Contexto:** <skill ou momento do projeto — ex: /start-feature --discover, planejamento de roadmap>
- **Critérios ativados:** <lista dos critérios ✅ da avaliação>
- **Custo da sessão:** <valor do /cost incremental — ex: "$0.42" ou "não medido">
- **Delta percebido:** alto | médio | baixo | nenhum
- **Notas:** <1 linha — o que foi diferente, ou por que não houve delta>
```

### Passo 3.3 — Exibir resultado

Confirmar que o registro foi adicionado e exibir o total atual de entradas no OPUS_LOG.md.

Se OPUS_LOG.md tiver 5 ou mais entradas, exibir também a análise de padrões:

```text
## Padrões acumulados — pitadas de Opus

Entradas registradas: <N>
Delta alto ou médio: <X> de <N> (<pct>%)
Custo total medido: <soma das entradas com valor — ou "N sessões sem medição">
Custo médio por sessão Opus: <média — ou "insuficiente para calcular">

Domínios com maior taxa de delta alto: <ranking>

Critérios com maior correlação com delta alto:
- <critério mais frequente nas entradas com delta alto>

Padrões onde Opus não entregou delta esperado:
- <domínio ou tipo de tarefa>

Recomendação de calibração: <ajuste sugerido nos critérios de ativação, se houver>
```

---

## Quando NÃO usar

- **Execução com plano definido** — em qualquer domínio: escrever copy de um posicionamento já decidido,
  implementar uma arquitetura já escolhida, executar um fluxo de UX já especificado
- **Tarefas mecânicas ou repetitivas** — reformatação, síntese de reuniões, geração de commits, lint, refactoring de rotina
- **Quando você está confortável com a direção** — use Opus para explorar incerteza real, não para confirmar certeza
- **Como fallback por insatisfação** — se o output de Sonnet não agradou, o problema provavelmente é o prompt, não o modelo
- **Sempre que algo parecer "importante"** — sem discriminação, colapsa para usar sempre e perde o valor de calibração

---

## Regras gerais

- A decisão de usar Opus permanece humana — a skill avalia, não decide
- Sempre identificar o domínio antes de entrar em sessão Opus (Passo 2.1)
- Sempre definir escopo explícito antes de iniciar (Passo 2.2)
- Registrar o delta após cada sessão Opus — sem registro, não há calibração
- O critério de ativação é assimetria de risco (custo de erro × espaço multimodal), não confiança subjetiva
- Opus tem delta real em discovery/exploração/decisões estruturantes; gap é marginal em execução com plano definido
- **PARAR após Passo 1.3** — nunca auto-recomendar continuar para Modo 2 sem confirmação humana
