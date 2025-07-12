"""
Flask RAG (Retrieval-Augmented Generation) Application

This application provides a REST API endpoint for generating summaries from various sources:
- Keywords (via Wikipedia/DuckDuckGo)
- Web page URLs
- Direct text content

Author: RaghuRam2005
Version: 2.0.0
Dependencies: flask, python-dotenv, google-genai, requests, beautifulsoup4
"""

from flask import Flask, request, jsonify
from dotenv import load_dotenv
from google import genai
from google.genai import types
import requests
from bs4 import BeautifulSoup
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
    
    ## Enhancement: This function is updated to remove common Markdown syntax.
    """
    if not text or not isinstance(text, str):
        logger.debug("Invalid text input provided to clean_data")
        return ""
    
    try:
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Remove headers (e.g., #, ##, ###)
        text = re.sub(r'^\s*#+\s*', '', text, flags=re.MULTILINE)
        # Remove emphasis (e.g., *, **, _, __)
        text = re.sub(r'(\*|_){1,2}(.*?)\1{1,2}', r'\2', text)
        # Remove list items (e.g., * item, - item)
        text = re.sub(r'^\s*[\*\-]\s+', '', text, flags=re.MULTILINE)
        
        # Keep only alphanumeric characters, spaces, and basic punctuation
        text = re.sub(r'[^a-zA-Z0-9\s.,!?\-\'\n]', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        logger.debug(f"Text cleaned successfully, length: {len(text)}")
        return text
        
    except Exception as e:
        logger.error(f"Error cleaning text: {str(e)}")
        return ""


class RAGProcessor:
    """
    This class handles retrieving content from multiple sources (Wikipedia, DuckDuckGo, URLs)
    and generating AI-powered summaries.
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RAG-Processor/2.0 (Educational Purpose)'
        })
        logger.info("RAGProcessor initialized successfully")

    ## Method to scrape content from the url
    def scrape_url_content(self, url: str, timeout: int = 15) -> Optional[str]:
        """
        Scrape the main textual content from a given URL.
        
        Args:
            url (str): The URL to scrape.
            timeout (int, optional): Request timeout in seconds. Defaults to 15.
            
        Returns:
            Optional[str]: The extracted text content, or None on failure.
        """
        try:
            logger.info(f"Scraping content from URL: {url}")
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()

            # Use BeautifulSoup to parse the HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script and style elements
            for script_or_style in soup(['script', 'style']):
                script_or_style.decompose()

            # Get text from common article tags, prioritize <article>
            if soup.article:
                text = soup.article.get_text()
            else:
                # Fallback to a combination of other common tags
                tags = soup.find_all(['p', 'h1', 'h2', 'h3'])
                text = '\n'.join(tag.get_text() for tag in tags)

            if not text:
                # If no text found with specific tags, get all visible text
                text = soup.get_text()

            logger.info(f"Successfully scraped content, length: {len(text)}")
            return text

        except requests.RequestException as e:
            logger.error(f"HTTP error during URL scraping for {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during URL scraping for {url}: {str(e)}")
            return None

    def search_wikipedia(self, keyword: str, timeout: int = 10) -> Optional[str]:
        """Search Wikipedia for content related to the given keyword."""
        WIKI_URL = "https://en.wikipedia.org/w/api.php"
        try:
            logger.info(f"Searching Wikipedia for keyword: {keyword}")
            search_params = {"action": "opensearch", "namespace": 0, "search": keyword, "limit": 1, "format": "json"}
            search_response = self.session.get(WIKI_URL, params=search_params, timeout=timeout)
            search_response.raise_for_status()
            search_data = search_response.json()
            if not search_data[1]:
                logger.warning(f"No Wikipedia articles found for keyword: {keyword}")
                return None
            title = search_data[1][0]
            logger.info(f"Found Wikipedia article: {title}")
            content_params = {"action": "query", "format": "json", "prop": "extracts", "explaintext": True, "titles": title}
            content_response = self.session.get(WIKI_URL, params=content_params, timeout=timeout)
            content_response.raise_for_status()
            content_data = content_response.json()
            pages = content_data["query"]["pages"]
            content = next(iter(pages.values()), {}).get("extract", "")
            if content:
                logger.info(f"Retrieved Wikipedia content, length: {len(content)}")
                return content
            else:
                logger.warning(f"No content extracted from Wikipedia for: {keyword}")
                return None
        except Exception as e:
            logger.error(f"Error during Wikipedia search: {str(e)}")
            return None

    def search_duckduckgo_instant(self, keyword: str, timeout: int = 10) -> Optional[Dict[str, str]]:
        """Search DuckDuckGo Instant Answer API."""
        try:
            logger.info(f"Searching DuckDuckGo for keyword: {keyword}")
            url = "https://api.duckduckgo.com/"
            params = {'q': keyword, 'format': 'json', 'no_redirect': '1', 'no_html': '1'}
            response = self.session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            if data.get('Abstract'):
                return {'title': data.get('Heading', keyword), 'extract': data.get('Abstract', ''), 'source': data.get('AbstractSource', 'DuckDuckGo')}
            if data.get('Definition'):
                return {'title': keyword, 'extract': data.get('Definition', ''), 'source': data.get('DefinitionSource', 'DuckDuckGo')}
            logger.warning(f"No relevant content found in DuckDuckGo for: {keyword}")
            return None
        except Exception as e:
            logger.error(f"Error during DuckDuckGo search: {str(e)}")
            return None

    def _get_content_from_keyword(self, keyword: str) -> str:
        """Helper to retrieve content by searching a keyword."""
        raw_content = ""
        # Try Wikipedia first
        raw_content = self.search_wikipedia(keyword)
        # Fallback to DuckDuckGo
        if not raw_content:
            ddg_result = self.search_duckduckgo_instant(keyword)
            if ddg_result:
                raw_content = ddg_result.get('extract', '')
        return raw_content or ""

    def generate_summary(self, source_text: str, topic_hint: str) -> str:
        """
        Generates an AI summary for the given text.

        ## Enhancement: This method now focuses only on AI generation with an improved prompt.
        
        Args:
            source_text (str): The text content to be summarized.
            topic_hint (str): A hint about the topic (e.g., the keyword or URL).

        Returns:
            str: The generated summary or a fallback message.
        """
        cleaned_content = clean_data(source_text)
        
        if not cleaned_content or len(cleaned_content.strip()) < 50:
            logger.warning(f"Content for '{topic_hint}' is too short after cleaning.")
            return f"Sorry, the provided content for '{topic_hint}' was not substantial enough to summarize."

        try:
            logger.info(f"Generating AI summary for topic: {topic_hint}")
            prompt = f"""Summarize the following content about '{topic_hint}'.
            Provide a clear, professional, and concise summary in well-structured plain text.
            Do not use any markdown formatting (like *, #, or lists).
            Focus on the key facts and main points. The summary should be 2-3 paragraphs long, around 500 words (don't exceede this limit).

            Content to summarize:
            ---
            {cleaned_content}
            ---
            """
            
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=500,
                    temperature=0.3,
                )
            )
            
            if response and hasattr(response, 'text') and response.text:
                summary = clean_data(response.text)
                if summary:
                    logger.info(f"Successfully generated summary for: {topic_hint}")
                    return summary
            
            logger.warning("AI generated an empty or invalid summary.")
            # Fallback if AI fails
            return cleaned_content

        except Exception as e:
            logger.error(f"Error generating summary with AI model: {str(e)}")
            return "An error occurred while generating the summary. Please try again later."


