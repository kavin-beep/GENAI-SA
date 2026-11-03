"""Connect chat and structured inputs to preflight, generation and reviewed output."""

from dataclasses import dataclass
import hashlib
import json
from uuid import uuid4
from core.formatter import DisplayPlan, format_result
from core.groq_client import GroqClient, SetupError
from core.prompts import PromptSpec
from core.safety import CoachProfile, HealthContext, prepare_chat_request, prepare_request
from core.schemas import GenerationParameters, GenerationResult


@dataclass(frozen=True)
class Draft:
    """Incomplete health answers never silently become 'No'."""
    entry: PromptSpec
    values: dict[str, str]
    language: str
    parameters: GenerationParameters
    health: HealthContext | None
    unanswered: bool

    def fingerprint(self) -> str:
        """Hide the previous result when relevant inputs change."""
        content = {"id": self.entry.id, "version": self.entry.version,
                   "values": self.values, "language": self.language,
                   "params": self.parameters.model_dump(), "unanswered": self.unanswered,
                   "health": self.health.model_dump() if self.health else None}
        return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()


@dataclass(frozen=True)
class Submission:
    """Only display-ready content is retained in session state."""
    result_id: str
    fingerprint: str
    prompt_id: str
    prompt_version: str
    view: DisplayPlan
    warnings: tuple[str, ...] = ()
    setup_message: str = ""


def submit(draft: Draft) -> Submission:
    """Explicit button action; local safety decisions bypass client creation."""
    setup_message = ""
    warnings: tuple[str, ...] = ()
    if draft.health is None:
        view = DisplayPlan(state="incomplete", heading="Answer every health question before continuing.", language="English")
    else:
        preflight = prepare_request(draft.entry, draft.values, draft.health,
                                    language=draft.language, parameters=draft.parameters)
        if draft.unanswered and preflight.may_generate:
            view = DisplayPlan(state="incomplete", heading="Answer every health question before continuing.", language="English")
        else:
            result = None
            if preflight.may_generate:
                try:
                    with GroqClient.from_streamlit() as client:
                        result = client.generate(preflight.request)
                    warnings = tuple(result.warnings)
                except SetupError as exc:
                    setup_message = str(exc)
                    result = GenerationResult(status="configuration_error", message="Complete API setup.")
                except Exception:
                    result = GenerationResult(status="service_error", message="The request could not be completed.")
            view = format_result(preflight, result)
    return Submission(uuid4().hex, draft.fingerprint(), draft.entry.id,
                      draft.entry.version, view, warnings, setup_message)


def submit_chat(
    conversation: list[tuple[str, str]], *, language: str,
    parameters: GenerationParameters,
    profile: CoachProfile | dict[str, object] | None = None,
    response_style: str = "Balanced",
) -> Submission:
    """Run a free-form chat turn through local screening, Groq and output review."""
    preflight = prepare_chat_request(
        conversation, language=language, parameters=parameters, profile=profile,
        response_style=response_style,
    )
    setup_message = ""
    warnings: tuple[str, ...] = ()
    result = None
    if preflight.may_generate:
        try:
            with GroqClient.from_streamlit() as client:
                # Requests with saved profile or memory bypass disk response caching.
                result = client.generate(preflight.request, use_cache=profile is None)
            warnings = tuple(result.warnings)
        except SetupError as exc:
            setup_message = str(exc)
            result = GenerationResult(status="configuration_error", message="Complete API setup.")
        except Exception:
            result = GenerationResult(status="service_error", message="The request could not be completed.")
    view = format_result(preflight, result)
    fingerprint = hashlib.sha256(json.dumps({
        "conversation": conversation, "language": language,
        "parameters": parameters.model_dump(), "response_style": response_style,
    }, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return Submission(uuid4().hex, fingerprint, "coach_chat", "v1", view, warnings, setup_message)
