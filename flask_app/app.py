"""
Flask RAG (Retrieval-Augmented Generation) Application

This application provides a REST API endpoint for generating summaries from various sources:
- Keywords (via Wikipedia/DuckDuckGo)
- Web page URLs
- Direct text content

Author: RaghuRam2005
Version: 2.1.0
Dependencies: flask, python-dotenv, google-genai, requests, beautifulsoup4
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from google import genai
from google.genai import types
import requests
from bs4 import BeautifulSoup
import os
import re
import newspaper
import trafilatura
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
CORS(app)

# Load environment variables from .env file
load_dotenv()

# Initialize Gemini AI client
GEMINI_API = os.getenv("GEMINI_API")
if not GEMINI_API:
    logger.error("GEMINI_API environment variable not found")
    raise ValueError("GEMINI_API environment variable is required")

client = genai.Client(api_key=GEMINI_API)


class ContentExtractor:
    """
    Content Extractor using multiple libraries
    """
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        logger.info("ContentExtractor initialized successfully")

    def extract_with_newspaper(self, url: str) -> Dict[str, Any]:
        """Extract content using newspaper3k library."""
        try:
            article = newspaper.Article(url)
            article.download()
            article.parse()
            
            return {
                'title': article.title or '',
                'text': article.text or '',
                'authors': article.authors or [],
                'publish_date': str(article.publish_date) if article.publish_date else '',
                'summary': article.summary or '',
                'keywords': article.keywords or [],
                'meta_keywords': article.meta_keywords or [],
                'meta_description': article.meta_description or '',
                'top_image': article.top_image or '',
                'images': list(article.images) or [],
                'movies': list(article.movies) or [],
                'source_url': url
            }
        except Exception as e:
            logger.error(f"Newspaper extraction failed for {url}: {str(e)}")
            return {}

    def extract_with_trafilatura(self, url: str) -> Dict[str, Any]:
        """Extract content using trafilatura library."""
        try:
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return {}
            
            # Extract main content
            text = trafilatura.extract(downloaded)
            
            # Extract metadata
            metadata = trafilatura.extract_metadata(downloaded)
            
            return {
                'title': metadata.title if metadata and metadata.title else '',
                'text': text or '',
                'author': metadata.author if metadata and metadata.author else '',
                'date': metadata.date if metadata and metadata.date else '',
                'description': metadata.description if metadata and metadata.description else '',
                'sitename': metadata.sitename if metadata and metadata.sitename else '',
                'source_url': url
            }
        except Exception as e:
            logger.error(f"Trafilatura extraction failed for {url}: {str(e)}")
            return {}

    def extract_with_beautifulsoup(self, url: str) -> Dict[str, Any]:
        """Fallback extraction using BeautifulSoup with enhanced selectors."""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'sidebar', 'aside', 'advertisement']):
                element.decompose()

            # Extract title
            title = ''
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
            
            # Try multiple selectors for main content
            content_selectors = [
                'article',
                '[role="main"]',
                '.main-content',
                '.content',
                '.post-content',
                '.entry-content',
                '#content',
                '.article-body',
                '.story-body'
            ]
            
            main_content = ''
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    main_content = content_elem.get_text()
                    break
            
            # Fallback to all paragraphs if no main content found
            if not main_content:
                paragraphs = soup.find_all('p')
                main_content = '\n'.join([p.get_text() for p in paragraphs])

            # Extract meta description
            meta_desc = ''
            meta_tag = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
            if meta_tag:
                meta_desc = meta_tag.get('content', '')

            return {
                'title': title,
                'text': main_content,
                'description': meta_desc,
                'source_url': url
            }
            
        except Exception as e:
            logger.error(f"BeautifulSoup extraction failed for {url}: {str(e)}")
            return {}

    def extract_content(self, url: str) -> Dict[str, Any]:
        """Extract content using multiple methods with fallbacks."""
        logger.info(f"Extracting content from: {url}")
        
        # Try newspaper3k first (best for articles)
        content = self.extract_with_newspaper(url)
        if content.get('text') and len(content['text'].strip()) > 100:
            logger.info("Successfully extracted content using newspaper3k")
            return content
        
        # Try trafilatura as fallback
        content = self.extract_with_trafilatura(url)
        if content.get('text') and len(content['text'].strip()) > 100:
            logger.info("Successfully extracted content using trafilatura")
            return content
        
        # Use BeautifulSoup as final fallback
        content = self.extract_with_beautifulsoup(url)
        if content.get('text') and len(content['text'].strip()) > 50:
            logger.info("Successfully extracted content using BeautifulSoup")
            return content
        
        # If all methods fail but we have title/description, return that
        if content.get('title') or content.get('description'):
            logger.warning(f"Limited content extracted for {url}, using title/description")
            fallback_text = f"Title: {content.get('title', 'N/A')}\nDescription: {content.get('description', 'N/A')}"
            content['text'] = fallback_text
            return content
        
        logger.error(f"Failed to extract meaningful content from {url}")
        return {}


class RAGProcessor:
    """
    This class handles retrieving content from multiple sources (Wikipedia, DuckDuckGo, URLs)
    and generating AI-powered summaries.
    """
    
    def __init__(self):
        self.content_extractor = ContentExtractor()
        logger.info("RAGProcessor initialized successfully")

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

    def search_duckduckgo_instant(self, keyword: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """Search DuckDuckGo Instant Answer API."""
        try:
            logger.info(f"Searching DuckDuckGo for keyword: {keyword}")
            url = "https://api.duckduckgo.com/"
            params = {
                'q': keyword, 
                'format': 'json', 
                'no_redirect': '1', 
                'no_html': '1'
            }
            
            session = requests.Session()
            response = session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            
            # Check for abstract
            if data.get('Abstract'):
                return {
                    'title': data.get('Heading', keyword),
                    'text': data.get('Abstract', ''),
                    'source_url': data.get('AbstractURL', ''),
                    'source_name': data.get('AbstractSource', 'DuckDuckGo'),
                    'description': f"Information about {keyword}"
                }
            
            # Check for definition
            if data.get('Definition'):
                return {
                    'title': keyword,
                    'text': data.get('Definition', ''),
                    'source_url': data.get('DefinitionURL', ''),
                    'source_name': data.get('DefinitionSource', 'DuckDuckGo'),
                    'description': f"Definition of {keyword}"
                }
            
            logger.warning(f"No relevant content found in DuckDuckGo for: {keyword}")
            return None
            
        except Exception as e:
            logger.error(f"Error during DuckDuckGo search: {str(e)}")
            return None
    
    def get_content_from_keyword(self, keyword: str) -> Optional[Dict[str, Any]]:
        """Retrieve content by searching a keyword."""
        # Try Wikipedia first
        content = self.search_wikipedia(keyword)
        if content:
            return content
        
        # Fallback to DuckDuckGo
        content = self.search_duckduckgo_instant(keyword)
        return content
    
    def get_content_from_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract content from URL."""
        return self.content_extractor.extract_content(url)
    
    def generate_enhanced_summary(self, content_data: Dict[str, Any], query_hint: str, content_type: str) -> str:
        """
        Generate markdown summary with sources using AI.
        
        Args:
            content_data: Dictionary containing extracted content and metadata
            query_hint: The original query (keyword, URL, or content hint)
            content_type: Type of content ('keyword', 'url', 'content')
        
        Returns:
            Markdown formatted summary with sources
        """
        try:
            # Prepare content for AI processing
            main_text = content_data.get('text', '')
            title = content_data.get('title', '')
            description = content_data.get('description', '')
            source_url = content_data.get('source_url', '')
            source_name = content_data.get('source_name', 'Unknown Source')
            
            # If we have very little content, generate based on title and description
            if len(main_text.strip()) < 100:
                if title or description:
                    logger.info(f"Generating summary from limited content for: {query_hint}")
                    limited_content = f"Title: {title}\nDescription: {description}"
                    main_text = limited_content
                else:
                    return f"**Unable to generate summary**\n\nInsufficient content available for '{query_hint}'. Please try a different source or provide more detailed information."

            # Prompt for gemini API
            prompt = f"""You are an expert content analyst. Create a comprehensive, well-structured summary in markdown format.

**Query:** {query_hint}
**Content Type:** {content_type}
**Source:** {source_name}

**Instructions:**
1. Create a detailed, informative summary (aim for 800-1200 words)
2. Use proper markdown formatting with headers, lists, and emphasis
3. Structure the content with clear sections using ## headers
4. Include key facts, important details, and main points
5. Add a "Sources" section at the end with proper citations
6. Make it engaging and comprehensive like a Perplexity AI response
7. If the content is limited, use your knowledge to expand on the topic while clearly indicating what comes from the source vs general knowledge

**Content to analyze:**
---
Title: {title}
Description: {description}
Main Content: {main_text[:4000]}  # Limit to avoid token overflow
---

Please provide a thorough, markdown-formatted summary:"""

            logger.info(f"Generating enhanced AI summary for: {query_hint}")
            
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                )
            )
            
            if response and hasattr(response, 'text') and response.text:
                summary = response.text.strip()
                
                # Add source information if not already included
                if source_url and "## Sources" not in summary and "## References" not in summary:
                    summary += f"\n\n## Sources\n\n- [{source_name}]({source_url})"
                elif source_name and not source_url:
                    summary += f"\n\n## Sources\n\n- {source_name}"
                
                logger.info(f"Successfully generated enhanced summary for: {query_hint}")
                return summary
            
            logger.warning("AI generated empty response")
            return f"**Summary Generation Error**\n\nUnable to generate summary for '{query_hint}'. Please try again."
            
        except Exception as e:
            logger.error(f"Error generating enhanced summary: {str(e)}")
            return f"**Error**\n\nAn error occurred while generating the summary for '{query_hint}': {str(e)}"


