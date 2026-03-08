# /handover

Gere uma entrada no `HANDOVER.md` resumindo esta sessão do Claude Code e adicione-a com append ao arquivo.

## Path do arquivo

Determine o path absoluto do repositório com:
```bash
git rev-parse --show-toplevel
```

Faça append em `$(git rev-parse --show-toplevel)/HANDOVER.md`.
Se o arquivo não existir, criar com um header de nível 1 antes da primeira entrada.

**Nunca hardcodar o path do HANDOVER.md** — sempre derivar via `git rev-parse --show-toplevel`.

## Instruções

Revise o histórico completo da conversa e produza um resumo conciso e estruturado no formato abaixo.
Depois faça **append** no arquivo (não sobrescrever).

### Formato a adicionar

```markdown
## <DATA-ATUAL>

### O que foi feito
- <lista de mudanças concretas>

### Decisões tomadas
- <decisão>: <justificativa>

### Armadilhas / lições aprendidas
- <gotcha ou lição>

### Próximos passos sugeridos
- <próximo passo acionável>

### Arquivos-chave modificados
- `path/to/file` — <descrição de uma linha>
```

## Regras

- Usar a data de hoje como header da seção no formato `YYYY-MM-DD`
- Ser concreto e específico — evitar afirmações vagas como "melhorou o código"
- Incluir apenas seções com conteúdo; omitir seções vazias
- Fazer append; nunca sobrescrever entradas existentes
- Após escrever, confirmar com: "HANDOVER.md atualizado (entrada YYYY-MM-DD adicionada)."
