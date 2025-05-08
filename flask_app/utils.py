import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from googlesearch import search
import google.generativeai as genai
from urllib.parse import urlparse
from sentence_transformers import SentenceTransformer, util
import urllib3

# Disables SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load API keys from environment variables
load_dotenv()
GEMINI_API = os.getenv("GEMINI")
if GEMINI_API:
    print("yes")
else:
    print("None")
genai.configure(api_key=GEMINI_API)
print(GEMINI_API)

def get_embeddings(query):
    """
    Generate the word embeddings for query using a pretrained model

    Args:
        query (str): this is the input given by user

    Returns:
        list: list of word embedding values for the given query
    """
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embedding = model.encode(query, conver_to_tensor=True)
    return embedding

def is_similar(query_embed, other_embed):
    """
    checks if the given two word embeddings are similar or not
    using cosine similarity function

    Args:
        query_embed (list): query given by the user
        other_embed (list): embedding history stored in cache

    Returns:
        _type_: returns True if both are similar False otherwise
    """
    cosine_sim = util.cos_sim(query_embed, other_embed)
    threshold = 0.8
    if cosine_sim > threshold:
        return True
    else:
        return False

def is_valid_url(url):
    """
    checks if URL is likely to contain valid content

    Args:
        url (str): The URL of the website to check

    Returns:
        bool: True, if URL is valid and False, if the URL is not valid
    """
    parsed = urlparse(url)
    path = parsed.path.lower()
    query = parsed.query.lower()

    # Common patterns in error pages
    invalid_patterns = [
        '/search', 'search=', 'results',
        'error', '404', 'notfound', 'redirect'
    ]

    # check path and query parameters
    if any(pattern in path or pattern in query for pattern in invalid_patterns):
        return False
    
    # if the path is too low (eg:homepage)
    if len(path.split('/')) < 3:
        return False
        
    return True


def search_articles(query):
    """
    Searches Google for articles related to the query and returns a list of articles

    Args:
        query (str): User queried topic

    Returns:
        list : contains list or valid URL's
    """
    articles = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    try:
        results = search(query, advanced=True, num_results=15)
    except Exception as e:
        print(f"Google search failed: {e}")
        return []
    
    for result in results:
        try:
            # Use HEAD request first to check status without downloading body
            response = requests.head(
                result.url, 
                headers=headers, 
                timeout=10, 
                allow_redirects=True,
                verify=False  # SSL verification disabled
            )
            
            # Check final URL after redirects
            final_url = response.url
            
            if (response.status_code == 200 
                and is_valid_url(final_url)
                and final_url not in articles):
                
                # Optional: Verify with GET request for content validation
                content_response = requests.get(
                    final_url,
                    headers=headers,
                    timeout=15,
                    verify=False
                )
                
                # Basic content validation
                if content_response.status_code == 200:
                    articles.append(final_url)
                    
        except requests.exceptions.RequestException:
            continue
        except KeyboardInterrupt:
            break
            
    return articles[:3]


def scrape_article_content(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    try:
        # Fetch the HTML content
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an error for bad status codes
        
        # Parse the HTML using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract text from common article tags (e.g., <p>, <h1>, <h2>, etc.)
        article_text = ""
        for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            article_text += tag.get_text(strip=True) + " "
        
        return article_text.strip()  # Remove leading/trailing spaces
    except requests.exceptions.RequestException as e:
        print(f"Failed to scrape {url}: {e}")
        return ""

def concatenate_content(articles):
    """
    concatenates the text from 'scrape_article_content' function

    Args:
        articles (list): contains the list of URL's

    Returns:
        str : concatenated text from the websites
    """
    # Scrape content from each URL
    all_content = ""
    for article in articles:
        print(f"Scraping: {article}")
        article_content = scrape_article_content(article)
        if article_content:
            all_content += article_content + "\n\n"  # Add spacing between articles
        
    return all_content.strip()

def generate_answer(content, query, history):
    """
    Generates an answer from the concatenated content using GPT-4.
    The content and the user's query are used to generate a contextual answer.
    """
    if history:
        history_prompt = " ".join(msg for msg in history)
    else:
        history_prompt = None
    prompt = f"""Previous conversation:\n{history_prompt}\n\nSummarize this {content} in around 100 words,  
    using the query {query} and history"""
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        answer = model.generate_content(prompt, 
                        generation_config=genai.GenerationConfig(
                            top_p=0.8,
                            temperature=0.5
                        )
                    )
        return answer.text
    except Exception as e:
        print(e)
        return None

#if __name__ == "__main__":
#    query = "what is machine learning"
#    embed = get_embeddings(query)
#    print(embed)
#    other_query = "Explain about machine learning"
#    other_embed = get_embeddings(other_query)
#    check = is_similar(embed, other_embed)
#    print(check)
