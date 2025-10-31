#!/bin/bash
# Setup script for Mortgage Application Assistant

echo "======================================================================"
echo "🏠 MORTGAGE APPLICATION ASSISTANT - Setup"
echo "======================================================================"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

echo "✅ Python found"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

echo ""
echo "Activating virtual environment..."
source venv/bin/activate

echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""
echo "✅ Dependencies installed successfully"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your OPENAI_API_KEY"
else
    echo ""
    echo "✅ .env file already exists"
fi

# Create output directory
mkdir -p output

echo ""
echo "======================================================================"
echo "✅ SETUP COMPLETE!"
echo "======================================================================"
echo ""
echo "Next steps:"
echo "  1. Edit .env file and add your OpenAI API key"
echo "  2. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo "  3. Run the demo:"
echo "     python demo.py"
echo "  4. Or use the interactive CLI:"
echo "     python src/interactive_cli.py"
echo ""
