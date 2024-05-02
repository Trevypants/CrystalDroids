"""Minimal Litestar application."""

from typing import Any
import logging

from litestar import Litestar, get, post, Request, Response, status_codes
from litestar.datastructures import State
from litestar.config.cors import CORSConfig

import google.auth
from google.cloud import firestore
import vertexai
from vertexai.preview.generative_models import GenerativeModel

from src.config import settings
from src.schemas import Role, Message, HistoryEntry, Conversation

logging.basicConfig(
    level=settings.log_level, format="%(asctime)s - %(levelname)s - %(message)s"
)


def internal_server_error_handler(request: Request, exc: Exception) -> Response:
    """This function will handle all internal server errors

    Parameters
    ----------
    request: Request
        The request object
    exc: Exception
        The exception that was raised

    Returns
    -------
    Response
        The response object
    """
    logging.error(
        {
            "path": request.url.path,
            "method": request.method,
            "query_params": request.query_params,
            "reason": str(exc),
        }
    )
    return Response(
        status_code=status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal Server Error"},
    )


def generate_empty_conv():
    return Conversation(
        history=[
            HistoryEntry(role=Role.USER, parts=[Message(text="Hello")]),
        ],
        created=firestore.SERVER_TIMESTAMP,
        updated=firestore.SERVER_TIMESTAMP,
        summary=None,
        summary_english=None,
    )


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
    # Initialize Google Cloud Credentials
    logging.info("Initializing Application...")

    _, project_id = google.auth.default()
    assert (
        project_id == settings.project_id
    ), f"Project ID mismatch: {project_id} != {settings.project_id}"
    logging.info(
        f"Using project `{project_id}`, location `{settings.location}`, and service account `{settings.service_account_email}`"
    )

    # Initialize Firestore
    logging.info(
        f"Initializing database connections to {settings.firestore_db} in project {settings.project_id}..."
    )
    if not getattr(app.state, "db", None):
        app.state.db = firestore.Client(
            project=settings.project_id,
            database=settings.firestore_db,
        )

    # Initialize Vertex AI
    logging.info("Initializing Vertex AI...")
    vertexai.init(
        project=settings.project_id,
        location=settings.location,
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


@get("/chat/{user_id}")
async def get_chat_history(state: State, user_id: str) -> Conversation:
    """Route Handler that retrieves the chat history for a user.

    Parameters
    ----------
    state : State
        The state of the application.
    user_id : str
        The user ID.

    Returns
    -------
    list[Conversation]
        The chat history.
    """
    db: firestore.Client = state.db

    conversations_ref = db.collection("conversations")
    doc_ref = conversations_ref.document(user_id)

    try:
        doc = doc_ref.get()
        if doc.exists:
            conversation_data: Conversation = Conversation(**doc.to_dict())
            return conversation_data
    except Exception as e:
        logging.error(f"Error loading conversation for User ID {user_id}: {e}")

    return generate_empty_conv()


@post("/chat/{user_id}")
async def chat(state: State, user_id: str, data: Message) -> Message:
    """Route Handler that starts/continues a chat with a user.

    Parameters
    ----------
    state : State
        The state of the application.
    user_id : str
        The user ID.
    data : Message
        The POST request data.

    Returns
    -------
    Message
        The response message.
    """
    doctor_fresh: GenerativeModel = state.model
    db: firestore.Client = state.db

    conversations_ref = db.collection("conversations")
    doc_ref = conversations_ref.document(user_id)

    logging.debug(f"Request: {data}")

    # Empty Conversation Data
    conversation_data = generate_empty_conv()

    try:
        # Attempt to retrieve the existing conversation
        doc = doc_ref.get()
        if doc.exists:
            logging.debug(f"Conversation Found for User ID {user_id}")
            conversation_data: Conversation = Conversation(**doc.to_dict())
            conversation_data.history.append(
                HistoryEntry(
                    role=Role.USER,
                    parts=[Message(text=f"{data.text}")],
                )
            )
        else:
            logging.debug(f"Conversation Not Found for User ID {user_id}")
    except Exception as e:
        logging.error(f"Error loading conversation for User ID {user_id}: {e}")

    logging.debug(f"Generating response for User ID {user_id}...")
    response = doctor_fresh.generate_content(
        conversation_data["history"],
        generation_config=settings.genai_config,
        safety_settings=settings.genai_safety_config,
    )
    conversation_data.history.append(
        HistoryEntry(role=Role.MODEL, parts=[Message(text=response.text)])
    )

    # Update Firestore
    logging.debug(f"Updating conversation for User ID {user_id}...")
    doc_ref.set(conversation_data.model_dump())

    if "DONE" in response.text or "DONE" in data.text:
        # Save the summaries
        conversation_data.summary = response.text
        response_conversion = doctor_fresh.generate_content(
            [f"Translate the following text into English: {response.text}"],
            generation_config=settings.genai_config,
            safety_settings=settings.genai_safety_config,
        )
        conversation_data.summary_english = response_conversion.text
        doc_ref.set(conversation_data.model_dump())
        logging.debug(f"Conversation for User ID {user_id} is DONE!")

    logging.debug(f"Response: {response.text}")
    return Message(text=response.text)


app = Litestar(
    route_handlers=[
        root,
        chat,
    ],
    on_startup=[app_startup],
    on_shutdown=[app_shutdown],
    cors_config=CORSConfig(allow_origins=settings.cors_allow_origins),
    exception_handlers={
        status_codes.HTTP_500_INTERNAL_SERVER_ERROR: internal_server_error_handler,
    },
)
