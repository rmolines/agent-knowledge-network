# Rule: Skill Workflow

Mapa completo das skills, quando usar cada uma, e como se relacionam.

> Contratos invariantes entre skills: ver `~/.claude/rules/skill-contracts.md`.
> Princípio central: skills leem o `## Handoff` section do artefato anterior por path convention; gate humano é relocado para revisão do bloco antes do `/clear`.

---

## Fluxo visual

```text
EXPLORAÇÃO (antes de criar um projeto)
──────────────────────────────────────────
  /explore [intuição] → explore.md → /start-project

ESTRATÉGICO (uma vez por projeto/milestone)
──────────────────────────────────────────
  /start-project → /plan-roadmap → /start-milestone

TÁTICO (por feature)
──────────────────────────────────────────
  /start-feature [--deep] → [implementar] → /validate → /ship-feature (simplify automático) → /close-feature

ORIENTAÇÃO (qualquer momento)
──────────────────────────────────────────
  /project-compass

INVESTIGAÇÃO (sem commit)
──────────────────────────────────────────
  /debug <descrição> → relatório de causa raiz → /fix (se necessário)

PITCH / DISCOVERY (antes do bet)
──────────────────────────────────────────
  /start-feature --discover <nome> → discovery.md + research.md → bet → /start-feature <nome>

AD-HOC (feature sem roadmap)
──────────────────────────────────────────
  /start-feature <nome> → [implementar] → /ship-feature → /close-feature
```

---

## Tabela de skills

| Skill | Quando usar | Input | Output | Próxima skill |
|-------|-------------|-------|--------|---------------|
| `/explore` | Explorar domínio desconhecido antes de criar projeto | Intuição/pergunta | `explore.md` com mapa + hipótese | `/start-project` ou `/explore --deepen` |
| `/explore --fast` | Scan rápido (≈ antigo refine-idea) | Ideia | Brief estruturado | `/start-project` |
| `/start-project` | Criar repositório do zero | Brief aprovado | Repo + skills especializadas | `/plan-roadmap` |
| `/plan-roadmap` | Definir milestones e features | Projeto existente | `roadmap.md` atualizado | `/start-milestone` |
| `/start-milestone` | Começar um novo milestone | `roadmap.md` ou `backlog.json` | `<M>/sprint.md` com features | `/start-feature` |
| `/start-feature` | Começar implementação (default: fast, sem pesquisa) | Nome da feature | Worktree + `plan.md` | `/validate`, `/ship-feature` |
| `/start-feature --deep` | Feature complexa que precisa de pesquisa técnica | Nome da feature | `research.md` + `plan.md` + worktree | `/validate`, `/ship-feature` |
| `/start-feature --discover` | Explorar um problema antes de fazer o bet | Nome/ideia | `discovery.md` + `research.md` (para sem worktree) | `/start-feature <nome>` |
| `/debug` | Investigar erro sem modificar nada | Descrição do problema | Relatório de causa raiz + fix sugerido | `/fix` (opcional) |
| `/validate` | Verificar alinhamento antes de fazer PR | Branch com código | Relatório drift/cobertura | `/ship-feature` ou correção |
| `/ship-feature` | Abrir PR após implementação | Código pronto | PR aberto no GitHub | `/close-feature` |
| `/close-feature` | Limpar após PR merged | PR merged | Worktree removido + docs + `backlog.json` atualizados | `/project-compass` |
| `/project-compass` | "Onde estou? O que fazer agora?" | Nenhum (lê git + `backlog.json` + sprint.md) | Relatório de estado + próxima ação | Varia |
| `/handover` | Passar contexto para outro agente | Branch atual | Resumo de estado da sessão | — |

---

## Estado = backlog.json + git + sprint.md

| Pergunta | Como descobrir |
|----------:|---------------|
| O que foi entregue? | `backlog.json` features com `status=done` · ou `gh pr list --state merged` |
| O que está em andamento? | `backlog.json` features com `status=in-progress` · ou `git branch -a \| grep feature/` |
| O que está planejado? | `backlog.json` features com `status=pending` · ou checkboxes `- [ ]` nos `sprint.md` |
| Qual milestone atual? | `backlog.json` milestone com `status=active` · ou primeiro com features pendentes |
| Próxima feature? | Primeiro `status=pending` no `backlog.json` do milestone ativo |
| Pitches sem bet? | `backlog.json` array `pitches` com `status=awaiting-bet` |

`backlog.json` é fonte primária quando existe; `sprint.md` e git são fallback e complemento.

---

## Caminho para drift

Se em qualquer momento você não souber onde está no projeto, rode `/project-compass`.
Essa skill lê git e sprint.md e sintetiza o estado atual — sem precisar lembrar de nada.

**Frases que indicam que você precisa do `/project-compass`:**
- "onde estamos no projeto?"
- "o que falta para este milestone?"
- "qual a próxima feature?"
- "estou perdido, o que devo fazer?"
