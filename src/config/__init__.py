import os
from dotenv import load_dotenv
from .config import BackendSettings

# Build the correct path to the .env file
dotenv_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    ".env",
)

# Load .env file variables
load_dotenv(dotenv_path=dotenv_path)

# Instantiate the Settings class
# Automatically places the ENV variables into the settings attributes
settings = BackendSettings()  # type: ignore
