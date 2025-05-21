# Website Cloner: Design Document

## 1. Requirements

### Problem Statement
Many businesses and developers need to analyze existing websites to understand their structure, design patterns, and business communication approach. This understanding helps in creating similar or competitive websites and understanding market positioning.

### User Needs
- Analyze a website's structure and content
- Extract design elements like colors and typography
- Understand the business type and positioning
- Create a comprehensive brand and business specification
- Visualize the gathered information in a readable format

### Project Scope
The Website Cloner will:
1. Accept a URL input
2. Crawl and analyze the website's structure (sitemap)
3. Extract content (text, colors, design elements, business type)
4. Generate business and brand specification documents
5. Create a visual HTML summary using Ollama (phi4:latest model)

### Success Criteria
- Successfully extract website content from 90% of common websites
- Identify key design elements with 80% accuracy
- Generate useful business and brand specifications
- Create a visually appealing summary page

## 2. Flow Design

The overall flow follows a Map-Reduce design pattern to efficiently process website topics:

```mermaid
flowchart TD
    input[URL Input] --> fetch[Fetch Website]
    fetch --> map[Map Phase]
    
    subgraph map[Map Phase]
        direction LR
        sitemap_batch[Sitemap Batch] 
        design_batch[Design Elements Batch]
        content_batch[Content Batch]
    end
    
    map --> reduce[Reduce Phase]
    
    subgraph reduce[Reduce Phase]
        combine[Combine Results]
        generate[Generate Specifications]
    end
    
    reduce --> visualize[Create HTML Summary]
    visualize --> llm[Ollama LLM]
    llm --> template[Apply Template]
    template --> output[HTML Output]
```

```mermaid
flowchart TD
    %% Core Architecture Files
    main["main.py"]
    flow["flow.py"]
    nodes["nodes.py"]
    
    %% Main tools
    analyze["analyze_website.py"]
    gen_summary["generate_summary.py"]
    llm_summary["generate_llm_summary.py"]
    render["render_html.py"]
    
    %% Test Files
    subgraph tests[tests/]
        test_llm["test_llm_generation.py"]
        test_extraction["test_extraction.py"]
        test_flow["test_flow.py"]
    end
    
    %% Templates
    templates["utils/templates/template_generator.py"]
    html_template["utils/templates/html_template.html"]
    
    %% Data files
    specs["output/specs.json"]
    sample_specs["output/sample_specs.json"]
    html_output["output/website_summary.html"]
    sample_output["output/sample_llm_summary.html"]
    
    %% Main Application Flow
    main -->|orchestrates| flow
    flow -->|manages| nodes
    nodes -->|processing| analyze
    
    %% Map-Reduce Implementation
    nodes -->|SitemapBatchNode| map_phase
    nodes -->|DesignElementsBatchNode| map_phase
    nodes -->|ContentBatchNode| map_phase
    subgraph map_phase[Map Phase]
    end
    
    nodes -->|CombineResultsNode| reduce_phase
    nodes -->|GenerateSpecsNode| reduce_phase
    subgraph reduce_phase[Reduce Phase]
    end
    
    map_phase --> reduce_phase
    reduce_phase -->|creates| specs
    
    %% HTML Generation Flow - CORRECTED DATA FLOW
    specs -->|input to| gen_summary
    gen_summary -->|passes specs.json path| llm_summary
    gen_summary -->|passes specs.json path| render
    llm_summary -->|reads specs.json| specs
    render -->|reads specs.json| specs
    llm_summary -->|generates| html_output
    render -->|generates| html_output
    
    %% Test workflow
    test_llm -->|creates| sample_specs
    test_llm -->|passes sample specs path| llm_summary
    llm_summary -->|reads sample specs| sample_specs
    llm_summary -->|test output| sample_output
    
    %% Template connections
    templates -->|provides| html_template
    html_template -->|used by| llm_summary
    
    %% API connection
    ollama[("Ollama API\nphi4:latest")]
    llm_summary -->|calls| ollama

    %% Style
    classDef coreFiles fill:#ff9999,stroke:#cc0000
    classDef primaryTools fill:#b3e0ff,stroke:#0066cc
    classDef secondaryTools fill:#ffcc99,stroke:#ff8000
    classDef dataFiles fill:#d9f2d9,stroke:#339933,font-weight:bold
    classDef apis fill:#e6ccff,stroke:#6600cc
    classDef phases fill:#ffff99,stroke:#ffcc00,opacity:0.7
    classDef testFiles fill:#ccccff,stroke:#6666cc
    classDef dataFlow stroke:#ff0000,stroke-width:2.5px
    
    class main,flow,nodes coreFiles
    class analyze,gen_summary,llm_summary primaryTools
    class render,templates secondaryTools
    class specs,sample_specs,html_output,sample_output,html_template dataFiles
    class ollama apis
    class map_phase,reduce_phase phases
    class tests,test_llm,test_extraction,test_flow testFiles
```

