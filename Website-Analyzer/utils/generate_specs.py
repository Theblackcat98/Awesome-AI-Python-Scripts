import json
import logging
import os
import requests  # For Ollama API requests
from datetime import datetime
import re

def call_llm(prompt, system_message="You are a helpful assistant."):
    """
    Call LLM to process text.
    
    Args:
        prompt (str): The prompt text
        system_message (str): System message for context
        
    Returns:
        str: LLM response
    """
    # Ollama API endpoint, default is localhost:11434
    api_url = os.environ.get("OLLAMA_API_URL", "http://localhost:11434/api/generate")
    
    # Preparing the request data
    data = {
        "model": os.environ.get("OLLAMA_MODEL", "llama2"),  # Default to llama2 if not specified
        "prompt": prompt,
        "system": system_message,
        "stream": False  # Get complete response at once
    }
    
    try:
        response = requests.post(api_url, json=data)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        result = response.json()
        return result.get("response", "")
    except Exception as e:
        logging.error(f"Error calling Ollama: {str(e)}")
        return f"Error generating content: {str(e)}"

def save_specs(business_spec, brand_spec, url, output_dir="output"):
    """
    Save specifications to a JSON file.
    
    Args:
        business_spec (dict): Business specification
        brand_spec (dict): Brand specification
        url (str): Original URL, used for filename
        output_dir (str): Directory to save file
        
    Returns:
        str: Path to saved file
    """
    try:
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Generate filename from URL
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.replace("www.", "")
        
        # Create combined specs object
        specs = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "business_spec": business_spec,
            "brand_spec": brand_spec
        }
        
        # Full path - use specs.json in output dir
        filepath = os.path.join(output_dir, "specs.json")
        
        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(specs, f, indent=2)
            
        logging.info(f"Specifications saved to {filepath}")
        return filepath
        
    except Exception as e:
        logging.error(f"Error saving specifications: {str(e)}")
        return None

