"""Conversation-first CoachBot with safe chat and allowlisted app commands."""

import re
import unicodedata
from dataclasses import replace
from html import escape
from uuid import uuid4

import streamlit as st

import config
from core.schemas import GenerationParameters
from core.safety import wants_markdown_download
from ui.account_memory import persist_account_memory
from ui.components import result_widgets
from ui.controller import submit_chat
from ui.screens import render_chat_header
from ui.theme import render_ai_stage


_LANGUAGES = {name.casefold(): name for name in config.LANGUAGE_OPTIONS if name != "Other language"}
_TOKEN_LIMITS = {"concise": 512, "balanced": 1024, "detailed": 2048}


def _make_thread() -> dict[str, object]:
    return {"id": uuid4().hex, "title": "New chat", "messages": []}


def initialize_chat_state() -> None:
    """Create one empty conversation when a signed-in session first opens Chat."""
    if "chat_threads" not in st.session_state:
        st.session_state["chat_threads"] = []
    if not st.session_state["chat_threads"]:
        thread = _make_thread()
        st.session_state["chat_threads"] = [thread]
        st.session_state["active_chat_id"] = thread["id"]
    thread_ids = {thread["id"] for thread in st.session_state["chat_threads"]}
    if st.session_state.get("active_chat_id") not in thread_ids:
        st.session_state["active_chat_id"] = st.session_state["chat_threads"][0]["id"]


def clear_chat_state() -> None:
    """Drop session conversations and pending sample text when leaving the workspace."""
    for key in ("chat_threads", "active_chat_id"):
        st.session_state.pop(key, None)


def _new_chat() -> None:
    thread = _make_thread()
    threads = list(st.session_state.get("chat_threads", []))
    threads.insert(0, thread)
    st.session_state["chat_threads"] = threads[:12]
    st.session_state["active_chat_id"] = thread["id"]
    st.session_state["active_page"] = "Chat"


def render_chat_sidebar(account_store=None, account_key: str | None = None) -> None:
    """Add familiar new-chat and recent-conversation controls to the sidebar."""
    initialize_chat_state()
    if st.button("＋  New chat", key="coachbot_new_chat", type="secondary", width="stretch"):
        _new_chat()
        persist_account_memory(account_store, account_key)
        st.rerun()
    st.markdown('<div class="cb-rail-label">Chats</div>', unsafe_allow_html=True)
    recent_threads = [thread for thread in st.session_state["chat_threads"] if thread["messages"]]
    if not recent_threads:
        st.caption("Your conversations will appear here.")
    for thread in recent_threads[:12]:
        title = str(thread["title"])
        active = thread["id"] == st.session_state["active_chat_id"]
        if st.button(
            ("●  " if active else "◦  ") + title,
            key=f"coachbot_thread_{thread['id']}",
            type="secondary",
            width="stretch",
        ):
            st.session_state["active_chat_id"] = thread["id"]
            st.session_state["active_page"] = "Chat"
            persist_account_memory(account_store, account_key)
            st.rerun()


def _active_thread() -> dict[str, object]:
    initialize_chat_state()
    return next(
        thread for thread in st.session_state["chat_threads"]
        if thread["id"] == st.session_state["active_chat_id"]
    )


