# Hiányosságok

## Nyitott döntések
1. Valódi browser/OS adapter még nincs kiválasztva (`Playwright`, `Selenium`, vagy host input bridge), ezért jelenleg determinisztikus baseline executor fut.
2. Valódi LLM provider integráció (`OpenAI`, `Azure OpenAI`, fallback stratégia) még nincs véglegesítve, ezért a LangChain pipeline stub modellel működik.
3. Artifact tárolási stratégia csak lokális volume-ra készült el, object storage cél (S3 kompatibilis) még nincs kiválasztva.
4. AuthN/AuthZ (API kulcs kezelés) még nincs implementálva.

## Kérdések a következő körhöz
1. Melyik browser automation adapter legyen a fő implementáció (`Playwright` vagy más)?
2. Melyik LLM providert és modelleket rögzítsük production baseline-nak?
