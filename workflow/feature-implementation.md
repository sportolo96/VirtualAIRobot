# Feature Implementation Workflow

## Scope
Implementation of new features (API, queue, agent loop, runner, artifacts).

## Steps
1. Define API contract (request/response, validation, error codes).
2. Define domain model and use cases (DDD + CQRS).
3. Implement infrastructure adapters (OS capture/input, AI client, queue client).
4. Connect worker and API, update run statuses.
5. Add tests: unit + integration baseline path.
6. Ensure tests are mock-only: no real AI calls and no online/network scanning in test execution.
7. Run static checks: `mypy` (type analysis) and `ruff` (lint/fix).
8. If new environment keys are introduced, update `.env` and `.env.example` in the same change.
9. Never place real secrets in `.env.example`; placeholders only.
10. Review `deficiencies.md` before task closure and update it to current state (resolved items removed/updated, new gaps added).
11. Update `docs/` and update `README.md` when behavior changes.
12. When a cohesive change set is complete, verify the active branch.
13. Before every commit and push, run mandatory make checks: `make test` and `make quality`.
14. No commit/push to `main`; feature branch is required.
15. If no active feature branch exists, propose a branch name and create/switch to it.
16. If work is complete on an active feature branch and mandatory checks pass, wait for explicit user approval before commit and push.

## Required Result
- Reproducible run in Docker environment.
- Traceable run state and step trace.
- Cohesive change sets committed and pushed from feature branches.
