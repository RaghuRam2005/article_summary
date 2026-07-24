"""Tavily-backed web search, domain-diversity selection, and single-URL extraction."""

import os
import logging
from urllib.parse import urlparse
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()  # safe/idempotent even though app.py also calls it

logger = logging.getLogger(__name__)

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    logger.error("TAVILY_API_KEY environment variable not found")
    raise ValueError("TAVILY_API_KEY environment variable is required")

TAVILY_SEARCH_URL = "https://api.tavily.com/search"
TAVILY_EXTRACT_URL = "https://api.tavily.com/extract"

TAVILY_MAX_RESULTS = 8   # over-fetch so the diversity filter has choices
MAX_SOURCES = 5          # final number of sources fed to the summarizer
MAX_PER_DOMAIN = 2       # bias-mitigation cap: no single outlet dominates


def _normalize_domain(url: str) -> str:
    netloc = urlparse(url).netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


def tavily_search(query: str, max_results: int = TAVILY_MAX_RESULTS, timeout: int = 10) -> List[Dict[str, Any]]:
    """
    Query Tavily's /search endpoint for real, current web/news results.

    Requests include_raw_content=True so each result carries Tavily's own fuller
    extracted text (already fetched and rendered server-side on Tavily's end) --
    this is what lets the keyword path skip scraping entirely.

    Returns a relevance-ranked list of {"url", "title", "content", "raw_content"}
    dicts. Never raises: returns [] on any network error, non-2xx response, or
    malformed JSON, so callers can fall back to the legacy Wikipedia/DDG path.
    """
    try:
        logger.info(f"Searching Tavily for query: {query}")
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "max_results": max_results,
            "include_raw_content": True,
        }
        response = requests.post(TAVILY_SEARCH_URL, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        logger.info(f"Tavily returned {len(results)} result(s) for: {query}")
        return results
    except requests.RequestException as e:
        logger.error(f"HTTP error during Tavily search for '{query}': {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error during Tavily search for '{query}': {str(e)}")
        return []


def select_diverse_results(
    results: List[Dict[str, Any]],
    max_sources: int = MAX_SOURCES,
    max_per_domain: int = MAX_PER_DOMAIN,
) -> List[Dict[str, Any]]:
    """
    Walk `results` in the order Tavily returned them (already relevance-ranked),
    keeping at most `max_per_domain` results per registrable domain, stopping
    once `max_sources` are collected. Adds a "domain" key to each kept result.

    This is the core bias-mitigation lever: it structurally prevents one
    outlet's framing from dominating the source set fed to the summarizer.
    """
    selected: List[Dict[str, Any]] = []
    per_domain_count: Dict[str, int] = {}

    for result in results:
        if len(selected) >= max_sources:
            break
        url = result.get("url", "")
        if not url:
            continue
        domain = _normalize_domain(url)
        if per_domain_count.get(domain, 0) >= max_per_domain:
            continue
        per_domain_count[domain] = per_domain_count.get(domain, 0) + 1
        selected.append({**result, "domain": domain})

    return selected


def tavily_extract(url: str, timeout: int = 15) -> Optional[str]:
    """
    Extract clean content from a single URL via Tavily's /extract endpoint.

    This is Tavily's server-side extraction (handles JS-rendered pages on their
    own infrastructure) -- used only as the last-resort fallback for the
    direct-URL input path, so the app never needs to run a local browser.

    Returns the extracted raw content, or None on failure/empty result.
    """
    try:
        logger.info(f"Requesting Tavily extract for URL: {url}")
        payload = {"api_key": TAVILY_API_KEY, "urls": [url]}
        response = requests.post(TAVILY_EXTRACT_URL, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        if not results:
            logger.warning(f"Tavily extract returned no results for: {url}")
            return None
        content = results[0].get("raw_content")
        if content:
            logger.info(f"Tavily extract succeeded for {url}, length: {len(content)}")
            return content
        return None
    except requests.RequestException as e:
        logger.error(f"HTTP error during Tavily extract for {url}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during Tavily extract for {url}: {str(e)}")
        return None
