# AGENTS

## Workflow Source
- Project workflow rules are defined in `workflow/*.md` files.
- Every new task must follow the appropriate workflow.

## Runtime Agents
- Planner Agent: proposes the next action toward the goal based on screenshots.
- Evaluator Agent: checks whether the latest action moved the run closer to success.
- Safety Agent: enforces action filtering and guardrails (forbidden actions, budget limits, loop protection).

## Documentation Rule
- For every behavior, API, queue, workflow, or runtime change, update the related `docs/*.md` files in the same change.

## Scope Rule
- The project is API-first: runtime configuration must come only from API requests.
- Scenario `.md` input is not part of the system.
