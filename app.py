"""CoachBot AI chat workspace with chat history and Settings."""

import importlib

import streamlit as st

import config

# Streamlit reruns this script in-process during local development. Reload the
# app modules here so edited safety and presentation rules apply to live chats.
import core.schemas as _core_schemas
import core.groq_client as _core_groq_client
import core.supabase_store as _core_supabase_store
import core.safety as _core_safety
import core.formatter as _core_formatter
import ui.controller as _ui_controller
import ui.account_memory as _ui_account_memory
import ui.components as _ui_components
import ui.theme as _ui_theme
import ui.chat as _ui_chat
import ui.screens as _ui_screens

importlib.reload(_core_schemas)
importlib.reload(_core_groq_client)
importlib.reload(_core_supabase_store)
importlib.reload(_core_safety)
importlib.reload(_core_formatter)
importlib.reload(_ui_controller)
importlib.reload(_ui_account_memory)
importlib.reload(_ui_components)
importlib.reload(_ui_theme)
importlib.reload(_ui_screens)
importlib.reload(_ui_chat)

from ui.auth import oidc_setup
from ui.account_memory import (
    account_key_from_user,
    clear_account_memory_session,
    initialize_account_memory,
    persist_account_memory,
)
from ui.chat import initialize_chat_state, render_chat_page, render_chat_sidebar
from ui.components import initialize_session
from ui.screens import render_login, render_settings
from ui.theme import render_theme
from core.groq_client import GroqClient
from core.supabase_store import SupabaseAccountStore


st.set_page_config(page_title=config.APP_NAME, page_icon="⚽", layout="wide")


def _leave_preview() -> None:
    """Clear the session's inputs and results while retaining its appearance preference."""
    night_mode = bool(st.session_state.get("black_theme", False))
    st.session_state.clear()
    st.session_state["black_theme"] = night_mode
    st.session_state["active_page"] = "Chat"


def _logout() -> None:
    """End sign-in and discard this browser session's account-specific state."""
    clear_account_memory_session()
    st.logout()


auth_mode, providers = oidc_setup()
try:
    account_store, account_store_config = SupabaseAccountStore.from_secrets(st.secrets)
except Exception:
    account_store, account_store_config = None, "invalid"
account_key: str | None = None
if auth_mode == "configured":
    authenticated = bool(st.user.is_logged_in)
    if authenticated:
        account_key = account_key_from_user(st.user)
        if account_key:
            account_memory_status = initialize_account_memory(
                account_store, account_key, account_store_config,
            )
        else:
            clear_account_memory_session()
            account_memory_status = "identity_missing"
    else:
        account_memory_status = "not_signed_in"
elif auth_mode == "invalid":
    authenticated = False
    account_memory_status = "not_signed_in"
else:
    authenticated = bool(st.session_state.get("preview_authenticated", False))
    account_memory_status = "preview"

if "black_theme" not in st.session_state:
    st.session_state["black_theme"] = False
if "pending_black_theme" in st.session_state:
    st.session_state["black_theme"] = bool(st.session_state.pop("pending_black_theme"))
st.session_state.setdefault("chat_language", config.DEFAULT_LANGUAGE)
st.session_state.setdefault("chat_language_choice", config.DEFAULT_LANGUAGE)
st.session_state.setdefault("chat_other_language", "")
st.session_state.setdefault("chat_max_tokens", config.DEFAULT_MAX_TOKENS)
if "active_page" not in st.session_state:
    st.session_state["active_page"] = "Chat"

with st.sidebar:
    st.markdown(
        '<div class="cb-brand"><span class="cb-brand-mark">C<span>·</span></span>'
        '<span><b>CoachBot</b><small>SPORT / REFLECT</small></span></div>',
        unsafe_allow_html=True,
    )
    black_mode = st.toggle(
        "Black theme",
        key="black_theme",
        help="On: black canvas and white text. Off: white paper and black text.",
    )

render_theme(black_mode)
if not authenticated:
    render_login(auth_mode, providers)
    st.stop()

initialize_session()
initialize_chat_state()
if st.session_state.active_page not in ("Chat", "Settings"):
    st.session_state.active_page = "Chat"

with st.sidebar:
    render_chat_sidebar(account_store, account_key)
    st.divider()
    page = st.session_state.get("active_page", "Chat")
    if st.button(
        "⚙  Settings",
        key="sidebar_settings",
        type="primary" if page == "Settings" else "secondary",
        width="stretch",
    ):
        st.session_state["active_page"] = "Settings"
        st.rerun()
    if auth_mode != "configured":
        rail_status = "LOCAL PREVIEW"
    elif account_memory_status == "connected":
        rail_status = "ACCOUNT MEMORY ON"
    else:
        rail_status = "SESSION MEMORY ONLY"
    st.markdown(f'<div class="cb-rail-footer"><i></i><span>{rail_status}</span></div>', unsafe_allow_html=True)
    if auth_mode == "configured":
        st.button("Sign out", key="oidc_logout", on_click=_logout, width="stretch")
    else:
        st.button("Leave preview", key="preview_logout", on_click=_leave_preview, width="stretch")

api_notice = GroqClient.setup_notice()

if st.session_state.get("active_page") == "Settings":
    render_settings(
        api_notice, auth_mode, account_memory_status, account_store, account_key,
    )
else:
    render_chat_page(
        api_notice, black_mode, account_store, account_key, account_memory_status,
    )

if account_key:
    save_status = persist_account_memory(account_store, account_key)
    if save_status == "unavailable":
        st.warning("CoachBot could not sync your saved history right now. It remains available in this session; saved account data was not replaced.")
