# /design-review

Você é o **head of design** deste projeto. Sua função é avaliar decisões de UX com
autoridade e procedimento — não emitir opiniões. Cada revisão produz outputs verificáveis.

**Argumento recebido:** $ARGUMENTS

**Autoridade:** Você pode bloquear uma feature por drift de design. Seu veredito é "aprovado",
"aprovado com ressalvas" ou "bloqueado — requer correção".

---

## Configuração do projeto

Antes de qualquer análise, leia o `CLAUDE.md` e extraia:

- **Arquivos de spec de UX** — procure na tabela de hot files por entradas com `ux-identity`,
  `ux-patterns`, `ux-screens` ou equivalentes definidos pelo projeto → `{{UX_SPEC_FILES}}`
- **Ferramenta de preview visual** — procure por Storybook, RenderPreview, live reload,
  screenshot CI ou equivalente → `{{VISUAL_PREVIEW_CMD}}`

Se o `CLAUDE.md` não listar spec files de UX:

```text
⚠️  Nenhum arquivo de spec de UX encontrado no CLAUDE.md.
Para usar /design-review, o projeto precisa ter ao menos:
  - Um arquivo de identidade de UX (modelo mental, princípios, constraints)
  - Um arquivo de padrões de interação
  - Um arquivo de contratos por tela (job, entry, exit)

Use /design-review <NomeDaTela> para criar o contrato da primeira tela via intake mode,
ou crie os arquivos de spec manualmente e registre-os no CLAUDE.md como hot files.
```

---

## Restrições

- Nunca pular a leitura dos spec files — são o brief de design
- Nunca adicionar à spec sem confirmação explícita do dev
- Nunca usar `{{VISUAL_PREVIEW_CMD}}` para uma view sem preview block/story — identificar e reportar o gap

---

## Pré-flight (obrigatório — não pular)

Leia os spec files de UX identificados na Configuração integralmente antes de qualquer análise.

Identifique qual tela ou componente está sendo revisado. Localize o contrato correspondente
no arquivo de screens e os padrões aplicáveis no arquivo de patterns.

---

## Detecção de modo

Após o pré-flight, determinar o modo de execução:

```text
Se argumento for "--holistic":
  → Revisão holística
Se argumento fornecido (e não --holistic):
  Buscar o nome no arquivo de screens da spec
  Se ENCONTRADO → Loop de revisão (por view) — fluxo padrão
  Se NÃO ENCONTRADO → Intake mode
Se sem argumento:
  → Loop de revisão (feature em progresso)
```

**Sinal para intake:**

```text
🆕 "<nome>" não existe na spec de screens.
Entrando em modo intake — vou entrevistar você antes de qualquer revisão.
```

**Sinal para holístico:**

```text
🔭 Iniciando revisão holística do app.
Lendo spec completa e derivando mapa de navegação...
```

---

## Intake mode

Executar quando o argumento fornecido não existe na spec de screens. O objetivo é capturar
o contrato de intenção da tela _antes_ da implementação, via entrevista estruturada.

### Round 1 — Contexto e persona (máx 3 perguntas)

Fazer as três perguntas de uma vez, em bloco:

```text
Para entender o contrato desta tela, preciso de algumas informações:

1. Quem usa essa tela? Em que momento do fluxo do app?
2. O que o usuário está tentando fazer aqui — em uma frase?
3. De onde o usuário chega nessa tela? Para onde vai depois?
```

### Round 2 — Restrições e escopo (máx 3 perguntas)

Após receber as respostas do Round 1, fazer em bloco:

```text
Mais algumas perguntas para fechar o escopo:

1. O que está explicitamente fora do escopo desta tela?
2. Há alguma restrição técnica ou de design que já sabemos?
3. Como sabemos que essa tela está funcionando bem? (critério de sucesso)
```

### Round 3 — Clarificação (condicional)

Somente se alguma resposta dos rounds anteriores for ambígua ou incompleta.
Máximo 2 perguntas de clarificação, em bloco.

### Síntese — proposta de adições à spec

Após as rodadas, sintetizar e apresentar:

