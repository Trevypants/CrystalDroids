"""Minimal Litestar application."""

from typing import Any
import logging

from pydantic import BaseModel
from litestar import Litestar, get, post
from litestar.datastructures import State
from litestar.config.cors import CORSConfig

from google.cloud import firestore
from vertexai.preview.generative_models import GenerativeModel

from src.config import settings

logging.basicConfig(
    level=settings.log_level, format="%(asctime)s - %(levelname)s - %(message)s"
)


class UserMessage(BaseModel):
    """Basic POST request model."""

    user_id: str
    message: str


### STARTUP ###
async def app_startup(app: Litestar):
    """This function initializes the database and models.

    It is called before the app has started.

    Parameters
    ----------
    app : Litestar
        The Litestar app instance.

    Returns
    -------
    None
    """
    # Initialize Firestore
    logging.info(
        f"Initializing database connections to {settings.firestore_db} in project {settings.project_id}..."
    )
    if not getattr(app.state, "db", None):
        app.state.db = firestore.Client(
            project=settings.project_id,
            database=settings.firestore_db,
        )

    # Initialize Generative Model
    logging.info(f"Initializing model {settings.genai_id}...")
    app.state.model = GenerativeModel(
        model_name=settings.genai_id,
        system_instruction=settings.genai_instructions,
        generation_config=settings.genai_config,
        safety_settings=settings.genai_safety_config,
    )


### SHUTDOWN ###
async def app_shutdown():
    """This function closes things.

    It is called after the app has shutdown.

    Returns
    -------
    None
    """
    logging.info("Closing...")


@get("/")
async def root() -> dict[str, Any]:
    """Route Handler that outputs hello world."""
    return {"hello": "world"}


@post("/chat")
async def chat(state: State, data: UserMessage) -> dict[str, str]:
    """Route Handler that starts/continues a chat with a user.

    Parameters
    ----------
    state : State
        The state of the application.
    data : UserMessage
        The POST request data.

    Returns
    -------
    dict[str, str]
        The response. Will have the following format: {"response": str}
    """
    doctor_fresh: GenerativeModel = app.state.model
    db: firestore.Client = app.state.db

    conversations_ref = db.collection("conversations")
    doc_ref = conversations_ref.document(data.user_id)

    logging.info(f"Request: {data}")

    try:
        # Attempt to retrieve the existing conversation
        doc = doc_ref.get()
        if doc.exists:
            logging.info(f"Conversation Found for User ID {data.user_id}")
            conversation_data = doc.to_dict()
            conversation_data["history"].append(
                {"role": "user", "parts": [{"text": f"{data.message}"}]}
            )
        else:
            logging.info(f"Conversation Not Found for User ID {data.user_id}")
            conversation_data = {
                "history": [
                    {"role": "user", "parts": [{"text": f"START. {data.message}"}]}
                ],
                "created": firestore.SERVER_TIMESTAMP,
                "updated": firestore.SERVER_TIMESTAMP,
            }  # Start a fresh conversation
    except Exception as e:
        logging.error(f"Error loading conversation for User ID {data.user_id}: {e}")
        conversation_data = {
            "history": [
                {"role": "user", "parts": [{"text": f"START. {data.message}"}]}
            ],
            "created": firestore.SERVER_TIMESTAMP,
            "updated": firestore.SERVER_TIMESTAMP,
        }

    response = doctor_fresh.generate_content(
        conversation_data["history"],
        generation_config=settings.genai_config,
        safety_settings=settings.genai_safety_config,
    )
    conversation_data["history"].append(
        {"role": "model", "parts": [{"text": response.text}]}
    )

    # Update Firestore
    doc_ref.set(conversation_data)

    if "DONE" in response.text or "DONE" in data.message:
        # save the summary
        conversation_data["summary"] = response.text
        response_conversion = doctor_fresh.generate_content(
            [f"Translate the following text into English: {response.text}"],
            generation_config=settings.genai_config,
            safety_settings=settings.genai_safety_config,
        )
        conversation_data["summary_english"] = response_conversion.text
        doc_ref.set(conversation_data)
        logging.info("Summary saved.")

    logging.info(f"Response: {response.text}")
    return {"response": response.text}


app = Litestar(
    route_handlers=[
        root,
        chat,
    ],
    on_startup=[app_startup],
    on_shutdown=[app_shutdown],
    cors_config=CORSConfig(allow_origins=settings.cors_allow_origins),
)
