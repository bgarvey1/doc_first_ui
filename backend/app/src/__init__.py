"""
Mortgage Application Assistant Package
AI-Powered URLA Form Filling System
"""

__version__ = "1.0.0"
__author__ = "Mortgage AI Assistant"

from .pdf_parser import PDFParser, URLAFormParser, parse_pdf, parse_urla
from .document_extractor import DocumentClassifier, DocumentExtractor, process_document
from .underwriting_engine import FreddieUnderwritingEngine, IncomeSource, IncomeAnalysis
from .urla_analyzer import URLAFormAnalyzer, URLAField, URLASection
from .mortgage_assistant import MortgageAssistant, MortgageApplication

__all__ = [
    'PDFParser',
    'URLAFormParser',
    'parse_pdf',
    'parse_urla',
    'DocumentClassifier',
    'DocumentExtractor',
    'process_document',
    'FreddieUnderwritingEngine',
    'IncomeSource',
    'IncomeAnalysis',
    'URLAFormAnalyzer',
    'URLAField',
    'URLASection',
    'MortgageAssistant',
    'MortgageApplication',
]
