# GitLab Delivery Workflow

## Scope
GitHub repóból GitLab felé történő szállítás és CI/CD előkészítés.

## Lépések
1. Git távoli beállítás ellenőrzése (`origin`, opcionális `gitlab`).
2. Branch stratégia rögzítése (main + feature branch-ek):
   - Fejlesztői változtatás commit/push csak feature branch-re mehet.
   - `main` branch-re közvetlen commit/push nem engedett.
   - Ha nincs aktív feature branch, branch név javaslat után branch létrehozás/váltás kötelező.
   - Ha a feladat befejeződött aktív feature branch-en, mehet a commit és push.
3. CI pipeline fájl(ok) létrehozása (lint, test, build).
4. Docker image build/publish lépések bekötése.
5. Release checklist dokumentálása.

## Kötelező Eredmény
- Reprodukálható build és teszt futás CI-ben.
- Verziózott, visszakövethető deploy útvonal.
- Változáscsomagok feature branch alapú commit/push folyamattal szállítva.
