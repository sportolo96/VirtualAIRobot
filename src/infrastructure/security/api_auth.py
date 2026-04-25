from __future__ import annotations

import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class AuthPrincipal:
    """Resolved API authentication identity."""

    client_id: str
    roles: tuple[str, ...]
    key_id: str
    source: str


@dataclass(frozen=True)
class _ClientKey:
    """Parsed key metadata for a client."""

    key_id: str
    secret: str
    status: str
    expires_at: datetime | None


@dataclass(frozen=True)
class _ApiClient:
    """Parsed client configuration."""

    client_id: str
    roles: tuple[str, ...]
    keys: tuple[_ClientKey, ...]


class ApiAuthError(Exception):
    """Base exception for API auth issues."""


class ApiAuthConfigError(ApiAuthError):
    """Invalid API auth configuration."""


class ApiAuthUnauthorized(ApiAuthError):
    """API key was missing or invalid."""


class ApiAuthRegistry:
    """API key registry with per-client key rotation support."""

    def __init__(self, shared_api_key: str, clients_json: str) -> None:
        self._shared_api_key = shared_api_key.strip()
        self._clients = self._parse_clients(clients_json=clients_json)

    def is_configured(self) -> bool:
        return bool(self._shared_api_key or self._clients)

    def authenticate(
        self,
        provided_key: str,
        requested_client_id: str | None = None,
        now: datetime | None = None,
    ) -> AuthPrincipal:
        secret = provided_key.strip()
        if not secret:
            raise ApiAuthUnauthorized("Unauthorized")

        candidate_client_id = (requested_client_id or "").strip()
        current_time = now or datetime.now(tz=timezone.utc)
        for client in self._clients:
            if candidate_client_id and candidate_client_id != client.client_id:
                continue
            for key in client.keys:
                if not self._is_key_usable(key=key, now=current_time):
                    continue
                if hmac.compare_digest(secret, key.secret):
                    return AuthPrincipal(
                        client_id=client.client_id,
                        roles=client.roles,
                        key_id=key.key_id,
                        source="client_registry",
                    )

        if self._shared_api_key and hmac.compare_digest(secret, self._shared_api_key):
            return AuthPrincipal(
                client_id="shared",
                roles=("runs.read", "runs.write", "admin"),
                key_id="shared",
                source="shared_key",
            )

        raise ApiAuthUnauthorized("Unauthorized")

    def has_role(self, principal: AuthPrincipal, required_role: str | None) -> bool:
        if required_role is None:
            return True
        normalized_roles = {role.strip() for role in principal.roles if role.strip()}
        if "*" in normalized_roles or "admin" in normalized_roles:
            return True
        return required_role in normalized_roles

    def _is_key_usable(self, key: _ClientKey, now: datetime) -> bool:
        status = key.status.strip().lower()
        if status not in {"active", "grace"}:
            return False
        if key.expires_at is None:
            return True
        return now < key.expires_at

    def _parse_clients(self, clients_json: str) -> tuple[_ApiClient, ...]:
        raw = clients_json.strip()
        if not raw:
            return ()

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ApiAuthConfigError("API_AUTH_CLIENTS_JSON is not valid JSON.") from exc

        if not isinstance(parsed, list):
            raise ApiAuthConfigError("API_AUTH_CLIENTS_JSON must be a JSON array.")

        clients: list[_ApiClient] = []
        for index, item in enumerate(parsed, start=1):
            if not isinstance(item, dict):
                raise ApiAuthConfigError(
                    f"API_AUTH_CLIENTS_JSON entry #{index} must be an object."
                )

            client_id = str(item.get("client_id", "")).strip()
            if not client_id:
                raise ApiAuthConfigError(f"API_AUTH_CLIENTS_JSON entry #{index} missing client_id.")

            roles_raw = item.get("roles", [])
            if not isinstance(roles_raw, list):
                raise ApiAuthConfigError(
                    f"API_AUTH_CLIENTS_JSON entry #{index} roles must be a list."
                )
            roles = tuple(str(role).strip() for role in roles_raw if str(role).strip())

            keys_raw = item.get("keys", [])
            if not isinstance(keys_raw, list) or not keys_raw:
                raise ApiAuthConfigError(
                    f"API_AUTH_CLIENTS_JSON entry #{index} keys must be a non-empty list."
                )

            parsed_keys: list[_ClientKey] = []
            for key_index, key_item in enumerate(keys_raw, start=1):
                if not isinstance(key_item, dict):
                    raise ApiAuthConfigError(
                        f"API_AUTH_CLIENTS_JSON entry #{index} key #{key_index} must be an object."
                    )

                secret = (
                    str(key_item.get("secret", "")).strip()
                    or str(key_item.get("key", "")).strip()
                    or str(key_item.get("value", "")).strip()
                )
                if not secret:
                    raise ApiAuthConfigError(
                        f"API_AUTH_CLIENTS_JSON entry #{index} key #{key_index} missing secret."
                    )

                key_id = (
                    str(key_item.get("key_id", "")).strip()
                    or str(key_item.get("id", "")).strip()
                    or f"{client_id}_key_{key_index}"
                )
                status = str(key_item.get("status", "active")).strip().lower() or "active"
                expires_at = self._parse_expires_at(
                    value=key_item.get("expires_at"),
                    client_id=client_id,
                    key_id=key_id,
                )
                parsed_keys.append(
                    _ClientKey(
                        key_id=key_id,
                        secret=secret,
                        status=status,
                        expires_at=expires_at,
                    )
                )

            clients.append(_ApiClient(client_id=client_id, roles=roles, keys=tuple(parsed_keys)))

        return tuple(clients)

    def _parse_expires_at(
        self,
        value: Any,
        client_id: str,
        key_id: str,
    ) -> datetime | None:
        if value in {None, ""}:
            return None
        if not isinstance(value, str):
            raise ApiAuthConfigError(
                f"expires_at must be a string for client '{client_id}' key '{key_id}'."
            )
        normalized = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError as exc:
            raise ApiAuthConfigError(
                f"Invalid expires_at for client '{client_id}' key '{key_id}'."
            ) from exc
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
