import streamlit as st
from openai import OpenAI
import requests
import base64

st.set_page_config(page_title="Lab 08 - Image Captioning Bot", page_icon="🖼️")

# OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Session state
if "url_response" not in st.session_state:
    st.session_state.url_response = None

if "upload_response" not in st.session_state:
    st.session_state.upload_response = None


def extract_text(response):
    """Safely extract text from the OpenAI response."""
    try:
        return response.choices[0].message.content
    except Exception:
        return "No response text was returned."


st.title("Image Captioning Bot")
st.write("Provide either an image URL or upload an image file and the bot will generate a description and captions for it.")

# -----------------------------
# Part A: Image URL Input
# -----------------------------
st.header("Image URL Input")
st.write("Paste a direct image URL below.")
url = st.text_input("Image URL")
st.caption("Make sure the URL leads directly to an image file, not a webpage.")

if st.button("Generate Caption for Inputted URL"):
    if url:
        try:
            # Optional check that URL is reachable
            response_check = requests.get(url, timeout=10)
            response_check.raise_for_status()

            url_response = client.chat.completions.create(
                model="gpt-4.1-mini",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": url,
                                    "detail": "auto"
                                }
                            },
                            {
                                "type": "text",
                                "text": (
                                    "Describe the image in at least 3 sentences. "
                                    "Write five different captions for this image. "
                                    "Captions must vary in length, with at least one very short caption "
                                    "and none longer than 2 sentences. "
                                    "Captions should vary in tone, including funny, intellectual, and aesthetic."
                                )
                            }
                        ]
                    }
                ]
            )

            st.session_state.url_response = extract_text(url_response)

        except Exception as e:
            st.session_state.url_response = f"Error: {e}"
    else:
        st.warning("Please enter an image URL first.")

if st.session_state.url_response:
    if url:
        st.image(url, caption="Inputted Image", use_container_width=True)
    st.write(st.session_state.url_response)


# -----------------------------
# Part B: File Upload
# -----------------------------
st.header("Image Upload Input")
uploaded = st.file_uploader(
    "Upload an image",
    type=["jpg", "jpeg", "png", "webp", "gif"]
)

if st.button("Generate Caption for Uploaded Image"):
    if uploaded is not None:
        try:
            image_bytes = uploaded.read()
            b64 = base64.b64encode(image_bytes).decode("utf-8")
            mime = uploaded.type
            data_uri = f"data:{mime};base64,{b64}"

            upload_response = client.chat.completions.create(
                model="gpt-4.1-mini",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": data_uri,
                                    "detail": "low"
                                }
                            },
                            {
                                "type": "text",
                                "text": (
                                    "Describe the image in at least 3 sentences. "
                                    "Write five different captions for this image. "
                                    "Captions must vary in length, with at least one very short caption "
                                    "and none longer than 2 sentences. "
                                    "Captions should vary in tone, including funny, intellectual, and aesthetic."
                                )
                            }
                        ]
                    }
                ]
            )

            st.session_state.upload_response = extract_text(upload_response)

        except Exception as e:
            st.session_state.upload_response = f"Error: {e}"
    else:
        st.warning("Please upload an image first.")

if st.session_state.upload_response:
    if uploaded is not None:
        st.image(uploaded, caption="Uploaded Image", use_container_width=True)
    st.write(st.session_state.upload_response)