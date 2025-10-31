#!/usr/bin/env python3
"""
Quick Start Script for Mortgage Application Assistant
Processes documents in the current directory and generates reports
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def check_requirements():
    """Check if required packages are installed"""
    required = ['PyPDF2', 'pdfplumber', 'fitz']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print("⚠️  Missing required packages. Installing...")
        print("\nRun: pip install -r requirements.txt\n")
        return False
    
    return True


def check_api_key():
    """Check if OpenAI API key is configured"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("\n⚠️  Warning: OPENAI_API_KEY not set")
        print("Set your API key in .env file for full AI features")
        print("The system will use rule-based extraction instead.\n")
        return False
    return True


def main():
    """Main quick start function"""
    print("=" * 70)
    print("🏠 MORTGAGE APPLICATION ASSISTANT - QUICK START")
    print("=" * 70)
    print()
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check API key (warning only)
    check_api_key()
    
    # Determine folder to process
    if len(sys.argv) > 1:
        folder = sys.argv[1]
    else:
        folder = '.'
        print(f"📁 Processing documents in current directory: {Path(folder).absolute()}")
    
    # Check folder exists
    folder_path = Path(folder)
    if not folder_path.exists():
        print(f"\n❌ Error: Folder not found: {folder}")
        sys.exit(1)
    
    # Count PDFs
    pdf_files = list(folder_path.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF file(s)\n")
    
    if len(pdf_files) == 0:
        print("❌ No PDF files found")
        print("\nUsage: python quickstart.py [folder_path]")
        sys.exit(1)
    
    # List files
    print("Documents to process:")
    for pdf in pdf_files:
        print(f"  • {pdf.name}")
    print()
    
    # Run processing
    try:
        from interactive_cli import InteractiveCLI
        
        cli = InteractiveCLI()
        cli.show_welcome()
        
        # Run full pipeline
        cli.process_documents(str(folder_path))
        cli.analyze_income()
        urla_data = cli.map_to_urla()
        
        if urla_data:
            cli.show_completion_status(urla_data)
        
        cli.create_application()
        cli.save_results()
        
        print("\n" + "=" * 70)
        print("✅ PROCESSING COMPLETE!")
        print("=" * 70)
        print("\nCheck the output/ directory for results:")
        print("  • processed_documents.json - Document classification and extraction")
        print("  • extracted_data.json - Organized extracted data")
        print("  • mortgage_application.json - Complete application")
        print("  • urla_structure.json - URLA form structure")
        print("\n")
        
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("\nPlease ensure all dependencies are installed:")
        print("  pip install -r requirements.txt\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
