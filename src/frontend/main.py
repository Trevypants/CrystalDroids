import requests
import sys
import streamlit as st

# add total project layout to path
sys.path.append(".")

from src.schemas import Role, Message, Conversation
from src.frontend.config import settings


ROLE_CONV = {
    Role.USER: "user",
    Role.MODEL: "assistant",
}


def get_chat(user_id: str) -> Conversation:
    """Get the chat history for a user.

    Parameters
    ----------
    user_id : str
        The user ID.

    Returns
    -------
    Conversation
        The chat history.
    """
    if "http" not in settings.backend_host:
        url_base = f"http://{settings.backend_host}:{settings.backend_port}"
    else:
        url_base = settings.backend_host
    response = requests.get(url_base + f"/chat/{user_id}")
    response.raise_for_status()
    return Conversation(**response.json())


def send_message(user_id: str, message: Message) -> Message:
    """Send a message to the chat.

    Parameters
    ----------
    user_id : str
        The user ID.
    message : Message
        The message to send.

    Returns
    -------
    Message
        The response message.
    """
    if "http" not in settings.backend_host:
        url_base = f"http://{settings.backend_host}:{settings.backend_port}"
    else:
        url_base = settings.backend_host
    response = requests.post(
        url_base + f"/chat/{user_id}",
        json=message.model_dump(),
    )
    response.raise_for_status()
    return Message(**response.json())


if __name__ == "__main__":
    with st.sidebar:
        user_id_key = st.text_input(
            label="User ID",
            value="",
            key="user_id_key",
            type="password",
        )
        "[View the source code](https://github.com/Trevypants/CrystalDroids)"

    st.title("💬 Medical Chatbot")
    st.caption("🚀 A streamlit medical chatbot powered by Google Gemini")

    if not user_id_key:
        st.info("Please enter a User ID to continue.")
        st.stop()

    # Make HTTP request to backend to get conversation
    conversation = get_chat(user_id=user_id_key)

    # Display the conversation
    if len(conversation.history) > 0:
        for hist in conversation.history:
            st.chat_message(ROLE_CONV[hist.role]).write(hist.parts[0].text)
    else:
        st.chat_message(ROLE_CONV[Role.MODEL]).write(
            "Whenever ready, please start the conversation."
        )

    # Get user input
    if user_input := st.chat_input(placeholder="Your Message", key="user_input"):
        # Store the user input
        conversation.add_message(parts=[Message(text=user_input)], role=Role.USER)

        # Display the user input
        st.chat_message(ROLE_CONV[Role.USER]).write(user_input)

        # Send message to backend
        response = send_message(
            user_id=user_id_key,
            message=Message(text=user_input),
        )

        # Store the response
        conversation.add_message(parts=[response], role=Role.MODEL)

        # Display the response
        st.chat_message(ROLE_CONV[Role.MODEL]).write(response.text)
