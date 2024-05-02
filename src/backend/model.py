import vertexai
from vertexai.preview.generative_models import GenerativeModel
from vertexai.preview.generative_models import (
    GenerationConfig,
    HarmCategory,
    HarmBlockThreshold,
)

from src.schemas import Conversation, Message
from src.config import settings


class ChatBot:
    model: GenerativeModel

    def __init__(
        self,
        project_id: str = settings.project_id,
        location: str = settings.location,
        genai_id: str = settings.genai_id,
        genai_instructions: list[str] = settings.genai_instructions,
        genai_config: GenerationConfig = settings.genai_config,
        genai_safety_config: dict[
            HarmCategory, HarmBlockThreshold
        ] = settings.genai_safety_config,
    ):
        """Initializes the ChatBot.

        Parameters
        ----------
        project_id : str
            The Google Cloud Project ID.
        location : str
            The location of the project.
        genai_id : str
            The GenAI model ID.
        genai_instructions : list[str]
            The GenAI model instructions.
        genai_config : GenerationConfig
            The GenAI model generation configuration.
        genai_safety_config : dict
            The GenAI model safety configuration.
        """
        # Initialize Vertex AI
        vertexai.init(
            project=project_id,
            location=location,
        )

        self.model = GenerativeModel(
            model_name=genai_id,
            system_instruction=genai_instructions,
            generation_config=genai_config,
            safety_settings=genai_safety_config,
        )

    async def generate_response(self, conversation: Conversation) -> Message:
        """Generates a response to the conversation.

        Parameters
        ----------
        conversation : Conversation
            The conversation data.

        Returns
        -------
        Message
            The response message.
        """
        response = await self.model.generate_content_async(
            [hist.model_dump() for hist in conversation.history],
            generation_config=settings.genai_config,
            safety_settings=settings.genai_safety_config,
        )
        return Message(text=response.text)

    async def add_summary(self, conversation: Conversation) -> Conversation:
        """Adds a summary to the conversation.

        Parameters
        ----------
        conversation : Conversation
            The conversation data. Assumes the last message in the conversation history
            has the summary.

        Returns
        -------
        Conversation
            The conversation data with the summary added.
        """
        # Save the summaries
        response = await self.model.generate_content_async(
            [f"Translate the following text into English: {conversation.summary}"],
            generation_config=settings.genai_config,
            safety_settings=settings.genai_safety_config,
        )
        return conversation.add_summary(
            summary=conversation.history[-1].parts[0].text,
            summary_english=response.text,
        )
