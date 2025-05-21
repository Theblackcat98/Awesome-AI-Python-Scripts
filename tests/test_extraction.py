#!/usr/bin/env python3

import json
import logging
from utils.get_website_content import get_website_content
from utils.extract_content import extract_content

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_extraction(url):
    """Test extraction on a given URL and print results."""
    print(f"Testing content extraction for: {url}")
    
    # Fetch the website content
    soup, status, error = get_website_content(url)
    
    if error or not soup:
        print(f"Error fetching {url}: {error}")
        return
    
    # Extract content
    content_data = extract_content(soup, url)
    
    # Print key information
    print("\nEXTRACTION RESULTS:")
    print("-" * 50)
    print(f"Business Type: {content_data['business_type']['type']} (confidence: {content_data['business_type']['confidence']}%)")
    print(f"Business Name: {content_data['business_info']['name']}")
    print(f"Business Tagline: {content_data['business_info']['tagline']}")
    
    # Print product count
    print(f"\nProducts detected: {len(content_data['products'])}")
    for i, product in enumerate(content_data['products'][:5], 1):  # Show first 5 products
        print(f"  {i}. {product['name']} - {product['price'] or 'No price'}")
        if i >= 5 and len(content_data['products']) > 5:
            print(f"  ... and {len(content_data['products']) - 5} more")
    
    # Print testimonial count
    print(f"\nTestimonials detected: {len(content_data['testimonials'])}")
    
    # Print social media
    print(f"\nSocial Media: {', '.join(content_data['business_info']['social_media']) or 'None detected'}")
    
    # Print contact info
    contact = content_data['business_info']['contact']
    print(f"\nContact Info:")
    print(f"  Phone: {contact['phone'] or 'Not found'}")
    print(f"  Email: {contact['email'] or 'Not found'}")
    print(f"  Address: {contact['address'] or 'Not found'}")
    
    # Print word count
    print(f"\nTotal word count: {content_data['word_count']}")
    
    # Save full content data to a file for inspection
    with open('test_extraction_result.json', 'w') as f:
        json.dump(content_data, f, indent=2)
    
    print("\nFull extraction results saved to test_extraction_result.json")

if __name__ == "__main__":
    # Test Theory Coffee
    test_extraction("https://theorycoffee.com/") 