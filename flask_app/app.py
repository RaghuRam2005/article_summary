"""
Flask RAG (Retrieval-Augmented Generation) Application

This application provides a REST API endpoint for generating summaries of keywords
using multiple search sources (Wikipedia, DuckDuckGo) and Google's Gemini AI model.

Author: RaghuRam2005
Version: 1.0.0
Dependencies: flask, python-dotenv, google-genai, requests
"""

from flask import Flask, request, jsonify
from dotenv import load_dotenv
from google import genai
from google.genai import types
import requests
import os
import re
import logging
from typing import Optional, Dict, Any, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask application
app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# Initialize Gemini AI client
GEMINI_API = os.getenv("GEMINI_API")
if not GEMINI_API:
    logger.error("GEMINI_API environment variable not found")
    raise ValueError("GEMINI_API environment variable is required")

client = genai.Client(api_key=GEMINI_API)


def clean_data(text: str) -> str:
    """
    Clean and normalize text data by removing unwanted characters and formatting.
    
    This function performs several cleaning operations:
    - Removes HTML tags
    - Keeps only alphanumeric characters, spaces, and basic punctuation
    - Normalizes whitespace (multiple spaces/newlines become single space)
    - Strips leading and trailing whitespace
    
    Args:
        text (str): Input text to clean. Can be None or empty string.
        
    Returns:
        str: Cleaned and normalized text. Returns empty string if input is invalid.
        
    Example:
        >>> clean_data("<p>Hello   world!</p>   ")
        "Hello world!"
    """
    # Validate input
    if not text or not isinstance(text, str):
        logger.debug("Invalid text input provided to clean_data")
        return ""
    
    try:
        # Remove HTML tags if present
        text = re.sub(r'<[^>]+>', '', text)
        
        # Keep only alphanumeric characters, spaces, and basic punctuation (.,!?-')
        text = re.sub(r'[^a-zA-Z0-9\s.,!?\-\'\n]', '', text)
        
        # Normalize whitespace - replace multiple spaces/newlines with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        logger.debug(f"Text cleaned successfully, length: {len(text)}")
        return text
        
    except Exception as e:
        logger.error(f"Error cleaning text: {str(e)}")
        return ""