def _setting_command(message: str) -> str | None:
    """Apply only explicit, reversible settings commands without calling the model."""
    changed: list[str] = []
    text = message.strip()
    folded = text.casefold()

    dark_request = bool(re.search(
        r"\b(?:switch|change|set)\s+(?:the\s+)?(?:app\s+)?(?:theme|mode)\s+to\s+(?:dark|black|night)(?:\s+mode)?\b|"
        r"\b(?:switch|change|set)\s+to\s+(?:dark|black|night)(?:\s+(?:theme|mode))?\b|"
        r"\b(?:turn|put)\s+on\s+(?:the\s+)?(?:dark|black|night)\s+(?:theme|mode)\b|"
        r"\bmake\s+(?:the\s+)?(?:app|workspace|screen|it|this)\s+(?:dark|black|night)\b",
        folded,
    ))
    light_request = bool(re.search(
        r"\b(?:switch|change|set)\s+(?:the\s+)?(?:app\s+)?(?:theme|mode)\s+to\s+(?:light|white|day)(?:\s+mode)?\b|"
        r"\b(?:switch|change|set)\s+to\s+(?:light|white|day)(?:\s+(?:theme|mode))?\b|"
        r"\b(?:turn|put)\s+on\s+(?:the\s+)?(?:light|white|day)\s+(?:theme|mode)\b|"
        r"\bmake\s+(?:the\s+)?(?:app|workspace|screen|it|this)\s+(?:light|white|day)\b",
        folded,
    ))
    if dark_request:
        st.session_state["pending_black_theme"] = True
        changed.append("the black theme")
    elif light_request:
        st.session_state["pending_black_theme"] = False
        changed.append("the light theme")

    profile_off = bool(re.search(
        r"\b(?:turn|switch|set)\s+(?:off|disable)\s+(?:the\s+)?(?:profile\s+personalization|personalization|memory(?:\s+sharing)?)\b|"
        r"\b(?:don't|do not|stop)\s+(?:use|using|include|sending)\s+(?:my\s+)?(?:saved\s+)?(?:profile|memory|details\s+and\s+memory)\b",
        folded,
    ))
    profile_on = bool(re.search(
        r"\b(?:turn|switch|set)\s+(?:on|enable)\s+(?:the\s+)?(?:profile\s+personalization|personalization|memory(?:\s+sharing)?)\b|"
        r"\b(?:use|include)\s+(?:my\s+)?(?:saved\s+)?(?:profile|memory|details\s+and\s+memory)\s+(?:in|for)\s+(?:our\s+)?chats?\b|"
        r"\bpersonalize\s+(?:my|your)\s+(?:answers?|coaching)\s+with\s+(?:my\s+)?profile\b",
        folded,
    ))
    if profile_off:
        st.session_state["coach_profile_enabled"] = False
        changed.append("saved memory sharing off")
    elif profile_on:
        st.session_state["coach_profile_enabled"] = True
        changed.append("saved memory sharing on")

    language_match = re.search(
        r"\b(?:reply|respond|answer|speak|talk)\s+(?:to\s+me\s+)?in\s+([^\n.!?;]{2,60})|"
        r"\b(?:switch|change|set)\s+(?:the\s+)?(?:response\s+)?language\s+to\s+([^\n.!?;]{2,60})",
        text,
        re.I,
    )
    if language_match:
        requested = next((part for part in language_match.groups() if part), "")
        requested = re.split(r"\s+and\s+(?:be|keep|make|switch|change|set|more)\b", requested, maxsplit=1, flags=re.I)[0]
        requested = re.sub(r"\s+(?:please|from now on|starting now|for this chat)$", "", requested, flags=re.I).strip(" ,")
        valid_language = (
            2 <= len(requested) <= 60
            and 1 <= len(requested.split()) <= 4
            and any(character.isalpha() for character in requested)
            and all(unicodedata.category(character)[0] in ("L", "M") or character in " -()" for character in requested)
        )
        if valid_language:
            language = _LANGUAGES.get(requested.casefold(), requested)
            st.session_state["chat_language"] = language
            st.session_state["chat_language_choice"] = language if language in config.LANGUAGE_OPTIONS[:-1] else "Other language"
            st.session_state["chat_other_language"] = "" if language in config.LANGUAGE_OPTIONS[:-1] else language
            changed.append(f"{language} responses")

    if re.search(r"\b(?:be (?:more )?concise|make it concise|keep (?:it|your answers?) short|make (?:your )?(?:answers?|responses?|replies) shorter|brief responses?)\b", folded):
        st.session_state["chat_max_tokens"] = _TOKEN_LIMITS["concise"]
        changed.append("concise replies")
    elif re.search(r"\b(?:be (?:more )?detailed|give (?:me )?more detail|longer answers?|detailed (?:answers?|responses?)|expand your answers?)\b", folded):
        st.session_state["chat_max_tokens"] = _TOKEN_LIMITS["detailed"]
        changed.append("detailed replies")

    style_commands = (
        (r"\b(?:be|make your replies?)\s+(?:more\s+)?(?:encouraging|supportive|warm)\b", "Encouraging", "an encouraging tone"),
        (r"\b(?:be|make your replies?)\s+(?:more\s+)?(?:direct|straightforward)\b", "Straightforward", "a straightforward tone"),
        (r"\b(?:use|switch to|change to)\s+(?:a\s+)?balanced\s+(?:response\s+)?tone\b", "Balanced", "a balanced tone"),
    )
    for pattern, style, label in style_commands:
        if re.search(pattern, folded):
            st.session_state["chat_response_style"] = style
            changed.append(label)
            break

    if not changed:
        return None
    joined = ", ".join(changed)
    return f"Done — I changed {joined}. You can change these again at any time."