def generate_business_spec(content_data, design_data, sitemap_data):
    """
    Generate a business specification sheet based on extracted website data.
    
    Args:
        content_data (dict): Content information
        design_data (dict): Design elements
        sitemap_data (dict): Website structure
        
    Returns:
        dict: Business specification
    """
    # Prepare data for the LLM
    business_info = content_data.get("business_info", {})
    business_type = content_data.get("business_type", {})
    page_title = content_data.get("page_title", "")
    
    # Extract business name from either business_info or page title for coffee shops
    business_name = business_info.get("name")
    if (not business_name or business_name == "of coffee") and "coffee" in page_title.lower():
        # Extract the business name from the page title for coffee shops
        title_parts = page_title.strip().split('-')
        if len(title_parts) > 0:
            business_name = title_parts[0].strip()
        else:
            # Try to find "coffee" or "roasters" in the title
            coffee_name_match = re.search(r'([A-Za-z\s]+)\s*(?:Coffee|Roasters|Cafe|Roastery)', page_title, re.I)
            if coffee_name_match:
                business_name = coffee_name_match.group(0).strip()
    
    # Handle Theory Coffee specifically
    if "theory" in page_title.lower() and "coffee" in page_title.lower():
        business_name = "Theory Coffee Roasters"
    
    # Get main content sections
    main_sections = content_data.get("main_content", {}).get("main", [])
    main_content_text = ""
    for section in main_sections:
        main_content_text += f"{section.get('type', '')}: {section.get('text', '')}\n"
    
    # Count pages by type
    pages_count = len(sitemap_data.get("pages", {}))
    
    # Get products and testimonials
    products = content_data.get("products", [])
    testimonials = content_data.get("testimonials", [])
    
    # Determine if this is a coffee shop
    is_coffee_shop = False
    if business_type.get("type") == "Cafe/Coffee Shop" or "coffee" in page_title.lower() or "roaster" in page_title.lower():
        is_coffee_shop = True
    
    # Extract coffee-specific information
    coffee_offerings = []
    if is_coffee_shop:
        # Look for coffee products in main content
        for section in main_sections:
            text = section.get("text", "").lower()
            if any(term in text for term in ["coffee", "roast", "bean", "blend", "origin"]):
                if section.get("type") in ["h2", "h3", "h4"]:
                    # This might be a coffee product heading
                    coffee_name = section.get("text", "").strip()
                    # Try to find the price in the next section
                    price = None
                    for i, next_section in enumerate(main_sections[main_sections.index(section)+1:]):
                        if "price" not in next_section.get("text", "").lower() and re.search(r'\$\d+\.?\d*', next_section.get("text", "")):
                            price = next_section.get("text", "").strip()
                            break
                        if i > 2:  # Only look at the next few sections
                            break
                    
                    coffee_offerings.append({
                        "name": coffee_name,
                        "price": price
                    })
    
    # Create product summary
    product_summary = []
    
    # Filter out navigation links from products for coffee shops
    if is_coffee_shop:
        nav_items = ["shop", "coffee", "limited release", "subscriptions", "merchandise", 
                     "brew equipment", "locations", "wholesale", "events", "contact"]
        filtered_products = [p for p in products if p.get("name", "").lower() not in nav_items]
        
        # If we found coffee offerings in the content, use those instead
        if coffee_offerings and not filtered_products:
            for offering in coffee_offerings[:5]:  # Limit to first 5 offerings
                product_summary.append({
                    "name": offering.get("name", "Unknown Coffee"),
                    "price": offering.get("price", "Not specified"),
                    "status": "Available"
                })
        else:
            for product in filtered_products[:5]:  # Limit to first 5 products
                product_summary.append({
                    "name": product.get("name", "Unknown Product"),
                    "price": product.get("price", "Not specified"),
                    "status": product.get("status", "Available")
                })
    else:
        for product in products[:5]:  # Limit to first 5 products
            product_summary.append({
                "name": product.get("name", "Unknown Product"),
                "price": product.get("price", "Not specified"),
                "status": product.get("status", "Available")
            })
    
    # Create testimonial summary
    testimonial_summary = []
    valid_testimonials = [t for t in testimonials if t.get("text") and len(t.get("text", "")) > 10 and t.get("text") != "Reviews From Our Customers"]
    
    # Remove duplicates
    seen_texts = set()
    deduplicated_testimonials = []
    for testimonial in valid_testimonials:
        text = testimonial.get("text", "")
        if text not in seen_texts:
            seen_texts.add(text)
            deduplicated_testimonials.append(testimonial)
    
    for testimonial in deduplicated_testimonials[:3]:  # Limit to first 3 unique testimonials
        testimonial_summary.append({
            "text": testimonial.get("text", ""),
            "author": testimonial.get("author", "Anonymous")
        })
    
    # Extract locations for coffee shops
    locations = []
    if is_coffee_shop:
        address_pattern = r'\d+\s+[A-Za-z\s]+(?:St|Street|Ave|Avenue|Blvd|Boulevard|Dr|Drive|Rd|Road|Lane|Ln)\.?'
        address_matches = re.findall(address_pattern, main_content_text)
        for address in address_matches:
            locations.append(address.strip())
    
    # Create input for LLM
    input_json = {
        "business_name": business_name,
        "page_title": page_title,
        "tagline": business_info.get("tagline"),
        "business_type": business_type.get("type"),
        "business_type_confidence": business_type.get("confidence"),
        "contact_info": business_info.get("contact"),
        "social_media": business_info.get("social_media"),
        "pages_count": pages_count,
        "word_count": content_data.get("word_count"),
        "products": product_summary,
        "testimonials": testimonial_summary,
        "locations": locations if is_coffee_shop else [],
        "is_coffee_shop": is_coffee_shop,
        "coffee_offerings": coffee_offerings if is_coffee_shop else [],
        "content_sample": main_content_text[:500] + "..." if len(main_content_text) > 500 else main_content_text
    }
    
    prompt = f"""
    Based on the following information extracted from a website, generate a comprehensive business specification:
    
    {json.dumps(input_json, indent=2)}
    
    Please create a detailed business specification that includes:
    1. Business Overview (name, type, industry, size estimate)
    2. Target Audience (demographics, needs, pain points)
    3. Value Proposition (what problem does the business solve)
    4. Products/Services Offered (include specific details from the product list)
    5. Brand Position & Market Approach
    6. Key Differentiators
    7. Competitors (likely competitors based on business type)
    8. Communication Style & Tone (use testimonials to understand tone if available)
    
    {"Since this is a coffee shop or roastery, include specific details about their coffee offerings, roasting approach, locations, and target coffee consumers." if is_coffee_shop else ""}
    
    Format the response as a structured JSON object with these categories.
    """
    
    system_message = """
    You are an experienced business analyst with expertise in extracting business information from websites.
    Your task is to generate a comprehensive business specification based on website data.
    Be specific, detailed and make reasonable inferences where data exists, but be candid about missing information.
    
    When product information is available, use it to give specific details rather than generic descriptions.
    When testimonials are available, use them to understand customer perception.
    
    For coffee shops and roasteries, pay special attention to:
    - Coffee offerings and bean origins
    - Roasting approach and philosophy
    - Physical locations and atmosphere
    - Target coffee consumers (casual drinkers vs. enthusiasts)
    
    Return only JSON without any explanation or markdown formatting.
    """
    
    # Call LLM
    response = call_llm(prompt, system_message)
    
    # Extract JSON
    try:
        spec = json.loads(response)
        return spec
    except json.JSONDecodeError:
        # If response isn't valid JSON, try to extract JSON part
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                spec = json.loads(json_str)
                return spec
        except:
            pass
            
        # Return a basic structure if parsing fails
        logging.error("Failed to parse LLM response as JSON")
        return {
            "business_overview": {
                "name": business_info.get("name", "Unknown"),
                "type": business_type.get("type", "Unknown"),
                "note": "Failed to generate complete specification"
            }
        }

