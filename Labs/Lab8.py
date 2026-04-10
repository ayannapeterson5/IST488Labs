import streamlit as st
from openai import OpenAI
import requests
import base64

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "url_response" not in st.session_state:
    st.session_state.url_response = None

if "upload_response" not in st.session_state:
    st.session_state.upload_response = None

st.title("Lab 08 - Image Captioning Bot")

# URL input section
st.header("Image URL Input")
url = st.text_input("Image URL")

if st.button("Generate Caption for Inputted URL"):
    if url:
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
                            "text": "Describe the image in at least 3 sentences. Write five different captions for this image."
                        }
                    ]
                }
            ]
        )
        st.session_state.url_response = url_response.choices[0].message.content

if st.session_state.url_response:
    st.write(st.session_state.url_response)

# Upload section
st.header("Image Upload Input")
uploaded = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png", "webp", "gif"])

if st.button("Generate Caption for Uploaded Image"):
    if uploaded is not None:
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
                            "text": "Describe the image in at least 3 sentences. Write five different captions for this image."
                        }
                    ]
                }
            ]
        )
        st.session_state.upload_response = upload_response.choices[0].message.content

if st.session_state.upload_response:
    st.write(st.session_state.upload_response)