def _model_conversation(messages: list[dict[str, object]]) -> list[tuple[str, str]]:
    """Keep accepted AI exchanges and the newest pending user turn as context."""
    conversation: list[tuple[str, str]] = []
    for index, item in enumerate(messages):
        if item.get("settings_command"):
            continue
        role = str(item.get("role", ""))
        if role == "user" and isinstance(item.get("content"), str):
            next_turn = next((
                candidate for candidate in messages[index + 1:]
                if not candidate.get("settings_command")
            ), None)
            if next_turn is not None and next_turn.get("role") == "assistant":
                submission = next_turn.get("submission")
                if submission is None or submission.view.state != "screened" or not submission.view.origin.startswith("AI suggestion"):
                    continue
            elif next_turn is not None:
                continue
            conversation.append((role, str(item["content"])))
        elif role == "assistant":
            submission = item.get("submission")
            if (
                submission is not None
                and submission.view.state == "screened"
                and submission.view.origin.startswith("AI suggestion")
            ):
                view = submission.view
                parts = [view.answer] if view.answer else []
                if view.cards:
                    parts.append("\n".join(
                        f"{card.title}: {card.action} Rationale: {card.rationale}"
                        for card in view.cards
                    ))
                if view.questions:
                    parts.append("Follow-up questions:\n" + "\n".join(f"- {question}" for question in view.questions))
                answer = "\n\n".join(part for part in parts if part.strip())
                if answer:
                    conversation.append((role, answer))
    return conversation


