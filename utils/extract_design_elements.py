from bs4 import BeautifulSoup
import re
import logging
from collections import Counter
import cssutils
import requests
from urllib.parse import urljoin

# Suppress cssutils logging
cssutils.log.setLevel(logging.CRITICAL)

def extract_hex_color(color_str):
    """Extract hex color from CSS color string."""
    if not color_str:
        return None
        
    # Check for hex color
    hex_match = re.search(r'#([0-9a-fA-F]{3,6})', color_str)
    if hex_match:
        return '#' + hex_match.group(1)
        
    # Check for rgb
    rgb_match = re.search(r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', color_str)
    if rgb_match:
        r, g, b = map(int, rgb_match.groups())
        return f'#{r:02x}{g:02x}{b:02x}'
        
    return None

def get_css_urls(soup, base_url):
    """Get list of CSS URLs from HTML."""
    css_urls = []
    
    # Get inline styles
    for style in soup.find_all('style'):
        if style.string:
            yield ('inline', style.string)
    
    # Get external stylesheets
    for link in soup.find_all('link', rel='stylesheet'):
        if link.get('href'):
            css_url = urljoin(base_url, link['href'])
            css_urls.append(css_url)
    
    # Fetch external CSS
    for url in css_urls:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                yield (url, response.text)
        except Exception as e:
            logging.error(f"Error fetching CSS from {url}: {str(e)}")

def extract_design_elements(soup, url):
    """
    Extract design elements from a webpage.
    
    Args:
        soup: BeautifulSoup object
        url: Original URL for resolving resources
        
    Returns:
        dict: Design elements
    """
    design = {
        "colors": {},
        "fonts": [],
        "layout": {
            "sections": 0,
            "columns": False,
            "responsive": False
        },
        "images": {
            "count": 0,
            "types": {}
        }
    }
    
    # Count images
    images = soup.find_all('img')
    design["images"]["count"] = len(images)
    
    # Image types counter
    img_types = Counter()
    for img in images:
        src = img.get('src', '')
        if '.' in src:
            ext = src.split('.')[-1].lower()
            if ext in ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp']:
                img_types[ext] += 1
    
    design["images"]["types"] = dict(img_types)
    
    # Extract colors from CSS
    colors = []
    
    # Extract inline colors from style attributes
    for tag in soup.find_all(style=True):
        style_str = tag['style']
        # Look for colors in style
        color_matches = re.findall(r'(?:color|background(?:-color)?)\s*:\s*([^;]+)', style_str)
        for color_str in color_matches:
            hex_color = extract_hex_color(color_str)
            if hex_color:
                colors.append(hex_color)
    
    # Extract colors from CSS files and inline styles
    for source, css_text in get_css_urls(soup, url):
        try:
            sheet = cssutils.parseString(css_text)
            for rule in sheet:
                if rule.type == rule.STYLE_RULE:
                    for property in rule.style:
                        if 'color' in property.name:
                            hex_color = extract_hex_color(property.value)
                            if hex_color:
                                colors.append(hex_color)
        except Exception as e:
            logging.error(f"Error parsing CSS from {source}: {str(e)}")
    
    # Count color occurrences
    color_counter = Counter(colors)
    design["colors"] = {color: count for color, count in color_counter.most_common(5)}
    
    # Extract fonts
    fonts = []
    font_patterns = [
        r'font-family\s*:\s*([^;]+)',
        r'font\s*:[^;]*family\s*:\s*([^;]+)'
    ]
    
    # Look in inline styles
    for tag in soup.find_all(style=True):
        for pattern in font_patterns:
            matches = re.findall(pattern, tag['style'])
            fonts.extend(matches)
    
    # Look in CSS
    for source, css_text in get_css_urls(soup, url):
        for pattern in font_patterns:
            matches = re.findall(pattern, css_text)
            fonts.extend(matches)
    
    # Clean and count fonts
    cleaned_fonts = []
    for font in fonts:
        # Split font families and clean
        for f in font.split(','):
            f = f.strip().strip('"\'').lower()
            if f and not f.startswith('#'):
                cleaned_fonts.append(f)
    
    font_counter = Counter(cleaned_fonts)
    design["fonts"] = [font for font, _ in font_counter.most_common(3)]
    
    # Check if page has responsive design
    meta_viewport = soup.find('meta', attrs={'name': 'viewport'})
    if meta_viewport:
        design["layout"]["responsive"] = True
    
    # Count main sections
    sections = soup.find_all(['section', 'div'], class_=re.compile(r'(section|container|wrapper)'))
    design["layout"]["sections"] = len(sections) or len(soup.find_all('div', class_=True))
    
    # Check for multi-column layout
    columns = soup.find_all(class_=re.compile(r'(column|col-|grid)'))
    design["layout"]["columns"] = len(columns) > 0
    
    return design

if __name__ == "__main__":
    from utils.get_website_content import get_website_content
    
    test_url = "https://example.com"
    soup, status, error = get_website_content(test_url)
    if not error and soup:
        design = extract_design_elements(soup, test_url)
        print("Design elements extracted:")
        print(f"Colors: {design['colors']}")
        print(f"Fonts: {design['fonts']}")
        print(f"Layout: {design['layout']}")
        print(f"Images: {design['images']}") 