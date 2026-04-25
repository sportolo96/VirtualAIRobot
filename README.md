# VirtualAIRobot

API-first, queue-based AI/OS automation baseline built with Python, Flask, Redis, RQ, and LangChain pipeline orchestration.

Runtime outcome policy:
- If the planner returns action `done`, the run is marked as `succeeded`.
- If the planner returns action `failed`, the run is marked as `failed`.

## Services
- `api`: Flask HTTP API
- `worker`: RQ worker processing run loops
- `redis`: queue and run state store

Screenshot runtime policy:
- Each step captures real OS-level screenshots (`pre` and `post`) from the active desktop session.
- Screenshot output size is normalized to the requested `runtime.viewport` per run.
- Screenshots include a visible cursor overlay marker so AI coordinates can be audited.
- The same screenshot image files are sent to planner and evaluator OpenAI calls as image input.

## Endpoints
- `POST /v1/runs`
- `GET /v1/runs/{run_id}`
- `GET /v1/runs/{run_id}/steps`
- `POST /v1/runs/{run_id}/cancel`
- `GET /health`

## Quickstart
```bash
make build
make start
make check
```

## AI Initialization
Current state:
- Planner and evaluator use live OpenAI Responses API calls.
- Run creation is blocked if AI runtime config or connectivity is missing.

Initialize environment for real provider integration:
1. Create your local `.env` from template:
```bash
cp .env.example .env
```
2. Edit `.env` with your real values:
```bash
AI_PROVIDER=openai
AI_MODEL=gpt-5.4
OPENAI_API_KEY=your_real_key_here
API_AUTH_ENABLED=false
API_AUTH_KEY=your_shared_api_key_here
WEBHOOK_ENABLED=false
WEBHOOK_TIMEOUT_SEC=10
WEBHOOK_MAX_RETRIES=3
WEBHOOK_RETRY_BACKOFF_SEC=1.0
WEBHOOK_SIGNING_SECRET=your_webhook_signing_secret_here
WEBHOOK_DEAD_LETTER_DIR=artifacts/dead_letters
DEFAULT_VIEWPORT_WIDTH=1080
DEFAULT_VIEWPORT_HEIGHT=1920
```
3. Start services:
```bash
make build
make start
```

Note:
- `OPENAI_API_KEY` is mandatory for `POST /v1/runs`.
- If `OPENAI_API_KEY` is missing, `POST /v1/runs` returns `503`.
- If OpenAI runtime connectivity check fails, `POST /v1/runs` returns `503`.
- API auth can be enabled with `API_AUTH_ENABLED=true`.
- When enabled, `/v1/*` endpoints require `X-API-Key` header.
- `GET /health` remains public.
- Completion webhook delivery can be enabled with `WEBHOOK_ENABLED=true`.
- Failed webhook deliveries are retried and then written to dead-letter JSON files.
- `WEBHOOK_SIGNING_SECRET` is optional for compatibility; callbacks still work without signature headers.
- If `WEBHOOK_SIGNING_SECRET` is set, callback requests include:
  - `X-VAR-Timestamp`
  - `X-VAR-Idempotency-Key`
  - `X-VAR-Signature` (`sha256=<hex>` over `timestamp.body`)
- Webhook best practice (recommended):
  - Enable `WEBHOOK_SIGNING_SECRET` in production.
  - Verify signature on the receiver side and reject stale timestamps (for example older than 5 minutes).
  - Store and deduplicate `X-VAR-Idempotency-Key` (for example TTL 24 hours).
  - Rotate webhook secrets with overlap support to avoid callback downtime.
- Docker make targets use `docker compose --env-file .env` explicitly (`make build`, `make start`).
- If `.env` is missing, Docker make targets fail fast.
- Default run viewport is read from `.env` (`DEFAULT_VIEWPORT_WIDTH`, `DEFAULT_VIEWPORT_HEIGHT`) when request payload omits `runtime.viewport`.
- `.env.example` contains placeholders only; never store real keys in `.env.example`.

## Production profile (recommended)
Compatibility note:
- `WEBHOOK_SIGNING_SECRET` remains optional in runtime behavior for backward compatibility.
- For production deployments, treat webhook signing as a required security baseline.

