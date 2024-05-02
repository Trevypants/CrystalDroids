"""Minimal Litestar application."""

import os
import logging

from litestar import Litestar, get, post, delete, Request, Response, status_codes
from litestar.datastructures import State
from litestar.config.cors import CORSConfig

import google.auth

from src.config import settings, LogLevel
from src.schemas import Message, Conversation, Role

from .db import FirestoreDB
from .model import ChatBot

logging.basicConfig(
    level=LogLevel.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
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


def init_gcp_credentials():
    """This function initializes the Google Cloud Platform credentials.
    It will check if there is a *.json file in the keys directory and set the
    GOOGLE_APPLICATION_CREDENTIALS environment variable.

    If the file doesn't exist, it will use the default credentials.

    Returns
    -------
    google.auth.credentials.Credentials
        The Google Cloud Platform credentials.
    """
    # Check if there is a *.json file in the keys directory
    key_file = None
    for file in os.listdir("src/keys"):
        if file.endswith(".json"):
            key_file = file
            break

    # Load the credentials
    if key_file is None:
        logging.warning("No Google Cloud credentials found in the keys directory.")
    else:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f"src/keys/{key_file}"
    return google.auth.default()


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
    logging.info("Initializing Application...")

    # Initialize Google Cloud Credentials
    _, project_id = init_gcp_credentials()
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
        app.state.db = FirestoreDB(
            project_id=settings.project_id,
            database=settings.firestore_db,
            collection_name="conversations",
        )

    # Initialize Generative Model
    logging.info(f"Initializing model {settings.genai_id}...")
    if not getattr(app.state, "model", None):
        app.state.model = ChatBot(
            project_id=settings.project_id,
            location=settings.location,
            genai_id=settings.genai_id,
            genai_instructions=settings.genai_instructions,
            genai_config=settings.genai_config,
            genai_safety_config=settings.genai_safety_config,
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
async def root() -> dict[str, str]:
    """Route Handler that outputs hello world."""
    return {"hello": "world"}


@get("/chat/{user_id:str}")
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
    Conversation
        The chat history.
    """
    db: FirestoreDB = state.db
    return await db.fetch_conversation(user_id=user_id)


@post("/test/chat/{user_id:str}")
async def test_chat(state: State, user_id: str, data: Message) -> Message:
    """Route Handler that tests the chat with a user. Will respond with the same message.
    Will not store the conversation in the database.

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
    logging.debug(f"Request: {data}")

    # Generate response
    logging.debug(f"Echoing response for User ID {user_id}...")
    response = data

    logging.debug(f"Response: {response.text}")
    return Message(text=response.text)


@post("/chat/{user_id:str}")
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
    logging.debug(f"Request: {data}")

    doctor_fresh: ChatBot = state.model
    db: FirestoreDB = state.db

    # Add user message to history
    logging.debug(
        f"Updating conversation for User ID {user_id} with USER message in firestore..."
    )
    await db.add_message(user_id=user_id, message=data, role=Role.USER)

    # Generate response
    logging.debug(f"Generating GenAI response for User ID {user_id}...")
    response = await doctor_fresh.generate_response(
        conversation=await db.fetch_conversation(user_id=user_id)
    )

    # Add model message to history
    logging.debug(
        f"Updating conversation for User ID {user_id} with MODEL message in firestore..."
    )
    await db.add_message(user_id=user_id, message=response, role=Role.MODEL)

    if "DONE" in response.text or "DONE" in data.text:
        logging.debug(
            f"Conversation for User ID {user_id} is DONE! Generating Summary..."
        )
        await db.update_conversation(
            user_id=user_id,
            conversation_data=await doctor_fresh.add_summary(
                conversation=await db.fetch_conversation(user_id=user_id)
            ),
        )

    logging.debug(f"Response: {response.text}")
    return Message(text=response.text)


@delete("/chat/{user_id:str}")
async def delete_chat(state: State, user_id: str) -> None:
    """Route Handler that deletes the chat history for a user.

    Parameters
    ----------
    state : State
        The state of the application.
    user_id : str
        The user ID.

    Returns
    -------
    dict[str, Any]
        The response message.
    """
    db: FirestoreDB = state.db
    await db.delete_conversation(user_id=user_id)


@delete("/chat")
async def delete_all_chats(state: State) -> None:
    """Route Handler that deletes all chat histories.

    Parameters
    ----------
    state : State
        The state of the application.

    Returns
    -------
    dict[str, str]
        The response message.
    """
    db: FirestoreDB = state.db
    await db.clear_collection(batch_size=100)


# Initialize the Litestar app
app = Litestar(
    route_handlers=[
        root,
        get_chat_history,
        chat,
        delete_chat,
        delete_all_chats,
        test_chat,
    ],
    on_startup=[app_startup],
    on_shutdown=[app_shutdown],
    cors_config=CORSConfig(allow_origins=settings.cors_allow_origins),
    exception_handlers={
        status_codes.HTTP_500_INTERNAL_SERVER_ERROR: internal_server_error_handler,
    },
)
