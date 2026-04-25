# GitLab Delivery Workflow

## Scope
Delivery from GitHub repository to GitLab and CI/CD preparation.

## Steps
1. Verify git remotes (`origin`, optional `gitlab`).
2. Define branch strategy (main + feature branches):
   - Development commits/pushes only from feature branches.
   - Direct commit/push to `main` is not allowed.
   - Before every commit and push, mandatory checks must pass using make commands:
     - `make test`
     - `make quality`
   - If no active feature branch exists, propose a branch name then create/switch.
   - If task is complete on active feature branch and mandatory checks pass, commit and push only after explicit user approval.
3. After push, prepare pull request message package:
   - Target branch: `main` (unless explicitly requested otherwise).
   - PR text language: English.
   - Required PR body sections:
     - `## Summary`
     - `## Validation`
     - `## Notes`
   - Provide a prefilled compare URL (`quick_pull=1`) and the plain PR text.
4. Create CI pipeline file(s) (lint, test, build).
5. Integrate Docker image build/publish steps.
6. Document release checklist.

## Required Result
- Reproducible build and test execution in CI.
- Versioned and traceable deployment path.
- Change sets delivered through feature-branch-based commit/push flow with PR-ready English delivery package.
