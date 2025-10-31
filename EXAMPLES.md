# Mortgage Application Assistant - Usage Examples

## Example 1: Quick Demo with Elmo James Documents

```bash
# Setup
source venv/bin/activate

# Run the demo with provided sample documents
python demo.py
```

This will process all of Elmo James's documents and generate:
- Income analysis per Freddie Mac guidelines
- URLA form mapping
- Completion status report
- JSON output files

## Example 2: Interactive CLI

```bash
python src/interactive_cli.py
```

Then follow the menu:
1. Select Document Folder → Enter `.` for current directory
2. Process Documents → Analyzes all PDFs
3. Analyze Income → Applies Freddie Mac rules
4. Map to URLA Form → Auto-fills available fields
5. View Completion Status → Shows what's missing
6. Save Results → Exports to output/

## Example 3: Process Specific Folder

```bash
# Process documents from a different folder
python src/interactive_cli.py /path/to/borrower/documents

# Or with the assistant directly
python src/mortgage_assistant.py /path/to/borrower/documents
```

## Example 4: Using Python API

### Process a Single Document

```python
from src.document_extractor import process_document

# Classify and extract from a W-2
classification, data = process_document('elmo_james_w2_2025.pdf')

print(f"Document Type: {classification.document_type}")
print(f"Confidence: {classification.confidence}")
print(f"Extracted Data: {data.extracted_fields}")
```

### Analyze Income

```python
from src.underwriting_engine import FreddieUnderwritingEngine

engine = FreddieUnderwritingEngine('freddie_income_guides.json')

# W-2 data from multiple years
w2_data = [
    {
        'year': '2025',
        'wages': 85000,
        'employer_name': 'Tech Corp',
        'employee_ssn': '123-45-6789'
    },
    {
        'year': '2024',
        'wages': 80000,
        'employer_name': 'Tech Corp',
        'employee_ssn': '123-45-6789'
    }
]

# Most recent paystub
paystub = {
    'pay_date': '2025-10-15',
    'ytd_gross': 70833,
    'gross_pay': 3269
}

# VOE
voe = {
    'employer_name': 'Tech Corp',
    'job_title': 'Software Engineer',
    'employment_start_date': '2020-01-15',
    'likelihood_of_continued_employment': 'Positive - excellent performer'
}

# Analyze
analysis = engine.analyze_w2_income(w2_data, paystub, voe)

# Print worksheet
print(engine.generate_income_calculation_worksheet(analysis))
```

### Work with URLA Form

```python
from src.urla_analyzer import URLAFormAnalyzer

analyzer = URLAFormAnalyzer()

# Get all sections
for section in analyzer.sections:
    print(f"{section.section_id}: {section.section_name}")
    print(f"  Fields: {len(section.fields)}")

# Get required fields
required = analyzer.get_required_fields()
print(f"\nTotal required fields: {len(required)}")

# Map extracted data
extracted_data = {
    'w2_data': w2_data[0],
    'paystub_data': paystub,
    'voe_data': voe
}

urla_data = analyzer.get_field_mapping_from_docs(extracted_data)
print(f"\nMapped {len(urla_data)} fields to URLA")

# Check completion
report = analyzer.generate_completion_report(urla_data)
print(f"Completion: {report['completion_percentage']}%")
print(f"Required completion: {report['required_percentage']}%")
```

### Complete Pipeline

```python
from src.mortgage_assistant import MortgageAssistant
import os

# Initialize (set OPENAI_API_KEY in environment)
assistant = MortgageAssistant(api_key=os.getenv('OPENAI_API_KEY'))

# Process all documents in a folder
results = assistant.process_document_folder('.')

# Analyze income
income_analysis = assistant.analyze_income()

# Map to URLA
urla_data = assistant.map_to_urla()

# Generate completion report
completion = assistant.generate_urla_report(urla_data)

# Create application
application = assistant.create_application()

# Show summary
print(assistant.generate_summary_report(application))

# Save everything
assistant.save_results('output')
application.to_json('output/mortgage_application.json')
```

