---
name: secure_terminal
description: Runs a non-interactive shell command and returns its output.
category: system
capabilities: [subprocess]
---

# Secure Terminal

Runs one shell command and returns exit code, stdout, and stderr.

**The user is asked to approve every single invocation, and that approval is
never remembered.** Expect to justify the command you are running.

## Use a purpose-built skill instead, where one exists

Shell access is the widest-blast-radius tool available. Before reaching for it:

- Inspecting Python structure → `repo_architecture_digest`
- Reading, writing or listing files → `file_access`
- Editing part of a file → `targeted_diff_applier`
- System stats → `system_health_monitor`

Use the terminal for things none of those cover: running a test suite,
inspecting `git` state, checking whether a command exists.

## Rules

- **Non-interactive only.** A command that waits for input will hit its timeout
  and be killed. No `vim`, no `top`, no prompts.
- Keep commands to a single purpose so the user can approve one clear action
  rather than an opaque chain.
- A non-zero exit code is reported as `success: false` with `stderr` populated —
  read it before retrying.
- There is a small denylist of catastrophic patterns, but it is **not a
  sandbox**. Assume anything you run will actually run.
