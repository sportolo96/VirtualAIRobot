# VirtualAIRobot - Rendszerterv

## 1. Cél
A rendszer célja weboldalak AI/OS szintű vezérlése úgy, hogy minden action között screenshot alapú AI döntés történjen a cél eléréséhez.

Kiemelt követelmények:
- API-first működés
- Aszinkron queue feldolgozás
- Actionönként screenshot + AI kiértékelés
- Paraméterezhető cél/URL/sikerfeltétel
- Részletes futási eredmény és értékelés visszaadása
- Kötelező Docker alapú konténeres futtatás

## 2. Architektúra

### 2.1 Komponensek
- API Service
- Queue (Redis)
- Worker Service
- Browser/OS Adapter réteg
- AI Planner/Evaluator orchestration (LangChain)
- Artifact Store (filesystem/object storage)

### 2.2 Rétegek (DDD + CQRS)
- `src/domain`: entitások és üzleti szabályok
- `src/application`: command/query use-case-ek
- `src/infrastructure`: queue, AI, browser, OS adapterek
- `src/interfaces`: HTTP API

### 2.3 LLM orchestration (LangChain best practice)
- A planner és evaluator külön prompt template-et használ, verziózott template fájlokkal.
- A hívások LCEL pipeline-on futnak: input mapping -> prompt template -> model -> structured output parser.
- A model kimenet minden esetben strukturált, validált DTO (például `PlannerDecision`, `StepEvaluation`).
- Retry, timeout, fallback és tracing az `infrastructure` rétegben történik.
- Domain üzleti szabály nem kerül promptba; a döntési guardok a `domain` és `application` rétegben maradnak.

## 3. Run Lifecycle

### 3.1 Állapotgép
- `queued`
- `running`
- `succeeded`
- `failed`
- `cancelled`
- `timeout`

### 3.2 Fő endpointok
- `POST /v1/runs`
- `GET /v1/runs/{run_id}`
- `GET /v1/runs/{run_id}/steps`
- `POST /v1/runs/{run_id}/cancel`

## 4. API Contract

### 4.1 Run indítás (request)
```json
{
  "goal": "Jelentkezz be és nyisd meg a profil oldalt",
  "start_url": "https://example.com/login",
  "success_criteria": {
    "type": "text_or_dom",
    "must_include": ["Profil", "Kijelentkezés"],
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
  "allowed_actions": ["move", "click", "scroll", "type", "key", "wait"],
  "llm": {
    "planner_model": "gpt-5.4",
    "evaluator_model": "gpt-5.4"
  }
}
```

### 4.2 Run státusz (response)
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
    "last_evaluation": "Login form submitted, waiting dashboard load"
  }
}
```

### 4.3 Final eredmény (response részlet)
```json
{
  "run_id": "run_01...",
  "status": "succeeded",
  "goal_achieved": true,
  "final_evaluation": {
    "score": 0.93,
    "reason": "A success feltételek teljesültek"
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

## 5. Execution Loop
Minden step kötelező sorrendje:
1. Pre-action screenshot capture
2. AI planner pipeline döntés a következő actionről (LangChain template + parser)
3. Action végrehajtás OS inputtal
4. Post-action screenshot capture
5. AI evaluator pipeline értékelés (LangChain template + parser)
6. Guard ellenőrzés (budget, retry, tiltott action)

A loop addig fut, amíg:
- a success_criteria teljesül, vagy
- limit túllépés történik, vagy
- manuális cancel érkezik.

## 6. Agent Szerepek
- Planner Agent: következő action kiválasztása a cél felé
- Evaluator Agent: action hatásának kiértékelése
- Safety Agent: végrehajtási korlátok és policy enforcement

## 7. Deployment and Runtime Config

### 7.1 Konténeres futtatás
- Kötelező deployment forma: Docker Compose alapú konténeres stack.
- Alap mód: `container_desktop` (Linux Xvfb/noVNC desktop a konténeren belül)
- API + Worker + Redis külön service
- Artifact volume mount kötelező

### 7.2 Cross-platform elv
- Linux host: natív konténer desktop mód
- macOS host: ugyanaz a konténer stack (Docker Desktop), noVNC megtekintéssel
- Opcionális későbbi mód: `host_bridge` (ha natív host input vezérlés is kell)

### 7.3 Fő kapcsolók (terv)
- `RUNTIME_MODE`
- `QUEUE_BACKEND`
- `AI_PROVIDER`, `AI_MODEL`
- `MAX_STEPS_DEFAULT`, `TIME_BUDGET_DEFAULT_SEC`
- `ARTIFACT_RETENTION_DAYS`

## 8. Megfigyelhetőség
- Run szintű structured log
- Step szintű action + evaluation trace
- Queue latency és run duration metrikák
- Hibák kategorizálása: validation, runtime, AI, timeout, cancellation

## 9. Biztonság és korlátok
- Engedélyezett action lista kényszerítése
- URL allowlist/denylist támogatás
- Hard time budget és step limit
- API kulcs alapú hitelesítés (későbbi implementációs fázis)

## 10. Nyitott pontok
- Artifact tárolás: lokális volume vs object storage
- Webhook callback szükségessége polling mellett
- Model fallback stratégia planner/evaluator szerepkörben