## Example 5: Batch Processing Multiple Borrowers

```python
from pathlib import Path
from src.mortgage_assistant import MortgageAssistant

borrower_folders = [
    '/path/to/borrower1/docs',
    '/path/to/borrower2/docs',
    '/path/to/borrower3/docs',
]

for folder in borrower_folders:
    borrower_name = Path(folder).parent.name
    print(f"\nProcessing {borrower_name}...")
    
    assistant = MortgageAssistant()
    assistant.process_document_folder(folder)
    application = assistant.create_application()
    
    # Save to borrower-specific output
    output_dir = f"output/{borrower_name}"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    assistant.save_results(output_dir)
    application.to_json(f"{output_dir}/application.json")
```

## Example 6: Custom Document Extraction

```python
from src.pdf_parser import PDFParser
from src.document_extractor import DocumentExtractor

# Parse PDF
parser = PDFParser('custom_document.pdf')
extracted_text = parser.extract_text()

# Extract tables if present
tables = parser.extract_tables()
if tables:
    print(f"Found {len(tables)} tables")

# Custom extraction
extractor = DocumentExtractor(api_key='your-key')

# For W-2
w2_data = extractor.extract_w2_data(extracted_text)
print(w2_data.extracted_fields)

# For paystub
paystub_data = extractor.extract_paystub_data(extracted_text)
print(paystub_data.extracted_fields)

# For VOE
voe_data = extractor.extract_voe_data(extracted_text)
print(voe_data.extracted_fields)
```

## Example 7: Generate Reports Only

```python
from src.underwriting_engine import FreddieUnderwritingEngine
from src.urla_analyzer import URLAFormAnalyzer
import json

# Load previously extracted data
with open('output/extracted_data.json') as f:
    data = json.load(f)

# Re-run income analysis
engine = FreddieUnderwritingEngine()
w2s = data.get('W2', [])
paystub = data.get('PAYSTUB', [{}])[0]
voe = data.get('VOE', [{}])[0]

analysis = engine.analyze_w2_income(w2s, paystub, voe)
print(engine.generate_income_calculation_worksheet(analysis))

# Re-check URLA completion
analyzer = URLAFormAnalyzer()
urla_data = analyzer.get_field_mapping_from_docs(data)
report = analyzer.generate_completion_report(urla_data)

print(f"\nForm Completion: {report['completion_percentage']}%")
print(f"Missing Required: {len(report['missing_required'])} fields")
```

## Example 8: Export URLA Structure

```python
from src.urla_analyzer import URLAFormAnalyzer
import json

analyzer = URLAFormAnalyzer()

# Export to JSON
analyzer.export_structure_to_json('urla_form_structure.json')

# Or get as dict
structure = {
    'sections': [section.to_dict() for section in analyzer.sections]
}

# Pretty print
print(json.dumps(structure, indent=2))
```

## Tips and Best Practices

### 1. Document Naming Convention
For best results, name your files descriptively:
- `borrower_name_w2_2024.pdf`
- `borrower_name_paystub_oct2025.pdf`
- `borrower_name_voe_2025.pdf`

### 2. API Key Management
```bash
# Use environment variable
export OPENAI_API_KEY='sk-...'

# Or in .env file
echo "OPENAI_API_KEY=sk-..." > .env
```

### 3. Batch Processing
Process multiple years of documents together for better accuracy.

### 4. Validation
Always validate extracted data:
```python
# Check confidence scores
if classification.confidence < 0.7:
    print("⚠️ Low confidence - manual review recommended")

# Verify required fields
if not analysis.meets_requirements:
    for issue in analysis.issues:
        print(f"Issue: {issue}")
```

### 5. Error Handling
```python
try:
    results = assistant.process_document_folder(folder)
except Exception as e:
    print(f"Error: {e}")
    # Log and continue with manual processing
```
