# Checkpoints

Use these checkpoints when breaking down larger migrations.

## Framework Adoption

- Add the framework path without deleting the current working path.
- Route one production path through it first.
- Verify with a real execution, not just imports.
- Remove legacy glue only after the new path is serving the real request.

## Multi-Layer Changes

- Separate backend contract changes from frontend rendering changes.
- Keep transport shapes stable while internals move.
- Avoid changing storage, orchestration, and UI copy in one step unless required.

## Cleanup Pass

- Search for stale imports, routes, configs, and docs.
- Remove dead files only after the replacement path is exercised.
- Re-run the smallest realistic end-to-end check after cleanup.
