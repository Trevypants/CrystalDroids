from enum import StrEnum

from pydantic import BaseModel, ConfigDict
from google.cloud import firestore


class Role(StrEnum):
    """Role enumeration."""

    USER = "user"
    MODEL = "model"


class Message(BaseModel):
    """Message model."""

    text: str


class HistoryEntry(BaseModel):
    """Firestore History Entry model."""

    role: Role
    parts: list[Message]


class Conversation(BaseModel):
    """Firestore Conversation Data model."""

    model_config = ConfigDict(allow_arbitrary_types=True)

    history: list[HistoryEntry]
    created: firestore.SERVER_TIMESTAMP
    updated: firestore.SERVER_TIMESTAMP
    summary: str | None = None
    summary_english: str | None = None
