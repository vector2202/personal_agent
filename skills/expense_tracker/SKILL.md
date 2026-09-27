---
name: expense_tracker
description: Logs, tracks, and analyzes personal expenses in a local database.
category: finance
action_field: action
capabilities: [db_write]
capability_overrides:
  ANALYZE: []
  LIST: []
---

# Expense Tracker

Deterministic expense storage and aggregation over a local SQLite database.
All arithmetic happens in SQL — never compute totals or percentages yourself.

## Choosing an action

- **`LOG`** — the user mentions spending money or buying something, in any
  tense or language. This writes to the database.
- **`ANALYZE`** — the user asks where their money went, for a breakdown, for
  a summary, or how they could save. Returns category totals, top merchants,
  and recent transactions. Read-only.
- **`LIST`** — the user wants to see recent transactions as-is, without
  analysis. Read-only.

## Logging rules

- `amount` must be a positive number. `"45"`, `"forty five"` and `-45` are all
  rejected — send `45`.
- `date` defaults to today. Only set it when the user names a different day,
  and always format as `YYYY-MM-DD`.
- `merchant` is *who was paid* (Amazon, Uber, Starbucks). `description` is
  *what was bought* ("toy for nephew", "airport ride"). Do not merge them.
- If the user does not imply a category, omit it — the skill files the expense
  under `General/Uncategorized` rather than guessing.

## Categories

Prefer an existing category so aggregation stays meaningful:
`Food & Dining`, `Groceries`, `Transportation`, `Shopping`, `Entertainment`,
`Utilities`, `Health`.

## Multilingual input

The user writes in Spanish as often as English. `"gasté 180 pesos en uber al
aeropuerto"` is `LOG` with `amount=180`, `merchant="Uber"`,
`category="Transportation"`, `description="airport ride"`. Currency words
(pesos, dólares) describe the amount — they are not part of it, and there is no
currency field. Amounts are stored as plain numbers.
