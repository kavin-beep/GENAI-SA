"""Reusable widgets, reviewed cards and session-local feedback controls."""

from html import escape
from uuid import uuid4
import streamlit as st
import config
from core.feedback import FeedbackEvent, save_feedback
from core.formatter import DisplayPlan, to_markdown
from core.prompts import REGISTRY
from core.safety import CoachProfile, HealthContext
from core.schemas import GenerationParameters
from ui.controller import Draft, Submission

_LABELS = {"sport": "Sport", "position": "Playing position", "region": "Region or local context",
           "situation": "What happened?", "available_resources": "People or resources available",
           "goal": "What would you like to understand?"}
_REGIONS = {"Head or neck": "head_neck", "Back": "back", "Shoulder or arm": "shoulder_arm",
            "Wrist or hand": "wrist_hand", "Hip": "hip", "Knee": "knee", "Ankle or foot": "ankle_foot", "Other": "other"}


@st.cache_data(show_spinner=False)
def feature_catalog(definitions: tuple[tuple[str, str, str], ...]) -> dict[str, str]:
    """Cache deterministic public labels only, never private inputs or replies."""
    return {prompt_id: prompt_id.replace("_", " ").capitalize() for prompt_id, _, _ in definitions}


def initialize_session() -> None:
    """Ordinary reruns retain widget values and session feedback."""
    if "feedback_session_id" not in st.session_state:
        st.session_state.feedback_session_id = uuid4().hex
    if "feedback_events" not in st.session_state:
        st.session_state.feedback_events = []
    if "saved_feedback_votes" not in st.session_state:
        st.session_state.saved_feedback_votes = {}
    if "coach_profile" not in st.session_state:
        st.session_state.coach_profile = CoachProfile().model_dump()
    if "coach_profile_enabled" not in st.session_state:
        st.session_state.coach_profile_enabled = False
    st.session_state.setdefault("chat_response_style", "Balanced")


def input_widgets(*, chat_mode: bool = False) -> Draft:
    """Collect private context in the chat settings popover or on the legacy form."""
    entries = REGISTRY.entries()
    catalog = feature_catalog(tuple((entry.id, entry.version, entry.intent) for entry in entries))
    values: dict[str, str] = {}
    with st.container(border=not chat_mode):
        if not chat_mode:
            st.markdown('<div class="cb-section-label">01 · Set the scene</div>', unsafe_allow_html=True)
            st.subheader("Your situation")
        else:
            st.caption("Sport and age are required. Leave optional details blank if you prefer.")
        feature = st.selectbox("Coaching feature", tuple(catalog), format_func=catalog.get, key="feature")
        entry = REGISTRY.get(feature)
        st.caption("Tactical reflection helps you discuss decisions. It does not prescribe physical training.")
        if feature == "tactical_reflection" and st.button(
            "Try a fictional sample", key="try_tactical_sample",
            help="Fills this form with an invented example. Review or change it before sending.",
        ):
            sample = {
                "sport": "Football",
                "position": "Midfielder",
                "age": 15,
                "region": "School team",
                "situation": "I passed to a marked teammate while another teammate was free.",
                "available_resources": "A notebook and a conversation with my coach",
                "goal": "Understand what to discuss when reviewing this decision.",
            }
            for name, value in sample.items():
                if chat_mode and name == "situation":
                    st.session_state["chat_sample_message"] = value
                else:
                    st.session_state[f"input_{name}"] = value
            st.session_state["injury_status"] = "None reported"
            st.session_state["injury_regions"] = []
            st.session_state["injury_description"] = ""
            st.session_state["pain"] = "No"
            st.session_state["concussion"] = "No"
            st.session_state["urgent"] = "No"
            st.session_state["language_choice"] = config.DEFAULT_LANGUAGE
            st.session_state["other_language"] = ""
            if config.MODEL_SUPPORTS_SAMPLING_PARAMETERS:
                st.session_state[f"temperature_{feature}"] = entry.recommended_temperature
                st.session_state[f"top_p_{feature}"] = entry.recommended_top_p
            st.session_state["max_tokens"] = config.DEFAULT_MAX_TOKENS
            st.session_state.pop("current_submission", None)
            st.success("Fictional sample loaded. Review or edit it before requesting suggestions.")

        def render_field(name: str) -> None:
            label = _LABELS.get(name, name.replace("_", " ").capitalize())
            if name == "age":
                age = st.number_input("Age", min_value=1, max_value=17, value=None, step=1,
                                      placeholder="Enter your age", key="input_age")
                values[name] = str(age) if age is not None else ""
            elif name in ("situation", "goal"):
                values[name] = st.text_area(label, max_chars=2000, key=f"input_{name}")
            else:
                values[name] = st.text_input(label, max_chars=2000, key=f"input_{name}")

        field_names = [
            name for name in entry.required_inputs
            if name != "injury_context" and not (chat_mode and name in ("situation", "goal"))
        ]
        compact_names = [name for name in ("sport", "position", "age") if name in field_names]
        if compact_names:
            columns = st.columns(len(compact_names))
            for name, column in zip(compact_names, columns):
                with column:
                    render_field(name)
        for name in field_names:
            if name not in compact_names:
                render_field(name)

    with st.container(border=not chat_mode):
        if not chat_mode:
            st.markdown('<div class="cb-section-label">02 · Check in</div>', unsafe_allow_html=True)
            st.subheader("Health and safety")
        else:
            st.markdown("**Health and safety**")
        st.caption("Choose each answer explicitly. Leave out your name and medical documents.")
        injury = st.radio("Injury history", ("None reported", "Reported", "Not sure"),
                          index=None, key="injury_status", horizontal=True)
        regions = st.multiselect("Affected areas, if relevant", tuple(_REGIONS), key="injury_regions")
        description = st.text_area("Injury context, if reported", max_chars=2000, key="injury_description",
                                   help="Brief context only. Do not include identifying details.")
        pain = st.radio("Are you currently in pain?", ("Yes", "No", "Not sure"),
                        index=None, key="pain", horizontal=True)
        concussion = st.radio("Is a concussion suspected?", ("Yes", "No", "Not sure"),
                              index=None, key="concussion", horizontal=True)
        urgent = st.radio(
            "Are there urgent symptoms?", ("Yes", "No", "Not sure"),
            index=None, key="urgent", horizontal=True,
            help="For example: repeated vomiting, a seizure, slurred speech or difficulty waking. This is not a complete list.",
        )
        values["injury_context"] = description.strip() or ("none" if injury == "None reported" else "unknown")
    unanswered = any(value is None for value in (injury, pain, concussion, urgent))
    known_concern = any(value == "Yes" for value in (pain, concussion, urgent))
    if unanswered and not known_concern:
        health = None
    else:
        uncertain = any(value in (None, "Not sure") for value in (injury, pain, concussion, urgent))
        status = "unknown" if uncertain else {"None reported": "none", "Reported": "reported"}[injury]
        health = HealthContext(injury_status=status, injury_regions=tuple(_REGIONS[item] for item in regions),
                               current_pain=pain == "Yes", suspected_concussion=concussion == "Yes", urgent_symptoms=urgent == "Yes")
    with st.container(border=not chat_mode):
        if not chat_mode:
            st.markdown('<div class="cb-section-label">03 · Choose your response</div>', unsafe_allow_html=True)
            st.subheader("Response preferences")
        else:
            st.markdown("**Response preferences**")
        choice = st.selectbox("Response language", config.LANGUAGE_OPTIONS, key="language_choice")
        other = st.text_input("Other language name", key="other_language", max_chars=60,
                              disabled=choice != "Other language")
        language = other.strip() if choice == "Other language" else choice
        st.caption("English is the default. Interface labels and fixed safety notices stay in English.")
        with st.expander("Response settings"):
            if config.MODEL_SUPPORTS_SAMPLING_PARAMETERS:
                temperature = st.slider("Temperature", 0.0, 2.0, entry.recommended_temperature, 0.1,
                                        key=f"temperature_{feature}",
                                        help="A lower value does not guarantee accuracy or safety.")
                top_p = st.slider("Top_p", 0.05, 1.0, entry.recommended_top_p, 0.05, key=f"top_p_{feature}")
            else:
                temperature, top_p = entry.recommended_temperature, entry.recommended_top_p
                st.caption("This model accepts temperature and top_p settings. These controls change sampling, not factual accuracy or safety.")
            max_tokens = st.selectbox("Maximum output tokens", (256, 512, 1024, 2048), index=3, key="max_tokens",
                                      help="A small limit can cut off a response; partial advice will not be shown.")
    if chat_mode:
        values["situation"] = ""
        values["goal"] = "Reflect on the described moment and prepare a question for a coach."
        for name in ("position", "region", "available_resources"):
            values[name] = values[name].strip() or "Not provided"
    return Draft(entry, values, language, GenerationParameters(temperature=temperature, top_p=top_p, max_tokens=max_tokens), health, unanswered)


def render_plan(view: DisplayPlan, *, chat_mode: bool = False) -> None:
    """Render screened model strings as plain text; keep each rationale beside its advice."""
    if chat_mode:
        if view.state != "screened" and view.heading:
            st.markdown(f"**{escape(view.heading)}**")
        if view.answer:
            st.markdown(view.answer)
        for index, card in enumerate(view.cards, start=1):
            st.markdown(
                f"**{index}. {escape(card.title)}**\n\n{escape(card.action)}\n\n"
                f"*Why: {escape(card.rationale)}*"
            )
        if view.questions:
            st.markdown("**A couple of questions**")
            for question in view.questions:
                st.markdown(f"- {escape(question)}")
        return

    st.markdown(f'<div class="cb-chat-plan-heading">{escape(view.heading)}</div>', unsafe_allow_html=True)
    st.caption(f"{escape(view.language)} · {escape(view.origin)}")
    if view.answer:
        st.markdown(f'<div class="cb-chat-answer">{escape(view.answer)}</div>', unsafe_allow_html=True)
    st.caption(escape(view.disclaimer))
    st.caption(escape(view.review_note))
    for index, card in enumerate(view.cards, start=1):
        with st.container(border=True):
            st.markdown(f'<div class="cb-recommendation-title">{index}. {escape(card.title)}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="cb-recommendation-copy">{escape(card.action)}</div>', unsafe_allow_html=True)
            st.markdown('<div class="cb-rationale-label">Rationale</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="cb-recommendation-copy">{escape(card.rationale)}</div>', unsafe_allow_html=True)
    if view.questions:
        st.markdown("**Clarifying questions**")
        for question in view.questions:
            st.markdown(f'<div class="cb-recommendation-copy">{escape(question)}</div>', unsafe_allow_html=True)


def result_widgets(
    submission: Submission, *, key_prefix: str = "plan",
    include_feedback_download: bool = True, show_feedback: bool = True,
    chat_mode: bool = False,
) -> None:
    """Votes and downloads rerun only the UI, never the generation client."""
    render_plan(submission.view, chat_mode=chat_mode)
    if submission.setup_message:
        st.info(submission.setup_message)
    for warning in submission.warnings:
        st.warning(warning)
    if submission.view.cards or submission.view.answer:
        offer_markdown = (
            submission.prompt_id != "coach_chat"
            or getattr(submission.view, "markdown_download_requested", False)
        )
        if offer_markdown:
            is_plan = bool(submission.view.cards)
            label = "Download plan (.md)" if is_plan else "Download answer (.md)"
            filename = "coachbot-plan.md" if is_plan else "coachbot-answer.md"
            st.download_button(label, to_markdown(submission.view),
                               file_name=filename, mime="text/markdown", key=f"{key_prefix}_download", width="stretch")
    if submission.view.state == "screened" and show_feedback:
        st.markdown("**Was this response useful?**")
        vote = st.feedback("thumbs", key=f"vote_{submission.result_id}")
        if vote is not None and st.session_state.saved_feedback_votes.get(submission.result_id) != vote:
            event = FeedbackEvent(result_id=submission.result_id, prompt_id=submission.prompt_id,
                                  prompt_version=submission.prompt_version, vote="up" if vote else "down")
            st.session_state.feedback_events.append(event.model_dump_json())
            st.session_state.saved_feedback_votes[submission.result_id] = vote
            st.session_state["feedback_storage_ok"] = save_feedback(event, st.session_state.feedback_session_id)
        if submission.result_id in st.session_state.saved_feedback_votes:
            st.success("Thank you—your feedback has been recorded for this session.")
            if not st.session_state.get("feedback_storage_ok", True):
                st.warning("Local storage was unavailable. Download your feedback to keep a copy.")
    if include_feedback_download and st.session_state.feedback_events:
        st.download_button("Download my feedback (.jsonl)", "\n".join(st.session_state.feedback_events) + "\n",
                           file_name="coachbot-feedback.jsonl", mime="application/x-ndjson", key="feedback_download")
        st.caption("Feedback stores votes and response IDs, not your sporting or injury details. Cloud-local files may be lost after a restart.")
