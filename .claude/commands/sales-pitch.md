# /sales-pitch

Gera um pitch customizado do projeto para uma audiência específica, lendo os arquivos do projeto como fonte de verdade.
Use quando precisar convencer um stakeholder a adotar o setup Claude Code + este template.

**Argumento opcional:** `$ARGUMENTS` — audiência-alvo. Valores: `business`, `tech`, `cto`. Se omitido, pergunta ao usuário.

---

## Dispatch table de audiências

Parsear `$ARGUMENTS`:

| Argumento | Modo |
|-----------|------|
| `business` | Modo A — Stakeholder de negócio |
| `tech` | Modo B — Dev / Tech lead |
| `cto` | Modo C — CTO / VP Eng |
| vazio ou qualquer outro valor | Perguntar ao usuário (Fase 2) |

---

## Fase 1 — Ler o projeto

Execute todas as leituras simultaneamente:

```bash
cat CLAUDE.md 2>/dev/null || echo "(sem CLAUDE.md)"
cat .claude/backlog.json 2>/dev/null || echo "(sem backlog.json)"
cat LEARNINGS.md 2>/dev/null || echo "(sem LEARNINGS.md)"
cat memory/MEMORY.md 2>/dev/null || echo "(sem MEMORY.md)"
cat README.md 2>/dev/null || echo "(sem README.md)"
```

Extrair de cada arquivo:

- **CLAUDE.md** → descrição do projeto (seção "Project overview"), workflow de features, comandos disponíveis
- **backlog.json** → contagem de features por status (done / in-progress / pending), nome do projeto
- **LEARNINGS.md** → problemas já resolvidos (prova de refinamento e seriedade técnica)
- **memory/MEMORY.md** → core value prop, decisões arquiteturais, distribuição
- **README.md** → linguagem de marketing pronta, quickstart, filosofia

**Verificar se há dados suficientes para gerar o pitch:**

Usar fallback (Fase 3) se qualquer uma das condições abaixo for verdadeira:
- 3 ou mais arquivos estiverem ausentes ou retornarem apenas `(sem ...)`
- CLAUDE.md existir mas a seção "Project overview" contiver apenas `<!-- TODO: ... -->`

Se fallback for necessário: executar **Fase 3** primeiro, depois retornar para **Fase 2** (detecção de audiência) e só então gerar o pitch.

---

## Fase 2 — Detectar audiência

Se `$ARGUMENTS` foi fornecido e é um valor válido (`business`, `tech`, `cto`): usar diretamente.

Se não foi fornecido ou é inválido, perguntar:

> Para quem é este pitch?
>
> **A) Stakeholder de negócio** — founder, CEO, investidor, PM: foco em ROI e agilidade
> **B) Dev / Tech lead** — colega desenvolvedor ou tech lead: foco em workflow e produtividade
> **C) CTO / VP Eng** — liderança técnica: foco em escalabilidade, governança e memória institucional
>
> (Responda A, B ou C)

Aguardar resposta antes de continuar.

---

## Fase 3 — Fallback interativo (se projeto sem dados suficientes)

Se os arquivos não têm conteúdo suficiente, fazer até 3 perguntas, **uma por vez**, aguardando resposta antes de prosseguir:

**Pergunta 1:**
> O que este projeto faz? (1-2 frases — o problema que resolve e para quem)

**Pergunta 2:**
> Como Claude Code + este template ajudou no desenvolvimento? (ex: velocidade, qualidade, processo)

**Pergunta 3:**
> Qual é o principal resultado que você quer destacar? (ex: "lançamos em 3 semanas", "zero bugs em produção", "time de 2 pessoas entrega como um time de 6")

Usar as respostas como base para a geração — não inventar dados não fornecidos.

---

## Fase 4 — Gerar o pitch

### Modo A — Stakeholder de negócio (business)

**Regras de tradução de jargão:**

| Termo técnico | Tradução para negócio |
|---|---|
| Skills / comandos | Fluxos de trabalho estruturados |
| Hooks | Validações automáticas |
| MCP | Integrações com ferramentas internas |
| Worktree | Ambiente isolado por funcionalidade |
| Commit / PR | Entrega versionada com revisão |

**Formato de output:**

