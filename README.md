# 🏠 Mortgage Application Assistant

AI-Powered system for processing mortgage documents and intelligently filling out the Uniform Residential Loan Application (URLA) form.

## Overview

This system automates the tedious process of extracting information from various mortgage-related documents (W-2s, paystubs, verification of employment, bank statements, etc.) and intelligently maps that data to the appropriate fields in the URLA (Fannie Mae Form 1003). It also validates the data against Freddie Mac underwriting guidelines to ensure compliance.

## Features

- 📄 **Automatic Document Classification**: Uses AI to identify document types (W-2, paystub, VOE, credit reports, etc.)
- 🔍 **Intelligent Data Extraction**: Extracts structured data from PDFs using both rule-based and AI-powered methods
- 📊 **Freddie Mac Compliance**: Implements underwriting rules from Freddie Mac Sections 5301-5305
- 💰 **Income Analysis**: Calculates qualifying income with 2-year history analysis and continuance verification
- 📋 **URLA Form Mapping**: Automatically maps extracted data to URLA form fields
- 🏦 **MISMO 3.4 XML Generation**: Creates industry-standard mortgage XML files for LOS integration
- 🔍 **Gap Analysis**: Identifies missing or incomplete information with actionable recommendations
- ✅ **Validation & Reporting**: Generates compliance reports and completion status
- 🎨 **Interactive CLI**: User-friendly command-line interface with rich formatting

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MORTGAGE ASSISTANT                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌───────────────┐    ┌──────────────────┐                 │
│  │ PDF Parser    │───>│ Document         │                 │
│  │ - PyPDF2      │    │ Classifier       │                 │
│  │ - pdfplumber  │    │ - Rule-based     │                 │
│  │ - PyMuPDF     │    │ - AI-powered     │                 │
│  └───────────────┘    └──────────────────┘                 │
│                              │                               │
│                              v                               │
│                       ┌──────────────────┐                  │
│                       │ Document         │                  │
│                       │ Extractor        │                  │
│                       │ - Regex patterns │                  │
│                       │ - AI extraction  │                  │
│                       └──────────────────┘                  │
│                              │                               │
│         ┌────────────────────┴────────────────────┐        │
│         │                                          │        │
│         v                                          v        │
│  ┌──────────────────┐                    ┌──────────────┐  │
│  │ Underwriting     │                    │ URLA         │  │
│  │ Engine           │                    │ Analyzer     │  │
│  │ - Freddie Mac    │                    │ - Form       │  │
│  │   Guidelines     │                    │   Structure  │  │
│  │ - Income Calc    │                    │ - Mapping    │  │
│  │ - Validation     │                    │ - Validation │  │
│  └──────────────────┘                    └──────────────┘  │
│         │                                          │        │
│         └────────────────────┬────────────────────┘        │
│                              v                              │
│                       ┌──────────────────┐                 │
│                       │ Application      │                 │
│                       │ Generator        │                 │
│                       │ - Reports        │                 │
│                       │ - JSON Output    │                 │
│                       └──────────────────┘                 │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites

- Python 3.9 or higher
- OpenAI API key (for AI-powered extraction)

### Setup

1. **Clone or navigate to the project directory**:
   ```bash
   cd /Users/brendangarvey/doc_first_ui
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API key**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

   Your `.env` file should contain:
   ```
   OPENAI_API_KEY=sk-your-api-key-here
   ```

## Usage

### Quick Start

**NEW: Complete MISMO Workflow Demo**

```bash
python mismo_demo.py
```

This interactive demo showcases the complete workflow:
1. Extract data from all PDF documents
2. Apply Freddie Mac underwriting guidelines
3. Generate industry-standard MISMO 3.4 XML
4. Produce gap analysis report with missing information
5. Save all results to `output/` directory

**Original Interactive CLI**

```bash
python src/interactive_cli.py
```

Or process a folder directly:

```bash
python src/interactive_cli.py /path/to/documents
```

### Example: Processing Elmo James's Documents

```bash
# The current directory contains Elmo James's synthetic documents
python mismo_demo.py
```

This will:
1. Scan for all PDF files
2. Classify each document (W-2, paystub, VOE, etc.)
3. Extract structured data from each document
4. Analyze income using Freddie Mac guidelines
5. Map extracted data to URLA form fields
6. Generate MISMO 3.4 XML for LOS integration
7. Analyze information gaps with severity levels
8. Generate compliance reports
9. Save results to `output/` directory including:
   - `mortgage_application.xml` (MISMO format)
   - `gap_analysis_report.txt` (missing info)
   - `extracted_data.json` (structured data)
   - `mortgage_application.json` (complete app)

### Command-Line Mode

For automation or scripting:

```bash
python src/mortgage_assistant.py /path/to/documents
```

### Using Individual Modules

#### Parse a PDF:
```python
from src.pdf_parser import PDFParser

