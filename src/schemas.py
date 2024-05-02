from enum import StrEnum
import datetime

from pydantic import BaseModel, ConfigDict, AwareDatetime


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

    model_config = ConfigDict(arbitrary_types_allowed=True)

    history: list[HistoryEntry]
    created: AwareDatetime = datetime.datetime.now(datetime.UTC)
    updated: AwareDatetime = datetime.datetime.now(datetime.UTC)
    summary: str | None = None
    summary_english: str | None = None

    def add_message(self, parts: list[Message], role: Role):
        """Add a message to the conversation.

        Parameters
        ----------
        parts : list[Message]
            The message parts.
        role : Role
            The role of the message.

        Returns
        -------
        Conversation
            The updated conversation.
        """
        if len(self.history) > 0:
            last_role = self.history[-1].role
            if last_role == role:
                raise ValueError(
                    f"Role {role} is the same as the last message role {last_role}, skipping..."
                )
        self.history.append(HistoryEntry(role=role, parts=parts))
        self.updated = datetime.datetime.now(datetime.UTC)
        return self

    def add_summary(self, summary: str, summary_english: str):
        """Add a summary to the conversation.

        Parameters
        ----------
        summary : str
            The summary in the conversation language.
        summary_english : str
            The summary in English.

        Returns
        -------
        Conversation
            The updated conversation.
        """
        self.summary = summary
        self.summary_english = summary_english
        self.updated = datetime.datetime.now(datetime.UTC)
        return self


def generate_empty_conv():
    return Conversation(
        history=[],
        created=datetime.datetime.now(datetime.UTC),
        updated=datetime.datetime.now(datetime.UTC),
        summary=None,
        summary_english=None,
    )
