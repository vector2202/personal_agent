---
name: targeted_diff_applier
description: Replaces one exact block of text inside an existing file.
category: dev
capabilities: [filesystem_modify]
---

# Targeted Diff Applier

Finds one exact block of text in a file and swaps it for another, leaving the
rest of the file untouched. This is the safe way to edit code — far better than
rewriting a whole file with `file_access` WRITE, which discards anything you
did not reproduce perfectly.

**This modifies work that already exists, so the user is asked every time and
the approval is never saved permanently.**

## How to use it correctly

1. **Read the file first** (`file_access` READ or `repo_architecture_digest`).
   Never guess at the current contents.
2. Copy `target_block` **exactly** — including indentation, blank lines, and
   trailing spaces. Whitespace mismatches are the most common failure.
3. Make `target_block` long enough to be **unique** in the file.

## Failure modes, and what they mean

- *"target block was not found"* — your copy does not match byte-for-byte.
  Re-read the file rather than guessing again.
- *"Ambiguous match: appears N times"* — include more surrounding context so
  the block becomes unique. The edit is refused rather than applied to the
  wrong place.

Both failures leave the file **completely unchanged**, so it is always safe to
retry with a better block.

## Caution

`file_path` is **not** restricted to a workspace directory — this skill can
modify any file the process can reach. Only ever target files the user is
actually asking you to change.
