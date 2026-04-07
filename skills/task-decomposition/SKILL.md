---
name: task-decomposition
description: Break large implementation, refactor, migration, or architecture requests into smaller, testable steps with explicit checkpoints, dependency order, and rollback awareness. Use when the work spans multiple files, multiple layers, risky framework changes, or cannot be completed safely as a single blind edit.
---

# Task Decomposition

## Core Workflow

Use this skill to turn a broad request into a sequence of bounded changes that preserve momentum and verification quality.

1. Define the real target state in one sentence.
2. Separate `must-change now` from `can follow later`.
3. Identify the first thin slice that creates value without forcing the whole migration.
4. Order steps by dependency, not by convenience.
5. Add a verification checkpoint after every meaningful slice.
6. Keep compatibility surfaces stable until the new path is validated.

## Decomposition Rules

- Prefer slices that can be validated in isolation.
- Keep each slice focused on one of these shapes:
  - `structure`
  - `contract`
  - `execution`
  - `validation`
  - `cleanup`
- Preserve the current working path until the replacement path is proven.
- Avoid mixing migration work with optional polish in the same slice.
- When a change is risky, add an adapter or compatibility wrapper before replacing the old path.

## Slice Template

For each slice, define:

- Goal: what becomes true after this step.
- Write scope: which files or modules change.
- Compatibility note: what must keep working during the step.
- Verification: which command, import, build, or behavior proves it worked.
- Exit condition: what lets the next slice start.

## When To Split Further

Split a task again when any of these are true:

- one step touches unrelated layers
- one step has more than one main risk
- one step cannot be verified quickly
- one step mixes refactor and behavior change
- one step would be hard to roll back

## Migration Pattern

Use this order for large migrations:

1. Add the new path behind a stable interface.
2. Route one entry point through the new path.
3. Validate real behavior.
4. Expand usage.
5. Remove the legacy path only after the new path is trusted.

## Checkpoints

Before marking the work complete, confirm:

- imports still resolve
- the main entry point still runs
- the new path is actually exercised
- dead code from the replaced path is removed
- documentation reflects the new default path

Read [checkpoints.md](references/checkpoints.md) when the migration involves framework adoption, orchestration changes, or staged cleanup.

## Output Shape

When presenting the breakdown, prefer:

1. Target state
2. Current blockers
3. Ordered slices
4. What will be implemented now
5. What stays for later
