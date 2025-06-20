"""
Streamlit RAG Frontend Application

This application provides a user-friendly web interface for the RAG (Retrieval-Augmented 
Generation) keyword summarization service. Users can enter keywords and receive AI-generated 
summaries based on multiple search sources.

Features:
- Real-time keyword summarization
- User authentication (Login/Signup UI)
- Responsive web interface
- Error handling and user feedback
- Integration with Flask backend API

Author: Your Name
Version: 1.0.0
Dependencies: streamlit, requests
"""

import streamlit as st
import requests
import os
import json
import time
from typing import Optional, Dict, Any
import logging

# Configure logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =================== CONFIGURATION ===================

# Backend API configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")
REQUEST_TIMEOUT = 30  # seconds
MAX_KEYWORD_LENGTH = 200
MIN_KEYWORD_LENGTH = 3

# =================== UTILITY FUNCTIONS ===================

def validate_keyword(keyword: str) -> tuple[bool, str]:
    """
    Validate the input keyword for API submission.
    
    Args:
        keyword (str): The keyword to validate
        
    Returns:
        tuple[bool, str]: (is_valid, error_message)
        
    Example:
        >>> is_valid, error = validate_keyword("AI")
        >>> print(is_valid, error)
        False, "Please enter a more descriptive keyword (at least 3 characters)."
    """
    if not keyword:
        return False, "Please enter a keyword."
    
    keyword = keyword.strip()
    
    if len(keyword) < MIN_KEYWORD_LENGTH:
        return False, f"Please enter a more descriptive keyword (at least {MIN_KEYWORD_LENGTH} characters)."
    
    if len(keyword) > MAX_KEYWORD_LENGTH:
        return False, f"Keyword is too long (maximum {MAX_KEYWORD_LENGTH} characters)."
    
    # Check if keyword contains only whitespace or special characters
    if not any(c.isalnum() for c in keyword):
        return False, "Keyword must contain at least one alphanumeric character."
    
    return True, ""


def make_api_request(keyword: str) -> Optional[Dict[Any, Any]]:
    """
    Make API request to the backend service for keyword summarization.
    
    Args:
        keyword (str): The keyword to summarize
        
    Returns:
        Optional[Dict[Any, Any]]: API response data if successful, None otherwise
        
    Raises:
        requests.RequestException: If HTTP request fails
        json.JSONDecodeError: If response is not valid JSON
    """
    try:
        logger.info(f"Making API request for keyword: {keyword}")
        
        # Prepare request data
        request_data = {"keyword": keyword.strip()}
        
        # Make API request with timeout
        response = requests.post(
            url=f"{BACKEND_URL}/keyword",  # Fixed: changed from /KEYWORD to /keyword
            json=request_data,
            timeout=REQUEST_TIMEOUT,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Streamlit-RAG-Frontend/1.0'
            }
        )
        
        # Log response status
        logger.info(f"API response status: {response.status_code}")
        
        # Handle different response status codes
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400:
            error_data = response.json() if response.content else {"error": "Bad request"}
            st.error(f"Request error: {error_data.get('error', 'Invalid request')}")
            return None
        elif response.status_code == 500:
            st.error("Server error. Please try again later.")
            return None
        else:
            st.error(f"Unexpected error (Status {response.status_code}). Please try again.")
            return None
            
    except requests.exceptions.Timeout:
        st.error("Request timed out. The server might be busy. Please try again.")
        logger.error("API request timed out")
        return None
        
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to the server. Please check if the backend is running.")
        logger.error("Connection error to backend")
        return None
        
    except requests.exceptions.RequestException as e:
        st.error("Network error occurred. Please check your connection.")
        logger.error(f"Request exception: {str(e)}")
        return None
        
    except json.JSONDecodeError:
        st.error("Invalid response format from server.")
        logger.error("Invalid JSON response from server")
        return None
        
    except Exception as e:
        st.error("An unexpected error occurred. Please try again.")
        logger.error(f"Unexpected error in API request: {str(e)}")
        return None


def display_summary(summary_data: Dict[Any, Any]) -> None:
    """
    Display the summary response in a formatted manner.
    
    Args:
        summary_data (Dict[Any, Any]): The API response containing summary information
    """
    try:
        # Extract summary from response
        summary = summary_data.get('summary', '').strip()
        keyword = summary_data.get('keyword', '').strip()
        
        if not summary:
            st.warning("No summary content was generated. Please try a different keyword.")
            return
        
        # Display the summary with formatting
        st.success("✅ Summary generated successfully!")
        
        # Create an expandable section for the summary
        with st.expander(f"📝 Summary for: **{keyword}**", expanded=True):
            st.markdown(summary)
            
            # Add metadata if available
            col1, col2 = st.columns(2)
            with col1:
                st.caption(f"🔍 Keyword: {keyword}")
            with col2:
                st.caption(f"📊 Length: {len(summary)} characters")
        
        # Add copy button functionality
        if st.button("📋 Copy Summary", help="Copy summary to clipboard"):
            # Note: Direct clipboard access requires additional setup in Streamlit
            st.code(summary, language="text")
            st.info("Summary displayed above - you can select and copy it manually.")
            
    except Exception as e:
        st.error("Error displaying summary. Please try again.")
        logger.error(f"Error in display_summary: {str(e)}")


def render_sidebar() -> None:
    """
    Render the sidebar.
    
    Note: This is a UI placeholder for future authentication implementation.
    The actual authentication logic would need to be implemented with a proper
    #backend authentication system.
    #"""
    #with st.sidebar:
    #    st.header("🔐 Authentication")
    #    
    #    # Create tabs for login and signup
    #    tab1, tab2 = st.tabs(["🔑 Login", "📝 Signup"])
#
    #    with tab1:
    #        st.subheader("Login to Your Account")
    #        
    #        login_username = st.text_input(
    #            label="Username", 
    #            placeholder="Enter your username", 
    #            key="login_user",
    #            help="Enter your registered username"
    #        )
    #        
    #        login_password = st.text_input(
    #            label="Password", 
    #            placeholder="Enter your password", 
    #            type="password", 
    #            key="login_pass",
    #            help="Enter your account password"
    #        )
    #        
    #        if st.button("🔓 Login", key="login_btn", type="primary"):
    #            if login_username and login_password:
    #                # Placeholder for actual authentication logic
    #                st.success(f"Welcome back, {login_username}! (Demo mode)")
    #                st.balloons()
    #            else:
    #                st.error("Please fill in both username and password.")
#
    #    with tab2:
    #        st.subheader("Create New Account")
    #        
    #        signup_username = st.text_input(
    #            label="Username", 
    #            placeholder="Choose a username", 
    #            key="signup_user",
    #            help="Choose a unique username (3+ characters)"
    #        )
    #        
    #        signup_password = st.text_input(
    #            label="Password", 
    #            placeholder="Create a password", 
    #            type="password", 
    #            key="signup_pass",
    #            help="Password should be at least 8 characters"
    #        )
    #        
    #        signup_confirm_pass = st.text_input(
    #            label="Confirm Password", 
    #            label_visibility="collapsed", 
    #            placeholder="Confirm your password", 
    #            type="password", 
    #            key="signup_confirm_pass",
    #            help="Re-enter your password to confirm"
    #        )
    #        
    #        if st.button("📝 Sign Up", key="signup_btn", type="primary"):
    #            # Basic validation for demo
    #            if not all([signup_username, signup_password, signup_confirm_pass]):
    #                st.error("Please fill in all fields.")
    #            elif len(signup_username) < 3:
    #                st.error("Username must be at least 3 characters long.")
    #            elif len(signup_password) < 8:
    #                st.error("Password must be at least 8 characters long.")
    #            elif signup_password != signup_confirm_pass:
    #                st.error("Passwords do not match.")
    #            else:
    #                # Placeholder for actual signup logic
    #                st.success(f"Account created for {signup_username}! (Demo mode)")
    #                st.balloons()
    with st.sidebar:
        st.markdown("### 📊 App Info")
        st.info(f"🌐 Backend: {BACKEND_URL}")
        
        # Health check button
        if st.button("🔍 Check Backend Status", help="Test connection to backend"):
            with st.spinner("Checking backend..."):
                try:
                    health_response = requests.get(
                        f"{BACKEND_URL}/health", 
                        timeout=5
                    )
                    if health_response.status_code == 200:
                        st.success("✅ Backend is healthy!")
                    else:
                        st.error("❌ Backend health check failed")
                except Exception:
                    st.error("❌ Cannot connect to backend")


