import streamlit as st
from openai import OpenAI
from pydantic import BaseModel

# Page setup
st.set_page_config(page_title="Lab 6 - OpenAI Responses Agent", page_icon="🤖")

# OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Pydantic model for structured output
class ResearchSummary(BaseModel):
    main_answer: str
    key_facts: list[str]
    source_hint: str

# Session state
if "last_response_id" not in st.session_state:
    st.session_state.last_response_id = None

# Title
st.title("Research Assistant Agent")

# Sidebar toggles
st.sidebar.header("Options")
structured_mode = st.sidebar.checkbox("Return structured summary")
stream_mode = st.sidebar.checkbox("Stream response")

# Note about web search
st.caption("This agent has web search enabled.")

# First user input
user_question = st.text_input("Ask a question:")

if user_question:
    if structured_mode:
        response = client.responses.parse(
            model="gpt-4o",
            instructions="You are a helpful research assistant. Cite your sources.",
            input=user_question,
            tools=[{"type": "web_search_preview"}],
            text_format=ResearchSummary
        )

        st.session_state.last_response_id = response.id
        parsed = response.output_parsed

        st.subheader("Answer")
        st.write(parsed.main_answer)

        st.subheader("Key Facts")
        for fact in parsed.key_facts:
            st.write(f"- {fact}")

        st.caption(parsed.source_hint)

    elif stream_mode:
        stream = client.responses.create(
            model="gpt-4o",
            instructions="You are a helpful research assistant. Cite your sources.",
            input=user_question,
            tools=[{"type": "web_search_preview"}],
            stream=True
        )

        full_text = ""
        placeholder = st.empty()

        for event in stream:
            if event.type == "response.output_text.delta":
                full_text += event.delta
                placeholder.write(full_text)
            elif event.type == "response.completed":
                st.session_state.last_response_id = event.response.id

    else:
        response = client.responses.create(
            model="gpt-4o",
            instructions="You are a helpful research assistant. Cite your sources.",
            input=user_question,
            tools=[{"type": "web_search_preview"}]
        )

        st.session_state.last_response_id = response.id

        st.subheader("Answer")
        st.write(response.output_text)

# Follow-up section
st.divider()
follow_up = st.text_input("Ask a follow-up question:")

if follow_up and st.session_state.last_response_id:
    if structured_mode:
        followup_response = client.responses.parse(
            model="gpt-4o",
            instructions="You are a helpful research assistant. Cite your sources.",
            input=follow_up,
            tools=[{"type": "web_search_preview"}],
            previous_response_id=st.session_state.last_response_id,
            text_format=ResearchSummary
        )

        st.session_state.last_response_id = followup_response.id
        parsed_followup = followup_response.output_parsed

        st.subheader("Follow-Up Answer")
        st.write(parsed_followup.main_answer)

        st.subheader("Key Facts")
        for fact in parsed_followup.key_facts:
            st.write(f"- {fact}")

        st.caption(parsed_followup.source_hint)

    elif stream_mode:
        followup_stream = client.responses.create(
            model="gpt-4o",
            instructions="You are a helpful research assistant. Cite your sources.",
            input=follow_up,
            tools=[{"type": "web_search_preview"}],
            previous_response_id=st.session_state.last_response_id,
            stream=True
        )

        followup_text = ""
        placeholder = st.empty()

        for event in followup_stream:
            if event.type == "response.output_text.delta":
                followup_text += event.delta
                placeholder.write(followup_text)
            elif event.type == "response.completed":
                st.session_state.last_response_id = event.response.id

    else:
        followup_response = client.responses.create(
            model="gpt-4o",
            instructions="You are a helpful research assistant. Cite your sources.",
            input=follow_up,
            tools=[{"type": "web_search_preview"}],
            previous_response_id=st.session_state.last_response_id
        )

        st.session_state.last_response_id = followup_response.id

        st.subheader("Follow-Up Answer")
        st.write(followup_response.output_text)