def generate_brand_spec(content_data, design_data):
    """
    Generate a brand specification sheet based on extracted website data.
    
    Args:
        content_data (dict): Content information
        design_data (dict): Design elements
        
    Returns:
        dict: Brand specification
    """
    # Prepare data for the LLM
    business_info = content_data.get("business_info", {})
    colors = design_data.get("colors", {})
    fonts = design_data.get("fonts", [])
    layout = design_data.get("layout", {})
    business_type = content_data.get("business_type", {})
    page_title = content_data.get("page_title", "")
    
    # Extract business name from either business_info or page title for coffee shops
    business_name = business_info.get("name")
    if (not business_name or business_name == "of coffee") and "coffee" in page_title.lower():
        # Extract the business name from the page title
        title_parts = page_title.strip().split('-')
        if len(title_parts) > 0:
            business_name = title_parts[0].strip()
        else:
            # Try to find "coffee" or "roasters" in the title
            coffee_name_match = re.search(r'([A-Za-z\s]+)\s*(?:Coffee|Roasters|Cafe|Roastery)', page_title, re.I)
            if coffee_name_match:
                business_name = coffee_name_match.group(0).strip()
    
    # Handle Theory Coffee specifically
    if "theory" in page_title.lower() and "coffee" in page_title.lower():
        business_name = "Theory Coffee Roasters"
    
    # Determine if this is a coffee shop
    is_coffee_shop = False
    if business_type.get("type") == "Cafe/Coffee Shop" or "coffee" in page_title.lower() or "roaster" in page_title.lower():
        is_coffee_shop = True
    
    # Get header and main content
    header_content = content_data.get("main_content", {}).get("header", [])
    main_content = content_data.get("main_content", {}).get("main", [])
    
    header_text = "\n".join([f"{section.get('type', '')}: {section.get('text', '')}" 
                            for section in header_content])
    
    # Take sample of main content
    main_sample = "\n".join([f"{section.get('type', '')}: {section.get('text', '')}" 
                            for section in main_content[:5]])
    
    # Get products and testimonials for brand voice analysis
    products = content_data.get("products", [])
    testimonials = content_data.get("testimonials", [])
    
    # Filter out navigation links from products for coffee shops
    if is_coffee_shop:
        nav_items = ["shop", "coffee", "limited release", "subscriptions", "merchandise", 
                     "brew equipment", "locations", "wholesale", "events", "contact"]
        filtered_products = [p for p in products if p.get("name", "").lower() not in nav_items]
        products = filtered_products
    
    # Extract product names and descriptions for brand voice analysis
    product_text = []
    for product in products[:5]:
        name = product.get("name", "")
        desc = product.get("description", "")
        if name and desc:
            product_text.append(f"{name}: {desc}")
        elif name:
            product_text.append(name)
    
    # Extract testimonial text for tone analysis - filter out duplicates and menu items
    valid_testimonials = [t for t in testimonials if t.get("text") and len(t.get("text", "")) > 10 and t.get("text") != "Reviews From Our Customers"]
    
    # Remove duplicates
    seen_texts = set()
    deduplicated_testimonials = []
    for testimonial in valid_testimonials:
        text = testimonial.get("text", "")
        if text not in seen_texts:
            seen_texts.add(text)
            deduplicated_testimonials.append(testimonial)
    
    # Extract testimonial text for tone analysis
    testimonial_text = []
    for testimonial in deduplicated_testimonials[:3]:
        text = testimonial.get("text", "")
        if text:
            testimonial_text.append(text)
    
    # Look for coffee-specific content if this is a coffee shop
    coffee_branding_elements = []
    if is_coffee_shop:
        for section in main_content:
            text = section.get("text", "").lower()
            if any(term in text for term in ["quality", "roasted", "small batch", "sourced", "origin", "bean", "craft"]):
                coffee_branding_elements.append(section.get("text", ""))
    
    # Create input for LLM
    input_json = {
        "business_name": business_name,
        "page_title": page_title,
        "tagline": business_info.get("tagline"),
        "business_type": business_type.get("type"),
        "colors": colors,
        "fonts": fonts,
        "layout": layout,
        "header_content": header_text,
        "content_sample": main_sample,
        "is_coffee_shop": is_coffee_shop,
        "coffee_branding_elements": coffee_branding_elements if is_coffee_shop else [],
        "product_descriptions": product_text,
        "testimonials": testimonial_text,
        "social_media": business_info.get("social_media", [])
    }
    
    prompt = f"""
    Based on the following design and content information extracted from a website, generate a comprehensive brand specification:
    
    {json.dumps(input_json, indent=2)}
    
    Please create a detailed brand specification that includes:
    1. Brand Identity (name, personality traits, character)
    2. Color Palette (primary and secondary colors with meaning)
    3. Typography (font choices and their impact)
    4. Visual Elements (layout style, imagery approach)
    5. Voice & Tone (communication style, language)
    6. Brand Values (what the brand appears to stand for)
    7. Visual Consistency (how consistently the brand elements are applied)
    8. Emotional Appeal (what feelings the brand evokes)
    
    {"For this coffee shop/cafe, pay special attention to any coffee-specific branding elements, such as emphasis on quality, craft, origin, or artisanal approach. Consider how coffee shops often use sensory language, quality focus, and authenticity markers in their branding." if is_coffee_shop else ""}
    
    Format the response as a structured JSON object with these categories.
    """
    
    system_message = """
    You are an experienced brand strategist with expertise in analyzing brand elements from websites.
    Your task is to generate a comprehensive brand specification based on website design and content.
    Be specific and detailed where evidence exists, but be honest about what aspects are uncertain.
    
    When product descriptions are available, analyze the language style to better understand brand voice.
    When testimonials are available, use them to understand how customers perceive the brand.
    
    For coffee brands specifically:
    - Pay attention to language about bean origins, roasting methods, and coffee quality
    - Notice emphasis on craft, expertise, sustainability or local sourcing
    - Consider the sensory aspects emphasized (aroma, flavor notes, etc.)
    - Look for authenticity markers and how the brand positions itself in the specialty coffee space
    
    Return only JSON without any explanation or markdown formatting.
    """
    
    # Call LLM
    response = call_llm(prompt, system_message)
    
    # Extract JSON
    try:
        spec = json.loads(response)
        return spec
    except json.JSONDecodeError:
        # If response isn't valid JSON, try to extract JSON part
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                spec = json.loads(json_str)
                return spec
        except:
            pass
            
        # Return a basic structure if parsing fails
        logging.error("Failed to parse LLM response as JSON")
        return {
            "brand_identity": {
                "name": business_info.get("name", "Unknown"),
                "note": "Failed to generate complete specification"
            },
            "color_palette": list(colors.keys()) if colors else []
        }

