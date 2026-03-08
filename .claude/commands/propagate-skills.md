---
name: propagate-skills
description: Use when skills have been edited and need to be committed or synced. Handles project skills (git commit + PR) and global skills (~/.claude/ layer).
---

# /propagate-skills

Sincroniza edições de skills entre as duas camadas da arquitetura.
Detecta o que mudou, decide a ação certa por camada, e executa.

---

## Arquitetura de duas camadas

### Camada Global — `~/.claude/commands/`

Skills de criação de projetos e meta-skills. Não estão em nenhum repo git por padrão — vivem só no disco local.

| Skill | Responsabilidade |
|---|---|
| `start-project` | Bootstrap de novo projeto |
| `explore` | Exploração de domínio |
| `plan-roadmap` | Milestones e roadmap |
| `propagate-skills` | Esta skill — meta |
| `think` | Raciocínio estruturado |

### Camada de Projeto — `.claude/commands/`

Skills de workflow: `start-feature`, `ship-feature`, `validate`, `fix`, `start-milestone`, `close-feature`, `handover`, etc.
Estão no repo git do projeto. Criadas a partir do template `rmolines/claude-kickstart`.

---

## Regra de propagação por camada

| Mudança feita em | Ação |
|---|---|
| `.claude/commands/` (skill de projeto) | Commit + PR no repo atual — nunca direto em main |
| `~/.claude/commands/` (skill global) — melhoria geral | PR em `rmolines/claude-kickstart` para futuros projetos herdarem |
| `~/.claude/commands/` (skill global) — específica do workflow pessoal | Nada — fica só local, não propagar |
| `~/.claude/CLAUDE.md` ou `~/.claude/rules/` | Igual às globais: PR no kickstart se geral, local se pessoal |

---

## Fluxo de execução

### Passo 1 — Detectar mudanças

```bash
# Skills do projeto
git diff --name-only .claude/commands/
git diff --name-only --cached .claude/commands/

# Outras mudanças relevantes no repo
git status --short
```

Skills globais não são rastreadas por git — verificar manualmente quais foram editadas na sessão atual.

### Passo 2 — Propagar camada de projeto

Se há mudanças em `.claude/commands/` ou em arquivos de infra (CLAUDE.md, rules/):

1. Verificar se está em worktree ou branch de feature:
   ```bash
   git branch --show-current
   ```
   - Em `main`: criar branch `chore/skills-<slug>`
   - Em branch de feature existente: commitar junto (se relacionado) ou criar branch separada

2. Commitar com:
   ```text
   chore(skills): <descrição das mudanças>

   - <skill 1>: <o que mudou>
   - <skill 2>: <o que mudou>

   Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
   ```

3. Abrir PR via GitHub MCP (sempre com `owner` + `repo` explícitos — não usar `gh pr create` em worktree):

   ```text
   mcp__plugin_github_github__create_pull_request(
     owner: "<owner>",
     repo: "<repo>",
     title: "chore(skills): <descrição>",
     body: "...",
     head: "<branch>",
     base: "main"
   )
   ```

### Passo 3 — Propagar camada global (se aplicável)

Para cada skill global editada, decidir:

- **É melhoria geral** (qualquer projeto se beneficiaria) → PR em `rmolines/claude-kickstart`
- **É ajuste pessoal** (workflow específico do usuário) → Nada, fica local

Se PR no kickstart for necessário: usar GitHub MCP com `owner: "rmolines"`, `repo: "claude-kickstart"`.

### Passo 4 — Confirmar

```text
Skills propagadas.

Camada de projeto: PR #<N> — <url>
Camada global: <"PR em rmolines/claude-kickstart #<N>" | "skills locais — sem propagação necessária">
```

---

## Regras

- Nunca commitar diretamente em `main` — sempre PR
- Sempre usar GitHub MCP para criar PRs (independente de CWD — funciona de worktree, subdiretório, etc.)
- Mensagem de commit: `chore(skills): ...` + Co-Authored-By
- Se `make check` existir no projeto: rodar antes de abrir PR
- Skills de projeto que são melhorias gerais → considerar backport para `claude-kickstart`

---

## Detecção automática (quando usar esta skill)

Invocar esta skill quando:
- Acabou de editar skills em `.claude/commands/` ou `~/.claude/commands/`
- Usuário pergunta "como propago isso?" ou "como commito as skills?"
- Fim de uma sessão de manutenção de skills (audit, improve-skill, create-skill)
