from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.shared.value_objects.id import Id


@dataclass(frozen=True)
class RunId(Id):
    """Run identifier value object."""

    @classmethod
    def new(cls) -> "RunId":
        return cls(value=f"run_{uuid.uuid4().hex}")
