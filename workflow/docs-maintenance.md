# Documentation Maintenance Workflow

## Scope
Any code or structural change in the VirtualAIRobot project.

## Mandatory Rule
- A functional change is complete only with documentation updates.
- For behavior changes, `README.md` updates are also mandatory.
- If new environment keys are added, both `.env` and `.env.example` must be updated.
- `.env.example` must never contain real secrets.
- `deficiencies.md` must be reviewed and updated to the current status in the same change set.

## What to Update
- API contract change: `docs/system-design.md` API section.
- Queue/state machine change: `docs/system-design.md` Run Lifecycle section.
- Agent loop or action logic change: `docs/system-design.md` Execution Loop section.
- Runtime/config change: `docs/system-design.md` Deployment and Runtime Config section.
- Usage/testing/operations change: relevant sections in `README.md`.
