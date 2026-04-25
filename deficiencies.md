# Deficiencies

## Open Decisions
1. The system is currently intentionally running in Playwright-free, pure OS/AI baseline mode; browser automation adapter selection is deferred.
2. Artifact storage is currently local-volume only; object storage target (S3-compatible) is not selected.
3. API auth supports per-client keys and RBAC, but policy administration is env-driven JSON only (no managed key service).
4. Webhook receiver security is enforced centrally, but signature secret lifecycle and audit retention policy are still operational decisions.

## Questions for Next Iteration
1. Should provider fallback remain strict sequential order, or do we need health-score weighting and circuit-breaker behavior?
