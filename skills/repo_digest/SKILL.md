---
name: repo_architecture_digest
description: Lists the classes, functions, and docstrings in a Python file.
category: dev
capabilities: [filesystem_read]
---

# Repo Architecture Digest

Parses a Python file with the `ast` module and returns its structure: class
names, their methods, top-level functions with argument names, docstrings, and
line numbers.

## Why prefer this over reading the file

Reading a source file costs roughly 2,000 tokens. This returns a structural
summary for a fraction of that, and the parsing happens locally — no model
inference is involved, so the result is exact rather than inferred.

Reach for this first when the question is *what is in this file* or *where is
X defined*. Only fall back to `file_access` READ when you need the actual
implementation of something specific.

## Limits

- **Python only.** Any other language returns a syntax error.
- **Top-level definitions only.** Classes nested inside functions, or functions
  defined inside other functions, are not reported.
- Async functions (`async def`) at the top level are not currently captured.
- A file that does not parse returns the syntax error and nothing else — useful
  in itself for spotting broken files.