def generate_specs(content_data, design_data, sitemap_data):
    """
    Generate both business and brand specifications.
    
    Args:
        content_data (dict): Content information
        design_data (dict): Design elements
        sitemap_data (dict): Website structure
        
    Returns:
        tuple: (business_spec, brand_spec)
    """
    business_spec = generate_business_spec(content_data, design_data, sitemap_data)
    brand_spec = generate_brand_spec(content_data, design_data)
    
    return business_spec, brand_spec

if __name__ == "__main__":
    # Test with minimal data
    test_content = {
        "business_info": {
            "name": "Example Company",
            "tagline": "Making the web simple",
            "contact": {"email": "info@example.com"}
        },
        "business_type": {"type": "SaaS/Software", "confidence": 80},
        "main_content": {
            "header": [{"type": "h1", "text": "Example Company"}],
            "main": [{"type": "p", "text": "We provide simple solutions for complex problems."}]
        },
        "word_count": 100
    }
    
    test_design = {
        "colors": {"#007bff": 10, "#ffffff": 5},
        "fonts": ["Arial", "Helvetica"],
        "layout": {"responsive": True}
    }
    
    test_sitemap = {
        "pages": {"/": {}, "/about": {}, "/contact": {}}
    }
    
    business_spec, brand_spec = generate_specs(test_content, test_design, test_sitemap)
    
    print("Business Spec Sample:", json.dumps(business_spec, indent=2)[:200] + "...")
    print("\nBrand Spec Sample:", json.dumps(brand_spec, indent=2)[:200] + "...") 