"""
OpenAI-Powered Semantic PDF Analyzer
Loads PDFs directly into OpenAI and extracts structured semantic data
"""
import os
import json
from pathlib import Path
from typing import Dict, List, Any
from dotenv import load_dotenv
from openai import OpenAI
import base64

# Load environment variables
load_dotenv()


class SemanticPDFAnalyzer:
    """Analyzes PDFs using OpenAI to extract semantic structured data"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('DEFAULT_MODEL', 'gpt-4o')
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file")
        
        self.client = OpenAI(api_key=self.api_key)
        self.output_dir = Path('semantic_json')
        self.output_dir.mkdir(exist_ok=True)
        
        print(f"✓ Initialized with model: {self.model}")
        print(f"✓ Output directory: {self.output_dir}")
    
    def convert_pdf_to_images(self, pdf_path: Path) -> List[str]:
        """Convert PDF to base64 encoded images"""
        try:
            from pdf2image import convert_from_path
            import io
            from PIL import Image
            
            # Convert PDF to images
            images = convert_from_path(str(pdf_path), dpi=150)
            
            base64_images = []
            for img in images:
                # Convert to bytes
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()
                
                # Encode to base64
                base64_encoded = base64.b64encode(img_byte_arr).decode('utf-8')
                base64_images.append(base64_encoded)
            
            return base64_images
        except ImportError:
            print("⚠️  pdf2image not available, will use text extraction")
            return []
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Fallback: Extract text from PDF"""
        try:
            import pdfplumber
            
            text = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text.append(page_text)
            
            return "\n\n".join(text)
        except Exception as e:
            print(f"Error extracting text from {pdf_path.name}: {e}")
            return ""
    
    def analyze_pdf_with_openai(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Send PDF to OpenAI for semantic analysis
        Returns structured JSON with document type and semantic data
        """
        
        print(f"\n📄 Analyzing: {pdf_path.name}")
        print("   Extracting text from PDF...")
        
        # Extract text from PDF
        pdf_text = self.extract_text_from_pdf(pdf_path)
        
        if not pdf_text:
            print(f"   ⚠️  No text extracted from {pdf_path.name}")
            return {
                "filename": pdf_path.name,
                "error": "No text could be extracted from PDF"
            }
        
        print(f"   ✓ Extracted {len(pdf_text)} characters")
        print("   Sending to OpenAI for semantic analysis...")
        
        # Create prompt for semantic analysis
        prompt = f"""You are analyzing a mortgage-related document. Please analyze the following PDF content and extract ALL information in a structured, semantic format.

Document content:
{pdf_text}

Please return a JSON object with the following structure:
{{
    "document_type": "one of: W2, PAYSTUB, VOE, BANK_STATEMENT, CREDIT_REPORT, MORTGAGE_STATEMENT, TAX_RETURN, or OTHER",
    "confidence": "confidence level in document classification (0.0-1.0)",
    "semantic_data": {{
        // All extracted information organized semantically
        // Include ALL fields you can identify with their semantic meaning
        // For example:
        // "borrower": {{"name": "...", "ssn": "...", "address": "..."}},
        // "employer": {{"name": "...", "address": "...", "phone": "..."}},
        // "income": {{"base": 0.0, "overtime": 0.0, "bonus": 0.0, "year_to_date": 0.0}},
        // "dates": {{"pay_period_start": "...", "pay_period_end": "...", "pay_date": "..."}},
        // etc.
    }},
    "raw_entities": {{
        // Key entities extracted with their semantic labels
        // Example: "person_name": "John Doe", "ssn": "123-45-6789", "dollar_amount": 5000.00
    }},
    "document_purpose": "Brief description of what this document is used for in mortgage underwriting",
    "key_information": [
        // List of the most important pieces of information from this document
    ],
    "metadata": {{
        "date_of_document": "extracted date if available",
        "issuer": "who issued this document",
        "recipient": "who received this document"
    }}
}}

Be thorough and extract EVERYTHING you can see. Include all names, numbers, dates, addresses, amounts, and any other relevant information. Structure it semantically so it's clear what each piece of data represents."""

        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing financial and mortgage documents. You extract structured, semantic data from documents and return it as valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                max_completion_tokens=4000
            )
            
            # Parse response
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            # Add metadata
            result["filename"] = pdf_path.name
            result["source_path"] = str(pdf_path)
            result["model_used"] = self.model
            result["tokens_used"] = {
                "prompt": response.usage.prompt_tokens,
                "completion": response.usage.completion_tokens,
                "total": response.usage.total_tokens
            }
            
            print(f"   ✓ Analysis complete!")
            print(f"   ✓ Document Type: {result.get('document_type', 'UNKNOWN')}")
            print(f"   ✓ Confidence: {result.get('confidence', 0)}")
            print(f"   ✓ Tokens used: {result['tokens_used']['total']}")
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"   ❌ Error parsing JSON response: {e}")
            print(f"   Raw response: {result_text[:200]}...")
            return {
                "filename": pdf_path.name,
                "error": f"JSON parsing error: {str(e)}",
                "raw_response": result_text[:500]
            }
        except Exception as e:
            print(f"   ❌ Error calling OpenAI API: {e}")
            return {
                "filename": pdf_path.name,
                "error": str(e)
            }
    
    def process_all_elmo_james_pdfs(self) -> List[Dict[str, Any]]:
        """Process all Elmo James PDFs in the current directory"""
        
        print("=" * 80)
        print("  SEMANTIC PDF ANALYSIS WITH OPENAI")
        print("=" * 80)
        print()
        
        # Find all Elmo James PDFs
        current_dir = Path.cwd()
        pdf_files = list(current_dir.glob("elmo_james*.pdf"))
        
        if not pdf_files:
            print("❌ No Elmo James PDF files found in current directory")
            return []
        
        print(f"✓ Found {len(pdf_files)} Elmo James documents:")
        for pdf in pdf_files:
            print(f"  • {pdf.name}")
        print()
        
        # Process each PDF
        results = []
        for i, pdf_path in enumerate(pdf_files, 1):
            print(f"\n[{i}/{len(pdf_files)}] Processing: {pdf_path.name}")
            print("-" * 80)
            
            result = self.analyze_pdf_with_openai(pdf_path)
            results.append(result)
            
            # Save individual result
            output_filename = pdf_path.stem + "_semantic.json"
            output_path = self.output_dir / output_filename
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"   ✓ Saved to: {output_path}")
        
        # Save combined results
        combined_path = self.output_dir / "all_documents_semantic.json"
        with open(combined_path, 'w', encoding='utf-8') as f:
            json.dump({
                "total_documents": len(results),
                "documents": results,
                "summary": self._generate_summary(results)
            }, f, indent=2, ensure_ascii=False)
        
        print("\n" + "=" * 80)
        print("  PROCESSING COMPLETE")
        print("=" * 80)
        print(f"\n✓ Processed {len(results)} documents")
        print(f"✓ Individual files saved to: {self.output_dir}/")
        print(f"✓ Combined results saved to: {combined_path}")
        
        # Print summary
        self._print_summary(results)
        
        return results
    
    def _generate_summary(self, results: List[Dict]) -> Dict[str, Any]:
        """Generate summary statistics"""
        doc_types = {}
        total_tokens = 0
        errors = 0
        
        for result in results:
            if "error" in result:
                errors += 1
            else:
                doc_type = result.get("document_type", "UNKNOWN")
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
                
                if "tokens_used" in result:
                    total_tokens += result["tokens_used"]["total"]
        
        return {
            "total_documents": len(results),
            "document_types": doc_types,
            "total_tokens_used": total_tokens,
            "errors": errors,
            "successful": len(results) - errors
        }
    
    def _print_summary(self, results: List[Dict]):
        """Print processing summary"""
        summary = self._generate_summary(results)
        
        print("\n📊 SUMMARY")
        print("-" * 80)
        print(f"Total Documents: {summary['total_documents']}")
        print(f"Successful: {summary['successful']}")
        print(f"Errors: {summary['errors']}")
        print(f"Total Tokens Used: {summary['total_tokens_used']:,}")
        print("\nDocument Types:")
        for doc_type, count in summary['document_types'].items():
            print(f"  • {doc_type}: {count}")


def main():
    """Main entry point"""
    try:
        analyzer = SemanticPDFAnalyzer()
        results = analyzer.process_all_elmo_james_pdfs()
        
        print("\n✨ All semantic JSON files are ready in the semantic_json/ directory!")
        print("\nNext steps:")
        print("  1. Review the semantic JSON files")
        print("  2. Use this structured data for MISMO generation")
        print("  3. Check semantic_json/all_documents_semantic.json for combined data")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
