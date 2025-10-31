"""
Document Classifier and Extractor
Uses AI to classify document types and extract structured information
"""
import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import re

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from pdf_parser import PDFParser, ExtractedText


@dataclass
class DocumentClassification:
    """Classification result for a document"""
    document_type: str
    confidence: float
    suggested_category: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ExtractedData:
    """Structured data extracted from a document"""
    document_type: str
    filename: str
    extracted_fields: Dict[str, Any]
    extraction_date: str
    confidence_score: float = 0.0
    
    def to_dict(self) -> Dict:
        return asdict(self)


class DocumentClassifier:
    """Classifies documents using AI"""
    
    DOCUMENT_TYPES = {
        'W2': 'W-2 Wage and Tax Statement',
        'PAYSTUB': 'Pay Stub / Pay Statement',
        'VOE': 'Verification of Employment',
        'BANK_STATEMENT': 'Bank Statement',
        'CREDIT_REPORT': 'Credit Report',
        'MORTGAGE_STATEMENT': 'Mortgage Statement',
        'TAX_RETURN': 'Tax Return (1040)',
        'URLA': 'Uniform Residential Loan Application',
        'OTHER': 'Other Document'
    }
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if self.api_key and OpenAI:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
    
    def classify_document(self, extracted_text: ExtractedText) -> DocumentClassification:
        """Classify a document based on its text content"""
        
        # Rule-based classification first (fast and reliable for common cases)
        text_lower = extracted_text.full_text.lower()
        
        if 'form w-2' in text_lower or 'wage and tax statement' in text_lower:
            return DocumentClassification('W2', 0.95, 'INCOME_VERIFICATION')
        
        if 'verification of employment' in text_lower or 'voe' in text_lower:
            return DocumentClassification('VOE', 0.90, 'INCOME_VERIFICATION')
        
        if any(term in text_lower for term in ['pay stub', 'paystub', 'earnings statement']):
            return DocumentClassification('PAYSTUB', 0.90, 'INCOME_VERIFICATION')
        
        if 'credit report' in text_lower or 'credit score' in text_lower or 'fico' in text_lower:
            return DocumentClassification('CREDIT_REPORT', 0.90, 'CREDIT_ANALYSIS')
        
        if 'bank statement' in text_lower or 'account statement' in text_lower:
            return DocumentClassification('BANK_STATEMENT', 0.85, 'ASSET_VERIFICATION')
        
        if 'mortgage statement' in text_lower or 'principal balance' in text_lower:
            return DocumentClassification('MORTGAGE_STATEMENT', 0.85, 'LIABILITY_VERIFICATION')
        
        if 'uniform residential loan application' in text_lower or 'fannie mae form 1003' in text_lower:
            return DocumentClassification('URLA', 0.95, 'LOAN_APPLICATION')
        
        # If rule-based fails, use AI if available
        if self.client:
            return self._ai_classify(extracted_text)
        
        return DocumentClassification('OTHER', 0.50, 'UNKNOWN')
    
    def _ai_classify(self, extracted_text: ExtractedText) -> DocumentClassification:
        """Use AI to classify document"""
        
        prompt = f"""Classify the following document into one of these categories:
{json.dumps(self.DOCUMENT_TYPES, indent=2)}

Document text (first 2000 characters):
{extracted_text.full_text[:2000]}

Respond with JSON in this format:
{{
    "document_type": "one of the keys from DOCUMENT_TYPES",
    "confidence": 0.0 to 1.0,
    "suggested_category": "INCOME_VERIFICATION, ASSET_VERIFICATION, LIABILITY_VERIFICATION, CREDIT_ANALYSIS, LOAN_APPLICATION, or UNKNOWN"
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a document classification expert for mortgage underwriting."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            return DocumentClassification(**result)
        except Exception as e:
            print(f"AI classification error: {e}")
            return DocumentClassification('OTHER', 0.50, 'UNKNOWN')


class DocumentExtractor:
    """Extracts structured information from classified documents"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if self.api_key and OpenAI:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
    
    def extract_w2_data(self, extracted_text: ExtractedText) -> ExtractedData:
        """Extract data from W-2 form"""
        
        text = extracted_text.full_text
        
        # Extract using regex patterns first
        fields = {
            'employer_name': self._extract_field(text, r'(?:employer|company)\s*name[:\s]*([^\n]+)', 1),
            'employer_ein': self._extract_field(text, r'ein[:\s]*([0-9\-]+)', 1),
            'employee_name': self._extract_field(text, r'(?:employee|worker)\s*name[:\s]*([^\n]+)', 1),
            'employee_ssn': self._extract_field(text, r'ssn[:\s]*([0-9\-]+)', 1),
            'wages': self._extract_currency(text, r'wages[,\s]*tips[,\s]*other\s*compensation[:\s]*\$?\s*([0-9,\.]+)'),
            'federal_tax_withheld': self._extract_currency(text, r'federal\s*income\s*tax\s*withheld[:\s]*\$?\s*([0-9,\.]+)'),
            'year': self._extract_field(text, r'(?:tax\s*year|year)[:\s]*([0-9]{4})', 1)
        }
        
        # Use AI for more accurate extraction if available
        if self.client:
            ai_fields = self._ai_extract_w2(text)
            fields.update({k: v for k, v in ai_fields.items() if v})
        
        return ExtractedData(
            document_type='W2',
            filename=extracted_text.metadata.filename,
            extracted_fields=fields,
            extraction_date=datetime.now().isoformat(),
            confidence_score=0.85
        )
    
    def extract_paystub_data(self, extracted_text: ExtractedText) -> ExtractedData:
        """Extract data from paystub"""
        
        text = extracted_text.full_text
        
        fields = {
            'employer_name': self._extract_field(text, r'(?:employer|company)[:\s]*([^\n]+)', 1),
            'employee_name': self._extract_field(text, r'(?:employee|name)[:\s]*([^\n]+)', 1),
            'pay_period_start': self._extract_field(text, r'pay\s*period[:\s]*([0-9\/\-]+)', 1),
            'pay_period_end': self._extract_field(text, r'(?:to|through|end)[:\s]*([0-9\/\-]+)', 1),
            'pay_date': self._extract_field(text, r'pay\s*date[:\s]*([0-9\/\-]+)', 1),
            'gross_pay': self._extract_currency(text, r'gross\s*pay[:\s]*\$?\s*([0-9,\.]+)'),
            'net_pay': self._extract_currency(text, r'net\s*pay[:\s]*\$?\s*([0-9,\.]+)'),
            'ytd_gross': self._extract_currency(text, r'ytd\s*gross[:\s]*\$?\s*([0-9,\.]+)'),
            'ytd_net': self._extract_currency(text, r'ytd\s*net[:\s]*\$?\s*([0-9,\.]+)')
        }
        
        if self.client:
            ai_fields = self._ai_extract_paystub(text)
            fields.update({k: v for k, v in ai_fields.items() if v})
        
        return ExtractedData(
            document_type='PAYSTUB',
            filename=extracted_text.metadata.filename,
            extracted_fields=fields,
            extraction_date=datetime.now().isoformat(),
            confidence_score=0.80
        )
    
    def extract_voe_data(self, extracted_text: ExtractedText) -> ExtractedData:
        """Extract data from Verification of Employment"""
        
        text = extracted_text.full_text
        
        fields = {
            'employer_name': self._extract_field(text, r'employer[:\s]*([^\n]+)', 1),
            'employee_name': self._extract_field(text, r'employee[:\s]*([^\n]+)', 1),
            'job_title': self._extract_field(text, r'(?:job\s*title|position)[:\s]*([^\n]+)', 1),
            'employment_start_date': self._extract_field(text, r'(?:hire|start|employment)\s*date[:\s]*([0-9\/\-]+)', 1),
            'employment_status': self._extract_field(text, r'(?:status|type)[:\s]*(full[- ]time|part[- ]time|contract)', 1),
            'base_salary': self._extract_currency(text, r'(?:base\s*salary|annual\s*income)[:\s]*\$?\s*([0-9,\.]+)'),
            'likelihood_of_continued_employment': self._extract_field(text, r'likelihood[^\n]*([^\n]+)', 1)
        }
        
        if self.client:
            ai_fields = self._ai_extract_voe(text)
            fields.update({k: v for k, v in ai_fields.items() if v})
        
        return ExtractedData(
            document_type='VOE',
            filename=extracted_text.metadata.filename,
            extracted_fields=fields,
            extraction_date=datetime.now().isoformat(),
            confidence_score=0.85
        )
    
    def extract(self, extracted_text: ExtractedText, doc_type: str) -> ExtractedData:
        """Main extraction method that routes to specific extractors"""
        
        extractors = {
            'W2': self.extract_w2_data,
            'PAYSTUB': self.extract_paystub_data,
            'VOE': self.extract_voe_data
        }
        
        extractor = extractors.get(doc_type)
        if extractor:
            return extractor(extracted_text)
        
        # Generic extraction for unknown types
        return ExtractedData(
            document_type=doc_type,
            filename=extracted_text.metadata.filename,
            extracted_fields={'raw_text': extracted_text.full_text[:1000]},
            extraction_date=datetime.now().isoformat(),
            confidence_score=0.50
        )
    
    def _extract_field(self, text: str, pattern: str, group: int = 0) -> Optional[str]:
        """Extract a field using regex"""
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(group).strip() if match else None
    
    def _extract_currency(self, text: str, pattern: str) -> Optional[float]:
        """Extract currency value"""
        value_str = self._extract_field(text, pattern, 1)
        if value_str:
            # Remove commas and convert to float
            try:
                return float(value_str.replace(',', ''))
            except ValueError:
                pass
        return None
    
    def _ai_extract_w2(self, text: str) -> Dict[str, Any]:
        """Use AI to extract W-2 fields"""
        
        prompt = f"""Extract the following fields from this W-2 form:
- employer_name
- employer_ein
- employee_name
- employee_ssn
- wages (Box 1)
- federal_tax_withheld (Box 2)
- social_security_wages (Box 3)
- year

Document text:
{text[:3000]}

Respond with JSON containing these fields. Use null for missing values.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a document data extraction expert."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"AI extraction error: {e}")
            return {}
    
    def _ai_extract_paystub(self, text: str) -> Dict[str, Any]:
        """Use AI to extract paystub fields"""
        
        prompt = f"""Extract the following fields from this paystub:
- employer_name
- employee_name
- pay_period_start
- pay_period_end
- pay_date
- gross_pay (current period)
- net_pay (current period)
- ytd_gross (year-to-date gross)
- ytd_net (year-to-date net)
- hourly_rate (if applicable)
- hours_worked (if applicable)

Document text:
{text[:3000]}

Respond with JSON containing these fields. Use null for missing values.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a document data extraction expert."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"AI extraction error: {e}")
            return {}
    
    def _ai_extract_voe(self, text: str) -> Dict[str, Any]:
        """Use AI to extract VOE fields"""
        
        prompt = f"""Extract the following fields from this Verification of Employment:
- employer_name
- employee_name
- job_title
- employment_start_date
- employment_status (full-time, part-time, contract)
- base_salary (annual)
- hourly_rate (if applicable)
- hours_per_week
- likelihood_of_continued_employment
- verifier_name
- verifier_title
- verification_date

Document text:
{text[:3000]}

Respond with JSON containing these fields. Use null for missing values.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a document data extraction expert."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"AI extraction error: {e}")
            return {}


def process_document(file_path: str, api_key: Optional[str] = None) -> tuple[DocumentClassification, ExtractedData]:
    """Process a document: parse, classify, and extract data"""
    
    # Parse PDF
    parser = PDFParser(file_path)
    extracted_text = parser.extract_text()
    
    # Classify
    classifier = DocumentClassifier(api_key)
    classification = classifier.classify_document(extracted_text)
    
    # Extract
    extractor = DocumentExtractor(api_key)
    extracted_data = extractor.extract(extracted_text, classification.document_type)
    
    return classification, extracted_data


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        
        print(f"Processing: {pdf_path}\n")
        
        classification, data = process_document(pdf_path)
        
        print("Classification:")
        print(json.dumps(classification.to_dict(), indent=2))
        
        print("\nExtracted Data:")
        print(json.dumps(data.to_dict(), indent=2))
