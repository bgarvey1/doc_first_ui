# MISMO Integration Guide

## Overview

The mortgage document processing system now supports industry-standard **MISMO 3.4 XML** format for data exchange. This enables seamless integration with loan origination systems (LOS) and underwriting platforms.

## Complete Workflow

```
PDF Documents → Data Extraction → Freddie Mac Validation → MISMO XML → Gap Analysis
```

### Step-by-Step Process

1. **Document Extraction**
   - Parse PDF documents (W-2, paystubs, VOE, bank statements, etc.)
   - Classify document types using AI or rule-based methods
   - Extract structured data from each document

2. **Income Analysis**
   - Apply Freddie Mac underwriting guidelines (Sections 5301-5305)
   - Calculate qualifying income from multiple sources
   - Verify 2-year income history and 3-year continuance
   - Generate income calculation worksheets

3. **MISMO Generation**
   - Map extracted data to MISMO 3.4 XML structure
   - Create industry-standard mortgage application file
   - Include borrower, employment, income, assets, liabilities, and loan details

4. **Gap Analysis**
   - Identify missing or incomplete information
   - Categorize gaps by severity (Critical/Warning/Info)
   - Generate actionable report with recommendations

## Quick Start

### Run the Complete Demo

```bash
# Make sure you're in the doc_first_ui directory
python mismo_demo.py
```

This interactive demo will:
- Process all Elmo James PDF documents
- Apply Freddie Mac income analysis
- Generate MISMO XML
- Create gap analysis report
- Save all results to `output/` directory

### Output Files

After running the demo, you'll find these files in the `output/` directory:

- **`mortgage_application.xml`** - MISMO 3.4 XML file (industry standard)
- **`gap_analysis_report.txt`** - Missing information report with action items
- **`mortgage_application.json`** - Complete application data (JSON format)
- **`extracted_data.json`** - Raw extracted data from all documents
- **`processed_documents.json`** - Document processing details

## MISMO XML Structure

The generated MISMO 3.4 XML includes:

### Borrower Information
- Personal details (name, SSN, DOB, marital status)
- Contact information (email, phone)
- Current and previous addresses
- Citizenship and dependent information

### Employment & Income
- Current employer details
- Employment history
- Base income, overtime, bonus, commission
- Self-employment income (if applicable)

### Assets
- Bank accounts (checking, savings, money market)
- Investment accounts
- Retirement accounts (401k, IRA)
- Other assets (stocks, bonds, etc.)

### Liabilities
- Mortgages and home equity loans
- Auto loans
- Credit cards
- Student loans
- Other debts

### Loan Details
- Loan amount and purpose
- Loan type (Conventional, FHA, VA, etc.)
- Interest rate and term
- Property information and valuation

## Gap Analysis Report

The gap analysis identifies three severity levels:

### 🔴 Critical Gaps
**Must be resolved before loan processing**
- Required fields per FNMA/Freddie Mac guidelines
- Missing SSN, employment info, income documentation
- Incomplete property or loan details

**Example:**
```
🔴 CRITICAL GAPS (Must be resolved before loan processing)
────────────────────────────────────────────────────────────

1. Missing Social Security Number
   Section: Borrower Information
   Field: ssn
   Action Required: Provide Social Security Number to proceed with application
   MISMO Path: DEAL/PARTIES/PARTY/TAXPAYER_IDENTIFIERS/TAXPAYER_IDENTIFIER
```

### ⚠️ Warning Gaps
**Recommended to resolve - may cause delays**
- Important but not strictly required fields
- Missing contact information
- Incomplete asset or income details

**Example:**
```
⚠️ WARNING GAPS (Recommended to resolve)
────────────────────────────────────────────────────────────

1. Missing Email address
   Section: Additional Information
   Field: email
   Recommendation: Required for electronic communication
```

### ℹ️ Informational Gaps
**Optional information**
- Helpful but not required for processing
- Additional income sources
- Optional declarations

## Using the System Programmatically

### Generate MISMO XML

```python
from mortgage_assistant import MortgageAssistant

# Initialize assistant
assistant = MortgageAssistant()

# Process documents
assistant.process_document_folder("./documents", "*.pdf")

# Analyze income
income_analysis = assistant.analyze_income()

# Generate MISMO XML
mismo_xml = assistant.generate_mismo_xml(income_analysis)

# Save to file
with open("output/loan_application.xml", 'w') as f:
    f.write(mismo_xml)
```

### Run Gap Analysis

```python
from gap_analyzer import GapAnalyzer
from mismo_parser import MISMOParser

# Parse MISMO XML
parser = MISMOParser()
mismo_data = parser.parse_string(mismo_xml)

# Analyze gaps
analyzer = GapAnalyzer()
gaps = analyzer.analyze_all(mismo_data, extracted_data)

# Generate report
report = analyzer.generate_report(gaps)
print(report)

# Get completion percentage
completion = analyzer.get_completion_percentage(gaps)
print(f"Application {completion:.1f}% complete")
```

### Parse Existing MISMO Files

```python
from mismo_parser import parse_mismo_file

# Parse MISMO XML file
mismo_data = parse_mismo_file("mismo-sample.xml")

# Access borrower info
print(f"Borrower: {mismo_data.borrower.first_name} {mismo_data.borrower.last_name}")
print(f"SSN: {mismo_data.borrower.ssn}")
print(f"Employer: {mismo_data.borrower.employer_name}")
print(f"Base Income: ${mismo_data.borrower.base_income:,.2f}/month")

# Access loan info
print(f"Loan Amount: ${mismo_data.loan.loan_amount:,.2f}")
print(f"Property: {mismo_data.loan.property_address}")
```

