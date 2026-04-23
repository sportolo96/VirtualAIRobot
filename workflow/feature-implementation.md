# Feature Implementation Workflow

## Scope
Minden új funkció (API, queue, agent loop, runner, artifact) implementálása.

## Lépések
1. API contract rögzítése (request/response, validáció, hibakódok).
2. Domain model és use-case definiálása (DDD + CQRS).
3. Infrastructure adapter implementálása (OS capture/input, AI client, queue client).
4. Worker és API összekötése, státusz frissítés.
5. Tesztek: unit + integrációs alapútvonal.
6. Dokumentáció frissítése a `docs/` alatt.

## Kötelező Eredmény
- Megismételhető futás Docker környezetben.
- Nyomon követhető run state és step trace.
