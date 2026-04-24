# Deficiencies

## Open Decisions
1. The system is currently intentionally running in Playwright-free, pure OS/AI baseline mode; browser automation adapter selection is deferred.
2. Artifact storage is currently local-volume only; object storage target (S3-compatible) is not selected.
3. AuthN/AuthZ (API key handling) is not implemented yet.

## Questions for Next Iteration
1. Is multi-provider routing required (`OpenAI`, `Azure OpenAI`, fallback policy), or should OpenAI remain the single production baseline?
