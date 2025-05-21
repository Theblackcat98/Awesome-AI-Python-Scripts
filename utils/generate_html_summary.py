import json
import os
import logging
from datetime import datetime
from pathlib import Path

# Import our templated HTML generator
try:
    from utils.templates.html_summary_template import generate_html_summary as templated_html_summary
    USE_TEMPLATE = True
except ImportError:
    USE_TEMPLATE = False
    logging.warning("HTML template not found, using fallback HTML generator")

def generate_html_summary(url, business_spec, brand_spec, sitemap_data, design_data, content_data=None):
    """
    Generate an HTML summary page based on the extracted specifications.
    
    Args:
        url (str): Original URL
        business_spec (dict): Business specification
        brand_spec (dict): Brand specification
        sitemap_data (dict): Website structure
        design_data (dict): Design elements
        content_data (dict, optional): Raw extracted content data
        
    Returns:
        str: HTML content
    """
    # Try to use the template if available
    if USE_TEMPLATE:
        try:
            return templated_html_summary(url, business_spec, brand_spec, sitemap_data, design_data, content_data)
        except Exception as e:
            logging.error(f"Error using template HTML generator: {str(e)}")
            logging.info("Falling back to built-in HTML generator")
    
    # Get primary colors from design data
    colors = list(design_data.get('colors', {}).keys())
    primary_color = colors[0] if colors else "#4a90e2"
    accent_color = colors[1] if len(colors) > 1 else "#34495e"
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Get site structure info
    page_count = len(sitemap_data.get('pages', {}))
    pages_list = list(sitemap_data.get('pages', {}).keys())
    pages_sample = ", ".join(pages_list[:5])
    if len(pages_list) > 5:
        pages_sample += f", ... and {len(pages_list) - 5} more"
    
    # Prepare business overview - handle nested structure
    business_overview = {}
    
    # First check for the nested structure (business_specification.Business_Overview)
    if 'business_specification' in business_spec:
        business_overview = business_spec.get('business_specification', {}).get('Business_Overview', {})
    # Fallback to direct keys
    elif 'Business_Overview' in business_spec:
        business_overview = business_spec.get('Business_Overview', {})
    elif 'business_overview' in business_spec:
        business_overview = business_spec.get('business_overview', {})
    
    # Get business name
    business_name = business_overview.get('name', 'Unknown Business')
    business_type = business_overview.get('type', 'Unknown Type')
    
    # Prepare audience and value prop
    target_audience = {}
    if 'business_specification' in business_spec:
        target_audience = business_spec.get('business_specification', {}).get('Target_Audience', {})
    else:
        target_audience = business_spec.get('target_audience', {}) or business_spec.get('Target_Audience', {})
    
    # Extract value proposition
    value_proposition = "Not specified"
    if 'business_specification' in business_spec:
        value_prop_obj = business_spec.get('business_specification', {}).get('Value_Proposition', {})
        if value_prop_obj:
            value_proposition = value_prop_obj.get('problem_solution', '') or value_prop_obj.get('problem_solved', 'Not specified')
    else:
        value_prop_obj = business_spec.get('value_proposition', {}) or business_spec.get('Value_Proposition', {})
        if isinstance(value_prop_obj, dict):
            value_proposition = value_prop_obj.get('problem_solved', 'Not specified')
        elif isinstance(value_prop_obj, str):
            value_proposition = value_prop_obj
    
    # Products/Services section
    products_services = "Not specified"
    if 'business_specification' in business_spec:
        products_obj = business_spec.get('business_specification', {}).get('Products_Services_Offered', {})
        if products_obj:
            if 'details' in products_obj:
                products_services = products_obj.get('details', 'Not specified')
            elif 'specific_coffees' in products_obj or 'coffee_subscriptions' in products_obj:
                coffee_desc = []
                if 'specific_coffees' in products_obj:
                    coffee_desc.append(f"Offers {len(products_obj['specific_coffees'])} different coffee varieties")
                if 'coffee_subscriptions' in products_obj:
                    coffee_desc.append("Provides coffee subscription services")
                products_services = ". ".join(coffee_desc)
    else:
        products_obj = business_spec.get('products_services_offered', {}) or business_spec.get('Products_Services_Offered', {})
        if isinstance(products_obj, dict):
            products_services = products_obj.get('description', 'Not specified')
        elif isinstance(products_obj, str):
            products_services = products_obj
    
    # Prepare brand identity elements
    brand_identity = {}
    color_palette = {}
    typography = {}
    visual_elements = {}
    voice_tone = {}
    brand_values = {}
    emotional_appeal = {}
    
    if 'Brand Identity' in brand_spec:
        # Direct structure from specs.json
        brand_identity = brand_spec.get('Brand Identity', {})
        color_palette = brand_spec.get('Color Palette', {})
        typography = brand_spec.get('Typography', {})
        visual_elements = brand_spec.get('Visual Elements', {})
        voice_tone = brand_spec.get('Voice & Tone', {})
        brand_values = brand_spec.get('Brand Values', {})
        emotional_appeal = brand_spec.get('Emotional Appeal', {})
    else:
        # Nested structure within brand_specification
        brand_specification = brand_spec.get('brand_specification', {})
        if brand_specification:
            brand_identity = brand_specification.get('brand_identity', {})
            color_palette = brand_specification.get('color_palette', {})
            typography = brand_specification.get('typography', {})
            visual_elements = brand_specification.get('visual_elements', {})
            voice_tone = brand_specification.get('voice_and_tone', {})
            brand_values = brand_specification.get('brand_values', [])
            emotional_appeal = brand_specification.get('emotional_appeal', {})
        else:
            # Fallback to direct keys
            brand_identity = brand_spec.get('brand_identity', {})
            color_palette = brand_spec.get('color_palette', {})
            typography = brand_spec.get('typography', {})
            visual_elements = brand_spec.get('visual_elements', {})
            voice_tone = brand_spec.get('voice_tone', {})
            brand_values = brand_spec.get('brand_values', [])
            emotional_appeal = brand_spec.get('emotional_appeal', {})
    
    # Extract personality traits
    brand_personality = brand_identity.get('personality_traits', [])
    if isinstance(brand_personality, list):
        personality_traits = ", ".join(brand_personality)
    else:
        personality_traits = str(brand_personality)
    
    # Prepare color palette
    color_swatches = ""
    processed_colors = {}
    
    # Handle primary_colors/secondary_colors structure
    if isinstance(color_palette, dict):
        primary_colors = []
        if 'primary_colors' in color_palette:
            primary_colors = color_palette.get('primary_colors', [])
            if isinstance(primary_colors, list):
                for color_item in primary_colors:
                    if isinstance(color_item, dict) and 'color' in color_item:
                        color = color_item['color']
                        meaning = color_item.get('meaning', '')
                        processed_colors[color] = meaning
                    elif isinstance(color_item, str):
                        processed_colors[color_item] = ''
            elif isinstance(primary_colors, dict):
                for color, meaning in primary_colors.items():
                    processed_colors[color] = meaning
        
        secondary_colors = []
        if 'secondary_colors' in color_palette:
            secondary_colors = color_palette.get('secondary_colors', [])
            if isinstance(secondary_colors, list):
                for color_item in secondary_colors:
                    if isinstance(color_item, dict) and 'color' in color_item:
                        color = color_item['color']
                        meaning = color_item.get('meaning', '')
                        processed_colors[color] = meaning
                    elif isinstance(color_item, str):
                        processed_colors[color_item] = ''
            elif isinstance(secondary_colors, dict):
                for color, meaning in secondary_colors.items():
                    processed_colors[color] = meaning
        
        # If no processed colors yet, check for direct color-meaning pairs
        if not processed_colors and isinstance(color_palette, dict):
            for color, meaning in color_palette.items():
                if color.startswith('#') or color.startswith('rgb'):
                    processed_colors[color] = meaning
    elif isinstance(color_palette, list):
        for color in color_palette:
            processed_colors[color] = ''
    
    # Generate HTML for colors
    for color, meaning in processed_colors.items():
        meaning_text = f"<p>{meaning}</p>" if meaning else ""
        color_swatches += f"""
        <div class="color-swatch">
            <div class="swatch" style="background-color: {color}"></div>
            <div class="swatch-info">
                <code>{color}</code>
                {meaning_text}
            </div>
        </div>
        """
    
    # Prepare typography - handle different structures
    fonts = []
    
    if isinstance(typography, dict):
        if 'font_choices' in typography:
            font_choices = typography.get('font_choices', [])
            if isinstance(font_choices, list):
                for font_item in font_choices:
                    if isinstance(font_item, dict):
                        fonts.append(font_item.get('name', str(font_item)))
                    else:
                        fonts.append(str(font_item))
        elif 'fonts' in typography:
            font_obj = typography.get('fonts', {})
            if isinstance(font_obj, dict):
                fonts = list(font_obj.keys())
            elif isinstance(font_obj, list):
                fonts = font_obj
            else:
                fonts = [str(font_obj)]
    elif isinstance(typography, list):
        fonts = typography
    
    # Ensure fonts is a list
    if not isinstance(fonts, list):
        fonts = [str(fonts)]
    
    # Handle empty fonts
    if not fonts:
        fonts = ["No fonts specified"]
    
    # Format fonts for display
    fonts_display = ", ".join([str(font) for font in fonts if font])
    
    # Prepare voice and tone
    if isinstance(voice_tone, dict):
        communication_style = voice_tone.get('communication_style', 'Not specified')
        language = voice_tone.get('language', 'Not specified')
        if isinstance(language, list):
            language = ", ".join(language)
    else:
        communication_style = str(voice_tone)
        language = 'Not specified'
    
    # Format brand values
    if isinstance(brand_values, dict):
        brand_values_display = ""
        for key, value in brand_values.items():
            if isinstance(value, list):
                brand_values_display += f"<p><strong>{key}:</strong> {', '.join(value)}</p>"
            else:
                brand_values_display += f"<p><strong>{key}:</strong> {value}</p>"
    elif isinstance(brand_values, list):
        brand_values_display = ", ".join(brand_values)
    else:
        brand_values_display = str(brand_values)
    
    # Format emotional appeal
    if isinstance(emotional_appeal, dict):
        emotional_appeal_display = ""
        for key, value in emotional_appeal.items():
            if isinstance(value, list):
                emotional_appeal_display += f"<p><strong>{key}:</strong> {', '.join(value)}</p>"
            else:
                emotional_appeal_display += f"<p><strong>{key}:</strong> {value}</p>"
    else:
        emotional_appeal_display = str(emotional_appeal)
    
    # Get products from business_spec or content_data
    products = []
    if 'business_specification' in business_spec:
        products_spec = business_spec.get('business_specification', {}).get('Products_Services_Offered', {})
        if products_spec:
            if 'specific_coffees' in products_spec:
                coffee_products = products_spec.get('specific_coffees', [])
                for coffee in coffee_products:
                    if isinstance(coffee, dict):
                        products.append({
                            "name": coffee.get('name', 'Coffee Product'),
                            "price": coffee.get('price', 'Price not specified'),
                            "status": "Available"
                        })
            if 'coffee_subscriptions' in products_spec:
                subscription_products = products_spec.get('coffee_subscriptions', [])
                for sub in subscription_products:
                    if isinstance(sub, dict):
                        products.append({
                            "name": sub.get('name', 'Coffee Subscription'),
                            "price": sub.get('price', 'Price not specified'),
                            "status": "Available"
                        })
            if 'merchandise' in products_spec:
                merch_products = products_spec.get('merchandise', [])
                for merch in merch_products:
                    if isinstance(merch, dict):
                        products.append({
                            "name": merch.get('name', 'Merchandise Item'),
                            "price": merch.get('price', 'Price not specified'),
                            "status": "Available"
                        })
    
    # If no products were found in the business_spec, try content_data
    if not products and content_data and 'products' in content_data:
        products = content_data.get('products', [])
    # Fallback to products directly in business_spec
    elif not products:
        products = business_spec.get('products', [])
    
    # Generate HTML for products
    products_html = ""
    if products:
        products_html = """
        <h3>Products</h3>
        <div class="products-grid">
        """
        for product in products[:6]:  # Limit to 6 products
            product_name = product.get('name', 'Unnamed Product')
            product_price = product.get('price', 'Price not available')
            product_status = product.get('status', 'Available')
            product_image = product.get('image_url', '')
            
            status_class = "sold-out" if product_status == "Sold Out" else ""
            
            image_html = ""
            if product_image:
                image_html = f'<img src="{product_image}" alt="{product_name}" class="product-image">'
            
            products_html += f"""
            <div class="product-card {status_class}">
                {image_html}
                <h4>{product_name}</h4>
                <p class="price">{product_price}</p>
                <p class="status">{product_status}</p>
            </div>
            """
        
        products_html += """
        </div>
        """
    
    # Get testimonials from business_spec or content_data
    testimonials = []
    
    # First try to extract testimonials from business_spec
    if 'business_specification' in business_spec:
        comm_style = business_spec.get('business_specification', {}).get('Communication_Style_Tone', {})
        if isinstance(comm_style, dict) and 'tone_from_testimonials' in comm_style:
            tone_text = comm_style.get('tone_from_testimonials', '')
            if tone_text:
                testimonials.append({
                    "text": tone_text,
                    "author": "Customer Testimonial"
                })
    
    # If no testimonials were found, try content_data
    if not testimonials and content_data and 'testimonials' in content_data:
        testimonials = content_data.get('testimonials', [])
    # Fallback to testimonials directly in business_spec
    elif not testimonials:
        testimonials = business_spec.get('testimonials', [])
    
    # Generate HTML for testimonials
    testimonials_html = ""
    if testimonials:
        testimonials_html = """
        <h3>Customer Testimonials</h3>
        <div class="testimonial-grid">
        """
        for testimonial in testimonials[:3]:  # Limit to 3 testimonials
            testimonial_text = testimonial.get('text', '')
            testimonial_author = testimonial.get('author', 'Anonymous')
            
            testimonials_html += f"""
            <div class="testimonial">
                <blockquote>"{testimonial_text}"</blockquote>
                <cite>- {testimonial_author}</cite>
            </div>
            """
        
        testimonials_html += """
        </div>
        """
    
    # Get market approach and differentiators
    market_approach = "Not specified"
    key_differentiators = "Not specified"
    
    if 'business_specification' in business_spec:
        market_spec = business_spec.get('business_specification', {}).get('Brand_Position_Market_Approach', {})
        if market_spec:
            if isinstance(market_spec, dict):
                positioning = market_spec.get('positioning', '')
                approach = market_spec.get('market_approach', [])
                
                if approach and isinstance(approach, list):
                    approach = ", ".join(approach)
                
                market_parts = []
                if positioning:
                    market_parts.append(positioning)
                if approach:
                    market_parts.append(approach)
                    
                if market_parts:
                    market_approach = " ".join(market_parts)
        
        diff_spec = business_spec.get('business_specification', {}).get('Key_Differentiators', {})
        if diff_spec:
            if isinstance(diff_spec, dict):
                unique_features = diff_spec.get('unique_features', [])
                if unique_features and isinstance(unique_features, list):
                    key_differentiators = ", ".join(unique_features)
                elif 'differentiating_factors' in diff_spec:
                    key_differentiators = diff_spec.get('differentiating_factors', 'Not specified')
    
    # Generate HTML
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Website Analysis: {business_name}</title>
        <style>
            :root {{
                --primary-color: {primary_color};
                --accent-color: {accent_color};
                --text-color: #333;
                --light-bg: #f5f7fa;
                --card-bg: #ffffff;
                --border-radius: 8px;
                --shadow: 0 4px 6px rgba(0,0,0,0.1);
                --font-main: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            }}
            
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}
            
            body {{
                font-family: var(--font-main);
                line-height: 1.6;
                color: var(--text-color);
                background-color: var(--light-bg);
                padding: 0;
                margin: 0;
            }}
            
            header {{
                background-color: var(--primary-color);
                color: white;
                padding: 2rem;
                text-align: center;
            }}
            
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem;
            }}
            
            h1, h2, h3, h4 {{
                margin-bottom: 1rem;
                line-height: 1.3;
            }}
            
            h1 {{
                font-size: 2.5rem;
            }}
            
            h2 {{
                font-size: 2rem;
                color: var(--primary-color);
                border-bottom: 2px solid var(--primary-color);
                padding-bottom: 0.5rem;
                margin-top: 2rem;
            }}
            
            h3 {{
                font-size: 1.5rem;
                color: var(--accent-color);
                margin-top: 1.5rem;
            }}
            
            p {{
                margin-bottom: 1rem;
            }}
            
            .section {{
                background: var(--card-bg);
                border-radius: var(--border-radius);
                box-shadow: var(--shadow);
                padding: 2rem;
                margin-bottom: 2rem;
            }}
            
            .meta {{
                font-size: 0.9rem;
                color: #666;
                margin-bottom: 2rem;
            }}
            
            .grid-2 {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 2rem;
            }}
            
            .list-item {{
                margin-bottom: 0.5rem;
                display: flex;
                align-items: top;
            }}
            
            .list-item i {{
                color: var(--primary-color);
                margin-right: 0.5rem;
                display: inline-block;
                width: 1.2rem;
            }}
            
            .tag {{
                display: inline-block;
                background-color: var(--primary-color);
                color: white;
                padding: 0.3rem 0.8rem;
                border-radius: 50px;
                margin: 0.25rem;
                font-size: 0.9rem;
            }}
            
            .color-swatches {{
                display: flex;
                flex-wrap: wrap;
                gap: 1rem;
                margin-top: 1rem;
            }}
            
            .color-swatch {{
                display: flex;
                align-items: center;
                margin-bottom: 1rem;
                flex: 1 1 300px;
            }}
            
            .swatch {{
                width: 80px;
                height: 80px;
                border-radius: var(--border-radius);
                margin-right: 1rem;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                border: 1px solid rgba(0,0,0,0.1);
            }}
            
            .swatch-info {{
                flex: 1;
            }}
            
            .swatch-info code {{
                display: inline-block;
                background-color: var(--light-bg);
                padding: 0.2rem 0.5rem;
                border-radius: 4px;
                margin-bottom: 0.5rem;
                font-family: monospace;
            }}
            
            .products-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 1.5rem;
                margin-top: 1.5rem;
            }}
            
            .product-card {{
                background: var(--light-bg);
                border-radius: var(--border-radius);
                padding: 1rem;
                box-shadow: var(--shadow);
                text-align: center;
            }}
            
            .product-card.sold-out {{
                opacity: 0.7;
            }}
            
            .product-card .product-image {{
                max-width: 100%;
                height: 150px;
                object-fit: cover;
                border-radius: var(--border-radius);
                margin-bottom: 1rem;
            }}
            
            .product-card .price {{
                font-weight: bold;
                color: var(--accent-color);
            }}
            
            .product-card .status {{
                font-size: 0.9rem;
                color: #666;
            }}
            
            .testimonial-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 1.5rem;
                margin-top: 1.5rem;
            }}
            
            .testimonial {{
                background: var(--light-bg);
                border-radius: var(--border-radius);
                padding: 1.5rem;
                box-shadow: var(--shadow);
                font-style: italic;
            }}
            
            .testimonial blockquote {{
                margin: 0 0 1rem 0;
                line-height: 1.6;
            }}
            
            .testimonial cite {{
                font-style: normal;
                font-weight: bold;
                color: var(--accent-color);
                display: block;
                text-align: right;
            }}
            
            footer {{
                background-color: var(--accent-color);
                color: white;
                text-align: center;
                padding: 1.5rem;
                margin-top: 2rem;
            }}
            
            @media (max-width: 768px) {{
                .container {{
                    padding: 1rem;
                }}
                
                .grid-2 {{
                    grid-template-columns: 1fr;
                }}
            }}
        </style>
    </head>
    <body>
        <header>
            <h1>Website Analysis: {business_name}</h1>
            <p>Source: <a href="{url}" style="color: white; text-decoration: underline;">{url}</a></p>
        </header>
        
        <div class="container">
            <div class="meta">
                <p>Analysis generated on {timestamp}</p>
                <p>Site structure: {page_count} pages identified ({pages_sample})</p>
            </div>
            
            <div class="section">
                <h2>Business Specification</h2>
                
                <h3>Business Overview</h3>
                <p><strong>Business Name:</strong> {business_name}</p>
                <p><strong>Business Type:</strong> {business_type}</p>
                <p><strong>Industry:</strong> {business_overview.get('industry', 'Not specified')}</p>
                <p><strong>Size Estimate:</strong> {business_overview.get('size_estimate', 'Not specified')}</p>
                
                <h3>Target Audience</h3>
                <div class="grid-2">
                    <div>
                        <p><strong>Demographics:</strong> {target_audience.get('demographics', 'Not specified') if not isinstance(target_audience.get('demographics'), list) else ', '.join(target_audience.get('demographics'))}</p>
                        <p><strong>Needs:</strong> {target_audience.get('needs', 'Not specified') if not isinstance(target_audience.get('needs'), list) else ', '.join(target_audience.get('needs'))}</p>
                    </div>
                    <div>
                        <p><strong>Pain Points:</strong> {target_audience.get('pain_points', 'Not specified') if not isinstance(target_audience.get('pain_points'), list) else ', '.join(target_audience.get('pain_points'))}</p>
                    </div>
                </div>
                
                <h3>Value Proposition</h3>
                <p>{value_proposition}</p>
                
                <h3>Products/Services</h3>
                <p>{products_services}</p>
                
                {products_html}
                
                {testimonials_html}
                
                <h3>Brand Position & Key Differentiators</h3>
                <p><strong>Market Approach:</strong> {market_approach}</p>
                <p><strong>Key Differentiators:</strong> {key_differentiators}</p>
            </div>
            
            <div class="section">
                <h2>Brand Specification</h2>
                
                <h3>Brand Identity</h3>
                <p><strong>Personality Traits:</strong> {personality_traits}</p>
                <p><strong>Character:</strong> {brand_identity.get('character', 'Not specified')}</p>
                
                <h3>Color Palette</h3>
                <div class="color-swatches">
                    {color_swatches}
                </div>
                
                <h3>Typography</h3>
                <p><strong>Fonts:</strong> {fonts_display}</p>
                <p><strong>Impact:</strong> {typography.get('impact', 'Not specified') if isinstance(typography, dict) else 'Not specified'}</p>
                
                <h3>Visual Elements</h3>
                <p><strong>Layout Style:</strong> {visual_elements.get('layout_style', 'Not specified')}</p>
                <p><strong>Imagery Approach:</strong> {visual_elements.get('imagery_approach', 'Not specified')}</p>
                
                <h3>Voice & Tone</h3>
                <p><strong>Communication Style:</strong> {communication_style}</p>
                <p><strong>Language:</strong> {language}</p>
                
                <h3>Brand Values</h3>
                <div>{brand_values_display}</div>
                
                <h3>Emotional Appeal</h3>
                <div>{emotional_appeal_display}</div>
            </div>
        </div>
        
        <footer>
            <p>Generated by Website Cloner Tool</p>
        </footer>
    </body>
    </html>
    """
    
    return html

def save_html_summary(html_content, url, output_dir="output"):
    """
    Save HTML summary to file.
    
    Args:
        html_content (str): HTML content to save
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
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{domain}_{timestamp}.html"
        
        # Full path
        filepath = os.path.join(output_dir, filename)
        
        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        logging.info(f"HTML summary saved to {filepath}")
        return filepath
        
    except Exception as e:
        logging.error(f"Error saving HTML summary: {str(e)}")
        return None