# Initialize the RAG processor instance
rag_processor = RAGProcessor()


## Routes to handle the post requests
@app.route("/summarize", methods=['POST'])
def summarize_content():
    """
    REST API endpoint to generate summaries from a keyword, URL, or direct content.
    
    The endpoint prioritizes input in the following order: content > url > keyword.
    
    Request Format (provide ONE of the keys):
        {
            "content": "Text to summarize directly...",
            "url": "https://example.com/article",
            "keyword": "artificial intelligence"
        }
    
    Response Format:
        {
            "summary": "AI-generated summary text",
            "source": "type of input (e.g., 'direct content', 'https://...')"
            "status": "success"
        }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided", "status": "error"}), 400

        content_to_summarize = ""
        source_identifier = ""

        # 1. Prioritize direct content
        if 'content' in data and isinstance(data['content'], str) and data['content'].strip():
            content_to_summarize = data['content']
            source_identifier = "direct content"
            logger.info("Processing request with direct content.")

        # 2. Else, check for URL
        elif 'url' in data and isinstance(data['url'], str) and data['url'].strip():
            url = data['url']
            # Basic URL validation
            if not re.match(r'^https?://', url):
                return jsonify({"error": "Invalid URL format provided", "status": "error"}), 400
            
            source_identifier = url
            content_to_summarize = rag_processor.scrape_url_content(url)
            if not content_to_summarize:
                return jsonify({"error": f"Failed to retrieve content from URL: {url}", "status": "error"}), 400
            logger.info(f"Processing request with URL: {url}")

        # 3. Else, fall back to keyword
        elif 'keyword' in data and isinstance(data['keyword'], str) and data['keyword'].strip():
            keyword = data['keyword'].strip()
            if len(keyword) > 200:
                return jsonify({"error": "Keyword is too long (max 200 chars)", "status": "error"}), 400
            
            source_identifier = keyword
            content_to_summarize = rag_processor._get_content_from_keyword(keyword)
            if not content_to_summarize:
                 return jsonify({"error": f"Could not find any information for the keyword: '{keyword}'", "status": "error"}), 404
            logger.info(f"Processing request with keyword: {keyword}")

        # If no valid input was found
        else:
            return jsonify({
                "error": "Request must contain a non-empty 'content', 'url', or 'keyword' field.",
                "status": "error"
            }), 400

        # Generate summary from the obtained content
        summary = rag_processor.generate_summary(content_to_summarize, source_identifier)
        
        response_data = {
            "source": source_identifier,
            "summary": summary,
            "status": "success"
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in summarize_content endpoint: {str(e)}")
        return jsonify({"error": "Internal server error", "status": "error"}), 500


@app.route("/health", methods=['GET'])
def health_check():
    """Health check endpoint to verify API availability."""
    return jsonify({
        "status": "healthy",
        "service": "RAG Content Summarizer",
        "version": "2.0.0"
    }), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors with a JSON response."""
    return jsonify({
        "error": "Endpoint not found",
        "status": "error",
        "available_endpoints": ["/summarize (POST)", "/health (GET)"]
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 Method Not Allowed errors."""
    return jsonify({"error": "Method not allowed for this endpoint", "status": "error"}), 405


if __name__ == "__main__":
    logger.info("Starting Flask RAG Application v2.0.0")
    logger.info("Available endpoints:")
    logger.info("  POST /summarize - Generate summary from keyword, URL, or content")
    logger.info("  GET /health - Health check")
    
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )
