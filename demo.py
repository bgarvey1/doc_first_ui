#!/usr/bin/env python3
"""
Demo Script - Process Elmo James's Documents
Demonstrates the complete workflow with the provided sample documents
"""
import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def run_demo():
    """Run the complete demo with Elmo James's documents"""
    
    print("=" * 80)
    print("🏠 MORTGAGE APPLICATION ASSISTANT - DEMO")
    print("Processing Elmo James's Mortgage Documents")
    print("=" * 80)
    print()
    
    # Check if we're in the right directory
    current_dir = Path.cwd()
    sample_files = [
        'elmo_james_w2_2025.pdf',
        'elmo_james_paystub_oct2025.pdf',
        'elmo_james_voe_2025.pdf',
        'freddie_income_guides.json',
        'URLA-2019-Borrower-v28.pdf'
    ]
    
    missing_files = []
    for file in sample_files:
        if not (current_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("⚠️  Warning: Some expected files are missing:")
        for file in missing_files:
            print(f"  - {file}")
        print()
    
    # Import after path setup
    try:
        from mortgage_assistant import MortgageAssistant
        from pdf_parser import PDFParser
        import json
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("\nPlease install requirements first:")
        print("  pip install -r requirements.txt\n")
        return
    
    # Initialize assistant
    print("Initializing Mortgage Assistant...")
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️  No OpenAI API key found. Using rule-based extraction only.")
    
    assistant = MortgageAssistant(api_key=api_key)
    
    # Process documents
    print("\n" + "-" * 80)
    print("STEP 1: Document Processing")
    print("-" * 80)
    
    results = assistant.process_document_folder(str(current_dir), "elmo_james_*.pdf")
    
    print(f"\n✅ Processed {len(results)} documents")
    
    # Show what we found
    print("\nDocument Summary:")
    doc_types = {}
    for doc in results:
        if 'classification' in doc:
            doc_type = doc['classification']['document_type']
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
    
    for doc_type, count in doc_types.items():
        print(f"  • {doc_type}: {count}")
    
    # Analyze income
    print("\n" + "-" * 80)
    print("STEP 2: Income Analysis (Freddie Mac Guidelines)")
    print("-" * 80)
    
    income_analysis = assistant.analyze_income()
    
    # Map to URLA
    print("\n" + "-" * 80)
    print("STEP 3: URLA Form Mapping")
    print("-" * 80)
    
    urla_data = assistant.map_to_urla()
    
    # Show completion status
    print("\n" + "-" * 80)
    print("STEP 4: URLA Completion Status")
    print("-" * 80)
    
    completion = assistant.generate_urla_report(urla_data)
    
    # Create application
    print("\n" + "-" * 80)
    print("STEP 5: Creating Complete Application")
    print("-" * 80)
    
    application = assistant.create_application()
    
    # Show summary
    print("\n" + "=" * 80)
    print("APPLICATION SUMMARY")
    print("=" * 80)
    
    summary = assistant.generate_summary_report(application)
    print(summary)
    
    # Save results
    print("\n" + "-" * 80)
    print("STEP 6: Saving Results")
    print("-" * 80)
    
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    assistant.save_results(str(output_dir))
    application.to_json(str(output_dir / "mortgage_application.json"))
    assistant.urla_analyzer.export_structure_to_json(str(output_dir / "urla_structure.json"))
    
    print("\n✅ All files saved to output/ directory")
    print("\nGenerated files:")
    print("  📄 output/processed_documents.json")
    print("  📄 output/extracted_data.json")
    print("  📄 output/mortgage_application.json")
    print("  📄 output/urla_structure.json")
    
    # Show sample extracted data
    print("\n" + "=" * 80)
    print("SAMPLE EXTRACTED DATA")
    print("=" * 80)
    
    if 'W2' in assistant.extracted_data:
        print("\nW-2 Data (2025):")
        w2 = assistant.extracted_data['W2'][0]
        for key, value in list(w2.items())[:5]:
            print(f"  • {key}: {value}")
    
    if 'PAYSTUB' in assistant.extracted_data:
        print("\nPaystub Data:")
        paystub = assistant.extracted_data['PAYSTUB'][0]
        for key, value in list(paystub.items())[:5]:
            print(f"  • {key}: {value}")
    
    if 'VOE' in assistant.extracted_data:
        print("\nVerification of Employment:")
        voe = assistant.extracted_data['VOE'][0]
        for key, value in list(voe.items())[:5]:
            print(f"  • {key}: {value}")
    
    print("\n" + "=" * 80)
    print("✅ DEMO COMPLETE!")
    print("=" * 80)
    print("\nNext steps:")
    print("  1. Review the generated files in output/")
    print("  2. Check mortgage_application.json for the complete application")
    print("  3. Review URLA completion status and fill missing fields")
    print("  4. Run interactive_cli.py for a guided experience")
    print()


if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
