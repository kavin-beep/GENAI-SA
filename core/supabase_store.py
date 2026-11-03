"""Server-side Supabase storage for one signed-in CoachBot account."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests


TABLE_NAME = "coachbot_account_store"
REQUEST_TIMEOUT_SECONDS = 10


class SupabaseStoreError(RuntimeError):
    """A safe, non-secret failure reported by the account data store."""


def _as_mapping(value: object) -> dict[str, object]:
    if isinstance(value, Mapping):
        return dict(value)
    try:
        return dict(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return {}


class SupabaseAccountStore:
    """Use Supabase's REST API from the trusted Streamlit server only.

    The app derives account keys from Streamlit's verified OIDC `sub` claim and
    never accepts an account key from a browser field. The elevated API key is
    read only from private Streamlit secrets and is never sent to the browser.
    """

    def __init__(self, project_url: str, secret_key: str) -> None:
        parsed = urlparse(project_url.strip())
        local_http = parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"}
        if not parsed.hostname or (parsed.scheme != "https" and not local_http):
            raise ValueError("Use an HTTPS Supabase project URL.")
        if parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {"", "/"}:
            raise ValueError("The Supabase URL must not contain credentials or query values.")
        if not secret_key.strip():
            raise ValueError("A private Supabase secret key is required.")
        self._endpoint = project_url.strip().rstrip("/") + f"/rest/v1/{TABLE_NAME}"
        self._secret_key = secret_key.strip()
        self._session = requests.Session()

    @classmethod
    def from_secrets(cls, secrets: object) -> tuple[SupabaseAccountStore | None, str]:
        """Build from `[supabase]`; never return or display either secret value."""
        root = _as_mapping(secrets)
        section = _as_mapping(root.get("supabase"))
        if not section:
            return None, "not_configured"
        project_url = section.get("url")
        secret_key = section.get("secret_key")
        if not isinstance(project_url, str) or not project_url.strip() or not isinstance(secret_key, str) or not secret_key.strip():
            return None, "incomplete"
        if secret_key.strip().startswith("sb_publishable_"):
            return None, "invalid_key"
        try:
            return cls(project_url, secret_key), "configured"
        except ValueError:
            return None, "invalid"

    def _headers(self, *, upsert: bool = False) -> dict[str, str]:
        headers = {
            "apikey": self._secret_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if upsert:
            headers["Prefer"] = "resolution=merge-duplicates,return=minimal"
        return headers

    @staticmethod
    def _validate_account_key(account_key: str) -> str:
        if len(account_key) != 64 or any(character not in "0123456789abcdef" for character in account_key):
            raise ValueError("The signed-in account identifier is invalid.")
        return account_key

    def load(self, account_key: str) -> dict[str, object] | None:
        key = self._validate_account_key(account_key)
        try:
            response = self._session.get(
                self._endpoint,
                params={"select": "payload", "account_key": f"eq.{key}", "limit": "1"},
                headers=self._headers(),
                timeout=REQUEST_TIMEOUT_SECONDS,
                allow_redirects=False,
            )
            if 300 <= response.status_code < 400:
                raise requests.RequestException("Unexpected redirect.")
            response.raise_for_status()
            rows = response.json()
        except (requests.RequestException, ValueError):
            raise SupabaseStoreError("Saved account data could not be loaded from Supabase.") from None
        if not isinstance(rows, list) or not rows:
            return None
        payload = rows[0].get("payload") if isinstance(rows[0], dict) else None
        if not isinstance(payload, dict):
            raise SupabaseStoreError("Saved account data has an unsupported format.")
        return payload

    def save(self, account_key: str, payload: dict[str, object]) -> None:
        key = self._validate_account_key(account_key)
        try:
            response = self._session.post(
                self._endpoint,
                params={"on_conflict": "account_key"},
                json={
                    "account_key": key,
                    "payload": payload,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
                headers=self._headers(upsert=True),
                timeout=REQUEST_TIMEOUT_SECONDS,
                allow_redirects=False,
            )
            if 300 <= response.status_code < 400:
                raise requests.RequestException("Unexpected redirect.")
            response.raise_for_status()
        except requests.RequestException:
            raise SupabaseStoreError("Account changes could not be saved to Supabase.") from None
