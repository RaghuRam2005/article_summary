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
from flask_cors import CORS
from dotenv import load_dotenv
from google import genai
from google.genai import types
import requests
import os
import re
import logging
from urllib.parse import urlparse
from typing import Optional, Dict, Any, List

from db import init_db
from auth import auth_bp
from history import history_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# search/scraper read env vars (e.g. TAVILY_API_KEY) at import time, so they
# must be imported only after load_dotenv() has run
import search
import scraper

# Initialize Flask application
app = Flask(__name__)

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    logger.error("SECRET_KEY environment variable not found")
    raise ValueError("SECRET_KEY environment variable is required")
app.secret_key = SECRET_KEY

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
CORS(app, supports_credentials=True, origins=[FRONTEND_ORIGIN])

init_db()
app.register_blueprint(auth_bp)
app.register_blueprint(history_bp)

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


def _build_multi_source_prompt(prepared_sources: List[Dict[str, Any]], topic_hint: str) -> str:
    """Build the summarization prompt from multiple labeled, cleaned sources.

    Each source is attributed to its domain and the model is explicitly
    instructed to synthesize a neutral view and flag disagreement rather than
    adopt any single source's framing -- the prompt-level half of the app's
    bias-mitigation approach (the other half is the domain-diversity cap
    applied in RAGProcessor.gather_keyword_sources)."""
    source_blocks = "\n\n".join(
        f"[Source {s['index']} - {s['domain']}]\n{s['text']}"
        for s in prepared_sources
    )
    return f"""Summarize the following information about '{topic_hint}', gathered from {len(prepared_sources)} different source(s).

Each source below is labeled with the domain it came from. Sources may disagree with each other or frame the topic differently.

Instructions:
- Write a neutral, balanced summary that synthesizes the facts common across sources.
- Do not adopt the tone, framing, or conclusions of any single source as though it were the only viewpoint.
- If sources disagree on facts, figures, or framing, briefly note the disagreement (e.g. "some sources report X, while others report Y") instead of silently picking one side.
- If a claim appears in only one source and seems one-sided, attribute it to that source rather than stating it as settled fact.
- Do not use any markdown formatting (like *, #, or lists).
- The summary should be 2-3 paragraphs, around 500 words, and must not exceed this limit.

Sources:
---
{source_blocks}
---
"""


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
        Extract the main textual content from a given URL.

        Delegates to scraper.scrape_one, which tries a static fetch, then
        structured-data/tag extraction, then falls back to Tavily's /extract
        API for pages that turn out to be JS-rendered shells.

        Args:
            url (str): The URL to scrape.
            timeout (int, optional): Request timeout in seconds. Defaults to 15.

        Returns:
            Optional[str]: The extracted text content, or None on failure.
        """
        return scraper.scrape_one(url, timeout=timeout).get("text")

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
        """Legacy helper to retrieve content by searching a keyword via
        Wikipedia/DuckDuckGo. Kept as the fallback path for gather_keyword_sources
        when Tavily returns no results (e.g. API outage or rate limit)."""
        raw_content = ""
        # Try Wikipedia first
        raw_content = self.search_wikipedia(keyword)
        # Fallback to DuckDuckGo
        if not raw_content:
            ddg_result = self.search_duckduckgo_instant(keyword)
            if ddg_result:
                raw_content = ddg_result.get('extract', '')
        return raw_content or ""

    def gather_keyword_sources(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Retrieve multiple, domain-diverse sources for a keyword query.

        Uses Tavily's real web/news search so current events resolve, then caps
        how many results come from the same domain (the bias-mitigation lever)
        before handing the content straight to the summarizer -- Tavily already
        fetched/extracted each result server-side, so no scraping happens here.

        Falls back to the legacy Wikipedia/DuckDuckGo lookup (as a single
        source) if Tavily returns nothing.

        Returns a list of {"url", "domain", "title", "text"} dicts.
        """
        results = search.tavily_search(keyword)
        if not results:
            logger.warning(f"Tavily returned no results for '{keyword}', falling back to legacy search.")
            legacy_content = self._get_content_from_keyword(keyword)
            if not legacy_content:
                return []
            return [{"url": None, "domain": "wikipedia/duckduckgo", "title": keyword, "text": legacy_content}]

        diverse_results = search.select_diverse_results(results)
        sources = []
        for result in diverse_results:
            text = result.get("raw_content") or result.get("content") or ""
            if len(text.strip()) >= 50:
                sources.append({
                    "url": result.get("url"),
                    "domain": result.get("domain"),
                    "title": result.get("title"),
                    "text": text,
                })
        return sources

    def generate_summary(self, sources: List[Dict[str, Any]], topic_hint: str) -> str:
        """
        Generates an AI summary synthesized across one or more sources.

        Args:
            sources (List[Dict[str, Any]]): Each dict has at least a "text" key
                and, when known, a "domain" key used to attribute claims in the
                prompt so the model doesn't adopt a single source's framing.
            topic_hint (str): A hint about the topic (e.g., the keyword or URL).

        Returns:
            str: The generated summary or a fallback message.
        """
        prepared_sources = []
        for source in sources:
            cleaned = clean_data(source.get("text", ""))
            if cleaned and len(cleaned.strip()) >= 50:
                prepared_sources.append({
                    "domain": source.get("domain") or "user-provided",
                    "text": cleaned[:4000],
                })

        if not prepared_sources:
            logger.warning(f"Content for '{topic_hint}' is too short after cleaning.")
            return f"Sorry, the provided content for '{topic_hint}' was not substantial enough to summarize."

        for index, source in enumerate(prepared_sources, start=1):
            source["index"] = index

        try:
            logger.info(f"Generating AI summary for topic: {topic_hint} from {len(prepared_sources)} source(s)")
            prompt = _build_multi_source_prompt(prepared_sources, topic_hint)

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
            # Fallback if AI fails: return the first source's cleaned text
            return prepared_sources[0]["text"]

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

        sources: list = []
        source_identifier = ""

        # 1. Prioritize direct content
        if 'content' in data and isinstance(data['content'], str) and data['content'].strip():
            source_identifier = "direct content"
            sources = [{"url": None, "domain": "user-provided", "title": None, "text": data['content']}]
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
            sources = [{"url": url, "domain": urlparse(url).netloc, "title": None, "text": content_to_summarize}]
            logger.info(f"Processing request with URL: {url}")

        # 3. Else, fall back to keyword
        elif 'keyword' in data and isinstance(data['keyword'], str) and data['keyword'].strip():
            keyword = data['keyword'].strip()
            if len(keyword) > 200:
                return jsonify({"error": "Keyword is too long (max 200 chars)", "status": "error"}), 400

            source_identifier = keyword
            sources = rag_processor.gather_keyword_sources(keyword)
            if not sources:
                 return jsonify({"error": f"Could not find any information for the keyword: '{keyword}'", "status": "error"}), 404
            logger.info(f"Processing request with keyword: {keyword} ({len(sources)} source(s))")

        # If no valid input was found
        else:
            return jsonify({
                "error": "Request must contain a non-empty 'content', 'url', or 'keyword' field.",
                "status": "error"
            }), 400

        # Generate summary from the obtained source(s)
        summary = rag_processor.generate_summary(sources, source_identifier)

        response_data = {
            "source": source_identifier,
            "summary": summary,
            "sources": [{"url": s["url"], "domain": s["domain"]} for s in sources],
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

    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(
        debug=debug_mode,
        host="0.0.0.0",
        port=5000
    )
