"""Validated contracts shared by the client, future prompt registry and UI.

These are data shapes, not student-authored prompts. All recommendation-bearing
outputs use Recommendation so an action cannot pass without a short rationale.
"""

from typing import Annotated, Literal
import unicodedata

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

import config

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=600)]


class StrictModel(BaseModel):
    """Reject unexpected fields and type coercion rather than silently fixing data."""

    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True, allow_inf_nan=False)


class Recommendation(StrictModel):
    """A suggestion and its concise, user-facing justification (not hidden reasoning)."""

    title: str = Field(min_length=1, max_length=120)
    action: str = Field(min_length=1, max_length=1000)
    rationale: ShortText = Field(description="Brief justification linked to the supplied context and constraints.")


class CoachingResponse(StrictModel):
    """One reusable output contract for training, tactics and other coaching features.

    Recommendation text follows the selected language. Keys and machine-readable
    status values stay English. Validation checks shape, not medical correctness.
    """

    status: Literal["suggestions", "needs_clarification", "professional_referral"]
    language: str = Field(min_length=2, max_length=60, description="Exact requested language label.")
    recommendations: list[Recommendation] = Field(min_length=1, max_length=12)
    follow_up_questions: list[ShortText] = Field(max_length=3)


class ChatResponse(StrictModel):
    """Natural chat answer with optional recommendations for exportable plans."""

    status: Literal["suggestions", "needs_clarification", "professional_referral"]
    language: str = Field(min_length=2, max_length=60)
    answer: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]
    recommendations: list[Recommendation] = Field(max_length=12)
    follow_up_questions: list[ShortText] = Field(max_length=3)


class GenerationParameters(StrictModel):
    """Bounds are app limits; the selected model may have tighter capabilities."""

    temperature: float = Field(default=config.DEFAULT_TEMPERATURE, ge=0, le=2)
    top_p: float = Field(default=config.DEFAULT_TOP_P, gt=0, le=1)
    max_tokens: int = Field(default=config.DEFAULT_MAX_TOKENS, ge=128, le=8192)


class ConversationMessage(StrictModel):
    """One validated user or assistant turn passed as native chat context."""

    role: Literal["user", "assistant"]
    content: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]


class GenerationRequest(StrictModel):
    """Rendered prompt plus explicit settings and optional role-separated chat history."""

    prompt_id: str = Field(min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_.-]+$")
    prompt_version: str = Field(min_length=1, max_length=30, pattern=r"^[a-zA-Z0-9_.-]+$")
    prompt: str = Field(min_length=1, max_length=20000)
    system_constraints: str = Field(default="", max_length=10000)
    language: str = Field(default=config.DEFAULT_LANGUAGE, min_length=2, max_length=60)
    parameters: GenerationParameters = Field(default_factory=GenerationParameters)
    response_mode: Literal["plan", "chat"] = "plan"
    plan_requested: bool = False
    conversation: list[ConversationMessage] = Field(default_factory=list, max_length=99)
    profile_context: str = Field(default="", max_length=3000)

    @field_validator("language")
    @classmethod
    def language_label_only(cls, value: str) -> str:
        """Accept native language names without treating the selector as a prompt box."""
        if value == "Other language" or not any(c.isalpha() for c in value) or not all(unicodedata.category(c)[0] in ("L", "M") or c in " -()" for c in value):
            raise ValueError("Enter a language name, such as English or Tamil.")
        return value


class AttemptRecord(StrictModel):
    """Private diagnostic data; raw_output must never be rendered as coaching advice."""

    phase: Literal["initial", "repair"]
    number: int
    latency_ms: int
    status: str
    raw_output: str = ""
    finish_reason: str = ""
    input_tokens: int | None = None
    output_tokens: int | None = None
    thinking_tokens: int | None = None
    schema_valid: bool = False


class GenerationResult(StrictModel):
    """Typed success or safe degraded state; failures never expose partial advice."""

    status: Literal[
        "ok", "validation_error", "blocked", "rate_limited", "authentication_error",
        "invalid_request", "model_unavailable", "network_error", "service_error",
        "budget_exhausted", "configuration_error",
    ]
    message: str
    data: CoachingResponse | ChatResponse | None = None
    attempts: list[AttemptRecord] = Field(default_factory=list)
    cache_hit: bool = False
    calls_made: int = 0
    warnings: list[str] = Field(default_factory=list)
