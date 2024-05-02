"""Configuration file for the application."""

from enum import StrEnum

from pydantic_settings import BaseSettings


VERSION = "0.3.1"


class LogLevel(StrEnum):
    """Enum class for the log level."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class AppSettings(BaseSettings):
    """
    Settings class for the application.
    Will contain all ENV variables.
    """

    # Base
    version: str = VERSION

    # API Settings
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    # UI Settings
    frontend_host: str = "0.0.0.0"
    frontend_port: int = 3000
