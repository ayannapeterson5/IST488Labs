import streamlit as st
from openai import OpenAI
import requests
from bs4 import BeautifulSoup

# ------------------ PAGE SETUP ------------------
st.set_page_config(page_title="HW 2 – URL Summarizer", layout="centered")
st.title("HW 2: URL Summarizer")

client = OpenAI()

# ------------------ SIDEBAR ------------------
summary_type = st.sidebar.radio(
    "Summary type",
    [
        "100 words",
        "2 connecting paragraphs",
        "5 bullet points",
    ],
)

use_advanced = st.sidebar.checkbox("Use advanced model")

model = "gpt-4.1-nano"
if use_advanced:
    model = "gpt-4.1-mini"

# ------------------ HELPERS ------------------
def summary_instruction(choice):
    if choice == "100 words":
        return "Summarize the webpage in about 100 words."
    elif choice == "2 connecting paragraphs":
        return "Summarize the webpage in 2 connecting paragraphs."
    else:
        return "Summarize the webpage in exactly 5 bullet points."

def read_url_content(url):
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # remove noisy tags
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        return "\n".join(lines)

    except Exception as e:
        st.error(f"Error reading URL: {e}")
        return None

# ------------------ MAIN UI ------------------
url = st.text_input("Enter a URL to summarize")

if url and st.button("Generate Summary"):
    webpage_text = read_url_content(url)

    if webpage_text:
        instruction = summary_instruction(summary_type)

        messages = [
            {
                "role": "user",
                "content": f"Here is the webpage text:\n\n{webpage_text}\n\n{instruction}",
            }
        ]

        with st.spinner("Generating summary..."):
            stream = client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                temperature=0.3,
            )

            st.subheader("Summary")
            st.write_stream(stream)


