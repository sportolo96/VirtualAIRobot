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

## AI Initialization
Current state:
- The project currently uses a local stub AI pipeline.
- No API key is required for the current baseline runtime.

Initialize environment for real provider integration:
1. Create a `.env` file in project root:
```bash
cat > .env <<'EOF'
AI_PROVIDER=openai
AI_MODEL=chatgpt-5.4
OPENAI_API_KEY=your_real_key_here
EOF
```
2. Start with env file:
```bash
docker compose --env-file .env up --build
```

Note:
- `OPENAI_API_KEY` is prepared for the upcoming real provider binding.
- Until provider binding is implemented, runtime behavior is still stub-based.

## How to test and use
1. Start the stack:
```bash
docker compose up --build
```

2. Verify API health:
```bash
curl -sS http://localhost:8000/health
```

3. Create a run:
```bash
RUN_RESPONSE=$(curl -sS -X POST http://localhost:8000/v1/runs \
  -H 'Content-Type: application/json' \
  -d '{
    "goal":"Open profile page",
    "start_url":"https://example.com/login",
    "success_criteria":{"type":"text_or_dom","must_include":["Profile"],"must_not_include":["Error"]},
    "runtime":{"mode":"container_desktop","viewport":{"width":1080,"height":1920}},
    "limits":{"max_steps":5,"time_budget_sec":60,"max_retries_per_step":1},
    "allowed_actions":["move","click","scroll","type","key","wait","done","failed"],
    "llm":{"planner_model":"chatgpt-5.4","evaluator_model":"chatgpt-5.4"}
  }')
echo "$RUN_RESPONSE"
RUN_ID=$(echo "$RUN_RESPONSE" | python3 -c 'import json,sys; print(json.load(sys.stdin)["run_id"])')
echo "$RUN_ID"
```

4. Poll run status:
```bash
curl -sS http://localhost:8000/v1/runs/$RUN_ID
```

5. Inspect step trace:
```bash
curl -sS http://localhost:8000/v1/runs/$RUN_ID/steps
```

6. Cancel a run manually if needed:
```bash
curl -sS -X POST http://localhost:8000/v1/runs/$RUN_ID/cancel
```

7. Run tests locally:
```bash
python3 -m pytest -q
```

## Static Analysis and Auto-Fix
PHPStan-like static type check:
```bash
make typecheck
```

Lint check:
```bash
make lint
```

Auto-fix (lint + formatting), then type check:
```bash
make quality-fix
```

Full quality gate:
```bash
make quality
```
