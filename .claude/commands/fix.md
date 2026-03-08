# /fix

Você é um assistente de desenvolvimento executando o skill `/fix`.

Este skill corrige bugs e problemas pontuais em código existente.
É mais leve que o `/start-feature` — sem pesquisa multi-fase, sem checklist de infra.
Foco total em: entender o problema → encontrar a causa raiz → aplicar a menor correção possível.

O argumento passado é o nome ou descrição do bug: $ARGUMENTS

---

## Modos

- **Padrão** — diagnóstico rápido via leitura de arquivos + fix direto
- **`--investigate`** — diagnóstico profundo via subagente antes de tocar qualquer código
- **`--fast <nome>`** — pular diagnóstico, ir direto para execução (só quando a causa já é conhecida)

---

## Detecção de fase

Verifique a existência dos arquivos em `.claude/fix-plans/<nome>/`:

**Verificar debug report disponível:**
Antes de iniciar Fase 1, verificar se existe algum `report.md` em `.claude/debug-plans/`:

```bash
ls .claude/debug-plans/*/report.md 2>/dev/null
```

Se encontrado(s): apresentar lista e perguntar:
> "Encontrei relatório(s) de /debug disponível(is): [lista].
> Usar como base para o diagnóstico? (sim = pulo a investigação; não = diagnostico do zero)"

Se sim: ler o report.md escolhido, gerar `diagnosis.md` a partir dele (mapeando
"Causa raiz hipotética" → "Causa raiz", "Fix sugerido" → "Fix planejado"),
e pular direto para Fase 2.

| Arquivos presentes | Fase |
|---|---|
| Nenhum | Fase 1 — Diagnóstico |
| `diagnosis.md` existe | Fase 2 — Execução |

Se `--fast` foi passado: pular para **Fase 2** diretamente.

---

## FASE 1 — Diagnóstico

### Passo 1.1 — Coletar contexto

Perguntar ao usuário (se não veio nos argumentos):
- O que está acontecendo de errado? (comportamento observado vs. esperado)
- Onde está o problema? (arquivo, função, rota, tela — qualquer pista)
- Existe algum log de erro, stack trace ou mensagem relevante?

Se `--investigate` **não** foi passado: ir para Passo 1.2 (diagnóstico manual).
Se `--investigate` foi passado: ir para Passo 1.2i (diagnóstico via subagente).

---

### Passo 1.2 — Diagnóstico manual (modo padrão)

Com base nas pistas coletadas:

1. Identificar os arquivos mais prováveis de conter o bug
2. Ler os arquivos relevantes — entender o fluxo de execução ao redor do problema
3. Formular hipótese de causa raiz
4. Identificar a menor mudança que resolve o problema

Ir para Passo 1.3.

---

### Passo 1.2i — Diagnóstico via subagente (`--investigate`)

Lançar subagente `Explore` em background (`run_in_background=true`) com o seguinte prompt:

> Investigue este bug: `<descrição do bug>`.
> Pistas disponíveis: `<logs/stack trace/localização informados pelo usuário>`.
> Leia o CLAUDE.md do projeto para entender a stack. Depois:
> 1. Trace o fluxo de execução do ponto de entrada até onde o problema pode estar.
> 2. Identifique todos os arquivos candidatos a conter a causa raiz.
> 3. Leia cada arquivo candidato e formule hipóteses de causa, ordenadas por probabilidade.
> 4. Para cada hipótese: indique qual seria a menor mudança para corrigir.
> Retorne: causa raiz mais provável, arquivos envolvidos, fix recomendado, hipóteses alternativas (se houver).

Aguardar com `TaskOutput`. Sintetizar o resultado.

Ir para Passo 1.3.

---

### Passo 1.3 — Confirmar diagnóstico com o usuário

Apresentar:

```text
Diagnóstico: <nome>

Causa raiz: <hipótese>

Arquivos envolvidos:
- `path/to/file` — <por que está envolvido>

Fix proposto:
<descrição concisa da mudança — não vaga, ex: "alterar condição X na linha Y de foo.ts para considerar caso Z">

Hipóteses alternativas (se houver):
- <hipótese B> — <por que menos provável>
```

Aguardar confirmação do usuário:
- Confirmou → salvar diagnosis.md e ir para Fase 2
- Pediu ajuste → incorporar e re-apresentar
- Discordou completamente → revisitar Passo 1.2 com novas informações

