"""Build display cards and Markdown exports only after safety screening.

No Streamlit dependency: Stage 5 can render these typed cards with plain-text
widgets. The same cards drive exports, preventing missing rationales on download.
"""

from __future__ import annotations

import html
import re
import unicodedata

from pydantic import ConfigDict, Field

import config
from core.safety import Preflight, screen_output
from core.schemas import ChatResponse, GenerationResult, StrictModel


class SuggestionCard(StrictModel):
    """Every displayed recommendation has an action and its rationale together."""

    model_config = ConfigDict(frozen=True)
    title: str = Field(min_length=1)
    action: str = Field(min_length=1)
    rationale: str = Field(min_length=1)


class DisplayPlan(StrictModel):
    """UI-ready data. The UI must keep disclaimer and review note visible."""

    model_config = ConfigDict(frozen=True)
    state: str
    heading: str
    language: str
    answer: str = ""
    cards: tuple[SuggestionCard, ...] = ()
    questions: tuple[str, ...] = ()
    markdown_download_requested: bool = False
    disclaimer: str = config.SAFETY_DISCLAIMER
    review_note: str = "Automated checks are limited and do not establish medical safety. Review suggestions with a qualified adult."
    origin: str = "application"


_ERROR_MESSAGES = {
    "configuration_error": "Model setup is incomplete.",
    "authentication_error": "API access could not be verified.",
    "rate_limited": "The service's request limit was reached.",
    "budget_exhausted": "The configured call budget was reached.",
    "blocked": "The service declined this request.",
    "validation_error": "A complete structured response was not available.",
    "model_unavailable": "The configured model is unavailable.",
    "invalid_request": "The service rejected the request settings.",
    "network_error": "The connection failed or timed out.",
    "service_error": "The service could not complete the request.",
}


def _plain(value: str) -> str:
    """Remove hidden controls while preserving readable Unicode, tabs and newlines."""
    return "".join(c for c in value if not unicodedata.category(c).startswith("C") or c in "\n\t")


def format_result(preflight: Preflight, result: GenerationResult | None = None) -> DisplayPlan:
    """The single UI/export boundary; cached and fresh results are screened alike.

    Never read result.attempts for display. Even failed results with partial data
    are ignored. Fixed local safety notices remain English in all language modes.
    """
    if preflight.local_response is not None:
        response = preflight.local_response
        state, origin = "local_notice", "application safety notice"
    elif not preflight.may_generate:
        return DisplayPlan(state="unavailable", heading="Required details are incomplete.", language="English")
    elif result is None:
        return DisplayPlan(state="ready", heading="Ready to request suggestions.", language=preflight.context.language)
    elif result.status != "ok" or result.data is None:
        return DisplayPlan(state="unavailable", heading=_ERROR_MESSAGES.get(result.status, "No validated response is available."), language="English")
    else:
        review = screen_output(result.data, preflight.context)
        response = review.response
        state = "screened" if review.accepted else "withheld"
        origin = "AI suggestion (cached)" if review.accepted and result.cache_hit else "AI suggestion" if review.accepted else "application safety notice"
    if isinstance(response, ChatResponse):
        heading = {
            "suggestions": "CoachBot",
            "needs_clarification": "One more detail",
            "professional_referral": "Professional guidance",
        }[response.status]
    else:
        heading = {
            "suggestions": "Suggestions for discussion",
            "needs_clarification": "More information needed",
            "professional_referral": "Professional guidance needed",
        }[response.status]
    note = "Automated checks are limited and do not establish medical safety. Review suggestions with a qualified adult."
    if response.language != "English":
        note += " Text-pattern screening is mainly English and may miss unsafe advice in this language."
    return DisplayPlan(
        state=state, heading=heading, language=response.language, origin=origin, review_note=note,
        markdown_download_requested=bool(
            preflight.context and preflight.context.markdown_download_requested
        ),
        answer=_plain(response.answer) if isinstance(response, ChatResponse) else "",
        cards=tuple(SuggestionCard(title=_plain(rec.title), action=_plain(rec.action), rationale=_plain(rec.rationale)) for rec in response.recommendations),
        questions=tuple(_plain(question) for question in response.follow_up_questions),
    )


def _markdown_text(value: str) -> str:
    """Escape markup and links rather than trusting generated Markdown or HTML."""
    escaped = html.escape(_plain(value), quote=False)
    escaped = re.sub(r"([\\`*_{}\[\]()#+.!|~\-])", r"\\\1", escaped)
    return escaped.replace("\n", " ").replace("\r", " ")


def to_markdown(plan: DisplayPlan) -> str:
    """Export the same reviewed cards, with rationale beneath every action."""
    lines = ["# CoachBot AI", "", f"**{_markdown_text(plan.heading)}**", "",
             _markdown_text(plan.disclaimer), "", _markdown_text(plan.review_note), "",
             f"Language: {_markdown_text(plan.language)} · Source: {_markdown_text(plan.origin)}", ""]
    if plan.answer:
        lines.extend([_markdown_text(plan.answer), ""])
    for index, card in enumerate(plan.cards, start=1):
        lines.extend([f"## {index}. {_markdown_text(card.title)}", "", _markdown_text(card.action), "",
                      f"**Rationale:** {_markdown_text(card.rationale)}", ""])
    if plan.questions:
        lines.extend(["## Clarifying questions", ""])
        lines.extend(f"- {_markdown_text(question)}" for question in plan.questions)
        lines.append("")
    return "\n".join(lines)
