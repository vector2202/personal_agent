---
name: graph_rag_memory_indexer
description: Stores and queries durable facts about the user as a graph of entities and relationships.
category: memory
action_field: action
capabilities: [db_write]
capability_overrides:
  QUERY: []
  SEARCH: []
  FIND_PATH: []
  GET_ALL: []
---

# Graph Memory

Long-term memory, stored as entities (nodes) and relationships between them
(edges). This is how facts survive between conversations — the chat history does
not.

## Choosing an action

**Writes** (the user is asked to approve these):
- **`INSERT`** — record an entity and its attributes. `entity` is required.
- **`RELATE`** — connect two entities. Requires `entity`, `relation`, and
  `target_entity`. Both endpoints are created automatically if they do not
  already exist, so there is no need to `INSERT` first.

**Reads** (no approval needed):
- **`QUERY`** — everything known about one entity, plus its incoming and
  outgoing relationships. Use when you know the entity's name.
- **`SEARCH`** — substring match across entity names, attributes, and relations.
  Use when you are not sure what the entity is called.
- **`FIND_PATH`** — shortest chain of relationships between two entities. This
  is what answers questions that span domains.
- **`GET_ALL`** — the entire graph. Only for small graphs or debugging; it grows
  without limit.

## Conventions that keep the graph useful

- **Relations are uppercase verbs**: `PREFERS`, `WORKS_ON`, `BUILT_WITH`,
  `LIVES_IN`. They are uppercased automatically, so stay consistent in tense
  and direction.
- **Entity names are the identity.** `"Victor"` and `"victor"` are two separate
  nodes. Reuse the exact spelling already in the graph — `SEARCH` first if
  unsure.
- Direction matters: `(Victor) -[WORKS_ON]-> (personal_agent)` reads naturally
  in that order. Do not reverse it.

## What belongs in here

Durable facts about the user, their preferences, projects, and how those things
connect. Not transient conversation state, and not anything another skill owns
authoritatively — expenses live in `expense_tracker`, not here.
