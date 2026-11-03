"""Load, save and validate account-scoped CoachBot conversation memory."""

from __future__ import annotations

import hashlib
import json
import streamlit as st
from pydantic import ValidationError

import config
from core.formatter import DisplayPlan
from core.safety import CoachProfile
from core.supabase_store import SupabaseAccountStore, SupabaseStoreError
from ui.controller import Submission


_PAYLOAD_VERSION = 1
_VALID_TOKEN_LIMITS = {512, 1024, 2048}
_VALID_STYLES = {"Balanced", "Encouraging", "Straightforward"}
_PROFILE_WIDGET_MAP = {
    "profile_preferred_name": "preferred_name",
    "profile_age_band": "age_band",
    "profile_sport": "sport",
    "profile_position": "position",
    "profile_experience": "experience_level",
    "profile_goal": "goal",
    "profile_equipment": "equipment",
    "profile_memory": "memory",
}


def account_key_from_user(user: object) -> str | None:
    """Hash the verified OIDC subject; never store an email as the row key."""
    try:
        subject = user["sub"]  # type: ignore[index]
        issuer = user.get("iss", "google")  # type: ignore[attr-defined]
    except (KeyError, TypeError, AttributeError):
        return None
    if not isinstance(subject, str) or not subject.strip():
        return None
    if not isinstance(issuer, str) or not issuer.strip():
        issuer = "google"
    raw_key = f"coachbot-account-v1\0{issuer.strip()}\0{subject.strip()}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def _submission_to_dict(submission: object) -> dict[str, object] | None:
    view = getattr(submission, "view", None)
    if view is None or not callable(getattr(view, "model_dump", None)):
        return None
    try:
        return {
            "result_id": str(submission.result_id),
            "fingerprint": str(submission.fingerprint),
            "prompt_id": str(submission.prompt_id),
            "prompt_version": str(submission.prompt_version),
            "view": view.model_dump(mode="json"),
            "warnings": list(submission.warnings),
            "setup_message": str(submission.setup_message),
        }
    except (AttributeError, TypeError, ValueError):
        return None


def _submission_from_dict(value: object) -> Submission | None:
    if not isinstance(value, dict):
        return None
    try:
        warnings = value.get("warnings", [])
        if not isinstance(warnings, list) or any(not isinstance(item, str) for item in warnings):
            return None
        raw_view = value["view"]
        if not isinstance(raw_view, dict):
            return None
        view_data = dict(raw_view)
        view_data["cards"] = tuple(view_data.get("cards", ()))
        view_data["questions"] = tuple(view_data.get("questions", ()))
        return Submission(
            result_id=str(value["result_id"]),
            fingerprint=str(value["fingerprint"]),
            prompt_id=str(value["prompt_id"]),
            prompt_version=str(value["prompt_version"]),
            view=DisplayPlan.model_validate(view_data),
            warnings=tuple(warnings),
            setup_message=str(value.get("setup_message", "")),
        )
    except (KeyError, TypeError, ValueError, ValidationError):
        return None


def _thread_to_dict(thread: object) -> dict[str, object] | None:
    if not isinstance(thread, dict):
        return None
    thread_id, title, raw_messages = thread.get("id"), thread.get("title"), thread.get("messages")
    if not isinstance(thread_id, str) or not isinstance(title, str) or not isinstance(raw_messages, list):
        return None
    messages: list[dict[str, object]] = []
    for item in raw_messages:
        if not isinstance(item, dict) or item.get("role") not in {"user", "assistant"}:
            continue
        message: dict[str, object] = {"role": item["role"]}
        content = item.get("content")
        if isinstance(content, str) and len(content) <= 5000:
            message["content"] = content
        elif item["role"] == "user":
            continue
        if item.get("settings_command") is True:
            message["settings_command"] = True
        submission = _submission_to_dict(item.get("submission"))
        if submission is not None:
            message["submission"] = submission
        if item["role"] == "assistant" and submission is None and not message.get("settings_command"):
            continue
        messages.append(message)
    return {"id": thread_id, "title": title, "messages": messages}


