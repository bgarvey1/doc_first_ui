"""
Step 2: Convert plain extracted JSON to semantic JSON using OpenAI
Takes structured JSON from step 1 and creates rich semantic interpretation
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()


class JSONToSemanticConverter:
    """Convert plain extracted JSON to semantic JSON using OpenAI"""
    
    def __init__(self, model: str = None, output_dir: str = "semantic_json"):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = model or os.getenv('DEFAULT_MODEL', 'gpt-5-mini-2025-08-07')
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        print(f"✓ Initialized with model: {self.model}")
    
    def create_semantic_prompt(self, extracted_data: Dict[str, Any]) -> str:
        """Create a prompt for semantic analysis"""
        
        # Simplify the extracted data for the prompt - ONLY send the text, not layout info
        simplified = {
            "filename": extracted_data["filename"],
            "text_content": extracted_data["all_text"],
            "num_pages": extracted_data["metadata"]["num_pages"]
        }
        
        prompt = f"""You are analyzing mortgage documentation for underwriting purposes.

INPUT DATA (text extracted from PDF):
{json.dumps(simplified, indent=2)}

Your task is to create a semantic JSON representation that identifies:

1. **document_type**: Classify the document (PAYSTUB, W2, VOE, BANK_STATEMENT, CREDIT_REPORT, MORTGAGE_STATEMENT, etc.)
2. **confidence**: Your confidence in the classification (0.0 to 1.0)
3. **semantic_data**: Rich structured data with proper nesting and semantic meaning
   - Extract all relevant financial amounts, dates, names, addresses
   - Parse dollar amounts to numeric values
   - Convert dates to ISO format where possible
   - Identify relationships (borrower, employer, lender, etc.)
   - Extract account numbers, reference numbers, IDs
   - Capture any calculations, totals, year-to-date figures
4. **document_purpose**: Brief explanation of how this document is used in mortgage underwriting
5. **key_information**: Array of the most important facts from this document (max 15 items)

CRITICAL INSTRUCTIONS:
- DO NOT include word positions, page coordinates, or layout information
- DO NOT include raw_entities or metadata fields unless essential
- Focus ONLY on extracting the actual data values (amounts, dates, names, etc.)
- Use clear, hierarchical JSON structure
- Parse all dollar amounts to numbers (remove $ and commas)
- Use ISO date formats (YYYY-MM-DD) where possible
- Be concise but complete - extract all meaningful data
- For transaction lists, summarize or limit to most important entries

Return ONLY valid JSON with the structure above. Be efficient and focused."""

        return prompt
    
    def analyze_with_openai(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send extracted JSON to OpenAI for semantic analysis"""
        
        prompt = self.create_semantic_prompt(extracted_data)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a mortgage document analysis expert. Extract and structure information concisely, focusing only on the data values, not layout or positions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                max_completion_tokens=16000  # Increased to 16k to prevent truncation
            )
            
            content = response.choices[0].message.content
            
            # DEBUG: Check if content is empty
            if not content or content.strip() == "":
                return {
                    "filename": extracted_data["filename"],
                    "error": "OpenAI returned empty response",
                    "raw_response": "",
                    "finish_reason": response.choices[0].finish_reason,
                    "model": self.model,
                    "debug_info": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                }
            
            semantic_data = json.loads(content)
            
            # Add metadata about the analysis
            semantic_data["filename"] = extracted_data["filename"]
            semantic_data["source_path"] = extracted_data["source_path"]
            semantic_data["model_used"] = self.model
            semantic_data["tokens_used"] = {
                "prompt": response.usage.prompt_tokens,
                "completion": response.usage.completion_tokens,
                "total": response.usage.total_tokens
            }
            
            return semantic_data
            
        except json.JSONDecodeError as e:
            return {
                "filename": extracted_data["filename"],
                "error": f"JSON parsing error: {e}",
                "raw_response": content if 'content' in locals() else "",
                "content_length": len(content) if 'content' in locals() else 0
            }
        except Exception as e:
            return {
                "filename": extracted_data["filename"],
                "error": f"Analysis error: {str(e)}",
                "error_type": type(e).__name__
            }
    
    def process_extracted_json(self, json_path: Path) -> Path:
        """Process a single extracted JSON file to create semantic JSON"""
        
        print(f"🧠 Analyzing: {json_path.name}")
        
        # Load the extracted JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            extracted_data = json.load(f)
        
        print(f"  • Loaded {extracted_data['statistics']['total_characters']} characters")
        
        # Create semantic analysis
        semantic_data = self.analyze_with_openai(extracted_data)
        
        # Save semantic JSON
        original_filename = Path(extracted_data["filename"]).stem
        output_filename = original_filename + "_semantic.json"
        output_path = self.output_dir / output_filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(semantic_data, f, indent=2, ensure_ascii=False)
        
        if "error" in semantic_data:
            print(f"  ✗ ERROR: {semantic_data['error']}")
        else:
            doc_type = semantic_data.get('document_type', 'UNKNOWN')
            confidence = semantic_data.get('confidence', 0)
            tokens = semantic_data.get('tokens_used', {}).get('total', 0)
            print(f"  ✓ Type: {doc_type} (confidence: {confidence:.2f})")
            print(f"  ✓ Tokens: {tokens:,}")
            print(f"  ✓ Saved to: {output_path}")
        
        return output_path
    
    def process_all_extracted_json(self, input_dir: str = "extracted_json") -> List[Path]:
        """Process all extracted JSON files in the input directory"""
        
        input_path = Path(input_dir)
        json_files = sorted(input_path.glob("*_extracted.json"))
        
        if not json_files:
            print(f"⚠️  No '*_extracted.json' files found in {input_dir}/")
            return []
        
        print(f"\n{'='*60}")
        print(f"SEMANTIC ANALYSIS PIPELINE - Step 2: JSON → Semantic JSON")
        print(f"{'='*60}")
        print(f"Found {len(json_files)} JSON files to process\n")
        
        output_paths = []
        
        for idx, json_path in enumerate(json_files, 1):
            print(f"[{idx}/{len(json_files)}] ", end="")
            try:
                output_path = self.process_extracted_json(json_path)
                output_paths.append(output_path)
            except Exception as e:
                print(f"  ✗ ERROR: {e}")
                continue
            print()
        
        print(f"{'='*60}")
        print(f"✓ Analysis Complete: {len(output_paths)}/{len(json_files)} files processed")
        print(f"✓ Output directory: {self.output_dir}/")
        print(f"{'='*60}\n")
        
        return output_paths


def main():
    """Run the semantic analysis pipeline"""
    converter = JSONToSemanticConverter()
    converter.process_all_extracted_json(input_dir="extracted_json")


if __name__ == "__main__":
    main()
