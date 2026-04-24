# GitLab Delivery Workflow

## Scope
Delivery from GitHub repository to GitLab and CI/CD preparation.

## Steps
1. Verify git remotes (`origin`, optional `gitlab`).
2. Define branch strategy (main + feature branches):
   - Development commits/pushes only from feature branches.
   - Direct commit/push to `main` is not allowed.
   - If no active feature branch exists, propose a branch name then create/switch.
   - If task is complete on active feature branch, commit and push.
3. Create CI pipeline file(s) (lint, test, build).
4. Integrate Docker image build/publish steps.
5. Document release checklist.

## Required Result
- Reproducible build and test execution in CI.
- Versioned and traceable deployment path.
- Change sets delivered through feature-branch-based commit/push flow.