def _thread_from_dict(value: object) -> dict[str, object] | None:
    if not isinstance(value, dict):
        return None
    thread_id, title, raw_messages = value.get("id"), value.get("title"), value.get("messages")
    if not isinstance(thread_id, str) or not isinstance(title, str) or not isinstance(raw_messages, list):
        return None
    messages: list[dict[str, object]] = []
    for item in raw_messages:
        if not isinstance(item, dict) or item.get("role") not in {"user", "assistant"}:
            continue
        message: dict[str, object] = {"role": item["role"]}
        content = item.get("content")
        if isinstance(content, str) and len(content) <= 5000:
            message["content"] = content
        elif item["role"] == "user":
            continue
        if item.get("settings_command") is True:
            message["settings_command"] = True
        submission = _submission_from_dict(item.get("submission"))
        if submission is not None:
            message["submission"] = submission
        if item["role"] == "assistant" and submission is None and not message.get("settings_command"):
            continue
        messages.append(message)
    return {"id": thread_id, "title": title, "messages": messages}


def _snapshot() -> dict[str, object]:
    raw_profile = st.session_state.get("coach_profile", {})
    try:
        profile = CoachProfile.model_validate(raw_profile).model_dump(mode="json")
    except (ValueError, ValidationError):
        profile = CoachProfile().model_dump(mode="json")
    threads = [thread for raw in st.session_state.get("chat_threads", [])[:12]
               if (thread := _thread_to_dict(raw)) is not None]
    return {
        "version": _PAYLOAD_VERSION,
        "threads": threads,
        "active_chat_id": str(st.session_state.get("active_chat_id", "")),
        "profile": profile,
        "profile_enabled": bool(st.session_state.get("coach_profile_enabled", False)),
        "preferences": {
            "black_theme": bool(st.session_state.get("black_theme", False)),
            "chat_language": str(st.session_state.get("chat_language", config.DEFAULT_LANGUAGE))[:60],
            "chat_language_choice": str(st.session_state.get("chat_language_choice", config.DEFAULT_LANGUAGE))[:60],
            "chat_other_language": str(st.session_state.get("chat_other_language", ""))[:60],
            "chat_max_tokens": int(st.session_state.get("chat_max_tokens", config.DEFAULT_MAX_TOKENS)),
            "chat_response_style": str(st.session_state.get("chat_response_style", "Balanced"))[:30],
        },
    }


