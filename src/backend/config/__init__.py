"""Configuration module for the backend."""

from .config import BackendSettings  # noqa: F401

# Instantiate the Settings class
# Automatically places the ENV variables into the settings attributes
settings = BackendSettings()  # type: ignore