```text
## 🎯 [Nome do projeto] — Por que agora

---

### O problema

[Descreva o problema de negócio que o projeto resolve — em linguagem de usuário final, sem jargão técnico.]

---

### O que construímos

[O que o produto/sistema faz, em 2-3 frases. Foco em resultado, não em tecnologia.]

---

### Como desenvolvemos mais rápido e com mais qualidade

Com Claude Code e um processo estruturado de desenvolvimento:

- **[Resultado concreto 1]** — [evidência do projeto: feature entregue, tempo economizado, etc.]
- **[Resultado concreto 2]** — [evidência do projeto: qualidade, previsibilidade, etc.]
- **[Resultado concreto 3]** — [evidência do projeto: processo, documentação, aprendizados, etc.]

[Se backlog.json existir: "Até agora: X funcionalidades entregues, Y em desenvolvimento, Z planejadas."]

---

### Por que isso importa agora

[Contexto de urgência ou oportunidade — por que este momento é o certo para avançar.]

---

### Próximo passo

[Call to action claro e específico para a audiência — o que você quer que ela faça ou decida.]
```

---

### Modo B — Dev / Tech lead (tech)

**Formato de output:**

```text
## ⚙️ [Nome do projeto] — Stack e processo

---

### Problema de engenharia

[O problema técnico ou de processo que o projeto resolve.]

---

### Solução

[Arquitetura em 2-3 frases. Pode mencionar stack, padrões, decisões técnicas relevantes.]

---

### Workflow de desenvolvimento

O time usa Claude Code com um processo estruturado:

- `/start-feature` → planning com pesquisa → worktree isolado → execução
- `/validate` → verifica se implementação resolve o problema original antes do PR
- `/ship-feature` → auto-simplify + rebase + PR com checklist
- `/close-feature` → documenta learnings + atualiza memória do projeto

Resultado: cada feature vai do problema ao PR com rastreabilidade completa e sem drift.

---

### O que já foi construído

[Features entregues do backlog.json, ou lista manual se fornecida no fallback.]

---

### Onde estamos

[Se backlog.json existir: status atual — milestone, features em andamento, próximos passos. Se não existir e o usuário não forneceu no fallback: omitir esta seção — não estimar.]
```

---

### Modo C — CTO / VP Eng (cto)

**Formato de output:**

```text
## 📊 [Nome do projeto] — Visão técnica e organizacional

---

### Problema

[Problema de engenharia ou de organização que o projeto resolve.]

---

### Solução e arquitetura

[Decisões técnicas principais — stack, padrões, trade-offs feitos conscientemente.]

---

### Escalabilidade e governança

- **Memória institucional:** cada feature documenta learnings, handovers e decisões — novos membros do time têm contexto completo
- **Fluxos de trabalho padronizados:** o processo de desenvolvimento é definido em código (CLAUDE.md + skills), não em cabeças individuais
- **Validação automática:** lint, CI e hooks garantem qualidade sem depender de revisão manual exaustiva
- **Rastreabilidade:** cada entrega tem plano, implementação e documentação linkados

---

### Progresso

[Features entregues / em andamento / planejadas — do backlog.json ou fornecido no fallback.]

---

### Riscos conhecidos e mitigações

[Se LEARNINGS.md existir: listar riscos e mitigações encontrados. Se não existir: omitir esta seção inteiramente — não estimar.]

---

### Próxima decisão necessária

[O que precisa de aprovação ou direcionamento — call to action específico para CTO/VP Eng.]
```

---

## Notas de implementação

- **Nunca escrever em arquivo** — o pitch fica na conversa; o usuário copia o que precisar
- **Nunca inventar dados** — se backlog.json não existe e o usuário não forneceu números, omitir a seção de progresso; não estimar
- **Jargão trade-off por audiência** — Modo A: zero jargão; Modo B: jargão técnico OK; Modo C: jargão estratégico (governança, rastreabilidade)
- **Fallback unificado**: as duas condições (3+ arquivos ausentes; CLAUDE.md com TODO intacto) são avaliadas juntas em Fase 1 — fallback dispara se qualquer uma for verdadeira

---

## Quando usar

Rode `/sales-pitch` quando:

- Precisar convencer um não-técnico (founder, CEO, investidor) a aprovar o uso de Claude Code + este template
- Quiser apresentar o projeto em uma reunião de planejamento ou status
- Precisar de um email ou resumo rápido sobre o andamento do projeto
- Um novo stakeholder entrar no projeto e precisar de contexto

**Frases-gatilho:** "preciso apresentar isso", "como explico para o meu chefe", "pitch do projeto", "justificar o uso de Claude Code", "resumo para stakeholder"
