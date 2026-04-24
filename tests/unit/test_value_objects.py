from __future__ import annotations

import re

import pytest

from src.domain.value_objects.run_id import RunId
from src.domain.value_objects.run_limits import RunLimits
from src.domain.value_objects.run_status import RunStatus
from src.shared.value_objects.id import Id


def test_id_rejects_empty_value() -> None:
    with pytest.raises(ValueError, match="Id value cannot be empty"):
        Id(value="")


def test_id_string_conversion() -> None:
    identity = Id(value="abc")
    assert str(identity) == "abc"


@pytest.mark.parametrize(
    ("max_steps", "time_budget_sec", "max_retries_per_step", "expected_message"),
    [
        (0, 10, 0, "max_steps must be positive"),
        (10, 0, 0, "time_budget_sec must be positive"),
        (10, 10, -1, "max_retries_per_step cannot be negative"),
    ],
)
def test_run_limits_reject_invalid_values(
    max_steps: int,
    time_budget_sec: int,
    max_retries_per_step: int,
    expected_message: str,
) -> None:
    with pytest.raises(ValueError, match=expected_message):
        RunLimits(
            max_steps=max_steps,
            time_budget_sec=time_budget_sec,
            max_retries_per_step=max_retries_per_step,
        )


def test_run_status_terminal_property() -> None:
    assert RunStatus.QUEUED.is_terminal is False
    assert RunStatus.RUNNING.is_terminal is False
    assert RunStatus.SUCCEEDED.is_terminal is True
    assert RunStatus.FAILED.is_terminal is True
    assert RunStatus.CANCELLED.is_terminal is True
    assert RunStatus.TIMEOUT.is_terminal is True


def test_run_id_new_has_expected_prefix() -> None:
    run_id = RunId.new()
    assert re.match(r"^run_[a-f0-9]{32}$", run_id.value)
