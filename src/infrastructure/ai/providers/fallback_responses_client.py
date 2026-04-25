from __future__ import annotations

from collections.abc import Sequence

from src.infrastructure.ai.providers.responses_client import ResponsesClient


class FallbackResponsesClient:
    """Responses client that falls back across providers on failures."""

    def __init__(self, providers: Sequence[tuple[str, ResponsesClient]]) -> None:
        self._providers = list(providers)
        if not self._providers:
            raise ValueError("At least one provider must be configured")

    def complete_text(self, model: str, prompt: str, max_output_tokens: int = 400) -> str:
        return self._invoke(
            lambda client: client.complete_text(
                model=model,
                prompt=prompt,
                max_output_tokens=max_output_tokens,
            )
        )

    def complete_text_with_image(
        self,
        model: str,
        prompt: str,
        image_path: str,
        max_output_tokens: int = 400,
    ) -> str:
        return self._invoke(
            lambda client: client.complete_text_with_image(
                model=model,
                prompt=prompt,
                image_path=image_path,
                max_output_tokens=max_output_tokens,
            )
        )

    def health_check(self, model: str) -> None:
        self._invoke(lambda client: client.health_check(model=model))

    def _invoke(self, fn):
        errors: list[str] = []
        for provider_name, provider in self._providers:
            try:
                return fn(provider)
            except Exception as exc:
                errors.append(f"{provider_name}: {exc}")
        joined = "; ".join(errors) if errors else "unknown provider failure"
        raise RuntimeError(f"All AI providers failed: {joined}")
