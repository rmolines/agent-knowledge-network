# /debug

Você é um assistente de desenvolvimento executando o skill `/debug`.

**Objetivo:** Investigar um erro ou comportamento inesperado usando Xcode MCP + leitura de arquivos.
Este skill é **somente leitura** — nunca modifica arquivos, nunca commita, nunca faz push.

**Argumento:** $ARGUMENTS — descrição do problema ou erro. Se vazio, perguntar ao usuário.

---

## Regra fundamental

**NUNCA** durante esta skill:
- Usar `Write`, `Edit`, ou `Bash` com modificação de arquivo
- Usar `git add`, `git commit`, `git push`
- Criar arquivos novos

Se o problema for resolvível trivialmente: descrever o fix mas não aplicar.
Para aplicar um fix: encerrar o debug e sugerir `/fix <descrição>`.

---

## Passo 1 — Coletar descrição do problema

Se `$ARGUMENTS` não estiver vazio, usar como descrição. Senão, perguntar:
- O que está acontecendo?
- Em que arquivo ou fluxo o erro ocorre?
- O erro é de build, de runtime, ou de comportamento inesperado?

Antes de investigar: **listar o que não pode ser a causa** (raciocínio de base zero).
Isso evita bias de confirmação na investigação.

---

## Passo 2 — Investigação paralela

Lance os subagentes simultaneamente com Task tool (`run_in_background=true`).

**Subagente A — Xcode MCP:**

```text
1. XcodeListNavigatorIssues — erros e warnings no Issue Navigator
2. BuildProject — tentar build e capturar erros estruturados
3. Se build falhou: GetBuildLog para detalhes completos
4. Para cada arquivo com erro: XcodeRefreshCodeIssuesInFile
```

**Subagente B — Codebase:**

```text
Ler o(s) arquivo(s) relevantes mencionados na descrição do problema.
Ler CLAUDE.md para identificar armadilhas conhecidas que se aplicam ao erro.
Se existir LEARNINGS.md: verificar se o erro já foi documentado.
Retornar: conteúdo relevante dos arquivos com números de linha.
```

Aguardar com `TaskOutput`. Sintetizar antes de continuar.

---

## Passo 3 — Análise

Para cada erro encontrado:

1. Identificar o arquivo e número de linha exato
2. Ler o trecho relevante do arquivo (sem modificar)
3. Classificar: erro de tipo, erro de concorrência, API incorreta, lógica incorreta, configuração

**Verificar contra armadilhas conhecidas do CLAUDE.md:**
- Swift 6 / actor isolation
- SwiftData `let` vs `var`, thread-safety, save manual
- SwiftTerm DispatchQueue
- Curly quotes em string interpolation
- Bundle identifier em SPM binário
- Actor + I/O bloqueante

---

## Passo 4 — Relatório

Gerar o relatório no formato abaixo e salvá-lo em `.claude/debug-plans/<descrição-kebab>/report.md`
(criar o diretório se não existir). Exibir também na conversa.

`<descrição-kebab>` = primeira 3-4 palavras de `$ARGUMENTS` em kebab-case.

```text
## 🔍 Debug: <descrição curta>

### O que não pode ser a causa
- <eliminado A — por que>
- <eliminado B — por que>

### Causa raiz hipotética
<descrição precisa — arquivo + linha + por que>

### Evidências
- `<arquivo>:<linha>` — <trecho relevante>
- Issue Navigator: <erros listados>

### Armadilha conhecida?
<Sim — referência ao CLAUDE.md / LEARNINGS.md | Não — nova ocorrência>

### Fix sugerido
<Descrição textual do que precisa mudar — não aplicado>

Arquivo: `<path>`
Linha: <N>
Mudança: <o que fazer especificamente>

### Para aplicar
/fix <descrição concisa do problema>
```

---

## Quando usar

- Build falhou com erro críptico
- Comportamento inesperado em runtime sem stack trace claro
- Warning que não entende
- Quer investigar antes de decidir se vale criar uma feature ou fix
- Quer um segundo par de olhos antes de commitar

**Não usar para:**
- Implementar a solução — use `/fix` ou `/start-feature`
- Pesquisa de novas bibliotecas — use pesquisa direta
