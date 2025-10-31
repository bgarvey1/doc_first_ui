"""
Step 1: Extract structured data from PDFs using pdfplumber
Creates plain JSON files with text, tables, metadata
"""

import pdfplumber
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


class PDFToJSONExtractor:
    """Extract structured data from PDF files without AI interpretation"""
    
    def __init__(self, output_dir: str = "extracted_json"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def extract_pdf_structure(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract comprehensive structured data from a PDF
        
        Returns:
            Dictionary with text, tables, metadata, and structure
        """
        pdf_path = Path(pdf_path)
        
        result = {
            "filename": pdf_path.name,
            "source_path": str(pdf_path.absolute()),
            "extracted_at": datetime.now().isoformat(),
            "metadata": {},
            "pages": [],
            "all_text": "",
            "tables": [],
            "statistics": {}
        }
        
        with pdfplumber.open(pdf_path) as pdf:
            # Extract metadata
            result["metadata"] = {
                "num_pages": len(pdf.pages),
                "pdf_metadata": pdf.metadata or {}
            }
            
            all_text_parts = []
            
            # Extract each page
            for page_num, page in enumerate(pdf.pages, start=1):
                page_data = {
                    "page_number": page_num,
                    "text": page.extract_text() or "",
                    "width": page.width,
                    "height": page.height,
                    "tables": [],
                    "words": []
                }
                
                # Extract tables from this page
                tables = page.extract_tables()
                for table_idx, table in enumerate(tables):
                    if table:
                        page_data["tables"].append({
                            "table_number": table_idx + 1,
                            "rows": table,
                            "num_rows": len(table),
                            "num_cols": len(table[0]) if table else 0
                        })
                
                # Extract word positions (useful for understanding layout)
                words = page.extract_words()
                if words:
                    # Store word positions (can help identify headers, columns, etc.)
                    page_data["words"] = [
                        {
                            "text": w["text"],
                            "x0": round(w["x0"], 2),
                            "top": round(w["top"], 2),
                            "x1": round(w["x1"], 2),
                            "bottom": round(w["bottom"], 2)
                        }
                        for w in words[:100]  # Limit to first 100 words per page
                    ]
                
                result["pages"].append(page_data)
                all_text_parts.append(page_data["text"])
                
                # Add tables to global table list
                if page_data["tables"]:
                    for table in page_data["tables"]:
                        result["tables"].append({
                            "page": page_num,
                            **table
                        })
            
            result["all_text"] = "\n\n".join(all_text_parts)
            
            # Calculate statistics
            result["statistics"] = {
                "total_characters": len(result["all_text"]),
                "total_pages": len(result["pages"]),
                "total_tables": len(result["tables"]),
                "avg_chars_per_page": len(result["all_text"]) / len(result["pages"]) if result["pages"] else 0
            }
        
        return result
    
    def process_pdf(self, pdf_path: str) -> Path:
        """
        Process a single PDF and save the extracted JSON
        
        Returns:
            Path to the saved JSON file
        """
        pdf_path = Path(pdf_path)
        
        print(f"📄 Extracting: {pdf_path.name}")
        
        # Extract structure
        data = self.extract_pdf_structure(pdf_path)
        
        # Save to JSON
        output_filename = pdf_path.stem + "_extracted.json"
        output_path = self.output_dir / output_filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        stats = data["statistics"]
        print(f"  ✓ Saved to: {output_path}")
        print(f"  ✓ Pages: {stats['total_pages']}, Chars: {stats['total_characters']}, Tables: {stats['total_tables']}")
        
        return output_path
    
    def process_all_elmo_james_pdfs(self) -> List[Path]:
        """Process all Elmo James PDFs in the current directory"""
        
        current_dir = Path(".")
        pdf_files = sorted(current_dir.glob("elmo_james*.pdf"))
        
        if not pdf_files:
            print("⚠️  No 'elmo_james*.pdf' files found in current directory")
            return []
        
        print(f"\n{'='*60}")
        print(f"PDF EXTRACTION PIPELINE - Step 1: PDF → JSON")
        print(f"{'='*60}")
        print(f"Found {len(pdf_files)} PDF files to process\n")
        
        output_paths = []
        
        for idx, pdf_path in enumerate(pdf_files, 1):
            print(f"[{idx}/{len(pdf_files)}] ", end="")
            try:
                output_path = self.process_pdf(pdf_path)
                output_paths.append(output_path)
            except Exception as e:
                print(f"  ✗ ERROR: {e}")
                continue
            print()
        
        print(f"{'='*60}")
        print(f"✓ Extraction Complete: {len(output_paths)}/{len(pdf_files)} files processed")
        print(f"✓ Output directory: {self.output_dir}/")
        print(f"{'='*60}\n")
        
        return output_paths


def main():
    """Run the PDF extraction pipeline"""
    extractor = PDFToJSONExtractor(output_dir="extracted_json")
    extractor.process_all_elmo_james_pdfs()


if __name__ == "__main__":
    main()
