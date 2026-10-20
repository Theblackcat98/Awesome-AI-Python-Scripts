import datetime

def generate_html_summary(url, business_spec, brand_spec, sitemap_data, design_data, content_data=None):
    """
    Generate an HTML summary of the website analysis.
    
    Args:
        url (str): The URL of the website.
        business_spec (dict): Business specification data.
        brand_spec (dict): Brand specification data.
        sitemap_data (dict): Sitemap data.
        design_data (dict): Design data.
        content_data (dict, optional): Content data.
        
    Returns:
        str: HTML content.
    """
    try:
        print(f"Generating HTML for {url}")
        print(f"Business spec keys: {list(business_spec.keys())}")
        print(f"Brand spec keys: {list(brand_spec.keys())}")
        
        # Default values if data is missing
        business_name = "Unknown Business"
        business_type = "Unknown Type"
        business_industry = "Not specified"
        demographics = []
        products = []
        brand_personality = []
        primary_colors = []
        testimonials = []
        
        # Get business overview - handle different key naming conventions
        business_overview = {}
        for key in ['business_overview', 'Business_Overview', 'BusinessOverview']:
            if key in business_spec:
                business_overview = business_spec[key]
                break
        
        if business_overview:
            # Try different naming formats for name
            for name_key in ['name', 'Name']:
                if name_key in business_overview:
                    business_name = business_overview[name_key]
                    break
            
            # Try different naming formats for type
            for type_key in ['type', 'Type']:
                if type_key in business_overview:
                    business_type = business_overview[type_key]
                    break
            
            # Try different naming formats for industry
            for industry_key in ['industry', 'Industry']:
                if industry_key in business_overview:
                    business_industry = business_overview[industry_key]
                    break
        
        # Get target audience - handle both object and list structures
        target_audience_html = ""
        target_audience = {}
        for key in ['target_audience', 'Target_Audience', 'TargetAudience']:
            if key in business_spec:
                target_audience = business_spec[key]
                break
        
        if target_audience:
            # Handle Demographics as either string, object, or list
            demographics = []
            for key in ['demographics', 'Demographics']:
                if key in target_audience:
                    demographics = target_audience[key]
                    break
            
            if demographics:
                if isinstance(demographics, str):
                    target_audience_html += f"<p><strong>Demographics:</strong> {demographics}</p>"
                elif isinstance(demographics, list):
                    # If it's a list of dictionaries, extract relevant info
                    if demographics and isinstance(demographics[0], dict):
                        demo_items = []
                        for demo in demographics:
                            if 'age_range' in demo:
                                demo_items.append(f"Age: {demo['age_range']}")
                            if 'interests' in demo and isinstance(demo['interests'], list):
                                demo_items.append(f"Interests: {', '.join(demo['interests'])}")
                        if demo_items:
                            target_audience_html += f"""
                            <p><strong>Demographics:</strong></p>
                            <ul>
                                {"".join(f"<li>{item}</li>" for item in demo_items)}
                            </ul>
                            """
                    else:
                        target_audience_html += f"""
                        <p><strong>Demographics:</strong></p>
                        <ul>
                            {"".join(f"<li>{item}</li>" for item in demographics)}
                        </ul>
                        """
            
            # Handle Needs as either string or list
            needs = []
            for key in ['needs', 'Needs']:
                if key in target_audience:
                    needs = target_audience[key]
                    break
            
            if needs:
                if isinstance(needs, str):
                    target_audience_html += f"<p><strong>Needs:</strong> {needs}</p>"
                elif isinstance(needs, list):
                    target_audience_html += f"""
                    <p><strong>Needs:</strong></p>
                    <ul>
                        {"".join(f"<li>{item}</li>" for item in needs)}
                    </ul>
                    """
            
            # Handle Pain Points as either string or list
            pain_points = []
            for key in ['pain_points', 'Pain_Points', 'PainPoints']:
                if key in target_audience:
                    pain_points = target_audience[key]
                    break
            
            if pain_points:
                if isinstance(pain_points, str):
                    target_audience_html += f"<p><strong>Pain Points:</strong> {pain_points}</p>"
                elif isinstance(pain_points, list):
                    target_audience_html += f"""
                    <p><strong>Pain Points:</strong></p>
                    <ul>
                        {"".join(f"<li>{item}</li>" for item in pain_points)}
                    </ul>
                    """
        
        # Get products and services
        products_html = ""
        product_items = []
        
        # Look for products in different formats
        for key in ['products_services_offered', 'Products_Services_Offered', 'ProductsServicesOffered']:
            if key in business_spec:
                products = business_spec[key]
                break
        
        if products:
            if isinstance(products, list):
                # Handle list of product items
                for product in products:
                    if isinstance(product, dict):
                        product_name = product.get('name', 'Unnamed Product')
                        product_desc = product.get('details', product.get('description', 'No description'))
                        product_price = product.get('price', 'Price not specified')
                        
                        # If details is a list, it might contain specific offerings
                        if isinstance(product_desc, list) and all(isinstance(item, dict) for item in product_desc):
                            offerings = []
                            for item in product_desc:
                                origin = item.get('origin', '')
                                price = item.get('price_from', '')
                                if origin and price:
                                    offerings.append(f"{origin}: {price}")
                            if offerings:
                                product_desc = "<br>".join(offerings)
                        
                        product_items.append({
                            "name": product_name,
                            "description": product_desc,
                            "price": product_price
                        })
            elif isinstance(products, dict):
                # Handle dictionary structure
                if 'Coffee_Subscriptions' in products:
                    product_items.append({
                        "name": "Coffee Subscription",
                        "description": products.get('Coffee_Subscriptions', {}).get('Description', 'Subscription service'),
                        "price": products.get('Coffee_Subscriptions', {}).get('Pricing', 'Price varies')
                    })
                
                if 'In_Store_Purchases' in products and 'Offerings' in products['In_Store_Purchases']:
                    for item in products['In_Store_Purchases']['Offerings']:
                        product_items.append({
                            "name": item.get('Type', 'Coffee'),
                            "description": "In-store purchase option",
                            "price": item.get('Price', 'Price not specified')
                        })
                
                if 'Merchandise' in products and 'Description' in products['Merchandise']:
                    for item in products['Merchandise']['Description']:
                        product_items.append({
                            "name": item.get('Name', 'Merchandise Item'),
                            "description": "Branded merchandise",
                            "price": item.get('Price', 'Price not specified')
                        })
        
        # Generate products HTML
        if product_items:
            products_html = f"""
            <div class="grid">
                {"".join(f'<div class="card"><h4>{product.get("name", "Unnamed Product")}</h4><p>{product.get("description", "No description available")}</p><p><strong>Price:</strong> {product.get("price", "Not specified")}</p></div>' for product in product_items)}
            </div>
            """
        
        # Get brand identity
        brand_personality_html = ""
        brand_identity = {}
        
        # Check for different brand identity keys
        for key in ['brand_identity', 'BrandIdentity', 'Brand Identity']:
            if key in brand_spec:
                brand_identity = brand_spec[key]
                break
        
        if brand_identity:
            # Get personality traits 
            for key in ['personality_traits', 'PersonalityTraits']:
                if key in brand_identity:
                    brand_personality = brand_identity[key]
                    break
            
            if brand_personality:
                if isinstance(brand_personality, list):
                    brand_personality_html = f'<p><strong>Personality Traits:</strong> {", ".join(brand_personality)}</p>'
                else:
                    brand_personality_html = f'<p><strong>Personality Traits:</strong> {brand_personality}</p>'
        
        # Get color palette
        color_palette_html = ""
        color_palette = {}
        
        # Check for different color palette keys
        for key in ['color_palette', 'ColorPalette', 'Color Palette']:
            if key in brand_spec:
                color_palette = brand_spec[key]
                break
        
        if color_palette:
            # Check different keys for primary colors
            primary_colors_data = None
            for key in ['primary_colors', 'PrimaryColors']:
                if key in color_palette:
                    primary_colors_data = color_palette[key]
                    break
            
            if primary_colors_data:
                color_swatches = []
                if isinstance(primary_colors_data, list):
                    # Handle list of color objects
                    for color in primary_colors_data:
                        color_hex = color.get("color", "#ccc")
                        color_meaning = color.get("meaning", "Not specified")
                        color_swatches.append(f'<p><span class="color-swatch" style="background-color: {color_hex}"></span> {color_hex} - {color_meaning}</p>')
                elif isinstance(primary_colors_data, dict):
                    # Handle dictionary of colors
                    for color_hex, info in primary_colors_data.items():
                        if isinstance(info, dict):
                            color_meaning = info.get('meaning', info.get('description', 'Not specified'))
                        else:
                            color_meaning = info
                        color_swatches.append(f'<p><span class="color-swatch" style="background-color: {color_hex}"></span> {color_hex} - {color_meaning}</p>')
                
                if color_swatches:
                    color_palette_html = "".join(color_swatches)
        
        # Get testimonials
        testimonials_html = ""
        
        # Try different paths to testimonials
        testimonials = []
        
        # Try from Communication_Style_Tone/communication_style_tone
        for key in ['communication_style_tone', 'Communication_Style_Tone']:
            if key in business_spec:
                communication = business_spec[key]
                if isinstance(communication, dict):
                    # Check different keys for testimonials
                    for t_key in ['examples_from_testimonials', 'customer_testimonials']:
                        if t_key in communication:
                            testimonials = communication[t_key]
                            break
                break
        
        # If no testimonials found, check brand spec
        if not testimonials:
            for key in ['emotional_appeal', 'EmotionalAppeal', 'Emotional Appeal']:
                if key in brand_spec:
                    emotional = brand_spec[key]
                    if isinstance(emotional, dict) and 'customer_testimonials' in emotional:
                        testimonials = emotional['customer_testimonials']
                        break
        
        # Format testimonials to HTML
        if testimonials:
            if all(isinstance(t, str) for t in testimonials):
                testimonials_html = "".join(f'<div class="testimonial">"{testimonial}"</div>' for testimonial in testimonials)
            else:
                # Handle more complex testimonial structures if needed
                pass
        
        # Generate HTML
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Website Analysis: {business_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 0; }}
                header {{ background-color: #212121; color: white; padding: 2rem; text-align: center; }}
                h1, h2, h3, h4 {{ margin-top: 1.5rem; margin-bottom: 1rem; }}
                .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
                .section {{ background-color: #f9f9f9; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); padding: 2rem; margin-bottom: 2rem; }}
                .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }}
                .card {{ border: 1px solid #ddd; border-radius: 8px; padding: 1rem; }}
                .color-swatch {{ display: inline-block; width: 24px; height: 24px; margin-right: 8px; border: 1px solid #ddd; vertical-align: middle; }}
                footer {{ background-color: #212121; color: white; text-align: center; padding: 1.5rem; }}
                .testimonial {{ background-color: white; border-left: 4px solid #555; padding: 1rem; margin-bottom: 1rem; }}
            </style>
        </head>
        <body>
            <header>
                <h1>Website Analysis: {business_name}</h1>
                <p>Source: <a href="{url}" style="color: white; text-decoration: underline;">{url}</a></p>
            </header>
            
            <div class="container">
                <div class="section">
                    <h2>Business Specification</h2>
                    
                    <h3>Business Overview</h3>
                    <p><strong>Business Name:</strong> {business_name}</p>
                    <p><strong>Business Type:</strong> {business_type}</p>
                    <p><strong>Industry:</strong> {business_industry}</p>
                    
                    <h3>Target Audience</h3>
                    {target_audience_html}
                    
                    <h3>Products and Services</h3>
                    {products_html}
                </div>
                
                <div class="section">
                    <h2>Brand Specification</h2>
                    
                    <h3>Brand Identity</h3>
                    {brand_personality_html}
                    
                    <h3>Color Palette</h3>
                    {color_palette_html}
                    
                    <h3>Testimonials</h3>
                    {testimonials_html}
                </div>
            </div>
            
            <footer>
                <p>Generated by Website Cloner Tool</p>
                <p>Generated at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </footer>
        </body>
        </html>
        """
        
        return html_content
        
    except Exception as e:
        print(f"Error generating HTML summary: {str(e)}")
        # Return a simple error message as HTML
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Error Generating Summary</title></head>
        <body>
            <h1>Error Generating Website Analysis</h1>
            <p>An error occurred while generating the HTML summary: {str(e)}</p>
            <p>Please check the logs for more details.</p>
        </body>
        </html>
        """
