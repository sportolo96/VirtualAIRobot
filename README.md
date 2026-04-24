# VirtualAIRobot

API-first, queue-based AI/OS automation baseline built with Python, Flask, Redis, RQ, and LangChain pipeline orchestration.

Runtime outcome policy:
- If the planner returns action `done`, the run is marked as `succeeded`.
- If the planner returns action `failed`, the run is marked as `failed`.

## Services
- `api`: Flask HTTP API
- `worker`: RQ worker processing run loops
- `redis`: queue and run state store

## Endpoints
- `POST /v1/runs`
- `GET /v1/runs/{run_id}`
- `GET /v1/runs/{run_id}/steps`
- `POST /v1/runs/{run_id}/cancel`
- `GET /health`

## Quickstart
```bash
docker compose up --build
```

Create a run:
```bash
curl -sS -X POST http://localhost:8000/v1/runs \
  -H 'Content-Type: application/json' \
  -d '{
    "goal":"Open profile page",
    "start_url":"https://example.com/login",
    "success_criteria":{"type":"text_or_dom","must_include":["Profile"],"must_not_include":["Error"]},
    "runtime":{"mode":"container_desktop","viewport":{"width":1080,"height":1920}},
    "limits":{"max_steps":5,"time_budget_sec":60,"max_retries_per_step":1},
    "allowed_actions":["move","click","scroll","type","key","wait","done","failed"],
    "llm":{"planner_model":"chatgpt-5.4","evaluator_model":"chatgpt-5.4"}
  }'
```

Run tests:
```bash
pytest
```
