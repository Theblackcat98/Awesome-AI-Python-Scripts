# Website Cloner

A tool to clone and analyze websites, extract business and brand specifications, and generate HTML summaries.

## Overview

This project provides tools to:

1. Extract website content and analyze its structure
2. Generate business and brand specifications based on the extracted content
3. Create HTML summaries of the specifications using Ollama-based LLM generation

## Features

- Scrapes website content from a provided URL
- Builds a sitemap by crawling the website structure
- Extracts design elements including colors, fonts, and layout
- Analyzes content to determine business type and brand identity
- Generates detailed business and brand specifications
- Creates a visual HTML summary of the analysis using Ollama
- Implements the Map-Reduce pattern for efficient processing of large websites

## Requirements

- Python 3.8+
- Required packages listed in `requirements.txt`
- Ollama installed and running (for LLM-based HTML generation)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/website-cloner.git
cd website-cloner
```

2. Run the setup script (recommended):
```bash
./setup.sh
```

This will:
- Create a virtual environment
- Install dependencies
- Create necessary directories
- Set up a default .env file for Ollama configuration

Or manually:

3. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Set up your Ollama:
   - Install Ollama from [https://ollama.com](https://ollama.com)
   - Pull the model you want to use:
   ```bash
   ollama pull llama2  # Or another model of your choice
   ```
   - Start the Ollama service:
   ```bash
   ollama serve
   ```
   - Customize the model and API endpoint in `.env`:
   ```
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama2
   ```

## Usage

### 1. Analyze a website and generate specifications

```bash
python analyze_website.py --url https://example.com --output output/specs.json
```

This extracts content from the website and generates a `specs.json` file containing business and brand specifications.

### 2. Generate an HTML summary from specifications

```bash
python generate_summary.py --specs output/specs.json --output output/website_summary.html
```

This generates an HTML summary of the website specifications using Ollama. If LLM generation fails, it falls back to the original template-based method.

### 3. (Alternative) Generate HTML summary using the original template method

```bash
python render_html.py output/specs.json output/simple_summary.html
```

## File Structure

- `analyze_website.py` - Extracts website content and generates specifications
- `generate_summary.py` - Wrapper script to generate HTML summaries (uses LLM by default)
- `generate_llm_summary.py` - Uses Ollama to generate HTML summaries
- `render_html.py` - Original template-based HTML generator (fallback method)
- `test_llm_generation.py` - Test script for LLM-based HTML generation with sample data
- `utils/templates/template_generator.py` - Manages HTML templates for LLM generation
- `utils/templates/html_template.html` - Default HTML template

## How It Works

### Website Analysis

1. The tool scrapes the target website using `analyze_website.py`
2. It extracts text content, images, colors, and structure
3. Uses Ollama to analyze the content and generate business specifications
4. Saves the specifications to a JSON file

### HTML Summary Generation

#### LLM-based Approach (New)
1. Reads the specs.json file containing website specifications
2. Sends the specifications to Ollama with a prompt to generate HTML
3. The LLM processes the data structure and produces formatted HTML
4. The HTML is saved to the specified output file

#### Template-based Approach (Original/Fallback)
1. Reads the specs.json file
2. Applies a predefined template to generate HTML
3. Uses conditional logic to handle different data structures
4. The HTML is saved to the specified output file

## Testing

To test the LLM-based HTML generation with sample data:

```bash
python test_llm_generation.py
```

This creates a sample specs.json file and generates an HTML summary using the Ollama LLM approach.

## Customizing Templates

To customize the HTML template used by the LLM:

1. Edit the template in `utils/templates/html_template.html`
2. Or create a new template and update the path in `generate_llm_summary.py`

The template provides structure and styling guidance to the LLM while allowing it to fill in the content based on the specifications.

## Architecture

The Website Cloner implements a Map-Reduce pattern for efficient processing:

### Map Phase
- **InitialFetchNode**: Fetches the main page and prepares for crawling
- **SitemapBatchNode**: Builds a sitemap by crawling the website structure
- **DesignElementsBatchNode**: Processes pages in batches to extract design elements
- **ContentBatchNode**: Processes pages in batches to extract content

### Reduce Phase
- **CombineResultsNode**: Aggregates results from all processed pages
- **GenerateSpecsNode**: Generates business and brand specifications
- **CreateHtmlSummaryNode**: Creates a visual HTML summary

## Utility Functions

The Website Cloner provides utility functions for:

1. **Getting website content** - Scrapes the HTML content of a website
2. **Building a sitemap** - Creates a structured representation of the website's pages
3. **Extracting design elements** - Identifies colors, fonts, and layout styles
4. **Extracting content** - Analyzes text and business information
5. **Generating specifications** - Creates business and brand specifications
6. **Creating HTML summary** - Visualizes the analysis results

## Output

The tool generates an HTML summary page that includes:

- Business specification (business type, target audience, value proposition, etc.)
- Brand specification (color palette, typography, visual elements, etc.)
- Website structure overview

The HTML summary is saved to the `output` directory with a filename based on the domain and timestamp.

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