Recommended production env baseline:
```bash
API_AUTH_ENABLED=true
API_AUTH_KEY=replace_with_strong_shared_key
WEBHOOK_ENABLED=true
WEBHOOK_SIGNING_SECRET=replace_with_strong_webhook_secret
WEBHOOK_TIMEOUT_SEC=10
WEBHOOK_MAX_RETRIES=3
WEBHOOK_RETRY_BACKOFF_SEC=1.0
```

Receiver-side production checks:
- Verify `X-VAR-Signature` against `timestamp.body`.
- Reject stale `X-VAR-Timestamp` values (for example >300 seconds old).
- Deduplicate by `X-VAR-Idempotency-Key` using persistent TTL storage.
- Support webhook secret rotation with overlap window.

Action execution policy:
- Non-terminal actions are executed as real OS input events through `xdotool` in the worker container.
- Supported real events: `move`, `click`, `scroll`, `type`, `key`, `wait`.

## How to test and use
1. Start the stack:
```bash
make build
make start
```

2. Verify API health:
```bash
make check
```

3. Create a run:
```bash
# Remove the X-API-Key header line if API auth is disabled.
RUN_RESPONSE=$(curl -sS -X POST http://localhost:8000/v1/runs \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your_shared_api_key_here' \
  -d '{
    "goal":"Open profile page",
    "start_url":"https://example.com/login",
    "success_criteria":{"type":"text_or_dom","must_include":["Profile"],"must_not_include":["Error"]},
    "runtime":{"mode":"container_desktop","viewport":{"width":1080,"height":1920}},
    "limits":{"max_steps":5,"time_budget_sec":60,"max_retries_per_step":1},
    "allowed_actions":["move","click","scroll","type","key","wait","done","failed"],
    "llm":{"planner_model":"gpt-5.4","evaluator_model":"gpt-5.4"},
    "callbacks":{"completion_url":"https://example.test/webhook","headers":{"X-Webhook-Key":"abc"}}
  }')
echo "$RUN_RESPONSE"
RUN_ID=$(printf '%s' "$RUN_RESPONSE" | python3 -c 'import json,sys; data=json.load(sys.stdin); print(data.get("run_id",""))')
if [ -z "$RUN_ID" ]; then
  echo "Run creation failed:"
  echo "$RUN_RESPONSE"
  exit 1
fi
echo "$RUN_ID"
```

Non-political 444.hu example (inspect first 15 posts):
```bash
RUN_RESPONSE=$(curl -sS -X POST http://localhost:8000/v1/runs \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your_shared_api_key_here' \
  -d '{
    "goal":"Open 444.hu. Dismiss overlays. Inspect the first 15 homepage posts in order using scroll actions as needed. Select the most technology-focused non-political post among those 15, open it, and return done with action.target as the article title and action.value as visible article content.",
    "start_url":"https://444.hu",
    "success_criteria":{"type":"text_or_dom","must_include":["title","content"],"must_not_include":[]},
    "runtime":{"mode":"container_desktop"},
    "limits":{"max_steps":40,"time_budget_sec":900,"max_retries_per_step":2},
    "allowed_actions":["move","click","scroll","type","key","wait","done","failed"],
    "llm":{"planner_model":"gpt-5.4","evaluator_model":"gpt-5.4"}
  }')
echo "$RUN_RESPONSE"
RUN_ID=$(printf '%s' "$RUN_RESPONSE" | python3 -c 'import json,sys; data=json.load(sys.stdin); print(data.get("run_id",""))')
echo "$RUN_ID"
```

4. Poll run status:
```bash
curl -sS -H 'X-API-Key: your_shared_api_key_here' http://localhost:8000/v1/runs/$RUN_ID
```
Response headers include `X-Request-Id` for request tracing.

5. Inspect step trace:
```bash
curl -sS -H 'X-API-Key: your_shared_api_key_here' http://localhost:8000/v1/runs/$RUN_ID/steps
```

6. Cancel a run manually if needed:
```bash
curl -sS -X POST -H 'X-API-Key: your_shared_api_key_here' http://localhost:8000/v1/runs/$RUN_ID/cancel
```

7. Run tests locally:
```bash
python3 -m pytest -q
```

Test policy:
- Tests are mock-only and network-blocked.
- Real AI calls and online scanning are not allowed during tests.

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