### Map-Reduce Pattern Implementation

The Map-Reduce pattern will be implemented as follows:

1. **Map Phase**:
   - Each topic (sitemap, design elements, content) is processed in parallel using batch processing
   - For each topic, a BatchNode will process one page at a time
   - This approach allows for efficient processing of larger websites with many pages

2. **Reduce Phase**:
   - Results from individual page processing are combined
   - Combined data is used to generate comprehensive specifications
   - Final specifications reflect the entire website rather than individual pages

## 3. Batch Processing Nodes

### SitemapBatchNode
- **Purpose**: Process each page to build a complete sitemap
- **Input**: List of discovered URLs
- **Processing**: Extract page structure and links from each URL
- **Output**: Complete sitemap with all pages and their structure

### DesignElementsBatchNode
- **Purpose**: Process each page to extract design elements
- **Input**: List of pages from sitemap
- **Processing**: Extract colors, fonts, and layout from each page
- **Output**: Aggregated design elements data with frequency information

### ContentBatchNode
- **Purpose**: Process each page to extract content
- **Input**: List of pages from sitemap
- **Processing**: Extract text, business info, and page purpose from each page
- **Output**: Combined content data from all pages

## 4. Utilities

### External API Dependencies
1. **Ollama API**: For generating business and brand specifications and HTML summaries
   - Default Model: phi4:latest
   - Input: Website content and design elements
   - Output: Structured JSON specifications and HTML summary
   - Endpoint: http://localhost:11434/api/generate

### Key Utility Functions
1. **get_website_content** (`utils/get_website_content.py`)
   - Input: URL string
   - Output: BeautifulSoup object, status code, error (if any)
   - Necessity: Core functionality to retrieve website HTML

2. **build_sitemap** (`utils/build_sitemap.py`)
   - Input: Starting URL, max pages to crawl
   - Output: Dictionary with site structure
   - Necessity: Required to understand website organization

3. **extract_design_elements** (`utils/extract_design_elements.py`)
   - Input: BeautifulSoup object, URL
   - Output: Dictionary of design elements (colors, fonts, etc.)
   - Necessity: Required for brand specification

4. **extract_content** (`utils/extract_content.py`)
   - Input: BeautifulSoup object, URL
   - Output: Dictionary of content (text, business info, etc.)
   - Necessity: Required for business specification

5. **generate_specs** (`utils/generate_specs.py`)
   - Input: Content data, design data, sitemap data
   - Output: Business and brand specifications (JSON)
   - Necessity: Core analysis functionality

6. **generate_html_from_specs** (`generate_llm_summary.py`)
   - Input: Specs JSON file path, Output HTML file path
   - Process: Sends specifications to Ollama LLM with HTML template
   - Output: Complete HTML summary
   - Necessity: Core visualization functionality

7. **render_html** (`render_html.py`)
   - Input: Specs JSON file path, Output HTML file path
   - Process: Template-based HTML generation (fallback method)
   - Output: HTML summary
   - Necessity: Fallback if LLM generation fails

8. **get_template** (`utils/templates/template_generator.py`)
   - Input: Optional template path
   - Output: HTML template string
   - Necessity: Provides structure for LLM-generated HTML

## 5. Data Structure Design

### Shared Store
The data will flow through the application in a shared dictionary structure:

```
shared = {
    "url": "https://example.com",
    "soup": BeautifulSoup object,
    "pages_to_process": [
        "https://example.com",
        "https://example.com/about",
        ...
    ],
    "sitemap": {
        "base_url": "https://example.com",
        "pages": {
            "/": {
                "title": "Home",
                "headers": {...},
                "paragraphs_count": 10,
                "links": [...]
            },
            "/about": {...}
        }
    },
    "design": {
        "colors": {"#hexcode": count, ...},
        "fonts": ["font1", "font2", ...],
        "layout": {
            "sections": 5,
            "columns": true,
            "responsive": true
        },
        "images": {
            "count": 15,
            "types": {"jpg": 10, "png": 5}
        },
        "pages_data": {
            "/": {
                "colors": {...},
                "fonts": [...],
                ...
            },
            "/about": {
                ...
            }
        }
    },
    "content": {
        "page_title": "Example Website",
        "main_content": {
            "header": [...],
            "main": [...],
            "footer": [...]
        },
        "business_info": {
            "name": "Example Company",
            "tagline": "Making the web simple",
            "contact": {...},
            "social_media": [...]
        },
        "business_type": {
            "type": "SaaS/Software",
            "confidence": 85
        },
        "word_count": 1500,
        "pages_data": {
            "/": {
                "content": {...},
                "business_info": {...}
            },
            "/about": {
                ...
            }
        }
    },
    "business_spec": {...},
    "brand_spec": {...},
    "html_summary": "<!DOCTYPE html>...",
    "output_path": "/path/to/output.html"
}
```

### Specifications Output (specs.json)
The specifications are stored in JSON format:

```json
{
  "url": "https://example.com",
  "business_spec": {
    "business_overview": {
      "name": "Example Company",
      "type": "SaaS/Software",
      "industry": "Technology"
    },
    "target_audience": {
      "demographics": ["Business professionals", "IT managers"],
      "needs": ["Efficient workflow solutions"],
      "pain_points": ["Time-consuming manual processes"]
    },
    "value_proposition": {
      "problem_solution": "Streamlining business workflows to save time and reduce errors"
    },
    "products_services_offered": {
      "specific_products": [
        {"name": "Product A", "price": "$99/month", "description": "Core service offering"}
      ]
    }
  },
  "brand_spec": {
    "brand_identity": {
      "personality_traits": ["Professional", "Innovative", "Reliable"]
    },
    "color_palette": {
      "primary_colors": [
        {"color": "#4a90e2", "meaning": "Trust and reliability"},
        {"color": "#34495e", "meaning": "Professionalism"}
      ]
    },
    "typography": {
      "fonts": {
        "Helvetica": "Used for headings",
        "Arial": "Used for body text"
      }
    }
  }
}
```

## 6. Implementation Plan

### Phase 1: Core Functionality
1. Implement website content retrieval
2. Implement batch processing for sitemap building
3. Implement batch processing for design element extraction
4. Implement batch processing for content extraction

### Phase 2: Analysis
1. Implement reduce functionality to combine batch results
2. Implement specification generation with Ollama integration

### Phase 3: Visualization
1. Implement Ollama-based HTML summary generation using phi4:latest model
2. Implement template-based HTML generation as fallback
3. Create template management system

### Phase 4: Testing & Optimization
1. Test with various website types
2. Optimize batch processing efficiency
3. Improve extraction accuracy

## 7. HTML Generation Options

### Option 1: LLM-based Generation (Primary)
- Uses Ollama's phi4:latest model to generate HTML
- Advantages:
  - Better handles complex JSON structures
  - Flexible interpretation of data
  - More natural language descriptions
  - Adapts to different data formats
- Implementation:
  1. Load specs.json
  2. Get HTML template
  3. Create prompt with template and specs data
  4. Call Ollama API with prompt
  5. Save generated HTML to file

### Option 2: Template-based Generation (Fallback)
- Uses a predefined template with conditional logic
- Advantages:
  - No external API dependency
  - Faster execution
  - More predictable output
- Implementation:
  1. Load specs.json
  2. Extract key information
  3. Apply template with extracted data
  4. Save generated HTML to file
