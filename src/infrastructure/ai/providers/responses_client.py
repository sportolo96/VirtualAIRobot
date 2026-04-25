from __future__ import annotations

from typing import Protocol


class ResponsesClient(Protocol):
    """Provider client contract for text and image-enabled completions."""

    def complete_text(self, model: str, prompt: str, max_output_tokens: int = 400) -> str:
        raise NotImplementedError

    def complete_text_with_image(
        self,
        model: str,
        prompt: str,
        image_path: str,
        max_output_tokens: int = 400,
    ) -> str:
        raise NotImplementedError

    def health_check(self, model: str) -> None:
        raise NotImplementedError
