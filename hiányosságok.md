# Hiányosságok

## Nyitott döntések
1. A rendszer jelenleg szándékosan Playwright nélküli, puszta OS/AI baseline módban fut; a további browser automation adapter döntés későbbre halasztva.
2. Valódi LLM provider integráció (`OpenAI`, `Azure OpenAI`, fallback stratégia) még nincs véglegesítve, ezért a LangChain pipeline stub modellel működik.
3. API default modellnév `chatgpt-5.4`, de tényleges provider binding még nincs bekötve.
4. Artifact tárolási stratégia csak lokális volume-ra készült el, object storage cél (S3 kompatibilis) még nincs kiválasztva.
5. AuthN/AuthZ (API kulcs kezelés) még nincs implementálva.

## Kérdések a következő körhöz
1. Melyik LLM providert és modelleket rögzítsük production baseline-nak?
