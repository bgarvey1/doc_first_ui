"""Test a single document to debug the empty response issue"""

import json
from pathlib import Path
from json_to_semantic import JSONToSemanticConverter

def main():
    # Test the bank statement that's failing
    converter = JSONToSemanticConverter()
    
    json_path = Path("extracted_json/elmo_james_bank_statement_oct2025_extracted.json")
    
    print(f"Testing: {json_path.name}\n")
    
    result_path = converter.process_extracted_json(json_path)
    
    print(f"\nResult saved to: {result_path}")
    
    # Read and display the result
    with open(result_path, 'r') as f:
        result = json.load(f)
    
    print("\n" + "="*60)
    print("RESULT:")
    print("="*60)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
