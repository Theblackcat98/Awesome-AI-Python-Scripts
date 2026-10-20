#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p output

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOL
# Ollama API Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
EOL
    echo "Please update the .env file with your Ollama configuration"
fi

# Make main.py executable
chmod +x main.py

echo "Setup complete! You can now run: python main.py --url https://example.com"
echo "Or run individual tests: python test_flow.py https://example.com"
echo "For a full flow test: python test_flow.py https://example.com --full" 