class RAGSearcher:
    """
    Retrieval-Augmented Generation Searcher Class
    
    This class handles searching multiple data sources (Wikipedia, DuckDuckGo)
    and generating AI-powered summaries using Google's Gemini model.
    
    Attributes:
        session (requests.Session): Persistent HTTP session for API calls
        
    Methods:
        search_wikipedia: Search Wikipedia for article content
        search_duckduckgo_instant: Search DuckDuckGo Instant Answer API
        generate_summary: Generate AI summary from search results
    """
    
    def __init__(self):
        """
        Initialize the RAG searcher with a persistent HTTP session.
        
        The session allows for connection pooling and better performance
        when making multiple HTTP requests.
        """
        self.session = requests.Session()
        # Set default headers for better API compatibility
        self.session.headers.update({
            'User-Agent': 'RAG-Searcher/1.0 (Educational Purpose)'
        })
        logger.info("RAGSearcher initialized successfully")
    
    def search_wikipedia(self, keyword: str, timeout: int = 10) -> Optional[str]:
        """
        Search Wikipedia for content related to the given keyword.
        
        This method performs a two-step process:
        1. Search for articles matching the keyword using OpenSearch API
        2. Retrieve the full text content of the first matching article
        
        Args:
            keyword (str): The search term to look for on Wikipedia
            timeout (int, optional): Request timeout in seconds. Defaults to 10.
            
        Returns:
            Optional[str]: Article content if found, None if no results or error occurred
            
        Raises:
            ValueError: If no title can be extracted from search results
            requests.RequestException: If HTTP request fails
            
        Example:
            >>> searcher = RAGSearcher()
            >>> content = searcher.search_wikipedia("artificial intelligence")
            >>> print(len(content) if content else "No content found")
        """
        WIKI_URL = "https://en.wikipedia.org/w/api.php"
        
        try:
            logger.info(f"Searching Wikipedia for keyword: {keyword}")
            
            # Step 1: Search for article titles
            search_params = {
                "action": "opensearch",
                "namespace": 0,
                "search": keyword,
                "limit": 2,  # Get top 2 results for better accuracy
                "format": "json"
            }

            search_response = self.session.get(
                url=WIKI_URL, 
                params=search_params, 
                timeout=timeout
            )
            search_response.raise_for_status()
            
            search_data = search_response.json()
            
            # Extract the first article title
            if not search_data[1]:  # No search results found
                logger.warning(f"No Wikipedia articles found for keyword: {keyword}")
                return None
                
            title = search_data[1][0]  # Get first result title
            logger.info(f"Found Wikipedia article: {title}")
            
            # Step 2: Get full article content
            content_params = {
                "action": "query",
                "format": "json",
                "prop": "extracts",
                "explaintext": True,  # Get plain text without markup
                "titles": title
            }
            
            content_response = self.session.get(
                WIKI_URL, 
                params=content_params, 
                timeout=timeout
            )
            content_response.raise_for_status()
            
            content_data = content_response.json()
            
            # Extract article content from response
            pages = content_data["query"]["pages"]
            content = ""
            
            for page_id in pages:
                page_content = pages[page_id].get("extract", "")
                if page_content:
                    content += page_content
                    break  # Use first valid content found
            
            if content:
                logger.info(f"Retrieved Wikipedia content, length: {len(content)}")
                return content
            else:
                logger.warning(f"No content extracted from Wikipedia for: {keyword}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"HTTP error during Wikipedia search: {str(e)}")
            return None
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing Wikipedia response: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during Wikipedia search: {str(e)}")
            return None
    
    def search_duckduckgo_instant(self, keyword: str, timeout: int = 10) -> Optional[Dict[str, str]]:
        """
        Search DuckDuckGo Instant Answer API for quick facts and definitions.
        
        This method queries DuckDuckGo's API for instant answers, which include:
        - Abstract summaries
        - Definitions
        - Related topics
        
        Args:
            keyword (str): The search term to query
            timeout (int, optional): Request timeout in seconds. Defaults to 10.
            
        Returns:
            Optional[Dict[str, str]]: Dictionary with 'title', 'extract', and 'source' keys
                                   if successful, None otherwise
                                   
        Example:
            >>> searcher = RAGSearcher()
            >>> result = searcher.search_duckduckgo_instant("Python programming")
            >>> if result:
            ...     print(f"Title: {result['title']}")
            ...     print(f"Extract: {result['extract'][:100]}...")
        """
        try:
            logger.info(f"Searching DuckDuckGo for keyword: {keyword}")
            
            url = "https://api.duckduckgo.com/"
            params = {
                'q': keyword,
                'format': 'json',
                'no_redirect': '1',  # Don't follow redirects
                'no_html': '1'       # Return plain text
            }
            
            response = self.session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            
            data = response.json()
            
            # Priority 1: Check for abstract (most comprehensive)
            if data.get('Abstract'):
                logger.info("Found DuckDuckGo abstract")
                return {
                    'title': data.get('Heading', keyword),
                    'extract': data.get('Abstract', ''),
                    'source': data.get('AbstractSource', 'DuckDuckGo')
                }
            
            # Priority 2: Check for definition (concise explanation)
            if data.get('Definition'):
                logger.info("Found DuckDuckGo definition")
                return {
                    'title': keyword,
                    'extract': data.get('Definition', ''),
                    'source': data.get('DefinitionSource', 'DuckDuckGo')
                }
            
            # Priority 3: Check for related topics (fallback)
            if data.get('RelatedTopics'):
                topics = data['RelatedTopics'][:2]  # Get first 2 topics
                extract = ""
                
                for topic in topics:
                    if isinstance(topic, dict) and topic.get('Text'):
                        extract += topic['Text'] + "\n\n"
                
                if extract.strip():
                    logger.info("Found DuckDuckGo related topics")
                    return {
                        'title': keyword,
                        'extract': extract.strip(),
                        'source': 'DuckDuckGo'
                    }
            
            logger.warning(f"No relevant content found in DuckDuckGo for: {keyword}")
            return None
            
        except requests.RequestException as e:
            logger.error(f"HTTP error during DuckDuckGo search: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during DuckDuckGo search: {str(e)}")
            return None

    def generate_summary(self, keyword: str) -> str:
        """
        Generate an AI-powered summary for a given keyword using multiple sources.
        
        This method implements a fallback strategy:
        1. Try Wikipedia first (most comprehensive)
        2. Fall back to DuckDuckGo if Wikipedia fails
        3. Use Google Gemini AI to generate a concise summary
        
        Args:
            keyword (str): The keyword to search for and summarize
            
        Returns:
            str: Generated summary text, or empty string if all sources fail
            
        Process Flow:
            keyword -> search sources -> clean data -> AI summarization -> final summary
            
        Example:
            >>> searcher = RAGSearcher()
            >>> summary = searcher.generate_summary("machine learning")
            >>> print(f"Summary: {summary}")
        """
        # Validate input
        if not keyword or not isinstance(keyword, str):
            logger.warning("Invalid keyword provided to generate_summary")
            return ""
        
        logger.info(f"Generating summary for keyword: {keyword}")
        
        raw_content = ""
        
        # Define search sources in priority order
        search_sources = [
            ("Wikipedia", self.search_wikipedia),
            ("DuckDuckGo", self.search_duckduckgo_instant)
        ]

        # Try each source until we get valid data
        for source_name, source_func in search_sources:
            try:
                logger.info(f"Trying {source_name} for keyword: {keyword}")
                
                search_result = source_func(keyword)
                
                if search_result:
                    # Handle different return types from search functions
                    if isinstance(search_result, dict):
                        # DuckDuckGo returns a dictionary
                        raw_content = search_result.get('extract', '')
                    else:
                        # Wikipedia returns a string
                        raw_content = search_result
                    
                    # Clean the retrieved content
                    cleaned_content = clean_data(raw_content)
                    
                    if cleaned_content and len(cleaned_content.strip()) > 50:
                        # We have substantial content, proceed with summarization
                        logger.info(f"Successfully retrieved content from {source_name}")
                        raw_content = cleaned_content
                        break
                    else:
                        logger.warning(f"Content from {source_name} too short or empty")
                        continue
                        
            except Exception as e:
                logger.error(f"Error with {source_name}: {str(e)}")
                continue

        # If no valid content found from any source
        if not raw_content or len(raw_content.strip()) < 50:
            logger.warning(f"No sufficient content found for keyword: {keyword}")
            return f"Sorry, I couldn't find detailed information about '{keyword}'. Please try a different keyword or check the spelling."

        # Generate summary using Gemini AI
        try:
            logger.info("Generating AI summary using Gemini")
            
            # Create a focused prompt for better summarization
            prompt = f"""Please provide a clear, concise summary of the following content about '{keyword}'. 
            Focus on the most important information and key concepts. Keep it informative but brief (2-3 paragraphs maximum):

            {raw_content}"""
            
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",  # Updated to more recent model
                contents=prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                    # Add generation config for better control
                    max_output_tokens=500,  # Limit summary length
                    temperature=0.3,        # Lower temperature for more focused output
                )
            )
            
            if response and hasattr(response, 'text') and response.text:
                summary = clean_data(response.text)
                
                if summary:
                    logger.info(f"Successfully generated summary, length: {len(summary)}")
                    return summary
                else:
                    logger.warning("AI generated empty summary after cleaning")
            else:
                logger.warning("Empty or invalid response from AI model")
                
        except Exception as e:
            logger.error(f"Error generating summary with AI model: {str(e)}")
        
        # Fallback: return cleaned raw content if AI summarization fails
        logger.info("Falling back to cleaned raw content")
        return raw_content[:1000] + "..." if len(raw_content) > 1000 else raw_content


