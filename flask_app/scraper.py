"""Single-URL content extraction: static fetch, structured-data parse, tag
fallback, and a Tavily-extract escalation for pages that turn out to be
JS-rendered shells. Used only by the direct-URL /summarize input path -- the
keyword path gets its content straight from Tavily's search results and never
scrapes anything itself.
"""

import json
import logging
from typing import Any, Dict, Optional

import requests
from bs4 import BeautifulSoup

import search

logger = logging.getLogger(__name__)

USER_AGENT = "RAG-Processor/2.0 (Educational Purpose)"
STATIC_TIMEOUT = 15
MIN_CHARS = 400  # below this, escalate to the next extraction strategy

_session = requests.Session()
_session.headers.update({"User-Agent": USER_AGENT})


def fetch_html_static(url: str, timeout: int = STATIC_TIMEOUT) -> Optional[str]:
    """Plain GET for the page HTML, or None on any request failure."""
    try:
        logger.info(f"Fetching HTML for: {url}")
        response = _session.get(url, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f"HTTP error fetching {url}: {str(e)}")
        return None


def _text_from_json_ld(soup: BeautifulSoup) -> Optional[str]:
    for tag in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(tag.string or "")
        except (TypeError, ValueError):
            continue

        candidates = data if isinstance(data, list) else [data]
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            types_field = candidate.get("@type", "")
            types_list = types_field if isinstance(types_field, list) else [types_field]
            if any(t in ("Article", "NewsArticle", "BlogPosting") for t in types_list):
                body = candidate.get("articleBody") or candidate.get("description")
                if body:
                    return body
    return None


def _text_from_framework_state(soup: BeautifulSoup) -> Optional[str]:
    for tag_id in ("__NEXT_DATA__", "__NUXT_DATA__"):
        tag = soup.find("script", {"id": tag_id})
        if not tag or not tag.string:
            continue
        try:
            data = json.loads(tag.string)
        except ValueError:
            continue

        best: Optional[str] = None

        def _walk(node: Any) -> None:
            nonlocal best
            if isinstance(node, dict):
                for key, value in node.items():
                    if key in ("articleBody", "body", "content") and isinstance(value, str):
                        if best is None or len(value) > len(best):
                            best = value
                    else:
                        _walk(value)
            elif isinstance(node, list):
                for item in node:
                    _walk(item)

        _walk(data)
        if best:
            return best
    return None


def extract_structured_data(html: str) -> Optional[str]:
    """
    Look for embedded JSON that already contains the article body, even on
    pages that visually render client-side: schema.org Article/NewsArticle
    JSON-LD (articleBody/description), or a Next.js/Nuxt state blob
    (__NEXT_DATA__/__NUXT_DATA__) with an articleBody/body/content field.

    Free, no rendering -- catches most SSR JS-framework sites that ship real
    content in the initial HTML despite drawing the page client-side. Returns
    None if nothing usable is found.
    """
    soup = BeautifulSoup(html, "html.parser")
    return _text_from_json_ld(soup) or _text_from_framework_state(soup)


def extract_tags(html: str) -> str:
    """
    Tag-based fallback, lifted from the original scrape_url_content: prefer
    <article> text, fall back to p/h1/h2/h3 tags, fall back to full page text.
    """
    soup = BeautifulSoup(html, "html.parser")
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()

    if soup.article:
        text = soup.article.get_text()
    else:
        tags = soup.find_all(["p", "h1", "h2", "h3"])
        text = "\n".join(tag.get_text() for tag in tags)

    if not text:
        text = soup.get_text()

    return text


def scrape_one(url: str, timeout: int = STATIC_TIMEOUT) -> Dict[str, Any]:
    """
    Extract content for a single URL, escalating strategies only as needed:
      1. Static fetch. If the fetch itself fails, go straight to Tavily extract.
      2. Structured-data parse (JSON-LD / framework state blobs).
      3. Tag-based extraction.
      4. If both (2) and (3) are too thin, fall back to Tavily's /extract API,
         which handles JS-rendered pages on Tavily's own infrastructure.

    Returns {"url", "text": Optional[str], "method": "structured"|"tags"|
    "tavily_extract"|"failed"}, keeping whichever candidate text is longest
    among the attempts that produced something.
    """
    html = fetch_html_static(url, timeout=timeout)
    if html is None:
        text = search.tavily_extract(url)
        return {"url": url, "text": text, "method": "tavily_extract" if text else "failed"}

    best_text = ""
    best_method = "failed"

    structured_text = extract_structured_data(html)
    if structured_text and len(structured_text) > len(best_text):
        best_text, best_method = structured_text, "structured"

    tag_text = extract_tags(html)
    if tag_text and len(tag_text) > len(best_text):
        best_text, best_method = tag_text, "tags"

    if len(best_text) < MIN_CHARS:
        extracted = search.tavily_extract(url)
        if extracted and len(extracted) > len(best_text):
            best_text, best_method = extracted, "tavily_extract"

    if not best_text:
        return {"url": url, "text": None, "method": "failed"}

    logger.info(f"Scraped {url} via '{best_method}', length: {len(best_text)}")
    return {"url": url, "text": best_text, "method": best_method}