## MISMO 3.4 Standards

### Namespaces

The system supports official MISMO 3.4 namespaces:

```xml
xmlns="http://www.mismo.org/residential/2009/schemas"
xmlns:ULAD="http://www.datamodelextension.org/Schema/ULAD"
xmlns:DU="http://www.datamodelextension.org/Schema/DU"
```

### Field Mappings

Common URLA fields mapped to MISMO paths:

| URLA Field | MISMO XML Path |
|------------|---------------|
| Borrower Name | `DEAL/PARTIES/PARTY/INDIVIDUAL/NAME` |
| SSN | `DEAL/PARTIES/PARTY/TAXPAYER_IDENTIFIERS` |
| Employment | `DEAL/PARTIES/PARTY/ROLES/ROLE/BORROWER/EMPLOYERS` |
| Income | `DEAL/PARTIES/PARTY/ROLES/ROLE/BORROWER/CURRENT_INCOME` |
| Assets | `DEAL/ASSETS` |
| Liabilities | `DEAL/LIABILITIES` |
| Loan Amount | `DEAL/LOANS/LOAN/TERMS_OF_LOAN/BaseLoanAmount` |
| Property | `DEAL/COLLATERALS/COLLATERAL/SUBJECT_PROPERTY` |

## Integration with Loan Systems

### Supported Systems

The MISMO 3.4 XML format is compatible with:

- **Fannie Mae** - Desktop Underwriter (DU)
- **Freddie Mac** - Loan Product Advisor (LPA)
- **Encompass by ICE** - Leading LOS
- **Calyx Point** - Mortgage software
- **BytePro** - Origination platform
- **Ellie Mae** - Loan origination
- Many other MISMO-compliant systems

### Export Workflow

1. Generate MISMO XML using the system
2. Review gap analysis report
3. Fill in missing information
4. Validate XML structure
5. Import to your LOS platform
6. Continue with underwriting process

## Freddie Mac Compliance

The system implements these Freddie Mac Selling Guide sections:

- **Section 5301** - W-2 Income (2-year history required)
- **Section 5302** - Bonus & Overtime Income (2-year average)
- **Section 5303** - Commission Income
- **Section 5304** - Employment Verification
- **Section 5305** - Income Continuance (3-year likelihood)

Income calculations follow official worksheets and require:
- 2 most recent W-2 forms
- Most recent paystub (within 30 days)
- Verification of Employment (VOE) recommended
- Bonus/overtime averaged over 2 years if applicable

## Gap Severity Guide

### When Gaps are Critical

- Missing borrower identification (name, SSN, DOB)
- No employment information
- No income documentation
- Missing loan amount or property details
- Incomplete property address

### When Gaps are Warnings

- Missing contact information (email, phone)
- No asset documentation
- Incomplete employment dates
- Missing recommended income details
- No co-borrower information (if applicable)

### When Gaps are Informational

- Optional income sources not documented
- Additional assets not listed
- Previous address if < 2 years at current
- Non-required declarations

## Troubleshooting

### "No W-2 documents found"

Make sure your W-2 PDFs:
- Are in the documents folder
- Have recognizable W-2 content
- Include employee name, SSN, employer name, and wages

### "Missing SSN or critical borrower information"

Check that documents contain:
- Full legal name
- Social Security Number
- Date of birth
- Current address

### "MISMO XML validation errors"

Common issues:
- Missing required fields (check gap report)
- Invalid date formats (use YYYY-MM-DD)
- Invalid SSN format (use XXX-XX-XXXX)
- Missing loan or property information

### "Low completion percentage"

The completion percentage is based on **critical required fields only**. A score of:
- **90-100%**: Ready for submission
- **75-89%**: Almost ready, minor gaps
- **50-74%**: Substantial information needed
- **<50%**: Major information gaps

## Advanced Features

### Custom Field Mapping

You can customize MISMO field mappings in `mismo_generator.py`:

```python
def _build_borrower_from_data(self, extracted_data, income_analysis):
    # Add custom field mappings here
    borrower.custom_field = extracted_data.get('CUSTOM_DOC', {}).get('field')
    return borrower
```

### Additional Document Types

To support new document types:

1. Add to `document_extractor.py`:
   ```python
   class DocumentType(Enum):
       CUSTOM_TYPE = "CUSTOM_TYPE"
   ```

2. Add extraction logic:
   ```python
   def extract_custom_type_data(self, text: str) -> dict:
       # Custom extraction logic
       return {}
   ```

3. Update MISMO generator to use new data

### Custom Gap Analysis Rules

Add custom validation in `gap_analyzer.py`:

```python
def analyze_custom_requirements(self, mismo_data):
    gaps = []
    
    # Add custom validation logic
    if custom_condition:
        gaps.append(InformationGap(
            field_name='custom_field',
            section='Custom Section',
            severity=GapSeverity.WARNING,
            description='Custom requirement not met',
            recommendation='Provide custom documentation'
        ))
    
    return gaps
```

## Next Steps

1. **Run the demo** with sample Elmo James documents
2. **Review the gap report** to understand missing information
3. **Examine the MISMO XML** to see the generated output
4. **Integrate with your LOS** by importing the XML file
5. **Customize mappings** for your specific workflow needs

For more information, see:
- [README.md](README.md) - Main documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [EXAMPLES.md](EXAMPLES.md) - Usage examples
- [MISMO Sample XML](mismo-sample.xml) - Example MISMO file