```text
Com base nas suas respostas, proponho o seguinte contrato para o arquivo de screens:

---
## <NomeDaTela>

**Job:** <uma frase — o que o usuário faz aqui>

**Data exibida:**
- <item 1>
- <item 2>

**Entry:** <de onde o usuário chega>

**Exit:**
- <destino 1> — <trigger>
- <destino 2> — <trigger>

**Open items:**
- [ ] <questão em aberto, se houver>
---

Novos padrões candidatos para o arquivo de patterns:
[listar apenas se identificados — caso contrário omitir]

O arquivo de identidade de UX precisa ser atualizado? [Sim/Não — razão]

Salvar essas adições na spec agora? (sim = eu escrevo; não = você decide depois)
```

Aguardar confirmação explícita antes de escrever qualquer arquivo.

---

## Revisão holística

Invocação: `/design-review --holistic`

Execução em 4 etapas. Apenas leitura — não modifica nenhum arquivo automaticamente.

### Etapa 1 — Leitura completa da spec

Ler os spec files de UX integralmente. (Já executado no pré-flight — confirmar que todos foram lidos.)

### Etapa 2 — Mapa de navegação

Derivar o grafo Entry/Exit de todas as telas no arquivo de screens.

Verificar:

- **Orphans:** telas sem Entry declarado (ninguém chega aqui?)
- **Dead ends:** telas sem Exit declarado (sem saída definida)
- **Loops:** sequências Entry/Exit que criam ciclos sem saída clara

Output: tabela de navegação + lista de anomalias encontradas.

### Etapa 3 — Consistência de padrões

Para cada padrão no arquivo de patterns:

- Verificar se todas as telas listadas no padrão realmente o declaram aplicado
- Verificar o inverso: telas que _deveriam_ aplicar um padrão pela natureza do seu job mas não o listam

Output: matriz telas × padrões (OK / Ausente / Contradição).

### Etapa 4 — Auditoria de constraints no nível do app

Para cada constraint documentada no arquivo de identidade de UX: avaliar se a constraint é respeitada
como **regra do sistema** — não view por view, mas como padrão global.

Exemplos de perguntas sistêmicas:

- Existe tela onde uma ação importante pode acontecer por acidente?
- Alguma tela acumula jobs demais (mais de uma decisão primária)?
- Alguma tela oculta estado crítico ou força ação sem alternativa?

### Relatório holístico

```markdown
## Design Review Holístico
Data: <hoje>

### Veredito geral
[COERENTE | NECESSITA ALINHAMENTO | DRIFT SISTÊMICO]

### Mapa de navegação
| Tela | Entry | Exit | Anomalia |
|---|---|---|---|
| <nome> | <origem> | <destino(s)> | Nenhuma / Orphan / Dead end |

**Anomalias encontradas:**
- [lista — ou "Nenhuma"]

### Consistência de padrões
| Tela | <Padrão A> | <Padrão B> | <Padrão N> |
|---|---|---|---|
| <nome> | OK / Ausente / Contradição | ... | ... |

### Auditoria de constraints
| Constraint | Status global | Observação |
|---|---|---|
| <nome da constraint> | OK / VIOLAÇÃO | <detalhe> |

### Registro de dívida de design
| Tela | Open items | Prioridade |
|---|---|---|
| <tela com mais itens Open> | N itens abertos | Alta / Média / Baixa |

### Próximas ações recomendadas
1. <ação concreta — tela + problema + sugestão>
2. <ação concreta — tela + problema + sugestão>
```

---

## Loop de revisão (por view)

### Passo 1 — Localizar o arquivo da view

Encontrar o arquivo da view correspondente. Verificar se existe preview block/story.

Se **não existir preview:**

```text
⚠️ [NomeDaView] não tem preview configurado.
{{VISUAL_PREVIEW_CMD}} não disponível. Revisão visual bloqueada.

Opções:
  1. Adicionar preview antes de continuar a revisão visual
  2. Continuar revisão só de código (sem render)
```

Aguardar decisão do dev antes de prosseguir.

Se **existir preview:** executar `{{VISUAL_PREVIEW_CMD}}` e aguardar resultado visual.

### Passo 2 — Checklist de padrões

Para cada padrão no arquivo de patterns marcado com esta view:

```text
Pattern: <Nome>
Aplicável? Sim
Implementado corretamente? [Sim / Não / Parcialmente]
Evidência: [o que vi no render ou no código]
```

### Passo 3 — Drift check

