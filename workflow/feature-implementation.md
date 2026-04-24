# Feature Implementation Workflow

## Scope
Implementation of new features (API, queue, agent loop, runner, artifacts).

## Steps
1. Define API contract (request/response, validation, error codes).
2. Define domain model and use cases (DDD + CQRS).
3. Implement infrastructure adapters (OS capture/input, AI client, queue client).
4. Connect worker and API, update run statuses.
5. Add tests: unit + integration baseline path.
6. Run static checks: `mypy` (type analysis) and `ruff` (lint/fix).
7. Update `docs/` and update `README.md` when behavior changes.
8. When a cohesive change set is complete, verify the active branch.
9. No commit/push to `main`; feature branch is required.
10. If no active feature branch exists, propose a branch name and create/switch to it.
11. If work is complete on an active feature branch, commit and push.

## Required Result
- Reproducible run in Docker environment.
- Traceable run state and step trace.
- Cohesive change sets committed and pushed from feature branches.
