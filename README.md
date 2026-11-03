# Gemini Vision Chat

A chatbot that answers text questions and questions about uploaded images, powered by Google Gemini. It is built with Python and the official Google Gen AI SDK, with a Streamlit web interface.

![Gemini Vision Chat interface](screenshots/chat_interface.png)

## Features

- Ask questions in plain text and get answers from Gemini
- Attach a PNG, JPG or WEBP image and ask about it
- Follow-up questions remember the earlier conversation
- Suggestion buttons on the first screen (they change when an image is attached)
- Sidebar with image preview, Clear conversation button, and API key and model status
- Automatic retry and a fallback model when Google's servers are busy (503)
- Plain-language error messages that say what to do next

## Tech stack

| Part | Tool |
|---|---|
| Language | Python 3.11+ |
| AI | Google Gemini via `google-genai` |
| Interface | Streamlit with custom CSS |
| Config | `python-dotenv` (`.env` file) |
| Images | Pillow |

## Project structure

```
gemini_multimodal_chatbot/
├── app.py                  # Streamlit frontend
├── gemini_bot.py           # Gemini functions (backend, functions only)
├── styles.css              # All visual styling
├── requirements.txt        # Dependencies
├── .env                    # Your private API key (not committed)
├── .env.example            # Template for .env
├── .gitignore
├── .streamlit/
│   └── config.toml         # Theme colours
└── screenshots/
    └── chat_interface.png
```

## Setup (Windows)

You need Python 3.11 or newer and a free Gemini API key from https://aistudio.google.com/app/apikey

```
pip install uv
uv venv
.venv\Scripts\activate
uv pip install -r requirements.txt
```

## Add your API key

Open `.env` and replace the placeholder. Do not use quotes, and never upload this file to GitHub.

```
GEMINI_API_KEY=your_actual_api_key
```

Optional settings you can add to `.env`:

```
GEMINI_MODEL=gemini-3.8-flash
GEMINI_FALLBACK_MODELS=gemini-3.6-flash
```

## Run

```
python gemini_bot.py     # quick text test in the terminal
streamlit run app.py     # full app at http://localhost:8501
```

## How it works

1. `app.py` collects the text and the optional image.
2. `gemini_bot.py` loads `GEMINI_API_KEY` from `.env` and creates the client.
3. `build_conversation()` converts earlier text messages into Gemini content.
4. `get_gemini_response()` sends the text, plus the image as JPEG bytes, to Gemini.
5. If the model returns a temporary server error, `generate_with_retry()` waits, retries, then tries the fallback model.
6. Streamlit shows the answer and keeps the history in session state.

Notes:
- History lives in the browser session only. It is not saved permanently.
- Only earlier text is resent as context. Earlier images are not.
- The attached image goes with every new message until you remove it in the sidebar.
- Large images are shrunk to fit within 2048 pixels before sending.

## Example questions

| Input | What to expect |
|---|---|
| Explain Python functions with a simple example | Text explanation |
| Upload a food photo, "What is in this picture?" | Description of what is visible |
| Upload a flowchart, "Explain the steps" | Step-by-step explanation |
| Upload a receipt, "Read the items and total" | Visible text from the receipt |
| A follow-up after any answer | Uses the earlier conversation |

## Troubleshooting

- **API key missing:** `.env` must be in the same folder as `gemini_bot.py`, with the variable spelled `GEMINI_API_KEY`.
- **ModuleNotFoundError:** activate `.venv`, then run `uv pip install -r requirements.txt`.
- **Invalid key or permission error:** create or verify the key in Google AI Studio.
- **503 UNAVAILABLE / high demand:** this is Google's side and usually temporary. The app retries and then tries the fallback model.
- **"Both GOOGLE_API_KEY and GEMINI_API_KEY are set":** only a warning. Remove the `GOOGLE_API_KEY` Windows environment variable to use just the key in `.env`.
- **Model unavailable:** set `GEMINI_MODEL` in `.env` to a model your key can use.
- **Unsupported image:** use PNG, JPG, JPEG or WEBP.

## Documentation

- Google Gen AI Python SDK: https://googleapis.github.io/python-genai/
- Gemini API: https://ai.google.dev/api/generate-content
- API keys: https://aistudio.google.com/app/apikey
