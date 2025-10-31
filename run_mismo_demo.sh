#!/bin/bash
# Quick Start Script for MISMO Integration Demo

echo "=================================================="
echo "  MORTGAGE DOCUMENT PROCESSING - MISMO DEMO"
echo "=================================================="
echo ""

# Check if we're in the right directory
if [ ! -f "mismo_demo.py" ]; then
    echo "❌ Error: Please run this script from the doc_first_ui directory"
    exit 1
fi

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

echo "✓ Found Python: $(python3 --version)"
echo ""

# Check for virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Check if requirements are installed
if ! python -c "import pdfplumber" 2>/dev/null; then
    echo "📥 Installing requirements..."
    pip install -q -r requirements.txt
    echo "✓ Requirements installed"
    echo ""
else
    echo "✓ Requirements already installed"
    echo ""
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found"
    echo "   Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✓ Created .env file"
        echo "   Edit .env to add your OPENAI_API_KEY (optional)"
    else
        echo "   Warning: .env.example not found"
    fi
    echo ""
fi

# Check for Elmo James documents
ELMO_COUNT=$(ls -1 elmo_james*.pdf 2>/dev/null | wc -l | tr -d ' ')
if [ "$ELMO_COUNT" -eq 0 ]; then
    echo "⚠️  No Elmo James documents found in current directory"
    echo "   Expected files like: elmo_james_w2_2024.pdf, elmo_james_paystub_oct2025.pdf"
    echo ""
else
    echo "✓ Found $ELMO_COUNT Elmo James documents"
    echo ""
fi

# Create output directory
if [ ! -d "output" ]; then
    mkdir output
    echo "✓ Created output directory"
    echo ""
fi

echo "=================================================="
echo "  READY TO RUN DEMO"
echo "=================================================="
echo ""
echo "The demo will:"
echo "  1. Extract data from all PDF documents"
echo "  2. Apply Freddie Mac underwriting guidelines"
echo "  3. Generate MISMO 3.4 XML file"
echo "  4. Produce gap analysis report"
echo "  5. Save results to output/ directory"
echo ""
echo "Press Enter to start the demo, or Ctrl+C to cancel..."
read

# Run the demo
python mismo_demo.py

echo ""
echo "=================================================="
echo "  DEMO COMPLETE"
echo "=================================================="
echo ""
echo "Check the output/ directory for results:"
echo "  • mortgage_application.xml - MISMO XML file"
echo "  • gap_analysis_report.txt - Gap analysis"
echo "  • mortgage_application.json - Complete data"
echo "  • extracted_data.json - Structured data"
echo ""
echo "For more information, see:"
echo "  • MISMO_GUIDE.md - Complete guide"
echo "  • README.md - Main documentation"
echo "  • MISMO_IMPLEMENTATION_SUMMARY.md - What was built"
echo ""
