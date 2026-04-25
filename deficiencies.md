# Deficiencies

## Open Decisions
1. The system is currently intentionally running in Playwright-free, pure OS/AI baseline mode; browser automation adapter selection is deferred.
2. Artifact storage is currently local-volume only; object storage target (S3-compatible) is not selected.
3. Auth is currently shared API key only (`X-API-Key`); role-based access control and per-client key rotation are not implemented yet.
4. Webhook signing key rotation and receiver-side replay window policy are not standardized yet.

## Questions for Next Iteration
1. Is multi-provider routing required (`OpenAI`, `Azure OpenAI`, fallback policy), or should OpenAI remain the single production baseline?