### Passo 1.4 — Salvar diagnóstico

Criar `.claude/fix-plans/<nome>/diagnosis.md`:

```markdown
# Diagnóstico: <nome>

## Descrição do bug
<comportamento observado vs. esperado>

## Causa raiz
<hipótese confirmada>

## Arquivos envolvidos
- `path/to/file` — <papel no problema>

## Fix planejado
<o que exatamente será mudado>

## Hipóteses descartadas
<se houver — por que foram descartadas>

## Contexto adicional
<logs, stack trace, outras pistas relevantes>
```

Ao final:
```text
diagnosis.md salvo em .claude/fix-plans/<nome>/

Próximo passo: Fase 2 (Execução)
Recomendo /clear antes de continuar — rode /fix <nome> novamente.

────────────────────────────────────────────────
Cole na nova sessão após /clear:

Fix "<nome>" — Diagnóstico concluído.
Contexto salvo em: .claude/fix-plans/<nome>/diagnosis.md
Próximo comando: /fix <nome>
────────────────────────────────────────────────
```

---

## FASE 2 — Execução

### Passo 2.1 — Ler o diagnóstico

Ler `.claude/fix-plans/<nome>/diagnosis.md` integralmente.

Se `--fast` foi usado: perguntar causa raiz e fix planejado antes de prosseguir.

### Passo 2.2 — Criar worktree

Usar `EnterWorktree name=<nome>`.

### Passo 2.3 — Aplicar o fix

Regras:
- Ler o estado atual de cada arquivo antes de editar — nunca editar às cegas
- Aplicar a **menor mudança possível** que resolve o problema
- Não refatorar, não "melhorar" código vizinho, não adicionar features
- Se durante a execução a causa raiz mostrar-se diferente do diagnóstico: **parar e reportar** antes de continuar

Confirmar com "✅ Fix aplicado" ao concluir.

### Passo 2.4 — Validação

Lançar validação em background com Task tool (`run_in_background=true`):

**Subagente de validação:**
> 1. Rode o comando de teste do projeto (extraído do CLAUDE.md)
> 2. Se não houver comando configurado, procure e rode os testes mais próximos dos arquivos modificados
> 3. Reporte: ✅ ou ❌ com output completo

Enquanto aguarda: exibir resumo do que foi alterado (arquivos, linhas, natureza da mudança).

Quando o agente terminar:
- ✅ testes passando → reportar sucesso e lembrar de rodar `/ship-feature`
- ❌ testes falhando → exibir o erro completo; avaliar se é falha do fix ou teste pré-existente quebrado; aguardar orientação

### Passo 2.5 — Resultado

```text
Fix concluído!

Causa raiz: <resumo>
Mudança: <arquivo(s) modificado(s) — descrição de uma linha>
Testes: ✅ / ❌

Próximos passos:
- /ship-feature <nome> para entregar
- /close-feature <nome> após validação em produção
```

### Passo 2.6 — Changelog via `/close-feature`

**Não gerar entrada no CHANGELOG.md aqui.** O `/close-feature` é responsável pelo changelog.

Razão: o número do PR só está disponível após o `/ship-feature` mergear. Gerar antes resulta em entradas sem PR link.

Fluxo correto:
1. `/fix <nome>` → aplica o fix
2. `/ship-feature <nome>` → mergeia o PR, valida em produção (PR# disponível)
3. `/close-feature <nome>` → gera entrada `[fix]` no CHANGELOG.md com PR link

---

## Modo rápido — `--fast`

Para quando a causa já é conhecida e o fix é óbvio:
1. Perguntar: qual o arquivo e o que precisa mudar?
2. Criar `diagnosis.md` mínimo (sem subagente, sem confirmação de hipótese)
3. Ir direto para Fase 2

Usar apenas quando: causa inequívoca, mudança de 1-5 linhas, sem risco de regressão.

---

## Regras gerais

- Nunca editar arquivos sem lê-los primeiro
- Aplicar sempre a correção mínima — sem melhorias colaterais
- Se a causa raiz for diferente do diagnóstico durante a execução: parar e reportar
- **Worktree sempre — sem exceção**
- Se os testes falharem: não declarar o fix como concluído
- **Na Fase 2: executar autonomamente, sem parar entre passos pedindo confirmação**
- **Changelog é responsabilidade do `/close-feature` — nunca gerar aqui**
