"""
MISMO Workflow Demo (Non-Interactive)
Automated version without input prompts for testing
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from mortgage_assistant import MortgageAssistant


def print_header(title: str):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def main():
    """Run complete MISMO workflow automatically"""
    
    print_header("MORTGAGE DOCUMENT PROCESSING WITH MISMO INTEGRATION")
    print("Processing Elmo James documents automatically...")
    print()
    
    # Check for documents
    doc_folder = Path.cwd()
    pdf_files = list(doc_folder.glob("elmo_james*.pdf"))
    
    if not pdf_files:
        print("❌ Error: No Elmo James PDF files found")
        return
    
    print(f"✓ Found {len(pdf_files)} Elmo James documents")
    
    # Initialize assistant
    print_header("STEP 1: INITIALIZING")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("ℹ️  Using rule-based classification (no API key)")
    
    assistant = MortgageAssistant(api_key=api_key)
    print("✓ Assistant initialized")
    
    # Process documents
    print_header("STEP 2: PROCESSING DOCUMENTS")
    
    results = assistant.process_document_folder(str(doc_folder), "elmo_james*.pdf")
    
    print(f"\n✓ Processed {len(results)} documents")
    
    # Show document summary
    doc_types = {}
    for result in results:
        if 'classification' in result:
            doc_type = result['classification']['document_type']
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
    
    print("\nDocument Types:")
    for doc_type, count in sorted(doc_types.items()):
        print(f"  • {doc_type}: {count}")
    
    # Analyze income
    print_header("STEP 3: INCOME ANALYSIS")
    
    try:
        income_analysis = assistant.analyze_income()
        
        if income_analysis:
            print(f"\n✓ Income analysis complete")
            print(f"   Total Monthly Income: ${income_analysis.total_monthly_income:,.2f}")
            print(f"   Meets Requirements: {'YES' if income_analysis.meets_requirements else 'NO'}")
        else:
            print("\n⚠️  Income analysis incomplete (missing documents)")
    except Exception as e:
        print(f"\n⚠️  Income analysis error: {e}")
        income_analysis = None
    
    # Map to URLA
    print_header("STEP 4: URLA MAPPING")
    
    urla_data = assistant.map_to_urla()
    completion_status = assistant.generate_urla_report(urla_data)
    
    print(f"\n✓ URLA mapping complete")
    print(f"   Completion: {completion_status['completion_percentage']}%")
    
    # Generate MISMO XML
    print_header("STEP 5: GENERATING MISMO XML")
    
    try:
        mismo_xml = assistant.generate_mismo_xml(income_analysis)
        print(f"✓ MISMO XML generated ({len(mismo_xml):,} characters)")
        print("\nFirst 500 characters:")
        print("-" * 80)
        print(mismo_xml[:500])
        print("...")
        print("-" * 80)
    except Exception as e:
        print(f"❌ Error generating MISMO XML: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Gap Analysis
    print_header("STEP 6: GAP ANALYSIS")
    
    try:
        gap_report = assistant.analyze_gaps(mismo_xml)
        print(gap_report)
        
        completion_pct = assistant.gap_analyzer.get_completion_percentage()
        print(f"\n📊 Application Completion: {completion_pct:.1f}%")
    except Exception as e:
        print(f"❌ Error in gap analysis: {e}")
        import traceback
        traceback.print_exc()
        gap_report = None
    
    # Save results
    print_header("STEP 7: SAVING RESULTS")
    
    output_dir = "output"
    
    # Create complete application
    application = assistant.create_application()
    application.to_json(f"{output_dir}/mortgage_application.json")
    
    # Save all results
    assistant.save_results(output_dir=output_dir, mismo_xml=mismo_xml, gap_report=gap_report)
    
    print("\n✓ Results saved to output/:")
    print("   • mortgage_application.xml - MISMO 3.4 XML")
    print("   • gap_analysis_report.txt - Gap analysis")
    print("   • mortgage_application.json - Complete application")
    print("   • extracted_data.json - Structured data")
    print("   • processed_documents.json - Processing details")
    
    # Final summary
    print_header("WORKFLOW COMPLETE")
    
    print(assistant.generate_summary_report(application))
    
    print("\n" + "=" * 80)
    print("✨ Demo complete! Check output/ directory for all files.")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
