"""
Master pipeline: PDF → Extracted JSON → Semantic JSON

This two-step approach separates concerns:
1. Step 1 (pdf_to_json.py): Pure data extraction using pdfplumber
2. Step 2 (json_to_semantic.py): AI-powered semantic analysis using OpenAI

Benefits:
- Cleaner separation of concerns
- Better debugging (inspect intermediate JSON)
- More efficient (structured data to OpenAI, not raw text)
- Reusable (extracted JSON can be used for other purposes)
"""

from pdf_to_json import PDFToJSONExtractor
from json_to_semantic import JSONToSemanticConverter
from pathlib import Path


def main():
    """Run the complete two-step pipeline"""
    
    print("\n" + "="*70)
    print(" MORTGAGE DOCUMENT PROCESSING PIPELINE")
    print(" Step 1: PDF → Extracted JSON (pdfplumber)")
    print(" Step 2: Extracted JSON → Semantic JSON (OpenAI)")
    print("="*70 + "\n")
    
    # Step 1: Extract PDFs to structured JSON
    print("🔄 STEP 1: Extracting PDF data...\n")
    extractor = PDFToJSONExtractor(output_dir="extracted_json")
    extracted_paths = extractor.process_all_elmo_james_pdfs()
    
    if not extracted_paths:
        print("❌ No PDFs processed. Exiting.")
        return
    
    print(f"\n✓ Step 1 complete: {len(extracted_paths)} JSON files created\n")
    input("Press Enter to continue to Step 2 (semantic analysis)...")
    
    # Step 2: Convert extracted JSON to semantic JSON
    print("\n🔄 STEP 2: Creating semantic analysis...\n")
    converter = JSONToSemanticConverter(output_dir="semantic_json")
    semantic_paths = converter.process_all_extracted_json(input_dir="extracted_json")
    
    print(f"\n✓ Step 2 complete: {len(semantic_paths)} semantic JSON files created\n")
    
    # Summary
    print("="*70)
    print("✅ PIPELINE COMPLETE")
    print("="*70)
    print(f"Extracted JSON files: {len(extracted_paths)} → extracted_json/")
    print(f"Semantic JSON files:  {len(semantic_paths)} → semantic_json/")
    print("="*70)
    
    # List the semantic JSON files
    print("\n📊 Semantic JSON Files Created:")
    for path in sorted(semantic_paths):
        print(f"  • {path.name}")
    print()


if __name__ == "__main__":
    main()