def main():
    """
    Main application function that renders the Streamlit interface.
    
    This function sets up the page configuration, renders the UI components,
    handles user interactions, and manages the API communication flow.
    """
    # =================== PAGE CONFIGURATION ===================
    
    st.set_page_config(
        page_title="RAG Keyword Summarizer",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://github.com/RaghuRam2005/article_summary',
            'Report a bug': 'https://github.com/RaghuRam2005/article_summary/issues',
            'About': "RAG-powered keyword summarization using AI"
        }
    )
    
    # =================== HEADER SECTION ===================
    
    # Main title with emoji and styling
    st.title("🔍 Keyword Search & Summarization")
    
    # Subtitle and description (Markdown version)
    st.markdown(
        """
        ##### 🤖 AI-Powered Knowledge Discovery

        Enter a keyword or phrase to generate a comprehensive summary using advanced 
        **Retrieval Augmented Generation (RAG)** technology powered by Google's Gemini AI.
        """
    )
    # Tips and usage guidelines
    with st.expander("💡 Usage Tips & Examples", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🎯 Best Practices:**
            - Use specific, descriptive keywords
            - Try technical terms or concepts
            - Combine related words for better context
            - Avoid very common words
            """)
            
        with col2:
            st.markdown("""
            **✨ Example Keywords:**
            - "quantum computing applications"
            - "renewable energy trends 2024"
            - "machine learning algorithms"
            - "blockchain technology"
            """)
    
    # =================== SIDEBAR ===================
    
    render_sidebar()
    
    # =================== MAIN CONTENT AREA ===================
    
    # Create main content columns
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Keyword input section
        st.subheader("🔤 Enter Your Keyword")
        
        # Input field with enhanced styling
        input_keyword = st.text_input(
            label="Keyword or Phrase",
            placeholder="e.g., artificial intelligence, climate change, cryptocurrency...",
            help=f"Enter a keyword between {MIN_KEYWORD_LENGTH}-{MAX_KEYWORD_LENGTH} characters",
            label_visibility="collapsed"
        )
        
        # Real-time validation
        if input_keyword:
            is_valid, error_message = validate_keyword(input_keyword)
            if not is_valid:
                st.warning(f"⚠️ {error_message}")
            else:
                st.success(f"✅ Keyword looks good! ({len(input_keyword.strip())} characters)")
    
    with col2:
        # Action button section
        st.subheader("")
        
        # Main summarize button
        summarize_clicked = st.button(
            "🔍 Generate Summary", 
            type="primary",
            disabled=not input_keyword or not validate_keyword(input_keyword)[0],
            help="Click to generate an AI-powered summary",
            use_container_width=True
        )
    
    # =================== API REQUEST HANDLING ===================
    
    # Handle summarization request
    if summarize_clicked and input_keyword:
        # Validate input one more time
        is_valid, error_message = validate_keyword(input_keyword)
        
        if not is_valid:
            st.error(f"❌ {error_message}")
            return
        
        # Show loading state
        with st.spinner("🤖 Generating summary... This may take a few moments."):
            # Add progress bar for better UX
            progress_bar = st.progress(0)
            
            # Simulate progress steps
            for i in range(100):
                time.sleep(0.01)  # Small delay for visual effect
                progress_bar.progress(i + 1)
            
            # Make API request
            api_response = make_api_request(input_keyword)
        
        # Clear progress bar
        progress_bar.empty()
        
        # Handle API response
        if api_response:
            # Check if response contains summary
            if api_response.get('status') == 'success' and api_response.get('summary'):
                display_summary(api_response)
            elif api_response.get('status') == 'error':
                st.error(f"❌ {api_response.get('error', 'Unknown error occurred')}")
            else:
                st.warning("⚠️ No summary was generated. Please try a different keyword.")
        # If api_response is None, error was already displayed in make_api_request

# =================== APPLICATION ENTRY POINT ===================

if __name__ == "__main__":
    try:
        logger.info("Starting Streamlit RAG Frontend Application")
        logger.info(f"Backend URL: {BACKEND_URL}")
        main()
    except Exception as e:
        st.error("Failed to start the application.")
        logger.error(f"Application startup error: {str(e)}")
        st.exception(e)
