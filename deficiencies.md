# Deficiencies

## Open Decisions
1. The system is currently intentionally running in Playwright-free, pure OS/AI baseline mode; browser automation adapter selection is deferred.
2. Real LLM provider integration (`OpenAI`, `Azure OpenAI`, fallback strategy) is not finalized yet, so LangChain pipelines currently use stub model behavior.
3. API default model name is `chatgpt-5.4`, but actual provider binding is not connected yet.
4. Artifact storage is currently local-volume only; object storage target (S3-compatible) is not selected.
5. AuthN/AuthZ (API key handling) is not implemented yet.

## Questions for Next Iteration
1. Which LLM provider and exact model mapping should be the production baseline?
