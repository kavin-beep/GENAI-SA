"""Read optional Streamlit OIDC configuration without exposing its secrets."""

from collections.abc import Mapping

import streamlit as st


_PROVIDER_FIELDS = ("client_id", "client_secret", "server_metadata_url")
_SHARED_FIELDS = ("redirect_uri", "cookie_secret")


def _as_mapping(value: object) -> dict[str, object]:
    """Return a shallow mapping for Streamlit's secret tables."""
    if isinstance(value, Mapping):
        return dict(value)
    try:
        return dict(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return {}


def oidc_setup() -> tuple[str, tuple[str | None, ...]]:
    """Return preview, configured, or invalid without returning secret values."""
    try:
        auth = _as_mapping(st.secrets["auth"])
    except Exception:
        return "preview", ()

    if not auth:
        return "invalid", ()
    if not all(isinstance(auth.get(name), str) and str(auth[name]).strip() for name in _SHARED_FIELDS):
        return "invalid", ()

    if all(isinstance(auth.get(name), str) and str(auth[name]).strip() for name in _PROVIDER_FIELDS):
        return "configured", (None,)

    providers = tuple(
        str(name)
        for name, value in auth.items()
        if name not in (*_SHARED_FIELDS, *_PROVIDER_FIELDS)
        and all(
            isinstance(_as_mapping(value).get(field), str)
            and str(_as_mapping(value)[field]).strip()
            for field in _PROVIDER_FIELDS
        )
    )
    if providers:
        return "configured", providers
    return "invalid", ()
