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
7. Ha elkészült egy összefogható változáscsomag, ellenőrizni kell az aktív branch-et.
8. `main` branch-re nem mehet commit/push; feature branch szükséges.
9. Ha nincs aktív feature branch, branch név javaslatot kell adni, majd létrehozni/váltani.
10. Ha aktív feature branch-en befejeződött a feladat, mehet a commit és push.

## Kötelező Eredmény
- Megismételhető futás Docker környezetben.
- Nyomon követhető run state és step trace.
- Összefogható változáscsomagok feature branch-en commitálva és pusholva.
