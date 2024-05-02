"""Configuration module for the frontend."""

from .config import FrontendSettings  # noqa: F401

# Instantiate the Settings class
# Automatically places the ENV variables into the settings attributes
settings = FrontendSettings()  # type: ignore
