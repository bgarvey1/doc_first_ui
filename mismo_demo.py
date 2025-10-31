"""
MISMO Workflow Demo
Complete end-to-end demonstration of the mortgage document processing pipeline:
1. Extract data from PDF documents
2. Apply Freddie Mac underwriting guidelines
3. Generate MISMO XML
4. Analyze information gaps
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
    """Run complete MISMO workflow demonstration"""
    
    print_header("MORTGAGE DOCUMENT PROCESSING WITH MISMO INTEGRATION")
    print("This demo will:")
    print("  1. Extract data from all Elmo James PDF documents")
    print("  2. Apply Freddie Mac underwriting guidelines")
    print("  3. Generate MISMO 3.4 XML file")
    print("  4. Produce gap analysis report identifying missing information")
    print()
    
    # Check for documents
    doc_folder = Path.cwd()
    pdf_files = list(doc_folder.glob("elmo_james*.pdf"))
    
    if not pdf_files:
        print("❌ Error: No Elmo James PDF files found in current directory")
        print("Expected files like: elmo_james_w2_2024.pdf, elmo_james_paystub_oct2025.pdf, etc.")
        return
    
    print(f"✓ Found {len(pdf_files)} Elmo James documents")
    for pdf in pdf_files:
        print(f"  • {pdf.name}")
    
    input("\nPress Enter to begin processing...")
    
    # Initialize assistant
    print_header("INITIALIZING MORTGAGE ASSISTANT")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️  Warning: OPENAI_API_KEY not set")
        print("   Document classification will use rule-based methods only")
        print("   For best results, set API key in .env file")
        print()
    
    assistant = MortgageAssistant(api_key=api_key)
    print("✓ Assistant initialized")
    
    # Step 1: Process all documents
    print_header("STEP 1: PROCESSING DOCUMENTS")
    
    results = assistant.process_document_folder(str(doc_folder), "elmo_james*.pdf")
    
    print(f"\n✓ Processed {len(results)} documents")
    
    # Show document summary
    doc_types = {}
    for result in results:
        if 'classification' in result:
            doc_type = result['classification']['document_type']
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
    
    print("\nDocument Types Identified:")
    for doc_type, count in sorted(doc_types.items()):
        print(f"  • {doc_type}: {count}")
    
    input("\nPress Enter to continue to income analysis...")
    
    # Step 2: Analyze income with Freddie Mac guidelines
    print_header("STEP 2: INCOME ANALYSIS (FREDDIE MAC GUIDELINES)")
    
    income_analysis = assistant.analyze_income()
    
    if income_analysis:
        print(f"\n✓ Income analysis complete")
        print(f"   Total Monthly Income: ${income_analysis.total_monthly_income:,.2f}")
        print(f"   Meets Freddie Mac Requirements: {'YES' if income_analysis.meets_requirements else 'NO'}")
    else:
        print("\n⚠️  Income analysis could not be completed (missing required documents)")
    
    input("\nPress Enter to continue to URLA mapping...")
    
    # Step 3: Map to URLA form
    print_header("STEP 3: MAPPING TO URLA FORM")
    
    urla_data = assistant.map_to_urla()
    completion_status = assistant.generate_urla_report(urla_data)
    
    print(f"\n✓ URLA form mapping complete")
    print(f"   Fields Filled: {completion_status['filled_fields']}/{completion_status['total_fields']}")
    print(f"   Completion: {completion_status['completion_percentage']}%")
    
    input("\nPress Enter to generate MISMO XML...")
    
    # Step 4: Generate MISMO XML
    print_header("STEP 4: GENERATING MISMO 3.4 XML")
    
    mismo_xml = assistant.generate_mismo_xml(income_analysis)
    
    print(f"✓ MISMO XML generated ({len(mismo_xml)} characters)")
    print("\nSample XML (first 500 characters):")
    print("-" * 80)
    print(mismo_xml[:500] + "...")
    print("-" * 80)
    
    input("\nPress Enter to analyze information gaps...")
    
    # Step 5: Gap Analysis
    print_header("STEP 5: GAP ANALYSIS REPORT")
    
    gap_report = assistant.analyze_gaps(mismo_xml)
    print(gap_report)
    
    # Calculate completion percentage
    completion_pct = assistant.gap_analyzer.get_completion_percentage()
    
    print(f"\n📊 Application Completion: {completion_pct:.1f}%")
    
    input("\nPress Enter to save all results...")
    
    # Step 6: Save everything
    print_header("STEP 6: SAVING RESULTS")
    
    output_dir = "output"
    
    # Create complete application
    application = assistant.create_application()
    application.to_json(f"{output_dir}/mortgage_application.json")
    
    # Save all results
    assistant.save_results(output_dir=output_dir, mismo_xml=mismo_xml, gap_report=gap_report)
    
    print("\n✓ All results saved to output/ directory:")
    print("   • processed_documents.json - Document processing details")
    print("   • extracted_data.json - Structured data from all documents")
    print("   • mortgage_application.json - Complete application data")
    print("   • mortgage_application.xml - MISMO 3.4 XML file")
    print("   • gap_analysis_report.txt - Information gap analysis")
    
    # Generate final summary
    print_header("WORKFLOW COMPLETE - SUMMARY")
    
    print(assistant.generate_summary_report(application))
    
    print("\n" + "=" * 80)
    print("  NEXT STEPS")
    print("=" * 80)
    print("\n1. Review the gap analysis report for missing information")
    print("2. Gather additional documents or data to fill identified gaps")
    print("3. Re-run the workflow with updated documents")
    print("4. Submit the MISMO XML file to your loan origination system")
    print("\n" + "=" * 80)
    print("\n✨ Demo complete! Check the output/ directory for all generated files.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