parser = PDFParser('elmo_james_w2_2025.pdf')
extracted_text = parser.extract_text()
print(extracted_text.full_text)
```

#### Classify and extract from a document:
```python
from src.document_extractor import process_document

classification, data = process_document('elmo_james_paystub_oct2025.pdf')
print(f"Type: {classification.document_type}")
print(f"Data: {data.extracted_fields}")
```

#### Analyze income:
```python
from src.underwriting_engine import FreddieUnderwritingEngine

engine = FreddieUnderwritingEngine()
w2_data = [
    {'year': '2025', 'wages': 85000, 'employer_name': 'Tech Corp'},
    {'year': '2024', 'wages': 80000, 'employer_name': 'Tech Corp'}
]
paystub = {'pay_date': '2025-10-15', 'ytd_gross': 70833}
voe = {'likelihood_of_continued_employment': 'Positive'}

analysis = engine.analyze_w2_income(w2_data, paystub, voe)
print(engine.generate_income_calculation_worksheet(analysis))
```

## Project Structure

```
doc_first_ui/
├── src/
│   ├── pdf_parser.py           # PDF parsing and text extraction
│   ├── document_extractor.py   # Document classification and data extraction
│   ├── underwriting_engine.py  # Freddie Mac underwriting rules
│   ├── urla_analyzer.py        # URLA form structure and mapping
│   ├── mortgage_assistant.py   # Main orchestrator
│   └── interactive_cli.py      # Interactive CLI interface
├── freddie_income_guides.json  # Freddie Mac guidelines (Sections 5301-5305)
├── URLA-2019-Borrower-v28.pdf  # URLA form template
├── elmo_james_*.pdf            # Sample borrower documents
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
└── README.md                  # This file
```

## Document Types Supported

The system can automatically recognize and process:

- ✅ **W-2 Forms** - Wage and Tax Statements
- ✅ **Paystubs** - Pay statements with YTD information
- ✅ **VOE** - Verification of Employment
- ✅ **Bank Statements** - Checking and savings accounts
- ✅ **Credit Reports** - Credit history and scores
- ✅ **Mortgage Statements** - Existing mortgage information
- ✅ **Tax Returns** - 1040 forms (future enhancement)

## Freddie Mac Compliance

The system implements the following Freddie Mac guidelines:

### Section 5301: Stable Monthly Income
- ✅ Income must be verified, acceptable, and expected to continue ≥ 3 years
- ✅ Two-year consistent history required
- ✅ Documentation requirements enforced

### Section 5302: Employment & Income Documentation
- ✅ Paystub within 30 days of application
- ✅ W-2s for two prior years
- ✅ VOE for employment verification
- ✅ 10-day pre-closing verification

### Section 5303: Employed Income (W-2 Borrowers)
- ✅ Base non-fluctuating income calculation
- ✅ Bonus/overtime/commission averaging (24 months)
- ✅ Trend analysis for declining income
- ✅ Multiple employer income combination

## Output Files

After processing, the system generates:

1. **processed_documents.json** - Classification and extraction results for each document
2. **extracted_data.json** - Organized extracted data by document type
3. **mortgage_application.json** - Complete mortgage application data
4. **urla_structure.json** - URLA form structure with all fields

## Example Output

### Income Analysis Report
```
======================================================================
FREDDIE MAC INCOME CALCULATION WORKSHEET
Per Sections 5301-5303 of Freddie Mac Guidelines
======================================================================

