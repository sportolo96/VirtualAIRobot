from __future__ import annotations

import pytest

from src.infrastructure.ai.providers.fallback_responses_client import FallbackResponsesClient


class ProviderStub:
    """Simple provider stub for fallback tests."""

    def __init__(self, *, text: str | None = None, error: Exception | None = None) -> None:
        self._text = text
        self._error = error

    def complete_text(self, model: str, prompt: str, max_output_tokens: int = 400) -> str:
        _ = (model, prompt, max_output_tokens)
        if self._error is not None:
            raise self._error
        return self._text or ""

    def complete_text_with_image(
        self,
        model: str,
        prompt: str,
        image_path: str,
        max_output_tokens: int = 400,
    ) -> str:
        _ = (model, prompt, image_path, max_output_tokens)
        if self._error is not None:
            raise self._error
        return self._text or ""

    def health_check(self, model: str) -> None:
        _ = model
        if self._error is not None:
            raise self._error


def test_fallback_responses_client_uses_secondary_provider_on_failure() -> None:
    client = FallbackResponsesClient(
        providers=[
            ("openai", ProviderStub(error=RuntimeError("primary down"))),
            ("azure_openai", ProviderStub(text="OK from fallback")),
        ]
    )

    result = client.complete_text(model="gpt-5.4", prompt="hello")

    assert result == "OK from fallback"


def test_fallback_responses_client_raises_when_all_providers_fail() -> None:
    client = FallbackResponsesClient(
        providers=[
            ("openai", ProviderStub(error=RuntimeError("primary down"))),
            ("azure_openai", ProviderStub(error=RuntimeError("secondary down"))),
        ]
    )

    with pytest.raises(RuntimeError) as exc_info:
        client.complete_text(model="gpt-5.4", prompt="hello")

    message = str(exc_info.value)
    assert "All AI providers failed" in message
    assert "openai" in message
    assert "azure_openai" in message
