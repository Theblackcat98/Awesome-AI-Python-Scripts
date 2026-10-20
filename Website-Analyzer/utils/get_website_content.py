import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging

def get_website_content(url):
    """
    Retrieves the HTML content from a given URL.
    
    Args:
        url (str): The URL to retrieve content from
        
    Returns:
        tuple: (soup object, status code, error message if any)
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup, response.status_code, None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching {url}: {str(e)}")
        return None, None, str(e)

if __name__ == "__main__":
    test_url = "https://www.example.com/"
    soup, status, error = get_website_content(test_url)
    if error:
        print(f"Error: {error}")
    else:
        print(f"Status code: {status}")
        print(f"Title: {soup.title.string}")
        print(f"First paragraph: {soup.p.text if soup.p else 'No paragraph found'}") 