def render_chat_page(
    api_notice: str | None,
    black_mode: bool,
    account_store=None,
    account_key: str | None = None,
    account_memory_status: str = "not_configured",
) -> None:
    """Render a normal sports chat without a separate context form."""
    thread = _active_thread()
    thread_id = str(thread["id"])
    messages = thread["messages"]
    language = str(st.session_state.get("chat_language", config.DEFAULT_LANGUAGE))
    max_tokens = int(st.session_state.get("chat_max_tokens", config.DEFAULT_MAX_TOKENS))
    response_style = str(st.session_state.get("chat_response_style", "Balanced"))
    profile = (
        st.session_state.get("coach_profile", {})
        if st.session_state.get("coach_profile_enabled", False) else None
    )
    parameters = GenerationParameters(
        temperature=config.DEFAULT_TEMPERATURE,
        top_p=config.DEFAULT_TOP_P,
        max_tokens=max_tokens,
    )

    render_chat_header(language)
    if account_memory_status == "connected":
        st.caption("Your account memory is on. Earlier chats can inform this conversation.")
    elif account_memory_status == "unavailable":
        st.warning("Account memory is temporarily unavailable. CoachBot will use this session's chats, and won't replace saved data.")
    elif account_memory_status == "not_configured":
        st.caption("Chat memory lasts for this session until Supabase account storage is connected in Settings.")
    elif account_memory_status == "incomplete":
        st.caption("Supabase account memory is not active yet. Finish the private settings in Settings to save chats across visits.")
    elif account_memory_status == "invalid":
        st.caption("Check the Supabase project URL in Settings to turn on account memory.")
    elif account_memory_status == "invalid_key":
        st.caption("Use a Supabase server secret key in Settings to turn on account memory.")
    elif account_memory_status == "identity_missing":
        st.caption("Account memory is unavailable because sign-in did not provide an account ID.")
    if api_notice:
        st.info("Live replies are unavailable until a private Groq API key is configured.")

    if not messages:
        st.markdown(
            '<section class="cb-chat-empty"><h1>What can I help with?</h1>'
            '<p>Ask about sports, general wellness, or a practice plan.</p></section>',
            unsafe_allow_html=True,
        )
        render_ai_stage(black_mode, compact=True, chat_mode=True)
    else:
        for item in messages:
            if item["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(f'<div class="cb-user-message">{escape(str(item["content"]))}</div>', unsafe_allow_html=True)
            else:
                with st.chat_message("assistant", avatar="⚽"):
                    if item.get("settings_command"):
                        st.markdown(escape(str(item["content"])))
                    else:
                        result_widgets(
                            item["submission"],
                            key_prefix=f"chat_{item['submission'].result_id}",
                            include_feedback_download=False,
                            show_feedback=False,
                            chat_mode=True,
                        )

    message = st.chat_input(
        "Message CoachBot about sport or wellness…",
        max_chars=2000,
        key=f"coachbot_chat_input_{thread_id}",
    )
    st.markdown(
        '<div class="cb-chat-disclaimer">AI can make mistakes. Check sports and health advice with a qualified adult or professional.</div>',
        unsafe_allow_html=True,
    )
    if message and message.strip():
        user_text = message.strip()
        messages.append({"role": "user", "content": user_text})
        if thread["title"] == "New chat":
            thread["title"] = " ".join(user_text.split())[:36] or "New chat"

        # Save the user's turn before contacting Groq so a failed or interrupted
        # model request does not erase what they told CoachBot.
        persist_account_memory(account_store, account_key)

        command_reply = _setting_command(user_text)
        if command_reply:
            messages[-1]["settings_command"] = True
            messages.append({"role": "assistant", "content": command_reply, "settings_command": True})
            persist_account_memory(account_store, account_key)
            st.rerun()

        if wants_markdown_download(user_text):
            previous = next((
                item for item in reversed(messages[:-1])
                if item["role"] == "assistant" and item.get("submission") is not None
            ), None)
            if previous is not None:
                old_submission = previous["submission"]
                old_view = old_submission.view
                if old_view.state == "screened" and (old_view.cards or old_view.answer):
                    previous["submission"] = replace(
                        old_submission,
                        view=old_view.model_copy(update={"markdown_download_requested": True}),
                    )
                    messages[-1]["settings_command"] = True
                    messages.append({
                        "role": "assistant",
                        "content": "I’ve added a Markdown download to the response above.",
                        "settings_command": True,
                    })
                    persist_account_memory(account_store, account_key)
                    st.rerun()

        earlier_chats: list[tuple[str, str]] = []
        for saved_thread in reversed(st.session_state["chat_threads"]):
            if saved_thread["id"] != thread_id:
                earlier_chats.extend(_model_conversation(saved_thread["messages"]))
        conversation = earlier_chats + _model_conversation(messages)
        with st.spinner("CoachBot is thinking…"):
            submission = submit_chat(
                conversation, language=language, parameters=parameters, profile=profile,
                response_style=response_style,
            )
        messages.append({"role": "assistant", "submission": submission})
        persist_account_memory(account_store, account_key)
        st.rerun()
