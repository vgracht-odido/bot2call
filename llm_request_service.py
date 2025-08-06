import os
import logging
import requests
from typing import List, Dict, Any
from requests import Response
from google.cloud import error_reporting
from google.cloud.error_reporting import Client as ErrorReportingClient
from google.cloud.firestore import (
    Client as FirestoreClient,
    DocumentReference,
    DocumentSnapshot,
)
from utility_service import generate_token

FUNCTION_NAME = os.getenv("K_SERVICE", "")
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "")

# Instance level clients
cloud_error_client: ErrorReportingClient = None
if FUNCTION_NAME:
    cloud_error_client = error_reporting.Client()


class LLMRequestError(Exception):
    pass


class LLMClient:

    def __init__(self):
        pass

    @property
    def headers(self) -> dict:
        return {
            "Content-type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {generate_token(LLM_SERVICE_URL)}",
        }

    def request(self, data: dict, timeout: int = 5) -> Response:
        logging.info(self.headers)
        response = requests.post(
            LLM_SERVICE_URL, json=data, headers=self.headers, timeout=timeout
        )
        if not response.ok:
            raise LLMRequestError(
                f"Response {response.status_code}: " f"{response.json()}"
            )
        return response


class LLMPromptManagementService:

    def __init__(self):
        self.client = FirestoreClient()

    def get_prompt(self, prompt_id: str) -> str:
        """
        Retrieves the prompt from Firestore

        Args:
            prompt_id (str): document id to retrieve

        Returns:
            str: prompt to retrieve
        """
        prompts_collection = self.client.collection("llm-prompts")
        reference: DocumentReference = prompts_collection.document(
            "fulfillment-webhook"
        )
        snapshot: DocumentSnapshot = reference.get()
        if not snapshot.exists:
            return ""
        document: dict[str, str] = snapshot.to_dict()
        prompt: str = document.get(prompt_id)
        return prompt


class LLMRequestService:
    def __init__(self, session_id: str = ""):
        self.session_id = session_id
        self.prompt_service = LLMPromptManagementService()

    def get_location(self, user_message: str) -> str:
        prompt = self.prompt_service.get_prompt("get-location")
        data = {
            "custom": {
                "text": f"{user_message}",
                "prompt": prompt,
            }
        }
        return self.request(data)

    def summarize_conversation(
        self, conversation: str, replace_prompt: str = ""
    ) -> str:
        prompt = (
            replace_prompt
            if replace_prompt
            else self.prompt_service.get_prompt("summarize-chat-conversation")
        )
        data = {
            "custom": {
                "text": f"{conversation}",
                "prompt": prompt,
            }
        }
        return self.request(data, timeout=30)

    def summarize_conversations(
        self, conversations: Dict[str, str], replace_prompt: str = ""
    ) -> Dict[str, str]:
        prompt = (
            replace_prompt
            if replace_prompt
            else self.prompt_service.get_prompt("summarize-chat-conversation")
        )
        summaries = {}
        for session_id, conversation in conversations.items():
            data = {
                "custom": {
                    "text": f"{conversation}",
                    "prompt": prompt,
                }
            }
            summaries[session_id] = self.request(data, timeout=30)
        return summaries

    def tag_callback(
        self,
        summary: str,
        customer_comment: str = "",
        service: str = "",
        telesales: str = "",
        techniek: str = "",
        activatie: str = "",
        tag_prompt: str = "",
    ) -> str:
        data = {
            "custom": {
                "text": f"{summary}",
                "customer_comment": f"{customer_comment}",
                "service": f"{service}",
                "telesales": f"{telesales}",
                "techniek": f"{techniek}",
                "activatie": f"{activatie}",
                "prompt": tag_prompt,
            }
        }
        print(f"Data prepared: {data}\n")
        return self.request(data)

    def request(self, data: dict, timeout: int = 5) -> str:
        """
        Sends request to LLM Service endpoint

        Args:
            data (dict): data to be passed in request body

        Returns:
            str: text body of response
        """
        try:
            llm_client = LLMClient()
            response = llm_client.request(data, timeout=timeout)
            return response.text
        except Exception as e:
            logging.error(f"LLM request failed due to: {e}")
            if cloud_error_client:
                cloud_error_client.report_exception(user=self.session_id)
            return None
