"""Shared settings for CoachBot AI; never place credentials here."""

from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parent
APP_NAME: Final = "CoachBot AI"
# Strict JSON Schema is currently supported for this Groq model; verify account
# access with check_models.py before using a live request.
MODEL_NAME: str = "openai/gpt-oss-20b"
MODEL_SUPPORTS_SAMPLING_PARAMETERS: Final[bool] = True
GROQ_CHAT_COMPLETIONS_URL: Final[str] = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELS_URL: Final[str] = "https://api.groq.com/openai/v1/models"

DEFAULT_LANGUAGE: Final = "English"
LANGUAGE_OPTIONS: Final = (
    "English", "Hindi", "Tamil", "Telugu", "Bengali", "Marathi",
    "Kannada", "Malayalam", "Gujarati", "Punjabi", "Urdu", "Spanish",
    "French", "Arabic", "Portuguese", "German", "Chinese", "Japanese",
    "Korean", "Other language",
)
SCHEMA_KEY_LANGUAGE: Final = "English"
ENABLE_OTHER_LANGUAGE: Final = True
ENABLE_IMAGE_INPUT: Final = False

# Initial settings, not validated claims about coaching quality or safety.
DEFAULT_TEMPERATURE: Final = 0.5
DEFAULT_TOP_P: Final = 0.95
DEFAULT_MAX_TOKENS: Final = 2048  # Groq field: max_completion_tokens.
REQUEST_TIMEOUT_MS: Final = 30_000
MAX_REQUEST_ATTEMPTS: Final = 3
MAX_SCHEMA_REPAIR_ATTEMPTS: Final = 1

EVAL_TEMPERATURES: Final = (0.2, 0.5, 0.9)
EVAL_TOP_P_VALUES: Final = (0.8, 0.95)
EVAL_MAX_TOKENS_VALUES: Final = (256, 512, 1024)
EVAL_SLEEP_SECONDS: Final = 2.0
EVAL_DEFAULT_CALL_BUDGET: Final = 12
CACHE_DIR: Final = PROJECT_ROOT / ".cache" / "responses"
EVAL_RESULTS_DIR: Final = PROJECT_ROOT / "eval" / "results"
FEEDBACK_DIR: Final = PROJECT_ROOT / "data" / "feedback"

SAFETY_DISCLAIMER: Final = (
    "AI suggestions are not a substitute for a qualified coach or physician. "
    "For injury or recovery decisions, consult a qualified professional."
)
