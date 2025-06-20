import streamlit as st
import requests
from urllib.parse import urlparse
import os

BACKEND_URL = os.getenv("BACKEND_URL")

def valid_url_format(url:str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme in ('http', 'https'), result.netloc])
    except Exception:
        return False

def url_has_content(url:str, timeout=10) -> bool:
    try:
        if valid_url_format(url):
            response = requests.head(url, allow_redirects=True, timeout=timeout)
            if response.status_code >=400:
                response = requests.get(url, stream=True, timeout=timeout)
            return response.status_code < 400
        else:
            return False
    except Exception:
        return False

st.title("Article Summary")
st.markdown(
    """
    This tool uses Retreival Augumented Generation (RAG) to search for articles
    based on the keyword by the user. It uses Gemini API to summarize the content
    of the article
    """
)

with st.sidebar:
    GEMINI_API = st.text_input("Enter the Gemini API key", type="password")
    if not GEMINI_API:
        st.warning(
            """
            **Enter your Google Gemini API key in the sidebar to get started!** You can obtain your API key from the Google AI Studio:  
            [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)

            *Please note: Usage of the Gemini API may incur costs based on your consumption.*
            """
        )

tab1, tab2 = st.tabs(["Enter the Article URL", "Enter the keyword"])
input_keyword = None
input_url = None

with tab1:
    input_url = st.text_input("Enter the Article URL you want to summarize")
    if not url_has_content(input_url):
        st.warning(
        """
        Enter a valid URL to proceed
        """
        )

with tab2:
    st.markdown(
        """
        **Tip:** Enter a keyword or phrase (e.g., "climate change", "AI in healthcare") to search for relevant articles.
        """
    )
    input_keyword = st.text_input("Enter the keyword you want to know about")
    if input_keyword and len(input_keyword.strip()) < 3:
        st.warning("Please enter a more descriptive keyword (at least 3 characters).")

if not GEMINI_API:
    st.warning(
    """
    Gemini API not set, please enter the API to continue
    """
    )

response = None

if st.button("Summarize", type="primary") and (input_keyword or input_url) and GEMINI_API:
    try:
        if input_url:
            data = {
                "GEMINI_API" : GEMINI_API,
                "link" : input_url
            }
            response = requests.post(url=f"{BACKEND_URL}/URL", json=data)
        else:
            data = {
                "GEMINI_API" : GEMINI_API,
                "keyword" : input_keyword
            }
            response = requests.post(url=f"{BACKEND_URL}/KEYWORD", json=data)
        response.raise_for_status()
    except Exception:
        st.warning(
        """
        An Exception occured while posting data
        """
        )
        response = None

if response:
    try:
        data = response.json()
        if not data or 'summary' not in data:
            st.warning("No summary data received.")
        else:
            st.markdown(data['summary'])
    except Exception as e:
        st.warning("Invalid format from the server")
