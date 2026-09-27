---
name: github_portfolio_discoverer
description: Lists a GitHub user's public repositories with languages, topics, and star counts.
category: career
capabilities: [network]
---

# GitHub Portfolio Discoverer

Fetches a user's public repositories from the GitHub API, most recently updated
first, returning name, description, primary language, topics, stars, forks, and
last-updated timestamp.

## Rules

- `username` is a GitHub login, not a display name or email.
- **Forks are excluded** — only original repositories are returned.
- `topic_filter` matches GitHub repository topics, not languages or names. It is
  case-insensitive, and a repo with no topics will never match a filter.
- `limit` is 1–30 (default 5).

## Limits worth knowing

- **Unauthenticated**, so private repositories are invisible and the API allows
  only about 60 requests per hour from one address. Do not call this repeatedly
  in a loop.
- `stars` and `forks` are live counts at fetch time, so they will drift between
  calls. Do not treat an old number as current.
- Combine with `graph_rag_memory_indexer` to record durable conclusions about
  the user's work. The repository list itself is live data and should be
  re-fetched rather than remembered.