INCOME SOURCES:
----------------------------------------------------------------------

1. W2_BASE
   Employer: Tech Corp
   Amount: $7,083.33 MONTHLY
   Stable: Yes
   Continuance: Yes
   Notes: Based on 2025 W-2 wages

----------------------------------------------------------------------
TOTAL MONTHLY QUALIFYING INCOME: $7,083.33
----------------------------------------------------------------------

COMPLIANCE CHECK:
----------------------------------------------------------------------

Section 5301 Stable Income:
  ✓ Stable Income: True

Section 5302 Documentation:
  ✓ W2 Provided: True
  ✓ Paystub Provided: True
  ✓ Voe Provided: True
  ✓ Meets Doc Requirements: True

Section 5303 Employed Income:
  ✓ Two Year History: True
  ✓ Income Stable: True

======================================================================
MEETS FREDDIE MAC REQUIREMENTS: YES
======================================================================
```

## Configuration

### API Settings

Edit `.env` to configure:
- `OPENAI_API_KEY` - Your OpenAI API key
- `DEFAULT_MODEL` - AI model to use (default: gpt-4-turbo-preview)

### Customization

You can customize:
- Document classification rules in `document_extractor.py`
- Extraction patterns in `document_extractor.py`
- Underwriting rules in `underwriting_engine.py`
- URLA field definitions in `urla_analyzer.py`

## Troubleshooting

### Import Errors
If you see "Import could not be resolved" errors, install dependencies:
```bash
pip install -r requirements.txt
```

### API Key Issues
If AI extraction isn't working:
1. Check that `.env` file exists
2. Verify `OPENAI_API_KEY` is set correctly
3. Test with: `echo $OPENAI_API_KEY`

### PDF Parsing Issues
Some PDFs may require OCR. To enable:
```bash
# Install Tesseract OCR
brew install tesseract  # macOS
# or
apt-get install tesseract-ocr  # Linux
```

## Documentation

- **[MISMO_GUIDE.md](MISMO_GUIDE.md)** - Complete guide to MISMO XML integration and gap analysis
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed system architecture and design
- **[EXAMPLES.md](EXAMPLES.md)** - Usage examples and code samples
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Project overview and capabilities
- **[STRUCTURE.md](STRUCTURE.md)** - File structure and module organization

## Future Enhancements

- [ ] Auto-calculate DTI ratios
- [ ] Asset validation against bank statements
- [ ] Credit report parsing
- [ ] Property appraisal data extraction
- [ ] Co-borrower section processing
- [ ] PDF form filling (output URLA as fillable PDF)
- [ ] Web interface
- [ ] Database storage
- [ ] Integration with specific LOS platforms
- [ ] Automated document requests for missing information

## Contributing

This is a demonstration project. For production use, consider:
- Adding comprehensive error handling
- Implementing secure document storage
- Adding audit logging
- Enhancing validation rules
- Adding unit tests
- Implementing role-based access control

## License

This project is for demonstration purposes. Please ensure compliance with:
- Freddie Mac guidelines
- Fannie Mae requirements
- CFPB regulations
- State and federal lending laws
- MISMO standards

## Support

For issues or questions:
1. Check the documentation (especially [MISMO_GUIDE.md](MISMO_GUIDE.md))
2. Review example usage
3. Examine output files for debugging
4. Check the gap analysis report for missing data

## Credits

- Freddie Mac Single-Family Seller/Servicer Guide (Sections 5301-5305)
- Fannie Mae Form 1003 (URLA 2019)
- MISMO 3.4 Standards (Mortgage Industry Standards Maintenance Organization)
- OpenAI GPT-4 for AI-powered extraction

---

**Note**: This system is designed to assist mortgage professionals, not replace them. Always verify extracted data and ensure compliance with current regulations.