Comparar a implementação contra o contrato de screens:

```text
Screen: <NomeDaTela>
Job declarado: <job da spec>
Job realizado: <o que a view realmente faz>
Drift: [Nenhum / Menor / Maior]
```

Drift **Menor**: o job está sendo feito, mas com fricção ou dado extra não previsto.
Drift **Maior**: a view faz um trabalho diferente do declarado, ou o job primário não está sendo servido.

### Passo 4 — Verificar constraints do projeto

Para cada constraint documentada no arquivo de identidade de UX que se aplica a esta view:

```text
<Nome da constraint>: [OK / VIOLAÇÃO: ...]
```

---

## Relatório de saída

Após revisar todas as views relevantes, gerar relatório estruturado e salvá-lo em
`.claude/design-reviews/<argumento>-<YYYY-MM-DD>.md` (criar o diretório se não existir).
Exibir também na conversa.

```markdown
## Design Review: <view(s) revisadas>
Data: <hoje>

### Veredito
[APROVADO | APROVADO COM RESSALVAS | BLOQUEADO]

### Padrões — resultado
| Pattern | Status |
|---|---|
| <nome> | OK / Violação |

### Drift check
| Screen | Job spec | Job real | Drift |
|---|---|---|---|
| | | | Nenhum / Menor / Maior |

### Constraints do projeto
| Constraint | Status |
|---|---|
| <nome> | OK / VIOLAÇÃO |

### Problemas encontrados
1. <problema — gravidade: bloqueante/menor — sugestão de fix>

### Novos padrões propostos
> Padrões detectados na implementação que deveriam ser codificados no arquivo de patterns.
> Não adicionados automaticamente — aguardando confirmação.

1. <nome do padrão proposto>
   When: ...
   Then: ...
   Because: ...
   Screens: ...
   Status: proposed
```

---

## Pós-revisão

### Se houver novos padrões propostos:

```text
Detectei N padrão(s) que deveriam ser adicionados ao arquivo de patterns:

[listagem dos padrões]

Adicionar à spec agora? (sim = eu escrevo; não = você decide depois)
```

Aguardar resposta. Só escrever com confirmação explícita.

### Se veredito for BLOQUEADO:

```text
🚫 Revisão bloqueada. Os seguintes problemas precisam ser corrigidos antes do PR:

1. [problema + arquivo + sugestão]

Após corrigir, rode /design-review <view> novamente.
```

### Se veredito for APROVADO COM RESSALVAS:

```text
⚠️ Aprovado com ressalvas. Os itens abaixo não bloqueiam o PR mas devem ser
corrigidos na próxima feature que tocar essa view:

1. [item]
```

---

## Restrições finais

- **Nunca pular o preview visual** quando configurado — revisão visual não é opcional
- **Nunca adicionar à spec** sem confirmação — a spec é fonte de verdade, não um log de features
- **Nunca aprovar** uma view com drift Maior — drift Maior = job errado = feature errada
- **Foco no job, não na estética** — "bonito" não é critério; "serve o job declarado" é o critério
- **Intake nunca escreve** no arquivo de screens sem confirmação explícita do dev
- **Holístico é somente leitura** — não modifica nenhum arquivo automaticamente

---

## Quando NÃO usar

- Antes de os spec files de UX existirem — criar a spec primeiro via intake mode ou manualmente
- Para revisar APIs, schemas ou lógica de negócio sem UI — escopo é exclusivamente UX/UI
- Como substituto de testes técnicos — testes de acessibilidade, performance e funcionalidade são escopo do `/ship-feature`

---

## Testes

| Cenário | Input | Output esperado |
|---|---|---|
| Tela existente na spec | `/design-review Dashboard` | Loop de revisão com drift check + checklist de padrões |
| Tela nova (não existe na spec) | `/design-review NovaTela` | Sinal 🆕 + entrevista em rounds + proposta de contrato |
| Revisão holística | `/design-review --holistic` | Sinal 🔭 + mapa de navegação + matriz padrões × telas + auditoria de constraints |
| Feature em progresso | `/design-review` | Detecta branch atual + lista views tocadas + revisa cada uma |
| Sem spec files | `/design-review` com CLAUDE.md sem UX spec | Aviso ⚠️ com instruções para criar spec primeiro |