if __name__ == "__main__":
    # Test with sample data
    sample_url = "https://example.com"
    
    sample_business_spec = {
        "business_overview": {
            "name": "Example Company",
            "type": "SaaS/Software",
            "industry": "Technology",
            "size_estimate": "Small (10-50 employees)"
        },
        "target_audience": {
            "demographics": "Business professionals, 30-50 years old",
            "needs": "Efficient workflow solutions",
            "pain_points": "Time-consuming manual processes"
        },
        "value_proposition": "Streamlining business workflows to save time and reduce errors",
        "products_services_offered": "Cloud-based workflow automation software",
        "brand_position_market_approach": "Premium solution with personalized support",
        "key_differentiators": "User-friendly interface, excellent customer service"
    }
    
    sample_brand_spec = {
        "brand_identity": {
            "name": "Example Company",
            "personality_traits": ["Professional", "Innovative", "Reliable"],
            "character": "Helpful expert"
        },
        "color_palette": {
            "#4a90e2": "Trust and reliability",
            "#34495e": "Professionalism",
            "#2ecc71": "Growth and progress"
        },
        "typography": {
            "fonts": ["Helvetica", "Arial"],
            "impact": "Clean, modern, easy to read"
        },
        "visual_elements": {
            "layout_style": "Minimalist and organized",
            "imagery_approach": "Simple illustrations and icons"
        },
        "voice_tone": {
            "communication_style": "Professional but approachable",
            "language": "Clear, concise, jargon-free"
        },
        "brand_values": "Efficiency, reliability, innovation",
        "emotional_appeal": "Confidence and peace of mind"
    }
    
    sample_sitemap = {
        "pages": {
            "/": {"title": "Home"},
            "/about": {"title": "About Us"},
            "/features": {"title": "Features"},
            "/pricing": {"title": "Pricing"},
            "/contact": {"title": "Contact"}
        }
    }
    
    sample_design = {
        "colors": {
            "#4a90e2": 10,
            "#34495e": 8,
            "#2ecc71": 5
        },
        "fonts": ["Helvetica", "Arial"],
        "layout": {"responsive": True}
    }
    
    html_content = generate_html_summary(
        sample_url, 
        sample_business_spec, 
        sample_brand_spec, 
        sample_sitemap, 
        sample_design
    )
    
    output_path = save_html_summary(html_content, sample_url)
    if output_path:
        print(f"Sample HTML summary saved to: {output_path}") 