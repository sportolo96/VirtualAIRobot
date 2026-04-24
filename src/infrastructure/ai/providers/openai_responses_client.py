from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any
from urllib import error, request


class OpenAIResponsesClient:
    """Minimal OpenAI Responses API client."""

    def __init__(
        self,
        api_key: str,
        api_base_url: str = "https://api.openai.com/v1",
        timeout_sec: int = 30,
    ) -> None:
        self._api_key = api_key
        self._api_base_url = api_base_url.rstrip("/")
        self._timeout_sec = timeout_sec

    def complete_text(self, model: str, prompt: str, max_output_tokens: int = 400) -> str:
        return self._complete(
            model=model,
            prompt=prompt,
            max_output_tokens=max_output_tokens,
            image_path=None,
        )

    def complete_text_with_image(
        self,
        model: str,
        prompt: str,
        image_path: str,
        max_output_tokens: int = 400,
    ) -> str:
        return self._complete(
            model=model,
            prompt=prompt,
            max_output_tokens=max_output_tokens,
            image_path=image_path,
        )

    def _complete(
        self,
        model: str,
        prompt: str,
        max_output_tokens: int,
        image_path: str | None,
    ) -> str:
        content: list[dict[str, str]] = [{"type": "input_text", "text": prompt}]
        if image_path is not None:
            content.append(
                {
                    "type": "input_image",
                    "image_url": self._image_path_to_data_url(image_path=image_path),
                }
            )
        payload = {
            "model": model.strip(),
            "input": [
                {
                    "role": "user",
                    "content": content,
                }
            ],
            "max_output_tokens": max_output_tokens,
        }
        response = self._post_json(path="/responses", payload=payload)
        text = self._extract_text(response=response)
        if not text:
            raise RuntimeError("OpenAI response did not contain text output")
        return text

    def health_check(self, model: str) -> None:
        self.complete_text(
            model=model,
            prompt="Respond only with OK.",
            max_output_tokens=16,
        )

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url=f"{self._api_base_url}{path}",
            data=body,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self._timeout_sec) as response:
                raw = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail_raw = exc.read().decode("utf-8", errors="replace")
            detail = self._normalize_error_detail(detail_raw)
            raise RuntimeError(f"OpenAI request failed with HTTP {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"OpenAI request failed: {exc.reason}") from exc
        except TimeoutError as exc:
            raise RuntimeError("OpenAI request timed out") from exc

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError("OpenAI response was not valid JSON") from exc

        if not isinstance(parsed, dict):
            raise RuntimeError("OpenAI response payload was not an object")
        return parsed

    def _normalize_error_detail(self, detail_raw: str) -> str:
        try:
            parsed = json.loads(detail_raw)
        except json.JSONDecodeError:
            return " ".join(detail_raw.split())

        if isinstance(parsed, dict):
            err = parsed.get("error")
            if isinstance(err, dict):
                message = err.get("message")
                if isinstance(message, str) and message.strip():
                    return " ".join(message.split())
        return " ".join(detail_raw.split())

    def _image_path_to_data_url(self, image_path: str) -> str:
        path = Path(image_path)
        if not path.exists():
            raise RuntimeError(f"Screenshot file not found for AI input: {image_path}")

        suffix = path.suffix.lower()
        mime = "image/png"
        if suffix in {".jpg", ".jpeg"}:
            mime = "image/jpeg"
        elif suffix == ".webp":
            mime = "image/webp"

        image_bytes = path.read_bytes()
        encoded = base64.b64encode(image_bytes).decode("ascii")
        return f"data:{mime};base64,{encoded}"

    def _extract_text(self, response: dict[str, Any]) -> str:
        output_text = response.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text

        output = response.get("output")
        if not isinstance(output, list):
            return ""

        texts: list[str] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, dict):
                    continue
                part_type = str(part.get("type", ""))
                if part_type not in {"output_text", "text"}:
                    continue
                text = part.get("text")
                if isinstance(text, str) and text.strip():
                    texts.append(text)
        return "\n".join(texts).strip()
