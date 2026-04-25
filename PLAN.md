# VirtualAIRobot - Implementation Plan

## Goal
Build a production-ready API-first AI/OS automation platform with Docker runtime, queue-based execution, secure API access, secure webhook flows, and multi-provider AI fallback.

## Core Principles
- API-first operation: all runtime inputs come from HTTP API requests.
- Async processing: `POST /v1/runs` enqueues, worker executes.
- Mandatory step evidence: `pre`/`post` screenshots for every step.
- Deterministic runtime model control: planner/evaluator model selection comes from env settings.
- Security-first baseline: API auth with per-client key rotation + RBAC, webhook signature/timestamp/idempotency enforcement.
- Container-only deployment model: Docker Compose (`api`, `worker`, `redis`) on macOS and Linux.

## Phases

### F0 - Runtime Foundation (Completed)
- Python codebase with DDD + CQRS layers.
- Dockerfile and Docker Compose stack (`api`, `worker`, `redis`).
- Flask API, RQ worker, Redis-backed queue and state.
- Env-driven runtime configuration and Make-based operational commands.

### F1 - Run Lifecycle and Queue (Completed)
- `Run` aggregate and lifecycle states: `queued`, `running`, `succeeded`, `failed`, `cancelled`, `timeout`.
- Queue producer (`POST /v1/runs`) + worker consumer.
- Run status endpoint (`GET /v1/runs/{run_id}`) and cancel endpoint (`POST /v1/runs/{run_id}/cancel`).

### F2 - AI/OS Execution Loop (Completed)
- Execution loop: pre-capture -> planner -> action -> post-capture -> evaluator.
- LangChain template pipelines for planner/evaluator with structured outputs.
- Allowed-action guardrails and runtime limits (`max_steps`, `time_budget_sec`, `max_retries_per_step`).
- Terminal action policy: `done` => success, `failed` => failure.

### F3 - Security Hardening (Completed)
- API authentication supports:
  - shared key mode (`API_AUTH_KEY`)
  - per-client rotating keys + roles (`API_AUTH_CLIENTS_JSON`)
- Endpoint-level RBAC (`runs.read`, `runs.write`).
- Completion webhook sender includes retry + dead-letter handling.
- Central webhook receiver enforcement:
  - timestamp replay window
  - signature policy
  - idempotency deduplication (Redis NX+TTL)

### F4 - Multi-Provider AI Strategy (Completed)
- Primary provider + ordered fallback chain:
  - `openai`
  - `azure_openai`
- Provider routing via env:
  - `AI_PROVIDER`
  - `AI_FALLBACK_PROVIDERS`
- Runtime model selection via env:
  - `PLANNER_MODEL`
  - `EVALUATOR_MODEL`

### F5 - Documentation and Quality Gates (Completed)
- README, system design, and deficiencies documentation aligned with runtime behavior.
- Mock-only tests (no live AI/network), full unit/integration coverage for new flows.
- Mandatory quality checks: `make test`, `make lint`, `make typecheck`, `make quality`.

## Delivered Scope
- API endpoints: run create/status/steps/cancel + webhook receiver endpoint.
- Worker loop with mandatory screenshot evidence and AI evaluation.
- Redis persistence for runs/steps and webhook idempotency.
- Hardened auth, webhook enforcement, and multi-provider fallback runtime.
