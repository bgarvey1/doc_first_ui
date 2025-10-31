#!/usr/bin/env python3
"""
MASTER PIPELINE: Complete Mortgage Document Processing

This script runs the entire three-step pipeline:
1. Extract PDFs to structured JSON (pdfplumber)
2. Create semantic JSON with AI classification (GPT-5-mini)
3. Comprehensive underwriting analysis (GPT-5)
4. Generate MISMO 3.4 XML
5. Create executive summary

Usage:
    python run_complete_pipeline.py
"""

import sys
from pathlib import Path
from pdf_to_json import PDFToJSONExtractor
from json_to_semantic import JSONToSemanticConverter
from final_analysis import MortgageUnderwritingAnalyzer
from generate_mismo_xml import MISMOXMLGenerator
from create_summary import create_summary_document


def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80 + "\n")


def main():
    """Run the complete mortgage processing pipeline"""
    
    print("\n" + "="*80)
    print(" COMPLETE MORTGAGE DOCUMENT PROCESSING PIPELINE")
    print("="*80)
    print("\nThis pipeline will:")
    print("  1. Extract all PDF documents to structured JSON")
    print("  2. Create semantic JSON with AI document classification")
    print("  3. Perform comprehensive underwriting analysis with GPT-5")
    print("  4. Generate MISMO 3.4 XML")
    print("  5. Create executive summary report")
    print("\n" + "="*80)
    
    input("\n📋 Press Enter to begin the pipeline...")
    
    # =========================================================================
    # STEP 1: PDF EXTRACTION
    # =========================================================================
    print_header("STEP 1 OF 5: PDF Extraction")
    print("Extracting structured data from PDF files using pdfplumber...")
    print("This step uses NO AI - pure data extraction\n")
    
    try:
        extractor = PDFToJSONExtractor(output_dir="extracted_json")
        extracted_paths = extractor.process_all_elmo_james_pdfs()
        
        if not extracted_paths:
            print("\n❌ No PDFs found or processed. Exiting.")
            sys.exit(1)
        
        print(f"\n✅ Step 1 Complete: {len(extracted_paths)} files extracted")
        
    except Exception as e:
        print(f"\n❌ Step 1 Failed: {e}")
        sys.exit(1)
    
    input("\n📋 Press Enter to continue to Step 2...")
    
    # =========================================================================
    # STEP 2: SEMANTIC ANALYSIS
    # =========================================================================
    print_header("STEP 2 OF 5: Semantic Analysis")
    print("Creating semantic JSON with AI document classification...")
    print("Using: GPT-5-mini-2025-08-07 (fast model)\n")
    
    try:
        converter = JSONToSemanticConverter(output_dir="semantic_json")
        semantic_paths = converter.process_all_extracted_json(input_dir="extracted_json")
        
        if not semantic_paths:
            print("\n❌ No semantic files created. Exiting.")
            sys.exit(1)
        
        print(f"\n✅ Step 2 Complete: {len(semantic_paths)} semantic JSON files created")
        
    except Exception as e:
        print(f"\n❌ Step 2 Failed: {e}")
        sys.exit(1)
    
    input("\n📋 Press Enter to continue to Step 3...")
    
    # =========================================================================
    # STEP 3: COMPREHENSIVE ANALYSIS
    # =========================================================================
    print_header("STEP 3 OF 5: Comprehensive Underwriting Analysis")
    print("Performing complete mortgage underwriting review...")
    print("Using: GPT-5-2025-08-07 (full model)")
    print("Applying: Freddie Mac Guidelines Sections 5301-5305\n")
    
    try:
        analyzer = MortgageUnderwritingAnalyzer()
        analyzer.run()
        
        print(f"\n✅ Step 3 Complete: Underwriting analysis finished")
        
    except Exception as e:
        print(f"\n❌ Step 3 Failed: {e}")
        sys.exit(1)
    
    input("\n📋 Press Enter to continue to Step 4...")
    
    # =========================================================================
    # STEP 4: MISMO XML GENERATION
    # =========================================================================
    print_header("STEP 4 OF 5: MISMO XML Generation")
    print("Generating MISMO 3.4 XML from analyzed data...\n")
    
    try:
        generator = MISMOXMLGenerator()
        generator.process_latest_mismo_data()
        
        print(f"\n✅ Step 4 Complete: MISMO XML generated")
        
    except Exception as e:
        print(f"\n❌ Step 4 Failed: {e}")
        sys.exit(1)
    
    input("\n📋 Press Enter to continue to Step 5...")
    
    # =========================================================================
    # STEP 5: EXECUTIVE SUMMARY
    # =========================================================================
    print_header("STEP 5 OF 5: Executive Summary")
    print("Creating comprehensive executive summary...\n")
    
    try:
        create_summary_document()
        
        print(f"\n✅ Step 5 Complete: Executive summary created")
        
    except Exception as e:
        print(f"\n❌ Step 5 Failed: {e}")
        sys.exit(1)
    
    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    print("\n" + "="*80)
    print(" 🎉 PIPELINE COMPLETE!")
    print("="*80)
    
    print("\n📊 Output Directories:")
    print("  • extracted_json/  - Raw PDF extraction data")
    print("  • semantic_json/   - AI-classified semantic data")
    print("  • final_output/    - All analysis results")
    
    print("\n📄 Key Output Files:")
    print("  • final_output/executive_summary.txt - Human-readable summary")
    print("  • final_output/gap_analysis_*.txt - Gap analysis report")
    print("  • final_output/elmo_james_mismo_*.xml - MISMO 3.4 XML")
    print("  • final_output/borrower_profile_*.json - Borrower data")
    print("  • final_output/complete_analysis_*.json - Full analysis")
    
    print("\n" + "="*80)
    print("\n✅ All steps completed successfully!")
    print("   Review the executive_summary.txt file for complete results.\n")
    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Pipeline failed with error: {e}")
        sys.exit(1)
