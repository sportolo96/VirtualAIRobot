# VirtualAIRobot

VirtualAIRobot is a Dockerized API + worker system for goal-based OS/browser automation.  
You submit a goal, the worker executes step-by-step actions, and every step is stored with screenshots and evaluation.

## What It Does
- Runs asynchronous automation jobs through `api` + `worker` + `redis`.
- Captures `pre` and `post` screenshots on each step.
- Uses AI planner/evaluator pipelines to decide and evaluate next actions.
- Executes allowed OS actions (`move`, `click`, `scroll`, `type`, `key`, `wait`) in container desktop runtime.
- Returns run status, step trace, and terminal result (`done` -> `succeeded`, `failed` -> `failed`).

## Services
- `api`: Flask HTTP API
- `worker`: RQ worker
- `redis`: queue and run-state store

## API Endpoints
- `POST /v1/runs`
- `GET /v1/runs/{run_id}`
- `GET /v1/runs/{run_id}/steps`
- `POST /v1/runs/{run_id}/cancel`
- `POST /webhooks/run-completion`
- `GET /health`

## Quickstart
```bash
cp .env.example .env
make build
make start
make check
```

## Configuration
The runtime uses env configuration only.

### AI Provider And Model Settings
```bash
AI_PROVIDER=openai
AI_FALLBACK_PROVIDERS=azure_openai
AI_MODEL=gpt-5.4
PLANNER_MODEL=gpt-5.4
EVALUATOR_MODEL=gpt-5.4

OPENAI_API_KEY=replace_with_real_key
AZURE_OPENAI_API_KEY=replace_with_azure_key
AZURE_OPENAI_API_BASE_URL=https://your-resource.openai.azure.com/openai/v1
AZURE_OPENAI_API_VERSION=2024-10-21
```

Notes:
- `AI_PROVIDER` supports `openai` and `azure_openai`.
- `AI_FALLBACK_PROVIDERS` is ordered fallback chain.
- Model selection is env-driven (`PLANNER_MODEL`, `EVALUATOR_MODEL`), not request-driven.

### API Auth
```bash
API_AUTH_ENABLED=true
API_AUTH_KEY=replace_with_shared_key
API_AUTH_CLIENTS_JSON=[]
```

Auth modes:
- Shared key: `API_AUTH_KEY`.
- Per-client rotating keys + roles: `API_AUTH_CLIENTS_JSON`.

Role checks:
- `runs.read`: `GET /v1/runs/*`
- `runs.write`: `POST /v1/runs`, `POST /v1/runs/*/cancel`

### Outgoing Completion Webhook
```bash
WEBHOOK_ENABLED=true
WEBHOOK_TIMEOUT_SEC=10
WEBHOOK_MAX_RETRIES=3
WEBHOOK_RETRY_BACKOFF_SEC=1.0
WEBHOOK_SIGNING_SECRET=replace_with_signing_secret
WEBHOOK_DEAD_LETTER_DIR=artifacts/dead_letters
```

### Incoming Webhook Receiver Enforcement
```bash
WEBHOOK_RECEIVER_ENABLED=true
WEBHOOK_RECEIVER_SIGNING_SECRET=replace_with_receiver_secret
WEBHOOK_RECEIVER_REQUIRE_SIGNATURE=true
WEBHOOK_RECEIVER_MAX_AGE_SEC=300
WEBHOOK_RECEIVER_IDEMPOTENCY_TTL_SEC=86400
```

Receiver reference: `docs/webhook-receiver-validation.md`

### Runtime Defaults
```bash
DEFAULT_VIEWPORT_WIDTH=1920
DEFAULT_VIEWPORT_HEIGHT=1080
```

## Create A Run
```bash
RUN_RESPONSE=$(curl -sS -X POST http://localhost:8000/v1/runs \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: replace_with_api_key_if_enabled' \
  -d '{
    "goal":"Open profile page",
    "start_url":"https://example.com/login",
    "success_criteria":{"type":"text_or_dom","must_include":["Profile"],"must_not_include":["Error"]},
    "runtime":{"mode":"container_desktop","viewport":{"width":1080,"height":1920}},
    "limits":{"max_steps":5,"time_budget_sec":60,"max_retries_per_step":1},
    "allowed_actions":["move","click","scroll","type","key","wait","done","failed"],
    "callbacks":{"completion_url":"https://example.test/webhook","headers":{"X-Webhook-Key":"abc"}}
  }')

echo "$RUN_RESPONSE"
RUN_ID=$(printf '%s' "$RUN_RESPONSE" | python3 -c 'import json,sys; data=json.load(sys.stdin); print(data.get("run_id",""))')
echo "$RUN_ID"
```

Poll and inspect:
```bash
curl -sS -H 'X-API-Key: replace_with_api_key_if_enabled' http://localhost:8000/v1/runs/$RUN_ID
curl -sS -H 'X-API-Key: replace_with_api_key_if_enabled' http://localhost:8000/v1/runs/$RUN_ID/steps
```

## Quality Gates
```bash
make test
make lint
make typecheck
make quality
```

Test policy:
- Tests are mock-only and network-blocked.
- No real AI calls and no live online scanning in tests.

## Related Docs
- `docs/system-design.md`
- `docs/webhook-receiver-validation.md`
- `deficiencies.md`