def _fingerprint(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _changed_sections(before: object, after: dict[str, object]) -> set[str]:
    if not isinstance(before, dict):
        return {"threads", "profile", "preferences"}
    changed: set[str] = set()
    if before.get("threads") != after.get("threads") or before.get("active_chat_id") != after.get("active_chat_id"):
        changed.add("threads")
    if before.get("profile") != after.get("profile") or before.get("profile_enabled") != after.get("profile_enabled"):
        changed.add("profile")
    if before.get("preferences") != after.get("preferences"):
        changed.add("preferences")
    return changed


def _merge_payloads(
    remote: dict[str, object],
    local: dict[str, object],
    dirty_sections: set[str],
) -> dict[str, object]:
    """Keep offline edits while retaining saved rows from the connected account."""
    merged = dict(remote)
    merged["version"] = _PAYLOAD_VERSION
    if "threads" in dirty_sections:
        remote_threads = remote.get("threads", [])
        local_threads = local.get("threads", [])
        remote_threads = remote_threads if isinstance(remote_threads, list) else []
        local_threads = local_threads if isinstance(local_threads, list) else []
        combined: list[object] = []
        seen: set[str] = set()
        for item in [*local_threads, *remote_threads]:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                continue
            thread_id = item["id"]
            if thread_id not in seen:
                combined.append(item)
                seen.add(thread_id)
        merged["threads"] = combined[:12]
        local_active = local.get("active_chat_id", "")
        merged["active_chat_id"] = local_active if local_active in seen else remote.get("active_chat_id", "")
    if "profile" in dirty_sections:
        merged["profile"] = local.get("profile", {})
        merged["profile_enabled"] = local.get("profile_enabled", False)
    if "preferences" in dirty_sections:
        merged["preferences"] = local.get("preferences", {})
    return merged


def _reset_user_state() -> None:
    """Avoid reusing chat or profile values if the authenticated account changes."""
    st.session_state.clear()


def _apply_payload(payload: dict[str, object] | None) -> None:
    data = payload or {}
    if data.get("version", _PAYLOAD_VERSION) != _PAYLOAD_VERSION:
        raise ValueError("Unsupported saved account data version.")
    raw_threads = data.get("threads", [])
    if not isinstance(raw_threads, list):
        raise ValueError("Saved chat history has an unsupported format.")
    threads = [thread for raw in raw_threads[:12]
               if (thread := _thread_from_dict(raw)) is not None]
    try:
        profile = CoachProfile.model_validate(data.get("profile", {})).model_dump(mode="json")
    except (TypeError, ValueError, ValidationError) as exc:
        raise ValueError("Saved profile has an unsupported format.") from exc
    preferences = data.get("preferences", {})
    if not isinstance(preferences, dict):
        preferences = {}
    language_choice = preferences.get("chat_language_choice", config.DEFAULT_LANGUAGE)
    if language_choice not in config.LANGUAGE_OPTIONS:
        language_choice = config.DEFAULT_LANGUAGE
    token_limit = preferences.get("chat_max_tokens", config.DEFAULT_MAX_TOKENS)
    if token_limit not in _VALID_TOKEN_LIMITS:
        token_limit = config.DEFAULT_MAX_TOKENS
    response_style = preferences.get("chat_response_style", "Balanced")
    if response_style not in _VALID_STYLES:
        response_style = "Balanced"
    other_language = preferences.get("chat_other_language", "")
    if not isinstance(other_language, str):
        other_language = ""
    language = preferences.get("chat_language", config.DEFAULT_LANGUAGE)
    if not isinstance(language, str) or not language.strip():
        language = config.DEFAULT_LANGUAGE
    active_chat_id = data.get("active_chat_id", "")
    if not isinstance(active_chat_id, str):
        active_chat_id = ""

    st.session_state.update({
        "chat_threads": threads,
        "active_chat_id": active_chat_id,
        "coach_profile": profile,
        "coach_profile_enabled": bool(data.get("profile_enabled", False)),
        "black_theme": bool(preferences.get("black_theme", False)),
        "chat_language": language[:60],
        "chat_language_choice": language_choice,
        "chat_other_language": other_language[:60],
        "chat_max_tokens": int(token_limit),
        "chat_response_style": response_style,
    })
    for widget_key, field_name in _PROFILE_WIDGET_MAP.items():
        st.session_state[widget_key] = profile[field_name]


def initialize_account_memory(
    store: SupabaseAccountStore | None,
    account_key: str,
    config_status: str,
) -> str:
    """Load saved account data once per identity and report current storage state."""
    same_account = (
        st.session_state.get("_coachbot_account_owner") == account_key
        and st.session_state.get("_coachbot_account_loaded") is True
    )
    if same_account:
        old_status = str(st.session_state.get("_coachbot_account_store_status", "not_configured"))
        writable = st.session_state.get("_coachbot_account_store_writable") is True
        if store is None or config_status != "configured":
            status = config_status if config_status in {"not_configured", "incomplete", "invalid", "invalid_key"} else old_status
            st.session_state["_coachbot_account_store_status"] = status
            st.session_state["_coachbot_account_store_writable"] = False
            return status
        if writable:
            return old_status
        try:
            payload = store.load(account_key)
            if payload is not None:
                dirty_sections = set(st.session_state.get("_coachbot_dirty_sections", []))
                if dirty_sections:
                    local_payload = _snapshot()
                    _apply_payload(_merge_payloads(payload, local_payload, dirty_sections))
                else:
                    _apply_payload(payload)
                st.session_state["_coachbot_last_saved_fingerprint"] = _fingerprint(payload)
                st.session_state["_coachbot_last_snapshot"] = payload
            else:
                st.session_state["_coachbot_last_saved_fingerprint"] = ""
                st.session_state["_coachbot_last_snapshot"] = _snapshot()
            st.session_state["_coachbot_account_store_status"] = "connected"
            st.session_state["_coachbot_account_store_writable"] = True
            return "connected"
        except (SupabaseStoreError, ValueError):
            st.session_state["_coachbot_account_store_status"] = "unavailable"
            return "unavailable"

    _reset_user_state()
    status = config_status if config_status in {"not_configured", "incomplete", "invalid", "invalid_key"} else "unavailable"
    payload: dict[str, object] | None = None
    writable = False
    if store is not None:
        try:
            payload = store.load(account_key)
            _apply_payload(payload)
            status = "connected"
            writable = True
        except (SupabaseStoreError, ValueError):
            _apply_payload(None)
            status = "unavailable"
            writable = False
    else:
        _apply_payload(None)

    st.session_state["_coachbot_account_owner"] = account_key
    st.session_state["_coachbot_account_loaded"] = True
    st.session_state["_coachbot_account_store_status"] = status
    st.session_state["_coachbot_account_store_writable"] = writable
    st.session_state["_coachbot_last_saved_fingerprint"] = _fingerprint(payload) if payload is not None else ""
    st.session_state["_coachbot_last_snapshot"] = _snapshot()
    st.session_state["_coachbot_dirty_sections"] = []
    return status


def persist_account_memory(store: SupabaseAccountStore | None, account_key: str | None) -> str:
    """Save current chats/settings without writing anything outside the account row."""
    if (
        account_key is None
        or st.session_state.get("_coachbot_account_owner") != account_key
    ):
        return str(st.session_state.get("_coachbot_account_store_status", "not_configured"))
    payload = _snapshot()
    fingerprint = _fingerprint(payload)
    changed_sections = _changed_sections(st.session_state.get("_coachbot_last_snapshot"), payload)
    dirty_sections = set(st.session_state.get("_coachbot_dirty_sections", [])) | changed_sections
    if not dirty_sections and fingerprint == st.session_state.get("_coachbot_last_saved_fingerprint"):
        return str(st.session_state.get("_coachbot_account_store_status", "not_configured"))
    if store is None or st.session_state.get("_coachbot_account_store_writable") is not True:
        st.session_state["_coachbot_dirty_sections"] = sorted(dirty_sections)
        st.session_state["_coachbot_last_snapshot"] = payload
        return str(st.session_state.get("_coachbot_account_store_status", "not_configured"))
    if fingerprint == st.session_state.get("_coachbot_last_saved_fingerprint"):
        st.session_state["_coachbot_dirty_sections"] = []
        st.session_state["_coachbot_last_snapshot"] = payload
        st.session_state["_coachbot_account_store_status"] = "connected"
        return "connected"
    try:
        store.save(account_key, payload)
    except (SupabaseStoreError, ValueError):
        st.session_state["_coachbot_account_store_status"] = "unavailable"
        st.session_state["_coachbot_dirty_sections"] = sorted(dirty_sections)
        st.session_state["_coachbot_last_snapshot"] = payload
        return "unavailable"
    st.session_state["_coachbot_last_saved_fingerprint"] = fingerprint
    st.session_state["_coachbot_last_snapshot"] = payload
    st.session_state["_coachbot_dirty_sections"] = []
    st.session_state["_coachbot_account_store_status"] = "connected"
    return "connected"


def clear_account_memory_session() -> None:
    """Discard this browser session's account data on logout; remote history remains."""
    _reset_user_state()

