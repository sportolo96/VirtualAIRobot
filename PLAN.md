# VirtualAIRobot - Megvalósítási Terv

## Cél
Egy API-first, queue alapú AI/OS automatizációs rendszer készítése, ahol minden egyes action között kötelező a screenshot + AI kiértékelés, és az API visszaadja a teljes végrehajtási eredményt és értékelést.

## Alapelvek
- Nincs `.md` scenario input: minden futási paraméter API kérésből érkezik.
- Aszinkron futás: `POST /v1/runs` csak enqueue, futás workerben történik.
- Minden step előtt és után képernyőkép készül.
- A következő action mindig az aktuális screenshot AI-kiértékeléséből születik.
- Teljes konténerizáció, macOS és Linux hoston is futtatható módokkal.

## Fázisok

### F0 - Projekt alap és konténer runtime
- Python projekt váz (DDD + CQRS rétegek)
- Dockerfile + docker-compose (api, worker, redis)
- Környezeti kapcsolók (runtime mód, limits, AI provider, artifact storage)

### F1 - Run lifecycle és queue
- `Run` domain modell és állapotgép (`queued`, `running`, `succeeded`, `failed`, `cancelled`, `timeout`)
- Queue producer (`POST /v1/runs`) és worker fogyasztó
- Státusz API (`GET /v1/runs/{run_id}`)

### F2 - AI/OS iteratív végrehajtási ciklus
- Step loop: pre-capture -> plan -> execute -> post-capture -> evaluate
- LangChain best practice orchestration: planner/evaluator prompt template + LCEL pipeline
- Strukturált, validált LLM kimenet (decision/evaluation DTO)
- Engedélyezett action készlet és guardrail-ek
- `max_steps`, `time_budget_sec`, `max_retries_per_step` korlátok

### F3 - Eredmény és értékelés
- `GET /v1/runs/{run_id}/steps` részletes trace
- Final evaluation (goal reached / not reached + indoklás)
- Artifact hivatkozások (screenshotok, logok)

### F4 - Operáció és dokumentáció
- AGENTS és workflow szabályok véglegesítése
- docs frissítési folyamat
- GitLab feltöltés és CI/CD terv (későbbi push és pipeline)

## Első szállítási scope
- 1 enqueue endpoint
- 1 status endpoint
- 1 steps endpoint
- 1 worker loop a kötelező screenshot + AI-eval ciklussal
- Docker compose stack (api + worker + redis)
