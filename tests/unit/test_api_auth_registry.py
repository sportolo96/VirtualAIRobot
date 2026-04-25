from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.infrastructure.security.api_auth import (
    ApiAuthConfigError,
    ApiAuthRegistry,
    ApiAuthUnauthorized,
)


def test_api_auth_registry_authenticates_shared_key() -> None:
    registry = ApiAuthRegistry(shared_api_key="shared-secret", clients_json="")

    principal = registry.authenticate(provided_key="shared-secret")

    assert principal.client_id == "shared"
    assert "runs.write" in principal.roles


def test_api_auth_registry_authenticates_rotated_client_key() -> None:
    registry = ApiAuthRegistry(
        shared_api_key="",
        clients_json=(
            '[{"client_id":"ci","roles":["runs.read","runs.write"],"keys":['
            '{"id":"new","secret":"new-secret","status":"active"},'
            '{"id":"old","secret":"old-secret","status":"grace","expires_at":"2099-01-01T00:00:00+00:00"}'
            "]}]"
        ),
    )

    principal = registry.authenticate(provided_key="old-secret", requested_client_id="ci")

    assert principal.client_id == "ci"
    assert principal.key_id == "old"


def test_api_auth_registry_rejects_expired_rotation_key() -> None:
    registry = ApiAuthRegistry(
        shared_api_key="",
        clients_json=(
            '[{"client_id":"ci","roles":["runs.read"],"keys":['
            '{"id":"old","secret":"old-secret","status":"grace","expires_at":"2000-01-01T00:00:00+00:00"}'
            "]}]"
        ),
    )

    with pytest.raises(ApiAuthUnauthorized):
        registry.authenticate(
            provided_key="old-secret",
            requested_client_id="ci",
            now=datetime.now(tz=timezone.utc),
        )


def test_api_auth_registry_enforces_role_check() -> None:
    registry = ApiAuthRegistry(
        shared_api_key="",
        clients_json=(
            '[{"client_id":"reader","roles":["runs.read"],'
            '"keys":[{"id":"k1","secret":"reader-secret","status":"active"}]}]'
        ),
    )
    principal = registry.authenticate(provided_key="reader-secret")

    assert registry.has_role(principal=principal, required_role="runs.read") is True
    assert registry.has_role(principal=principal, required_role="runs.write") is False


def test_api_auth_registry_rejects_invalid_json() -> None:
    with pytest.raises(ApiAuthConfigError):
        ApiAuthRegistry(shared_api_key="", clients_json="{invalid")
