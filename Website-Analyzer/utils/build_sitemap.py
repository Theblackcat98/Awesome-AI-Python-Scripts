import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
from utils.get_website_content import get_website_content

def is_valid_url(url, base_domain):
    """
    Check if URL is valid and belongs to the same domain.
    
    Args:
        url (str): URL to check
        base_domain (str): Base domain to compare against
        
    Returns:
        bool: True if URL is valid and belongs to same domain
    """
    parsed = urlparse(url)
    return bool(parsed.netloc) and parsed.netloc == base_domain

def build_sitemap(start_url, max_pages=20):
    """
    Build a sitemap by crawling links from a website.
    
    Args:
        start_url (str): Starting URL to crawl
        max_pages (int): Maximum number of pages to crawl
        
    Returns:
        dict: Sitemap with structure information
    """
    base_url = urlparse(start_url)
    base_domain = base_url.netloc
    
    sitemap = {
        "base_url": start_url,
        "pages": {}
    }
    
    urls_to_visit = [start_url]
    visited_urls = set()
    
    while urls_to_visit and len(visited_urls) < max_pages:
        current_url = urls_to_visit.pop(0)
        if current_url in visited_urls:
            continue
        
        logging.info(f"Crawling: {current_url}")
        soup, status, error = get_website_content(current_url)
        
        if error or not soup:
            continue
            
        # Add to visited
        visited_urls.add(current_url)
        
        # Get page structure data
        page_structure = {
            "title": soup.title.string if soup.title else "No title",
            "headers": {
                "h1": [h.text.strip() for h in soup.find_all('h1')],
                "h2": [h.text.strip() for h in soup.find_all('h2')],
                "h3": [h.text.strip() for h in soup.find_all('h3')],
            },
            "paragraphs_count": len(soup.find_all('p')),
            "links": [],
        }
        
        # Add to sitemap
        page_key = current_url.replace(start_url, "") or "/"
        sitemap["pages"][page_key] = page_structure
        
        # Find new links
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(current_url, href)
            
            # Only add internal links that we haven't visited yet
            if is_valid_url(absolute_url, base_domain) and absolute_url not in visited_urls:
                urls_to_visit.append(absolute_url)
                page_structure["links"].append(absolute_url)
    
    return sitemap

if __name__ == "__main__":
    test_url = "https://example.com"
    sitemap = build_sitemap(test_url, max_pages=3)
    print(f"Found {len(sitemap['pages'])} pages")
    for page, info in sitemap["pages"].items():
        print(f"Page: {page}, Title: {info['title']}") 