# Initialize the RAG processor instance
rag_processor = RAGProcessor()


@app.route("/summarize", methods=['POST'])
def summarize_content():
    """
    Enhanced REST API endpoint to generate comprehensive markdown summaries with sources.
    
    Request Format (provide ONE of the keys):
        {
            "content": "Text to summarize directly...",
            "url": "https://example.com/article",
            "keyword": "artificial intelligence"
        }
    
    Response Format:
        {
            "summary": "Markdown-formatted comprehensive summary with sources",
            "source": "source information",
            "content_type": "direct content|url|keyword",
            "metadata": {
                "title": "extracted title",
                "source_url": "source URL if applicable",
                "word_count": "approximate word count"
            },
            "status": "success"
        }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided", "status": "error"}), 400

        content_data = None
        source_identifier = ""
        content_type = ""

        # 1. Prioritize direct content
        if 'content' in data and isinstance(data['content'], str) and data['content'].strip():
            text_content = data['content'].strip()
            content_data = {
                'text': text_content,
                'title': 'Direct Content',
                'description': 'User-provided content',
                'source_name': 'Direct Input',
                'source_url': ''
            }
            source_identifier = "direct content"
            content_type = "content"
            logger.info("Processing request with direct content.")

        # 2. Check for URL
        elif 'url' in data and isinstance(data['url'], str) and data['url'].strip():
            url = data['url'].strip()
            
            # Basic URL validation
            if not re.match(r'^https?://', url):
                return jsonify({"error": "Invalid URL format provided", "status": "error"}), 400
            
            content_data = rag_processor.get_content_from_url(url)
            if not content_data:
                return jsonify({
                    "error": f"Failed to extract content from URL: {url}",
                    "status": "error"
                }), 400
            
            source_identifier = url
            content_type = "url"
            logger.info(f"Processing request with URL: {url}")

        # 3. Fall back to keyword
        elif 'keyword' in data and isinstance(data['keyword'], str) and data['keyword'].strip():
            keyword = data['keyword'].strip()
            
            if len(keyword) > 200:
                return jsonify({"error": "Keyword is too long (max 200 chars)", "status": "error"}), 400
            
            content_data = rag_processor.get_content_from_keyword(keyword)
            if not content_data:
                return jsonify({
                    "error": f"Could not find any information for the keyword: '{keyword}'",
                    "status": "error"
                }), 404
            
            source_identifier = keyword
            content_type = "keyword"
            logger.info(f"Processing request with keyword: {keyword}")

        else:
            return jsonify({
                "error": "Request must contain a non-empty 'content', 'url', or 'keyword' field.",
                "status": "error"
            }), 400

        # Generate comprehensive markdown summary
        summary = rag_processor.generate_enhanced_summary(content_data, source_identifier, content_type)
        
        # Prepare metadata
        metadata = {
            "title": content_data.get('title', ''),
            "source_url": content_data.get('source_url', ''),
            "source_name": content_data.get('source_name', ''),
            "word_count": len(summary.split()) if summary else 0
        }
        
        response_data = {
            "summary": summary,
            "source": source_identifier,
            "content_type": content_type,
            "metadata": metadata,
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
        "service": "Enhanced RAG Content Summarizer",
        "version": "3.0.0",
        "features": [
            "Enhanced content extraction",
            "Markdown formatted summaries",
            "Source citations",
            "Multiple extraction methods",
            "Comprehensive AI summaries"
        ]
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
    logger.info("Starting Enhanced Flask RAG Application v3.0.0")
    logger.info("New features:")
    logger.info("  - Enhanced content extraction with multiple methods")
    logger.info("  - Comprehensive markdown summaries")
    logger.info("  - Source citations like Perplexity")
    logger.info("  - Improved handling of limited content")
    logger.info("  - No token limits for full summaries")
    logger.info("Available endpoints:")
    logger.info("  POST /summarize - Generate comprehensive summary with sources")
    logger.info("  GET /health - Health check")
    
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )
