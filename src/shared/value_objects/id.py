from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Id:
    """Base identifier value object."""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Id value cannot be empty")

    def __str__(self) -> str:
        return self.value
