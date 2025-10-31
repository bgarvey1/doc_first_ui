"""
PDF Document Parser Module
Handles extraction of text and form fields from PDF documents
"""
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
import pdfplumber
import PyPDF2
import fitz  # PyMuPDF
from dataclasses import dataclass, asdict
import json


@dataclass
class PDFMetadata:
    """Metadata extracted from a PDF document"""
    filename: str
    num_pages: int
    author: Optional[str] = None
    title: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ExtractedText:
    """Text content extracted from a PDF"""
    full_text: str
    pages: List[str]
    metadata: PDFMetadata
    
    def to_dict(self) -> Dict:
        return {
            'full_text': self.full_text,
            'pages': self.pages,
            'metadata': self.metadata.to_dict()
        }


class PDFParser:
    """Parser for extracting content from PDF documents"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
    
    def extract_metadata(self) -> PDFMetadata:
        """Extract metadata from the PDF"""
        with open(self.file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            metadata = pdf_reader.metadata
            
            return PDFMetadata(
                filename=self.file_path.name,
                num_pages=len(pdf_reader.pages),
                author=metadata.get('/Author'),
                title=metadata.get('/Title'),
                subject=metadata.get('/Subject'),
                creator=metadata.get('/Creator'),
                producer=metadata.get('/Producer')
            )
    
    def extract_text(self) -> ExtractedText:
        """Extract text content from the PDF using pdfplumber"""
        pages_text = []
        
        with pdfplumber.open(self.file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)
                else:
                    pages_text.append("")
        
        full_text = "\n\n--- PAGE BREAK ---\n\n".join(pages_text)
        metadata = self.extract_metadata()
        
        return ExtractedText(
            full_text=full_text,
            pages=pages_text,
            metadata=metadata
        )
    
    def extract_text_with_pymupdf(self) -> ExtractedText:
        """Alternative extraction using PyMuPDF for better accuracy"""
        doc = fitz.open(self.file_path)
        pages_text = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            pages_text.append(text)
        
        full_text = "\n\n--- PAGE BREAK ---\n\n".join(pages_text)
        metadata = self.extract_metadata()
        
        doc.close()
        
        return ExtractedText(
            full_text=full_text,
            pages=pages_text,
            metadata=metadata
        )
    
    def extract_form_fields(self) -> Dict[str, Any]:
        """Extract form fields from a fillable PDF"""
        form_fields = {}
        
        with open(self.file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            if pdf_reader.is_encrypted:
                return {"error": "PDF is encrypted"}
            
            # Try to extract form fields
            if hasattr(pdf_reader, 'get_fields'):
                fields = pdf_reader.get_fields()
                if fields:
                    for field_name, field_data in fields.items():
                        form_fields[field_name] = {
                            'value': field_data.get('/V', ''),
                            'type': field_data.get('/FT', ''),
                            'flags': field_data.get('/Ff', 0)
                        }
        
        return form_fields
    
    def extract_tables(self) -> List[List[List[str]]]:
        """Extract tables from the PDF"""
        all_tables = []
        
        with pdfplumber.open(self.file_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                if tables:
                    all_tables.extend(tables)
        
        return all_tables
    
    def get_page_images(self, page_num: int = 0) -> List[Dict]:
        """Extract images from a specific page"""
        doc = fitz.open(self.file_path)
        page = doc[page_num]
        
        images = []
        image_list = page.get_images()
        
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            images.append({
                'index': img_index,
                'width': base_image['width'],
                'height': base_image['height'],
                'colorspace': base_image['colorspace'],
                'ext': base_image['ext']
            })
        
        doc.close()
        return images


class URLAFormParser(PDFParser):
    """Specialized parser for URLA (Uniform Residential Loan Application) forms"""
    
    def parse_urla_structure(self) -> Dict[str, Any]:
        """Parse the URLA form structure and identify sections"""
        extracted_text = self.extract_text()
        form_fields = self.extract_form_fields()
        
        # URLA sections based on Fannie Mae Form 1003
        urla_sections = {
            'section_1a': 'Borrower Information',
            'section_1b': 'Current Employment/Self-Employment and Income',
            'section_1c': 'Previous Employment/Self-Employment and Income',
            'section_1d': 'Income from Other Sources',
            'section_2a': 'Financial Information - Assets',
            'section_2b': 'Financial Information - Liabilities',
            'section_3a': 'Financial Information - Real Estate',
            'section_3b': 'Financial Information - Other Real Estate Owned',
            'section_4a': 'Loan and Property Information',
            'section_4b': 'Property Information and Purpose of Loan',
            'section_5a': 'Declarations - Borrower',
            'section_5b': 'Declarations - Co-Borrower',
            'section_6': 'Acknowledgments and Agreements',
            'section_7': 'Military Service',
            'section_8': 'Demographic Information',
            'section_9': 'Loan Originator Information'
        }
        
        return {
            'sections': urla_sections,
            'form_fields': form_fields,
            'total_pages': extracted_text.metadata.num_pages,
            'text_sample': extracted_text.full_text[:1000] if extracted_text.full_text else None
        }


def parse_pdf(file_path: str, use_pymupdf: bool = False) -> ExtractedText:
    """Convenience function to parse a PDF and extract text"""
    parser = PDFParser(file_path)
    if use_pymupdf:
        return parser.extract_text_with_pymupdf()
    return parser.extract_text()


def parse_urla(file_path: str) -> Dict[str, Any]:
    """Convenience function to parse a URLA form"""
    parser = URLAFormParser(file_path)
    return parser.parse_urla_structure()


if __name__ == "__main__":
    # Test the parser
    import sys
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        parser = PDFParser(pdf_path)
        
        print(f"Parsing: {pdf_path}\n")
        
        # Extract metadata
        metadata = parser.extract_metadata()
        print("Metadata:")
        print(json.dumps(metadata.to_dict(), indent=2))
        
        # Extract text
        extracted = parser.extract_text()
        print(f"\nExtracted {len(extracted.pages)} pages")
        print(f"Total characters: {len(extracted.full_text)}")
        print("\nFirst 500 characters:")
        print(extracted.full_text[:500])
