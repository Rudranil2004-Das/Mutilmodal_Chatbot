from pathlib import Path

import streamlit as st
from PIL import Image

from gemini_bot import MODEL_NAME, api_key_is_set, get_gemini_response

st.set_page_config(
    page_title="Gemini Vision Chat",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

TEXT_SUGGESTIONS = [
    "Explain Python functions with a simple example",
    "What is machine learning?",
    "Give me 3 beginner project ideas",
]
IMAGE_SUGGESTIONS = [
    "Describe this image in detail",
    "Read any text you can see",
    "Explain what is happening step by step",
]


def load_styles():
    """Inject the custom stylesheet that gives the app its look."""
    css = Path(__file__).with_name("styles.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def queue_prompt(text):
    """Button callback: remember which suggestion was clicked."""
    st.session_state.queued = text


def load_image(uploaded_file):
    """Open the uploaded file as an RGB image (shrunk if it is huge)."""
    if uploaded_file is None:
        return None
    try:
        image = Image.open(uploaded_file).convert("RGB")
        image.thumbnail((2048, 2048))
        return image
    except Exception:
        st.sidebar.error("That file could not be read as an image. Try a PNG, JPG or WEBP.")
        return None


def render_sidebar():
    """Draw the sidebar and return the attached image (or None)."""
    with st.sidebar:
        st.markdown(
            """
            <div class="brand">
              <div class="mark">✦</div>
              <div><div class="name">Gemini Vision Chat</div>
              <div class="tag">Text and image questions</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<p class="side-title">Attach an image</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="side-hint">It is sent with every message until you remove it.</p>',
            unsafe_allow_html=True,
        )
        uploaded_file = st.file_uploader(
            "Attach an image",
            type=["png", "jpg", "jpeg", "webp"],
            label_visibility="collapsed",
        )
        image = load_image(uploaded_file)
        if image is not None:
            st.image(image, caption="Attached to your next message", width=270)

        st.markdown("<hr>", unsafe_allow_html=True)

        if st.button("Clear conversation", disabled=not st.session_state.messages):
            st.session_state.messages = []
            st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)

        key_ok = api_key_is_set()
        key_text = "API key loaded" if key_ok else "API key missing. Add it to .env"
        st.markdown(
            f"""
            <div class="status-row"><span class="dot {'ok' if key_ok else 'bad'}"></span>{key_text}</div>
            <div class="status-row"><span class="dot ok"></span>Model <code>{MODEL_NAME}</code></div>
            <div class="status-row"><span class="dot ok"></span>Text + image</div>
            """,
            unsafe_allow_html=True,
        )
    return image


def render_hero(image):
    """Empty state: headline plus suggestions that match the current input."""
    st.markdown(
        """
        <div class="hero">
          <h1>Ask in words.<br><span>Or show a picture.</span></h1>
          <p>Type a question, or attach an image in the sidebar and ask what is in it.
          Follow-up questions remember the conversation.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    label = "Ask about your image" if image is not None else "Try asking"
    st.markdown(f'<p class="suggest-label">{label}</p>', unsafe_allow_html=True)

    suggestions = IMAGE_SUGGESTIONS if image is not None else TEXT_SUGGESTIONS
    for text in suggestions:
        st.button(text, key=f"chip_{text}", on_click=queue_prompt, args=(text,))


def render_topbar():
    st.markdown(
        '<div class="topbar"><div class="mark">✦</div>'
        '<div class="title">Gemini Vision Chat</div></div>',
        unsafe_allow_html=True,
    )


def render_history():
    for message in st.session_state.messages:
        avatar = ":material/person:" if message["role"] == "user" else ":material/auto_awesome:"
        with st.chat_message(message["role"], avatar=avatar):
            if message.get("image") is not None:
                st.image(message["image"], width=300)
            st.markdown(message["content"])


def friendly_error(error):
    """Turn raw exceptions into a message that says what to do next."""
    text = str(error)
    lowered = text.lower()
    if "GEMINI_API_KEY" in text:
        return text
    if "api key" in lowered or "permission" in lowered or "401" in text or "403" in text:
        return "Gemini rejected the API key. Create or verify a key in Google AI Studio and update .env."
    if "404" in text or "not found" in lowered:
        return (
            f"The model `{MODEL_NAME}` is not available for your key. "
            "Set GEMINI_MODEL in .env to a model your key can use."
        )
    if "503" in text or "unavailable" in lowered or "high demand" in lowered:
        return "Google's servers are busy right now. Wait a few seconds and send your message again."
    if "429" in text or "quota" in lowered:
        return "You hit the usage limit. Wait a minute, then send your message again."
    return f"Something went wrong: {text}"


# ---------------------------------------------------------------- main
load_styles()

if "messages" not in st.session_state:
    st.session_state.messages = []

image = render_sidebar()

# A clicked suggestion arrives here as a queued prompt.
queued = st.session_state.pop("queued", None)
prompt = st.chat_input("Type a message, or ask about the attached image") or queued

if st.session_state.messages or prompt:
    render_topbar()
    render_history()
else:
    render_hero(image)

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt, "image": image})

    with st.chat_message("user", avatar=":material/person:"):
        if image is not None:
            st.image(image, width=300)
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=":material/auto_awesome:"):
        with st.spinner("Gemini is thinking..."):
            try:
                history = [
                    {"role": item["role"], "content": item["content"]}
                    for item in st.session_state.messages[:-1]
                ]
                answer = get_gemini_response(prompt, image, history)
                st.markdown(answer)
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer, "image": None}
                )
            except Exception as error:
                st.error(friendly_error(error))
                # Drop the unanswered message so a retry does not duplicate it.
                st.session_state.messages.pop()
