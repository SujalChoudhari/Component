# src/components/gemini_api_access.py
import os
from dotenv import load_dotenv
import requests
from src.base_component import BaseComponent
from typing import Dict, Any

# Ensure .env is loaded (though main.py handles this for the overall app)
# load_dotenv() # Generally not needed in component files if main script loads it

class GeminiAPIAccess(BaseComponent):
    """
    Allows interaction with the Gemini API for text generation and other tasks.
    """
    def __init__(self, name: str):
        super().__init__(name)
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent" # Changed to flash model for consistency with AI agent


    def onload(self):

        print(f"GeminiAPIAccess '{self.name}' is now active!")


    def use(self, prompt: str) -> str:
        """
        Sends a prompt to the Gemini API and returns the response.

        Args:
            prompt: The prompt to send to the Gemini API.

        Returns:
            The Gemini API's response as a string. Returns an error message if the API call fails.
        """
        if not self.api_key:
            return "Error: Gemini API key not found. Please set GEMINI_API_KEY environment variable."

        headers = {
            "Content-Type": "application/json",
        }
        data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
        }
        url = f"{self.api_url}?key={self.api_key}"

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            response_json = response.json()

            # --- CRITICAL FIX START ---
            if (response_json.get("candidates") and
                response_json["candidates"][0].get("content") and
                response_json["candidates"][0]["content"].get("parts") and
                response_json["candidates"][0]["content"]["parts"][0].get("text")):
                return response_json["candidates"][0]["content"]["parts"][0]["text"]
            elif response_json.get("promptFeedback") and response_json["promptFeedback"].get("blockReason"):
                return f"Response blocked by safety filters. Reason: {response_json['promptFeedback']['blockReason']}"
            else:
                return f"No readable text response from Gemini API. Full response: {response_json}"
            # --- CRITICAL FIX END ---

        except requests.exceptions.RequestException as e:
            return f"Error communicating with Gemini API: {e}"
        except KeyError as e:
            return f"Unexpected response format from Gemini API (KeyError: {e}). Response: {response_json}"
        except Exception as e:
            return f"An unexpected error occurred: {e}"


    def destroy(self):

        print(f"GeminiAPIAccess '{self.name}' is shutting down.")