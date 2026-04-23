# GitLab Delivery Workflow

## Scope
GitHub repóból GitLab felé történő szállítás és CI/CD előkészítés.

## Lépések
1. Git távoli beállítás ellenőrzése (`origin`, opcionális `gitlab`).
2. Branch stratégia rögzítése (main + feature branch-ek).
3. CI pipeline fájl(ok) létrehozása (lint, test, build).
4. Docker image build/publish lépések bekötése.
5. Release checklist dokumentálása.

## Kötelező Eredmény
- Reprodukálható build és teszt futás CI-ben.
- Verziózott, visszakövethető deploy útvonal.
