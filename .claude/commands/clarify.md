---
name: clarify
description: Use when the user has a vague feeling, embryonic idea, or intuition they can't yet articulate as a clear question — conducts a Socratic dialogue to crystallize the tension before /explore. ALWAYS use this skill when the user says things like "tenho uma ideia mas não sei o que é", "tenho um incômodo", "quero pensar sobre algo", "não sei nem por onde começar", "tenho uma sensação de que", "tem algo aqui mas não sei articular", or arrives with a vague impulse without a clear direction. Also use when the user has a presumed solution ("quero construir X") but hasn't examined the underlying problem yet.
---

# /clarify

Transforma uma intuição bruta em uma tensão articulada — pronta para entrar no `/explore`.

Conduz um interrogatório socrático onde você responde perguntas concretas e, no ato de responder, a ideia ganha forma. Você não precisa saber o que quer dizer antes de começar.

**Input:** $ARGUMENTS — pode ser: uma sensação vaga, uma palavra, um incômodo, nada

---

## Antes de começar

**Avaliação rápida:** Se o usuário já chegou com uma pergunta razoavelmente formada ou um domínio + gap claro, sugira ir direto para `/explore`.
A clarificação só agrega quando a ideia ainda não tem forma suficiente para o explore trabalhar.

Se chegou com algo vago (ou sem nada): prosseguir com os 3 movimentos abaixo.

> **Regra de inibição:** Não ofereça molduras, interpretações, nomes ou sínteses antes de o usuário ter dado pelo menos 3 exemplos ou situações concretas.
> Reflita de volta o que ouviu na linguagem do usuário — não na sua. Ser "útil" cedo é o principal risco: gera ilusão de clareza enquanto preserva a confusão original.
>
> **Ritmo:** Uma pergunta por vez. Aguarde a resposta antes de fazer a próxima. Perguntas empilhadas bloqueiam.

---

## Movimento 1 — Extração de sinal bruto

**Objetivo:** fazer o usuário externalizar o estado interno sem filtro. Você escuta e reflete. Não interpreta.

Perguntas que funcionam aqui são concretas, não abstratas:
- "Me dá um exemplo de uma situação onde você sentiu isso."
- "O que você queria que existisse e não existe?"
- "Quando pensa nisso, o que te incomoda agora mesmo?"
- "Qual foi o momento que fez você pensar nisso pela primeira vez?"

Após cada resposta: reflita de volta o que ouviu em uma frase, na linguagem do usuário. Não adicione interpretação. Pergunte o próximo.

Continue até ter pelo menos 3 exemplos ou situações concretas. Só então avance.

---

## Movimento 2 — Identificação de tensões

**Objetivo:** encontrar o gap entre o que o usuário vê e o que o mundo oferece. Três movimentos obrigatórios:

**Inversão** — revela os limites pelo negativo, que costumam ser mais claros que os positivos:
- "O que você definitivamente NÃO quer que isso seja?"
- "O que seria uma solução ruim para isso?"

**Separação de níveis** — distingue o que está colapsado:
- Sintoma: o que incomoda na superfície
- Problema estrutural: por que isso existe
- Desejo profundo: o que resolveria de verdade
Pergunte: "O incômodo é [sintoma]... mas o que você acha que está por baixo disso?"

**Teste de transferência** — separa o problema pessoal do problema de domínio:
- "Se você não existisse, esse problema existiria para outra pessoa?"

---

## Movimento 3 — Cristalização

**Objetivo:** o usuário sair com uma tensão articulada — não com uma solução.

Com base no que emergiu nos movimentos anteriores, proponha uma formulação:
- "Parece que o que você está sentindo é uma tensão entre X e Y. Chega perto?"

O usuário vai confirmar, corrigir ou refinar. Itere até ouvir algo como "é isso" ou "exatamente".

**Critério de parada:** o usuário consegue articular a tensão central em uma frase sem incluir a solução presumida. Não é sobre número de turnos — é sobre reconhecimento.

Se depois de algumas iterações o usuário ainda não reconhecer a formulação, volte ao Movimento 1 com uma pergunta diferente. Às vezes o sinal real ainda não emergiu.

---

## Avaliação final

Antes de salvar, avalie se a ideia clarificada já tem maturidade suficiente para `/explore` ou se ainda precisa de mais clarificação (`/clarify --deepen <slug>`). Sinalize com transparência.

---

## Formato de saída

Derivar o slug da tensão cristalizada (kebab-case, 2-4 palavras). Salvar em `.claude/feature-plans/<slug>/clarify.md`. Criar o diretório se não existir.

Exibir também na conversa.

```text
# Clarify: [título derivado da tensão — 4-6 palavras]

## Sinal bruto
[o que o usuário disse, na linguagem dele — sem reinterpretar]

## Tensões identificadas
- [o que não existe / o que incomoda]
- [o que definitivamente NÃO é]
- [sintoma vs. problema estrutural vs. desejo profundo]
- [o problema existe para outros? sim/não — implicação]

## Tensão cristalizada
[a pergunta/tensão central em uma frase — sem solução presumida]

## Próxima ação
**Veredicto:** [pronto para /explore | precisa mais clarificação]
**Próxima skill:** `/explore` ou `/clarify --deepen <slug>`
**Slug sugerido:** `<slug>`

## Handoff

next_skill: /explore <slug>

carry_forward:
- [tensão principal]: <a tensão cristalizada em uma frase>
- [sinal de origem]: <o exemplo concreto mais revelador que o usuário deu>
- [o que definitivamente não é]: <o que foi excluído pela inversão>

excluded:
- [formulações que o usuário rejeitou durante a cristalização]

invalidated:
- [o que ficaria stale se o escopo mudar]

confiança: draft | emergente | cristalizada
<!-- draft = sinal captado mas tensão ainda vaga; emergente = tensão identificada; cristalizada = usuário reconheceu "é isso" -->

---
Faça `/clear` para limpar a sessão e então rode `/explore <slug>`.
O contexto está preservado em `.claude/feature-plans/<slug>/clarify.md`.
---
```
