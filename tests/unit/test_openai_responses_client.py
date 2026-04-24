from __future__ import annotations

import io
import json
from email.message import Message
from pathlib import Path
from urllib import error

import pytest

from src.infrastructure.ai.providers import openai_responses_client as client_module
from src.infrastructure.ai.providers.openai_responses_client import OpenAIResponsesClient


def test_health_check_uses_supported_minimum_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def _complete_text_stub(
        self: OpenAIResponsesClient, model: str, prompt: str, max_output_tokens: int = 400
    ) -> str:
        captured["model"] = model
        captured["prompt"] = prompt
        captured["max_output_tokens"] = max_output_tokens
        return "OK"

    monkeypatch.setattr(OpenAIResponsesClient, "complete_text", _complete_text_stub)

    client = OpenAIResponsesClient(api_key="test-key")
    client.health_check(model="gpt-5.4")

    assert captured["model"] == "gpt-5.4"
    assert captured["max_output_tokens"] == 16


def test_post_json_compacts_openai_http_error_message(monkeypatch: pytest.MonkeyPatch) -> None:
    body = (
        b'{"error":{"message":"Invalid \'max_output_tokens\': integer below minimum value. '
        b'Expected a value >= 16, but got 8 instead."}}'
    )
    http_error = error.HTTPError(
        url="https://api.openai.com/v1/responses",
        code=400,
        msg="Bad Request",
        hdrs=Message(),
        fp=io.BytesIO(body),
    )

    def _urlopen_stub(*args, **kwargs):
        _ = (args, kwargs)
        raise http_error

    monkeypatch.setattr(client_module.request, "urlopen", _urlopen_stub)

    client = OpenAIResponsesClient(api_key="test-key")

    with pytest.raises(RuntimeError) as exc_info:
        client._post_json(
            path="/responses",
            payload={"model": "gpt-5.4", "input": [], "max_output_tokens": 16},
        )

    message = str(exc_info.value)
    assert "HTTP 400" in message
    assert "integer below minimum value" in message
    assert "\n" not in message


def test_complete_text_uses_provided_model_name(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_model: list[str] = []

    class _ResponseStub:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            _ = (exc_type, exc, tb)
            return False

        def read(self) -> bytes:
            return b'{"output_text":"OK"}'

    def _urlopen_stub(req, timeout: int):
        _ = timeout
        payload = json.loads(req.data.decode("utf-8"))
        captured_model.append(payload["model"])
        return _ResponseStub()

    monkeypatch.setattr(client_module.request, "urlopen", _urlopen_stub)

    client = OpenAIResponsesClient(api_key="test-key")
    result = client.complete_text(model="gpt-5.4", prompt="OK", max_output_tokens=16)

    assert result == "OK"
    assert captured_model == ["gpt-5.4"]


def test_complete_text_with_image_includes_input_image(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured_content: list[dict[str, str]] = []
    image_path = tmp_path / "frame.png"
    image_path.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
        b"\x00\x0cIDAT\x08\xd7c\xf8\x0f\x00\x01\x01\x01\x00\x18"
        b"\xdd\x8d\x18\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    class _ResponseStub:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            _ = (exc_type, exc, tb)
            return False

        def read(self) -> bytes:
            return b'{"output_text":"OK"}'

    def _urlopen_stub(req, timeout: int):
        _ = timeout
        payload = json.loads(req.data.decode("utf-8"))
        captured_content.extend(payload["input"][0]["content"])
        return _ResponseStub()

    monkeypatch.setattr(client_module.request, "urlopen", _urlopen_stub)

    client = OpenAIResponsesClient(api_key="test-key")
    result = client.complete_text_with_image(
        model="gpt-5.4",
        prompt="Analyze screenshot",
        image_path=str(image_path),
        max_output_tokens=16,
    )

    assert result == "OK"
    assert captured_content[0]["type"] == "input_text"
    assert captured_content[1]["type"] == "input_image"
    assert captured_content[1]["image_url"].startswith("data:image/png;base64,")
