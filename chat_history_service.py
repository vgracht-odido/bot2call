from datetime import datetime
from typing import Generator
from google.cloud.firestore import (
    Client as FirestoreClient,
    CollectionReference,
    DocumentSnapshot,
)


class ChatHistoryNotFoundException(Exception):
    pass


class ChatHistoryService:

    def __init__(self):
        self.client = FirestoreClient()
        self.collection = self.client.collection("chat-history-collection")

    def get_chat_history_by_id(self, session_id: str) -> list[dict]:
        """
        Retrieves the chat history document from Firestore based on the session_id

        Args:
            session_id (str): ID of the session to retrieve the chat history

        Returns:
            list: List containing messages in the chat session

        Raises:
            ChatHistoryNotFoundException: if session ID not present in collection
        """
        reference = self.collection.document(session_id)
        snapshot = reference.get()
        if not snapshot.exists:
            raise ChatHistoryNotFoundException(
                "Chat history missing for session" f"{session_id}"
            )
        collection: CollectionReference = reference.collection("messages")
        stream: Generator[DocumentSnapshot] = collection.stream()
        chat_history = []
        for message_snapshot in stream:
            creation_time: datetime = message_snapshot.create_time
            chat_history.append({**message_snapshot.to_dict(), "create_time": creation_time})
        return chat_history


    # @staticmethod
    # def get_all_user_messages_from_history(history: list[dict[str, str]]) -> str:
    #     """
    #     Retrieves all messages from a history and concatenates them

    #     Args:
    #         history (list): Body that contains all messages from user and bot

    #     Returns:
    #         str: Concatenated body of the user messages in a history
    #     """
    #     history = sorted(history, key=lambda x: x.get("create_time", datetime.min))
    #     messages = []
    #     for message in history:
    #         user_message = message.get("user_msg", "")
    #         button_label_message = message.get("button_label", "")
    #         bot_response = message.get("bot_response", {}).get("message")
    #         if user_message:
    #             messages.append(user_message)
    #         elif button_label_message:
    #             messages.append(button_label_message)
    #     concatenated_messages = "\n".join(messages)
    #     return concatenated_messages

    