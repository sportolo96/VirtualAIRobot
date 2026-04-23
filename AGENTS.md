# AGENTS

## Workflow Source
- A projekt workflow szabályait a `workflow/*.md` fájlok adják.
- Új feladatot mindig egy megfelelő workflow szerint kell végrehajtani.

## Runtime Agentek
- Planner Agent: a screenshot alapján javasolja a következő actiont a cél felé.
- Evaluator Agent: action után ellenőrzi, hogy közeledett-e a futás a success feltételhez.
- Safety Agent: action szűrés és guardrail ellenőrzés (tiltott action, budget túllépés, loop védelem).

## Dokumentációs Szabály
- Minden viselkedés-, API-, queue-, workflow- vagy runtime változás esetén a kapcsolódó `docs/*.md` fájlokat ugyanabban a változtatásban frissíteni kell.

## Scope Szabály
- A projekt API-first: futási konfiguráció csak API-ból érkezik.
- Scenario `.md` input nem része a rendszernek.
