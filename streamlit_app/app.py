import streamlit as st
import requests
import os

BACKEND_URL = os.getenv("BACKEND_URL")

st.title("Keyword Search 🔍")

st.markdown(
    """
    Enter a keyword or phrase to generate a concise summary from relevant articles using advanced Retrieval Augmented Generation (RAG) and Gemini API.

    - **Tip:** Try specific topics (e.g., "quantum computing", "renewable energy trends").
    - Summaries are generated in real-time based on the latest available content.
    """
)

with st.sidebar:
    st.header("Login or Signup")
    tab1, tab2 = st.tabs(["Login", "Signup"])

    with tab1:
        st.text_input(
            label="Username", 
            placeholder="Enter the username", 
            key="login_user"
        )
        st.text_input(
            label="Password", 
            placeholder="Enter the password", 
            type="password", 
            key="login_pass"
        )

    with tab2:
        st.text_input(
            label="Username", 
            placeholder="Enter the username", 
            key="signup_user"
        )
        st.text_input(
            label="Password", 
            placeholder="Enter the password", 
            type="password", 
            key="signup_pass"
        )
        st.text_input(
            label="Confirm Password", 
            label_visibility="collapsed", 
            placeholder="Re-enter the password", 
            type="password", 
            key="signup_confirm_pass"
        )



input_keyword = st.text_input("Enter the keyword you want to know about")
if input_keyword and len(input_keyword.strip()) < 3:
    st.warning("Please enter a more descriptive keyword (at least 3 characters).")

response = None

if st.button("Summarize", type="primary") and input_keyword:
    try:
        data = {
            "keyword" : input_keyword
        }
        response = requests.post(url=f"{BACKEND_URL}/KEYWORD", json=data)
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
