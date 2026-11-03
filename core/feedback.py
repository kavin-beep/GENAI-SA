"""Minimal feedback events without user inputs or generated advice."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4
from pydantic import Field
import config
from core.schemas import StrictModel


class FeedbackEvent(StrictModel):
    """Append-only events; the latest event per result is the current vote."""
    event_id: str = Field(default_factory=lambda: uuid4().hex)
    result_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    prompt_id: str
    prompt_version: str
    vote: Literal["up", "down"]
    recorded_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def save_feedback(event: FeedbackEvent, session_id: str, *, directory: Path | None = None) -> bool:
    """Separate session files; False lets the UI offer download after write failure."""
    if len(session_id) != 32 or any(c not in "0123456789abcdef" for c in session_id):
        raise ValueError("Use a generated session ID.")
    destination = (directory if directory is not None else config.FEEDBACK_DIR) / session_id
    try:
        destination.mkdir(parents=True, exist_ok=True)
        with (destination / "feedback.jsonl").open("a", encoding="utf-8") as file:
            file.write(event.model_dump_json() + "\n")
        return True
    except OSError:
        return False
