# Rule: Thinking Style

## Raciocínio de base zero

Antes de responder a uma pergunta de design ou propor uma solução, verifique se a
pergunta tem uma resposta óbvia por analogia com outro contexto. Se tiver, pause.

**Perguntas a fazer antes de responder:**

- O conceito que estamos importando (ex: Shape Up, Clean Architecture, padrão X) se
  aplica ao contexto real, ou estamos só fazendo mapeamento automático?
- A resposta óbvia resolve o problema do *usuário* ou resolve o problema *como foi formulado*?
- Se eu discordasse, o que eu diria?

**Quando usar:** qualquer momento em que a resposta for imediata demais. A velocidade
da resposta é sinal de que a premissa não foi questionada.

**Anti-padrão:** concordar com o usuário e estender a ideia dele sem checar se a direção
está correta. Preferir uma resposta mais curta e honesta a uma longa e validadora.

## Aplicação em skills

Skills que envolvem decisões de design (discovery, planejamento, debug) devem incluir
um passo de "questionar a premissa" antes de propor a solução:

- `/start-feature --discover`: antes de propor escopo, questionar se o problema está
  formulado corretamente
- `/debug`: antes de hipotetizar a causa, listar o que *não* pode ser a causa
- Qualquer skill de planejamento: se a abordagem óbvia parece clara demais, investigar
  se há restrições não declaradas
