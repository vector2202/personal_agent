---
name: automated_test_generator
description: Generates a pytest skeleton for the functions and classes in a Python file.
category: dev
capabilities: [filesystem_read, filesystem_write]
---

# Automated Test Generator

Parses a Python file and emits a runnable pytest file containing one test stub
per public function and one test class per public class.

## What it actually produces — read this before promising the user tests

The generated tests are **skeletons, not real assertions**. Each function gets
a `hasattr` existence check plus an empty `pass` body for edge cases. They will
run and pass immediately without testing any behaviour.

Treat the output as scaffolding: a correctly-named, correctly-imported file with
the boring structure already written. Filling in real assertions is a separate
job, and you should tell the user that rather than implying coverage exists.

## Rules

- Names starting with `_` are skipped as private.
- **Nothing is written to disk unless `output_test_path` is provided.** Without
  it the generated code is returned in the response only. The `saved_to_file`
  field says which happened — check it before telling the user a file exists.
- The import line is derived from the source path, so generated tests only work
  when run from the project root.
