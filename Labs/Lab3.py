import streamlit as st
from openai import OpenAI
import time

MODEL_NAME = "gpt-4o-mini"
MAX_TOKENS = 800  # token budget for the input buffer (rough estimate)

st.title("Lab 3 – Streaming Chatbot w/ Conversation Buffer")

def rough_tokens(text: str) -> int:
    # Rough estimate: ~1 token per ~4 characters
    return max(1, len(text) // 4)

def rough_tokens_messages(messages: list[dict]) -> int:
    total = 0
    for m in messages:
        total += rough_tokens(m.get("role", ""))
        total += rough_tokens(m.get("content", ""))
    return total

def build_token_buffer(all_messages: list[dict], max_tokens: int) -> list[dict]:
    """
    Slides say to keep track of previous messages and pass them as part of the prompt.
    This version keeps the system prompt + as many recent messages as fit under max_tokens.
    (Important: never drop the system prompt.) :contentReference[oaicite:3]{index=3} :contentReference[oaicite:4]{index=4}
    """
    if not all_messages:
        return []

    system_msg = all_messages[0]  # keep system prompt
    kept = [system_msg]
    used = rough_tokens_messages(kept)

    # Add messages from the end (most recent first) until we hit budget
    for msg in reversed(all_messages[1:]):
        msg_tokens = rough_tokens_messages([msg])
        if used + msg_tokens > max_tokens:
            break
        kept.insert(1, msg)  # insert after system
        used += msg_tokens

    return kept

if "client" not in st.session_state:
    st.session_state.client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Slides: "if messages is not initialized: messages = []" :contentReference[oaicite:5]{index=5}
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful chatbot. Explain things so a 10-year-old can understand. "
                "Be clear, simple, and friendly."
            ),
        }
    ]

# Lab Part C: we need a yes/no loop after asking “Do you want more info?” :contentReference[oaicite:6]{index=6}
if "waiting_for_more_info" not in st.session_state:
    st.session_state.waiting_for_more_info = False

# Slides: display each message in a chat message container :contentReference[oaicite:7]{index=7}
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

prompt = st.chat_input("Say something...")

if prompt:
    user_text = prompt.strip()
    user_lower = user_text.lower()

    if st.session_state.waiting_for_more_info:
        if user_lower in ["yes", "y"]:
            # Convert to a clear instruction for the model
            st.session_state.messages.append(
                {"role": "user", "content": "Yes, please give me more info."}
            )
        elif user_lower in ["no", "n"]:
            st.session_state.waiting_for_more_info = False
            msg = "Okay! What can I help you with?"
            with st.chat_message("assistant"):
                st.write(msg)
            st.session_state.messages.append({"role": "assistant", "content": msg})
            st.stop()
        else:
            msg = "Please type Yes or No. Do you want more info?"
            with st.chat_message("assistant"):
                st.write(msg)
            st.stop()
    else:
        # Slides: add user prompt to messages :contentReference[oaicite:8]{index=8}
        st.session_state.messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.write(user_text)

    messages_for_model = build_token_buffer(st.session_state.messages, MAX_TOKENS)

    # Requirement: calculate token total per request :contentReference[oaicite:9]{index=9}
    tokens_sent = rough_tokens_messages(messages_for_model)
    st.sidebar.write(f"Estimated tokens sent: {tokens_sent} / {MAX_TOKENS}")

    completion = st.session_state.client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages_for_model,
        temperature=0,
    )
    reply = completion.choices[0].message.content

    # Part C: always ask “Do you want more info?” after answering :contentReference[oaicite:10]{index=10}
    reply = reply + "\n\nDo you want more info?"

    def stream_text(text: str):
        for ch in text:
            yield ch
            time.sleep(0.01)

    with st.chat_message("assistant"):
        st.write_stream(stream_text(reply))

    # Slides: store assistant response in messages :contentReference[oaicite:11]{index=11}
    st.session_state.messages.append({"role": "assistant", "content": reply})

    # Now we are waiting for yes/no
    st.session_state.waiting_for_more_info = True


