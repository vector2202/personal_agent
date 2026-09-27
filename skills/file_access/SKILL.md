---
name: file_access
description: Reads, writes, and lists files inside the agent's workspace directory.
category: dev
action_field: operation
capabilities: [filesystem_write]
capability_overrides:
  READ: [filesystem_read]
  LIST: [filesystem_read]
---

# File Access

Plain file I/O, restricted to the configured workspace root. Any path that
resolves outside that root is refused — this is enforced in code, so do not
try to reach absolute paths elsewhere on the machine.

## Choosing an operation

- **`READ`** — return a file's full text. Prefer `repo_architecture_digest`
  for Python source when you only need its structure; reading a whole file
  costs roughly 2,000 tokens.
- **`WRITE`** — create or overwrite a file. Requires `content`. Missing parent
  directories are created automatically.
- **`LIST`** — enumerate a directory, returning names, sizes, and whether each
  entry is a directory.

## Rules

- `file_path` is relative to the workspace root. `../` escapes are rejected.
- `WRITE` **replaces the entire file**. To change part of an existing file use
  `targeted_diff_applier` instead — it is far harder to destroy work with.
- `READ` on a missing file returns an error, not an empty string. Check the
  result rather than assuming success.
