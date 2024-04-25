"""Minimal Litestar application."""

from typing import Any
import logging

from pydantic import BaseModel
from litestar import Litestar, get, post
from litestar.datastructures import State
from litestar.config.cors import CORSConfig

from google.cloud import firestore, aiplatform
import vertexai.preview as vertex_ai
from vertexai.preview.generative_models import (
    GenerationConfig,
    GenerativeModel,
    HarmBlockThreshold,
    HarmCategory,
    Part,
)

logging.basicConfig(level=logging.INFO)

PROJECT_ID = "qwiklabs-gcp-01-497878f334ed"
LOCATION = "europe-west4"
# MODEL_ID = "gemini-1.5-pro-preview-0409"
MODEL_ID = "gemini-1.0-pro-002"


class Message(BaseModel):
    user_id: str
    message: str


pdf_file = Part.from_uri(
    "gs://rituals-solve-with-g/info.pdf", mime_type="application/pdf"
)

cors_config = CORSConfig(
    allow_origins=["https://crystaldroids-ui-k7ji6xt3vq-ez.a.run.app"]
)

# Set model parameters
generation_config = GenerationConfig(
    temperature=0.7,
    top_p=1.0,
    top_k=32,
    candidate_count=1,
    max_output_tokens=8192,
)

# Set safety settings
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
}


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
    logging.info("Initializing database connections...")
    if not getattr(app.state, "db", None):
        app.state.db = firestore.Client(project=PROJECT_ID, database="maxima-conv")

    # Initialize model
    logging.info("Initializing model...")
    # vertex_ai.init(project=PROJECT_ID, location=LOCATION)

    # Load a model with system instructions
    app.state.model = GenerativeModel(
        MODEL_ID,
        system_instruction=[
            "You're a medical healthcare professional AI agent named DoctorFresh.",
            "You're leading a text conversation with a teenager who is starting treatment for their condition",
            "Adapt your tone of voice to make the teenager feel comfortable with sharing details, like they're talking to a friend.",
            "Your first goal is to assess how much the teenager knows about their current situation.",
            "Your second goal is to gather the information about their personal life, physical and mental symptomes in order to provide the teenager with a heathcare plan.",
            "The information needs to detailed enough to know the level of severity, ask follow-up questions if needed.",
            "You initiate the conversation after the initial prompt of 'START' by asking in what language the teenagers want to continue the conversation. Don't provide example languages.",
            "Keep your responses short and ask one question at a time.",
            "You continue the conversation until enough details are gathered to provide a summary about the teenager's symptomes and personal life",
            "When the answer contains 'DONE', you follow up with a professional summary of all gathered information in English.",
        ],
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


@get("/sync", sync_to_thread=False)
def sync_root() -> dict[str, Any]:
    """Route Handler that outputs hello world."""
    return {"hello": "world"}


@post("/chat")
async def chat(state: State, user_id: str, message: str) -> dict[str, str]:
    """Route Handler that starts/continues a chat with a user.

    Parameters
    ----------
    state : State
        The state of the application.
    user_id : str
        The user ID.
    message : str
        The message from the user.

    Returns
    -------
    dict[str, str]
        The response.
    """
    doctor_fresh: GenerativeModel = app.state.model
    db: firestore.Client = app.state.db

    conversations_ref = db.collection("conversations")
    doc_ref = conversations_ref.document(user_id)

    try:
        # Attempt to retrieve the existing conversation
        doc = doc_ref.get()
        if doc.exists:
            print("Conversation Found")
            conversation_data = doc.to_dict()
            conversation_data["history"].append(
                {"role": "user", "parts": [{"text": f"{message}"}]}
            )
        else:
            print("Conversation Not Found")
            conversation_data = {
                "history": [{"role": "user", "parts": [{"text": f"START. {message}"}]}],
                "created": firestore.SERVER_TIMESTAMP,
                "updated": firestore.SERVER_TIMESTAMP,
            }  # Start a fresh conversation
    except Exception as e:
        print(f"Error loading conversation: {e}")
        conversation_data = {
            "history": [{"role": "user", "parts": [{"text": f"START. {message}"}]}],
            "created": firestore.SERVER_TIMESTAMP,
            "updated": firestore.SERVER_TIMESTAMP,
        }

    response = doctor_fresh.generate_content(
        conversation_data["history"],
        generation_config=generation_config,
        safety_settings=safety_settings,
    )
    conversation_data["history"].append(
        {"role": "model", "parts": [{"text": response.text}]}
    )

    # Update Firestore
    doc_ref.set(conversation_data)

    if "DONE" in response.text or "DONE" in message:
        # save the summary
        conversation_data["summary"] = response.text
        response_conversion = doctor_fresh.generate_content(
            [f"Translate the following text into English: {response.text}"],
            generation_config=generation_config,
            safety_settings=safety_settings,
        )
        conversation_data["summary_english"] = response_conversion.text
        doc_ref.set(conversation_data)
        print("Summary is saved")

    # resp = doctor_fresh.generate_content(
    #     ["Tell me a joke."],
    #     generation_config=generation_config,
    #     safety_settings=safety_settings,
    # )
    return {"response": response.text}


app = Litestar(
    route_handlers=[
        root,
        sync_root,
        chat,
    ],
    on_startup=[app_startup],
    on_shutdown=[app_shutdown],
    cors_config=cors_config,
)
