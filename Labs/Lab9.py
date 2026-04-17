import streamlit as st
import json
import os
from openai import OpenAI

# -----------------------------
# Page Setup
# -----------------------------
st.set_page_config(page_title="Chatbot with Long-Term Memory", page_icon="🧠")
st.title("Chatbot with Long-Term Memory")

# -----------------------------
# API Client
# -----------------------------
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

MEMORY_FILE = "memories.json"

# -----------------------------
# Memory Functions
# -----------------------------
def load_memories():
    """Load memories from a JSON file. Return empty list if file does not exist."""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            return []
    return []

def save_memories(memories):
    """Save memories to a JSON file."""
    with open(MEMORY_FILE, "w") as file:
        json.dump(memories, file, indent=4)

def extract_new_memories(user_message, assistant_response, current_memories):
    """
    Use a smaller/cheaper model to identify new facts worth remembering.
    Returns a list of new memories.
    """
    memory_prompt = f"""
You are a memory extraction assistant.

Your job is to look at the user's message and the assistant's response and identify
new facts about the user that are worth remembering for future conversations.

Only return facts that are:
- specifically about the user
- useful in future chats
- not already in the memory list
- short and clear

Existing memories:
{json.dumps(current_memories)}

User message:
{user_message}

Assistant response:
{assistant_response}

Return ONLY a JSON list of strings.
Example:
["The user's name is Ayanna", "The user studies at Syracuse University"]
"""

    try:
        memory_completion = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": "You extract useful long-term memories about the user."},
                {"role": "user", "content": memory_prompt}
            ],
            temperature=0
        )

        new_memories = memory_completion.choices[0].message.content.strip()
        parsed_memories = json.loads(new_memories)

        if isinstance(parsed_memories, list):
            return parsed_memories
        return []
    except Exception:
        return []

# -----------------------------
# Session State
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------------
# Sidebar Memory Display
# -----------------------------
st.sidebar.header("Saved Memories")

memories = load_memories()

if memories:
    for memory in memories:
        st.sidebar.write(f"- {memory}")
else:
    st.sidebar.write("No memories yet. Start chatting!")

if st.sidebar.button("Clear All Memories"):
    save_memories([])
    st.rerun()

# -----------------------------
# Display Chat History
# -----------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# -----------------------------
# Chat Input
# -----------------------------
user_input = st.chat_input("Say something...")

if user_input:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Build system prompt with memory
    memory_text = ""
    if memories:
        memory_text = "Here are things you remember about this user from past conversations:\n"
        for memory in memories:
            memory_text += f"- {memory}\n"

    system_prompt = f"""
You are a helpful chatbot with long-term memory.
{memory_text}
Use these memories naturally when helpful, but do not mention them unless relevant.
"""

    # Build conversation
    messages_for_llm = [{"role": "system", "content": system_prompt}]
    messages_for_llm.extend(st.session_state.messages)

    # Get assistant response
    completion = client.chat.completions.create(
        model="gpt-4.1",
        messages=messages_for_llm,
        temperature=0.7
    )

    assistant_reply = completion.choices[0].message.content

    # Show assistant response
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
    with st.chat_message("assistant"):
        st.write(assistant_reply)

    # Extract and save new memories
    new_memories = extract_new_memories(user_input, assistant_reply, memories)

    if new_memories:
        updated_memories = memories.copy()
        for memory in new_memories:
            if memory not in updated_memories:
                updated_memories.append(memory)
        save_memories(updated_memories)  # refresh sidebar to show new memories