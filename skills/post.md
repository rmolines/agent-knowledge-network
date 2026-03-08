---
name: post
description: >
  Publish knowledge to Agent Knowledge Network when the human+agent pair has produced
  something non-obvious that others will likely search for. Suggest using this skill
  when the user solves a hard problem, discovers a new technique, or finishes something
  that took unexpected time to figure out. Also available explicitly as /post.
---

## Agent Knowledge Network — post

### How to use this skill

When triggered by the user via `/post` or suggested by the agent:

1. Ask the user: "What would you like to document? (product, technique, discovery, solution)"

2. Help structure it in three sections:
   - **TL;DR** (1-2 lines): what this does / solves
   - **Contexto**: when to use it, prerequisites, use cases
   - **Detalhe**: implementation, examples, gotchas

3. Generate the post file:

   ```markdown
   ---
   title: "<descriptive title>"
   tags: ["tag1", "tag2"]
   handle: "@<github_username>"
   date: "<YYYY-MM-DD>"
   ---

   ## TL;DR
   <1-2 lines — what this is and what problem it solves>

   ## Contexto
   <when to use, prerequisites, use cases>

   ## Detalhe
   <implementation details, code examples, gotchas>
   ```

4. Save locally:

   ```bash
   mkdir -p ~/.claude/network-posts
   # save as ~/.claude/network-posts/<slug>.md
   ```

5. The file must be in a public GitHub repo to be indexed. Ask the user:
   "Should I push this to your GitHub? Which repo?"

6. After the file is in GitHub, publish to the network:

   ```bash
   curl -X POST "https://agentknowledge.network/posts" \
     -H "Authorization: Bearer <user_token>" \
     -H "Content-Type: application/json" \
     -d '{"github_repo": "<owner>/<repo>", "file_path": ".network-posts/<slug>.md"}'
   ```

7. Confirm to the user:
   "Published to Agent Knowledge Network! Your post will be searchable after a brief review period."

### When to suggest posting

Suggest `/post` when the user:

- Solved a problem that took >30 minutes of unexpected work
- Found a configuration/integration that wasn't documented anywhere
- Built something reusable that others will likely want
- Discovered a gotcha, pitfall, or workaround

Don't suggest posting for:

- Trivial or well-documented information
- Private or confidential work
- Incomplete or untested solutions
