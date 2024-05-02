import logging
import datetime

from google.cloud import firestore

from src.config import settings
from src.schemas import Role, Message, Conversation, generate_empty_conv


class FirestoreDB:
    """Class for Firestore Database interaction."""

    client: firestore.AsyncClient
    collection: firestore.AsyncCollectionReference

    def __init__(
        self,
        project_id: str = settings.project_id,
        database: str = settings.firestore_db,
        collection_name: str = "conversations",
    ):
        """Initializes Firestore Database connection and
        references the specified collection.

        Parameters
        ----------
        project_id : str
            The Google Cloud Project ID.
        database : str
            The Firestore Database name.
        collection_name : str
            The Firestore Collection name.

        """
        # Initialize Firestore
        self.client = firestore.AsyncClient(
            project=project_id,
            database=database,
        )
        self.collection = self.client.collection(collection_name)

    async def fetch_conversation(self, user_id: str):
        """Fetches the conversation for the specified user.
        If the conversation doesn't exist, will return an empty conversation.

        Parameters
        ----------
        user_id : str
            The user ID.

        Returns
        -------
        Conversation
            The conversation data
        """
        doc_ref = self.collection.document(user_id)
        doc = await doc_ref.get()
        try:
            if doc.exists:
                logging.debug(f"Conversation Found for User ID {user_id}")
                return Conversation(**doc.to_dict())
            else:
                logging.debug(f"Conversation Not Found for User ID {user_id}")
        except Exception as e:
            logging.error(f"Error fetching conversation for User ID {user_id}: {e}")

        return generate_empty_conv()

    async def add_message(self, user_id: str, message: Message, role: Role):
        """Adds a message to the conversation.

        Parameters
        ----------
        user_id : str
            The user ID.
        message : Message
            The message data.
        role : Role
            The role of the message.
        """
        doc_ref = self.collection.document(user_id)
        conversation_data = await self.fetch_conversation(user_id)

        # Role checks
        if len(conversation_data.history) > 0:
            last_role = conversation_data.history[-1].role
            if last_role == role:
                logging.error(
                    f"Role {role} is the same as the last message role {last_role}, skipping..."
                )
                return

        # Add message to history
        conversation_data.add_message(
            parts=[message],
            role=role,
        )
        await doc_ref.set(conversation_data.model_dump())

    async def update_conversation(self, user_id: str, conversation_data: Conversation):
        """Updates the conversation data.

        Parameters
        ----------
        user_id : str
            The user ID.
        conversation_data : Conversation
            The conversation data.
        """
        conversation_data.updated = datetime.datetime.now(datetime.UTC)
        doc_ref = self.collection.document(user_id)
        await doc_ref.set(conversation_data.model_dump())

    async def delete_conversation(self, user_id: str):
        """Deletes the conversation data.

        Parameters
        ----------
        user_id : str
            The user ID.
        """
        doc_ref = self.collection.document(user_id)
        await doc_ref.delete()

    async def clear_collection(self, batch_size: int = 100):
        """Clears the collection.

        Parameters
        ----------
        batch_size : int
            The batch size for deletion.
        """
        deleted = 0
        if batch_size == 0:
            return

        docs = self.collection.limit(count=batch_size).stream()
        async for doc in docs:
            logging.debug(
                f"Deleting document {doc.id} => {Conversation(**doc.to_dict())}"
            )
            await doc.reference.delete()
            deleted += 1

        if deleted >= batch_size:
            return await self.clear_collection(batch_size=batch_size)
