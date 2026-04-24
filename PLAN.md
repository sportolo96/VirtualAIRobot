# VirtualAIRobot - Implementation Plan

## Goal
Build an API-first, queue-based AI/OS automation system where each step requires screenshot capture and AI evaluation, and the API returns full execution results and evaluation.

## Core Principles
- No `.md` scenario input: all run parameters come from API requests.
- Asynchronous execution: `POST /v1/runs` only enqueues; processing happens in workers.
- Screenshot capture is required before and after each step.
- The next action is always derived from AI evaluation of the current screenshot context.
- Docker-based containerized runtime is mandatory.
- Delivery format is a Docker Compose stack (`api`, `worker`, `redis`).
- The same containerized stack must run on both macOS and Linux hosts.

## Phases

### F0 - Project Foundation and Container Runtime
- Python project skeleton with DDD + CQRS layers.
- Dockerfile + docker-compose (`api`, `worker`, `redis`) in mandatory use.
- Flask API + RQ worker + Redis queue/state baseline implementation.
- Runtime configuration switches (runtime mode, limits, AI provider, artifact storage).

### F1 - Run Lifecycle and Queue
- `Run` domain model and state machine (`queued`, `running`, `succeeded`, `failed`, `cancelled`, `timeout`).
- Queue producer (`POST /v1/runs`) and worker consumer.
- Status API (`GET /v1/runs/{run_id}`).

### F2 - Iterative AI/OS Execution Cycle
- Step loop: pre-capture -> plan -> execute -> post-capture -> evaluate.
- LangChain best-practice orchestration: planner/evaluator prompt templates + LCEL pipelines.
- Structured, validated LLM output (decision/evaluation DTOs).
- Planner terminal action rule: `done` => success, `failed` => failure.
- Allowed action set and guardrails.
- Limits: `max_steps`, `time_budget_sec`, `max_retries_per_step`.

### F3 - Result and Evaluation
- Detailed trace endpoint: `GET /v1/runs/{run_id}/steps`.
- Final evaluation (goal reached / not reached + reasoning).
- Artifact references (screenshots, logs).

### F4 - Operations and Documentation
- Finalize AGENTS and workflow rules.
- Maintain documentation update flow.
- GitLab delivery and CI/CD plan (later push and pipeline integration).

## First Delivery Scope
- 1 enqueue endpoint.
- 1 status endpoint.
- 1 steps endpoint.
- 1 worker loop with mandatory screenshot + AI-eval cycle.
- Docker Compose stack (`api` + `worker` + `redis`).
