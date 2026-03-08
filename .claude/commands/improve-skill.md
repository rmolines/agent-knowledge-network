# /improve-skill

Você é um assistente executando o skill `/improve-skill`.

Este skill orquestra o ciclo completo de melhoria de uma skill existente no kickstart:
editar a versão canônica em `~/git/claude-kickstart`, abrir PR, e sincronizar de volta ao projeto.

**Argumento:** `$ARGUMENTS` — nome da skill (kebab-case) e descrição opcional da melhoria

---

## Passo 1 — Identificar skill e melhoria

### 1.1 — Extrair nome e descrição de `$ARGUMENTS`

Formato esperado: `<nome-da-skill> [descrição opcional da melhoria]`

- Se não houver argumento: perguntar o nome da skill (kebab-case) antes de continuar
- Se houver nome mas não descrição: continuar para 1.2 e perguntar a descrição depois
- Extrair apenas o primeiro token como nome; o restante é descrição preliminar

### 1.2 — Localizar o kickstart

Checar se `~/git/claude-kickstart` existe:

```bash
ls ~/git/claude-kickstart/.claude/commands/ 2>/dev/null || echo "NOT_FOUND"
```

Se não existir, tentar resolver via remote do projeto atual:

```bash
git remote get-url upstream 2>/dev/null || echo "NO_UPSTREAM"
```

Se ainda não encontrar: informar o usuário e encerrar.

### 1.3 — Verificar que a skill existe no kickstart

```bash
ls ~/git/claude-kickstart/.claude/commands/<nome>.md 2>/dev/null || echo "NOT_FOUND"
```

**Se a skill NÃO existir no kickstart:**

```text
Skill '<nome>' não existe em ~/git/claude-kickstart/.claude/commands/.

Use `/create-skill` para criar skills novas direto no kickstart.
/improve-skill só melhora skills que já existem na versão canônica.
```

Encerrar.

### 1.4 — Ler ambas as versões

Ler em paralelo:
- Versão do projeto atual: `.claude/commands/<nome>.md`
- Versão do kickstart: `~/git/claude-kickstart/.claude/commands/<nome>.md`

Se a versão do projeto não existir: avisar mas continuar (skill pode existir só no kickstart).

### 1.5 — Mostrar diff resumido (se ambas existirem)

Executar:

```bash
diff .claude/commands/<nome>.md ~/git/claude-kickstart/.claude/commands/<nome>.md
```

Apresentar o diff ao usuário de forma legível (não raw `diff` output — sintetizar as diferenças).

### 1.6 — Extrair ou perguntar a melhoria

Se a descrição foi passada em `$ARGUMENTS`: confirmá-la com o usuário.
Se não foi passada: perguntar:

```text
Qual melhoria você quer fazer no skill '<nome>'?
(Descreva o comportamento atual que está errado/ausente e o comportamento esperado após a melhoria.)
```

Aguardar resposta antes de continuar.

---

## Passo 2 — Aplicar melhoria no kickstart

### 2.1 — Criar branch no kickstart

```bash
cd ~/git/claude-kickstart
git fetch origin
git checkout -b improve/<nome>-$(date +%Y%m%d) origin/main
```

### 2.2 — Editar a skill

Editar `~/git/claude-kickstart/.claude/commands/<nome>.md` com a melhoria acordada.

Regras:
- Manter o estilo e formato da skill existente
- Não remover comportamentos existentes sem aprovação explícita do usuário
- Mudanças devem ser mínimas e focadas na melhoria descrita
- Comentar mudanças não óbvias com `<!-- TODO: ... -->` se necessário

### 2.3 — Mostrar diff final e aguardar confirmação

Executar:

```bash
cd ~/git/claude-kickstart
git diff .claude/commands/<nome>.md
```

Apresentar o diff de forma legível e perguntar:

```text
Diff acima reflete a melhoria. Deseja commitar?
- Sim → prosseguir para Passo 3
- Ajustar → descreva o ajuste e voltarei ao 2.2
- Cancelar → encerrar sem commitar
```

Aguardar confirmação antes de continuar.

---

## Passo 2.5 — Otimização de description (opcional)

Após aplicar a melhoria, oferecer **somente se a melhoria tocou no campo `description` do frontmatter**:

> "Quer rodar o description optimizer do skill-creator para medir se o trigger melhorou?
> (usa run_loop.py: 20 queries, 5 iterações, split train/test 60/40)"

**Se sim:** invocar `skill-creator` com `--eval-set` apontando para a skill editada.
Aguardar `best_description` e aplicar ao frontmatter antes de commitar.

**Se não:** prosseguir direto para Passo 3 (commit + PR).

Não oferecer este passo se a melhoria não tocou no campo `description` do frontmatter.

---

## Passo 3 — Commit + PR no kickstart

### 3.1 — Commit

Derivar `<descrição-curta>` da melhoria (máx. 50 chars, imperativo):

```bash
cd ~/git/claude-kickstart
git add .claude/commands/<nome>.md
git commit -m "improve(<nome>): <descrição-curta>"
```

### 3.2 — Push e PR

```bash
cd ~/git/claude-kickstart
git push origin improve/<nome>-<data>
# gh pr create pode detectar repo errado em worktrees — usar gh api diretamente:
gh api repos/rmolines/claude-kickstart/pulls \
  --method POST \
  -f title="improve(<nome>): <descrição-curta>" \
  -f head="improve/<nome>-<data>" \
  -f base="main" \
  -f body="## O que muda

<descrição completa da melhoria — comportamento antes vs. depois>

## Motivação

<por que esta melhoria é necessária — problema que resolve>

## Impacto em projetos que usam esta skill

<low/medium/high — e o que muda para o usuário da skill>

🤖 Generated with [Claude Code](https://claude.com/claude-code)" \
  --jq '.html_url'
```

Exibir a URL do PR ao usuário.

---

## Passo 4 — Aguardar merge e sincronizar

### 4.1 — Aguardar confirmação de merge

```text
PR aberto: <URL>

Aguardando merge. Avise quando o PR for merged para sincronizar ao projeto atual.
```

Aguardar confirmação do usuário.

### 4.2 — Sincronizar ao projeto atual

Após confirmação de merge:

```bash
cd <projeto-original>
make sync-skills
```

Se `make sync-skills` não existir: informar o usuário e sugerir verificar o Makefile.

### 4.3 — Verificar sincronização

```bash
cat .claude/commands/SYNC_VERSION
cat ~/git/claude-kickstart/.claude/commands/SYNC_VERSION
```

Se os valores baterem: confirmar sincronização bem-sucedida.
Se não baterem: avisar e sugerir rodar `make sync-skills` novamente.

Ao final, exibir:

```text
✅ Sincronização concluída.

Skill '<nome>' atualizada:
- kickstart: ~/git/claude-kickstart/.claude/commands/<nome>.md
- projeto:   .claude/commands/<nome>.md
- SYNC_VERSION: <valor>
```

---

## Regras gerais

- **Nunca commitar diretamente em `main` do kickstart** — sempre branch + PR
- **Sempre mostrar diff antes de commitar** — nunca commitar sem confirmação do usuário
- **Se skill não existir no kickstart**: recusar e redirecionar para `/create-skill`
- **Escopo mínimo**: editar apenas o arquivo da skill — não tocar outros arquivos do kickstart
- **Fora de escopo**: criar skills novas (use `/create-skill --upstream`)
