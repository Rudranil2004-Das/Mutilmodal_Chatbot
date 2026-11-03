import os
import time
from io import BytesIO

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

# Load variables from the .env file in the project folder.
load_dotenv()

# Change the model here, or set GEMINI_MODEL in .env, if your key uses another one.
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

# If the main model is overloaded (503), the app retries, then tries these models.
FALLBACK_MODELS = [
    name.strip()
    for name in os.getenv("GEMINI_FALLBACK_MODELS", "gemini-3.6-flash").split(",")
    if name.strip()
]
RETRY_DELAYS = (2, 5)  # seconds to wait before each retry

PLACEHOLDER_KEY = "PASTE_YOUR_GEMINI_API_KEY_HERE"

SYSTEM_INSTRUCTION = (
    "You are a helpful, clear, beginner-friendly assistant. "
    "Answer accurately. If an image is provided, describe only "
    "what can reasonably be observed and explain uncertainty."
)


def api_key_is_set():
    """Return True when a real-looking key is present (used by the UI badge)."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    return bool(api_key) and api_key != PLACEHOLDER_KEY


def get_api_key():
    """Read and validate the Gemini API key."""
    if not api_key_is_set():
        raise ValueError(
            "GEMINI_API_KEY was not found. Add your key to the .env file "
            "in the project folder, then restart the app."
        )
    return os.getenv("GEMINI_API_KEY").strip()


def create_gemini_client():
    """Create and return the Google Gen AI SDK client."""
    return genai.Client(api_key=get_api_key())


def build_conversation(prompt, chat_history):
    """Convert simple chat history into Gemini Content objects."""
    conversation = []

    for message in chat_history:
        role = "user" if message["role"] == "user" else "model"
        conversation.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=message["content"])],
            )
        )

    conversation.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)],
        )
    )
    return conversation


def generate_with_retry(client, contents, config):
    """Call Gemini; on temporary server errors (5xx) retry, then try fallback models."""
    models = [MODEL_NAME] + [name for name in FALLBACK_MODELS if name != MODEL_NAME]
    last_error = None

    for model in models:
        for attempt in range(len(RETRY_DELAYS) + 1):
            try:
                return client.models.generate_content(
                    model=model, contents=contents, config=config
                )
            except errors.ServerError as error:
                last_error = error
                if attempt < len(RETRY_DELAYS):
                    time.sleep(RETRY_DELAYS[attempt])

    raise last_error


def get_gemini_response(prompt, image=None, chat_history=None):
    """
    Send text, or text plus an image, to Gemini.

    chat_history is a list of dictionaries containing role and content.
    """
    if not prompt or not prompt.strip():
        raise ValueError("Please enter a message.")

    if chat_history is None:
        chat_history = []

    client = create_gemini_client()
    contents = build_conversation(prompt, chat_history)

    # Add the image to the latest user message when one is uploaded.
    if image is not None:
        image_buffer = BytesIO()
        image.convert("RGB").save(image_buffer, format="JPEG", quality=90)
        image_part = types.Part.from_bytes(
            data=image_buffer.getvalue(),
            mime_type="image/jpeg",
        )
        contents[-1].parts.append(image_part)

    response = generate_with_retry(
        client,
        contents,
        types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.7,
            max_output_tokens=2048,
        ),
    )

    if not response.text:
        return "Gemini did not return text. Please try a different prompt."

    return response.text


def test_text_chat():
    """Small command-line test for the text chatbot."""
    question = input("Ask Gemini: ")
    print("\nGemini:", get_gemini_response(question))


if __name__ == "__main__":
    test_text_chat()