# Initialize the RAG searcher instance
rag_searcher = RAGSearcher()


@app.route("/keyword", methods=['POST'])  # Fixed: changed from POSTS to POST
def summarize_keyword_content():
    """
    REST API endpoint to generate keyword summaries.
    
    This endpoint accepts POST requests with a JSON payload containing a keyword
    and returns an AI-generated summary based on multiple search sources.
    
    Request Format:
        POST /keyword
        Content-Type: application/json
        
        {
            "keyword": "your search term here"
        }
    
    Response Format:
        Success (200):
        {
            "keyword": "searched term",
            "summary": "AI-generated summary text",
            "status": "success"
        }
        
        Error (400):
        {
            "error": "error description",
            "status": "error"
        }
    
    Returns:
        tuple: (response_dict, status_code)
        
    Example:
        curl -X POST http://localhost:5000/keyword \
             -H "Content-Type: application/json" \
             -d '{"keyword": "artificial intelligence"}'
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        # Validate request data
        if not data:
            logger.warning("No JSON data provided in request")
            return jsonify({
                "error": "No JSON data provided",
                "status": "error"
            }), 400
        
        # Extract and validate keyword
        keyword = data.get('keyword')
        if not keyword:
            logger.warning("No keyword provided in request")
            return jsonify({
                "error": "Missing 'keyword' field in request",
                "status": "error"
            }), 400
        
        if not isinstance(keyword, str):
            logger.warning(f"Invalid keyword type: {type(keyword)}")
            return jsonify({
                "error": "Keyword must be a string",
                "status": "error"
            }), 400
        
        # Clean and validate keyword
        keyword = keyword.strip()
        if not keyword:
            logger.warning("Empty keyword provided after cleaning")
            return jsonify({
                "error": "Keyword cannot be empty",
                "status": "error"
            }), 400
        
        if len(keyword) > 200:  # Reasonable limit for keywords
            logger.warning(f"Keyword too long: {len(keyword)} characters")
            return jsonify({
                "error": "Keyword too long (maximum 200 characters)",
                "status": "error"
            }), 400
        
        logger.info(f"Processing keyword request: {keyword}")
        
        # Generate summary
        summary = rag_searcher.generate_summary(keyword)
        
        # Prepare response
        response_data = {
            "keyword": keyword,
            "summary": summary,
            "status": "success"
        }
        
        logger.info(f"Successfully processed keyword: {keyword}")
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in summarize_keyword_content: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "status": "error"
        }), 500


@app.route("/health", methods=['GET'])
def health_check():
    """
    Health check endpoint to verify API availability.
    
    Returns:
        dict: Simple health status response
        
    Example:
        curl http://localhost:5000/health
    """
    return jsonify({
        "status": "healthy",
        "service": "RAG Keyword Summarizer",
        "version": "1.0.0"
    }), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors with a JSON response."""
    return jsonify({
        "error": "Endpoint not found",
        "status": "error",
        "available_endpoints": ["/keyword (POST)", "/health (GET)"]
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 Method Not Allowed errors."""
    return jsonify({
        "error": "Method not allowed",
        "status": "error"
    }), 405


if __name__ == "__main__":
    """
    Run the Flask application in development mode.
    
    Configuration:
    - Debug mode: Enabled for development
    - Host: 0.0.0.0 (accessible from any IP)
    - Port: 5000 (default Flask port)
    
    Environment Variables Required:
    - GEMINI_API: Google Gemini API key
    
    Usage:
        python app.py
    """
    logger.info("Starting Flask RAG Application")
    logger.info(f"Available endpoints:")
    logger.info("  POST /keyword - Generate keyword summary")
    logger.info("  GET /health - Health check")
    
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )
