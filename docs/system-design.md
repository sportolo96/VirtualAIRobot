# VirtualAIRobot - System Design

## 1. Goal
The goal is AI/OS-level web automation where every action is driven by screenshot-based AI decisions toward a configured objective.

Key requirements:
- API-first operation
- Asynchronous queue processing
- Screenshot + AI evaluation per action
- Configurable goal/start URL/success criteria
- Detailed run result and evaluation response
- Mandatory Docker-based containerized runtime

## 2. Architecture

### 2.1 Components
- API Service (Flask)
- Queue (Redis + RQ)
- Worker Service (RQ worker)
- Browser/OS Adapter layer
- AI Planner/Evaluator orchestration (LangChain)
- Artifact Store (filesystem/object storage)

### 2.2 Layers (DDD + CQRS)
- `src/domain`: entities and business rules
- `src/application`: command/query use cases
- `src/infrastructure`: queue, AI, browser, OS adapters
- `src/interfaces`: HTTP API

### 2.3 LLM Orchestration (LangChain Best Practice)
- Planner and evaluator use separate prompt templates with versioned template files.
- Calls run through LCEL pipelines: input mapping -> prompt template -> model -> structured output parser.
- Model output is always structured and validated DTOs (for example `PlannerDecision`, `StepEvaluation`).
- Retry, timeout, fallback, and tracing are handled in the infrastructure layer.
- Domain business rules are not embedded in prompts; decision guards remain in domain/application layers.

### 2.4 First Implementation Baseline
- Queue producer: `POST /v1/runs` enqueues to RQ.
- Worker job: `src.interfaces.worker.jobs.process_run_job`.
- Run and step state are persisted in Redis via repository layer.
- Screenshot adapter captures real OS-level desktop screenshots into filesystem artifacts (`.png`) on each step.
- Desktop session and browser window size are initialized from run `runtime.viewport`.
- Screenshot output is normalized to the run viewport and includes cursor overlay markers.
- Planner/Evaluator run through LangChain template + parser pipelines with live OpenAI Responses API calls.
- Planner/Evaluator receive the same step screenshot image as OpenAI image input.
- Action execution uses OS-level input events via `xdotool` for supported non-terminal actions.

## 3. Run Lifecycle

### 3.1 State Machine
- `queued`
- `running`
- `succeeded`
- `failed`
- `cancelled`
- `timeout`

### 3.2 Main Endpoints
- `POST /v1/runs`
- `GET /v1/runs/{run_id}`
- `GET /v1/runs/{run_id}/steps`
- `POST /v1/runs/{run_id}/cancel`

Run create precondition:
- `POST /v1/runs` requires configured AI runtime (`AI_PROVIDER=openai` and `OPENAI_API_KEY`).
- If AI runtime is missing or live connectivity check fails, API returns `503` and does not enqueue the run.

## 4. API Contract

### 4.1 Run Create (request)
```json
{
  "goal": "Log in and open the profile page",
  "start_url": "https://example.com/login",
  "success_criteria": {
    "type": "text_or_dom",
    "must_include": ["Profile", "Logout"],
    "must_not_include": ["Login failed"]
  },
  "runtime": {
    "mode": "container_desktop",
    "viewport": { "width": 1080, "height": 1920 }
  },
  "limits": {
    "max_steps": 40,
    "time_budget_sec": 300,
    "max_retries_per_step": 2
  },
  "allowed_actions": ["move", "click", "scroll", "type", "key", "wait", "done", "failed"],
  "llm": {
    "planner_model": "gpt-5.4",
    "evaluator_model": "gpt-5.4"
  }
}
```

### 4.2 Run Status (response)
```json
{
  "run_id": "run_01...",
  "status": "running",
  "goal_achieved": false,
  "progress": {
    "current_step": 12,
    "max_steps": 40,
    "elapsed_sec": 88
  },
  "summary": {
    "last_action": "click",
    "last_evaluation": "Action executed, waiting for next state"
  }
}
```

### 4.3 Final Result (response excerpt)
```json
{
  "run_id": "run_01...",
  "status": "succeeded",
  "goal_achieved": true,
  "final_evaluation": {
    "reason": "Planner returned terminal action done",
    "terminal_action": "done"
  },
  "result": {
    "steps_total": 19,
    "actions_executed": 19,
    "artifacts": {
      "screenshots": ["/artifacts/run_01/step_001_pre.png"],
      "trace": "/artifacts/run_01/trace.json"
    }
  }
}
```

### 4.4 Run Create Runtime Error (response)
```json
{
  "error": "AI runtime is not configured. Set OPENAI_API_KEY to start runs."
}
```

## 5. Execution Loop
Mandatory step order:
1. Pre-action screenshot capture
2. AI planner pipeline decision (LangChain template + parser + screenshot image input)
3. Action execution through OS input layer
4. Post-action screenshot capture
5. AI evaluator pipeline evaluation (LangChain template + parser + screenshot image input)
6. Guard checks (budget, retry, forbidden actions)

The loop ends when:
- planner action is `done` (run succeeds), or
- planner action is `failed` (run fails), or
- a limit is exceeded, or
- manual cancel is requested.

## 6. Agent Roles
- Planner Agent: selects the next action toward the goal
- Evaluator Agent: evaluates action impact
- Safety Agent: enforces runtime constraints and policy

## 7. Deployment and Runtime Config

### 7.1 Containerized Runtime
- Mandatory deployment format: Docker Compose container stack.
- Base mode: `container_desktop` (Linux Xvfb/noVNC desktop inside container).
- API + Worker + Redis as separate services.
- Artifact volume mount is required.
- Redis is internal to the Compose network; host port publishing is not required.
- Project make targets invoke Compose with explicit env file: `docker compose --env-file .env`.

### 7.2 Cross-Platform Principle
- Linux host: native container desktop mode.
- macOS host: same container stack via Docker Desktop, with optional noVNC viewing.
- Optional future mode: `host_bridge` (if native host input control is needed).

### 7.3 Main Runtime Keys (plan)
- `RUNTIME_MODE`
- `QUEUE_BACKEND`
- `AI_PROVIDER`, `AI_MODEL`, `OPENAI_API_KEY`
- `DEFAULT_VIEWPORT_WIDTH`, `DEFAULT_VIEWPORT_HEIGHT`
- `MAX_STEPS_DEFAULT`, `TIME_BUDGET_DEFAULT_SEC`
- `ARTIFACT_RETENTION_DAYS`

## 8. Observability
- Run-level structured logs
- Step-level action + evaluation trace
- Queue latency and run duration metrics
- Error categories: validation, runtime, AI, timeout, cancellation

## 9. Security and Limits
- Enforced allowlist of actions
- URL allowlist/denylist support
- Hard time budget and step limits
- API-key based authentication (later phase)

## 10. Open Points
- Artifact storage target: local volume vs object storage
- Need for webhook callbacks in addition to polling
- Model fallback strategy across planner/evaluator roles
