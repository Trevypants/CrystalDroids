"""Configuration file for the application."""

from enum import StrEnum

from pydantic_settings import BaseSettings
from vertexai.preview.generative_models import (
    Part,
    GenerationConfig,
    HarmCategory,
    HarmBlockThreshold,
)


VERSION = "0.2.1"


class LogLevel(StrEnum):
    """Enum class for the log level."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class BackendSettings(BaseSettings):
    """
    Settings class for the backend application.
    Will contain all ENV variables.
    """

    # Base
    version: str = VERSION

    # GCP Project Settings
    project_id: str = "PROJECT-GOES-HERE"
    location: str = "LOCATION-GOES_HERE"
    # "gemini-1.5-pro-preview-0409" is rate limited to 5 requests per minute so we don't use
    genai_id: str = "gemini-1.0-pro-002"
    firestore_db: str = "FIRESTORE-DB-GOES-HERE"
    cloud_storage_bucket: str = "gs://BUCKET-URI-GOES-HERE"

    # GenAI Model Settings
    temperature: float = 0.7
    top_p: float = 1.0
    top_k: int = 32
    candidate_count: int = 1
    max_output_tokens: int = 8192

    # Logging
    log_level: LogLevel = LogLevel.INFO

    @property
    def genai_instructions(self) -> list[str]:
        """Get the GenAI model instructions."""
        return [
            "You're a medical healthcare professional AI agent named DoctorFresh.",
            "You're leading a text conversation with a teenager who is starting treatment for their condition",
            """Adapt your tone of voice to make the teenager feel comfortable with sharing details, 
            like they're talking to a friend.""",
            "Your first goal is to assess how much the teenager knows about their current situation.",
            """Your second goal is to gather the information about their personal life, physical and mental 
            symptoms in order to provide the teenager with a heathcare plan.""",
            "The information needs to detailed enough to know the level of severity, ask follow-up questions if needed.",
            """You initiate the conversation after the initial prompt of 'START' by asking in what language the 
            teenagers want to continue the conversation. Don't provide example languages.""",
            "Keep your responses short and ask one question at a time.",
            """You continue the conversation until enough details are gathered to provide a summary about the 
            teenager's symptoms and personal life.""",
            "When the answer contains 'DONE', you follow up with a professional summary of all gathered information in English.",
            Part.from_uri(self.pdf_file_uri, mime_type="application/pdf"),
        ]

    @property
    def genai_config(self) -> GenerationConfig:
        """Get the GenAI model configuration."""
        return GenerationConfig(
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            candidate_count=self.candidate_count,
            max_output_tokens=self.max_output_tokens,
        )

    @property
    def genai_safety_config(self) -> dict[HarmCategory, HarmBlockThreshold]:
        """Get the GenAI safety configuration."""
        return {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        }

    @property
    def cors_allow_origins(self) -> list[str]:
        """Get the CORS allowed origin configuation."""
        return ["*"]

    @property
    def pdf_file_uri(self) -> str:
        """Get the PDF file URI."""
        return f"{self.cloud_storage_bucket}/medical-form.pdf"
