"""
Mortgage Application Assistant
Main orchestrator that coordinates document processing, underwriting, and URLA form filling
"""
import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict

from pdf_parser import PDFParser, URLAFormParser
from document_extractor import DocumentClassifier, DocumentExtractor, process_document
from underwriting_engine import FreddieUnderwritingEngine, IncomeAnalysis
from urla_analyzer import URLAFormAnalyzer
from mismo_generator import MISMOGenerator
from gap_analyzer import GapAnalyzer


@dataclass
class MortgageApplication:
    """Complete mortgage application data"""
    borrower_info: Dict[str, Any]
    documents: List[Dict[str, Any]]
    income_analysis: Optional[IncomeAnalysis]
    urla_data: Dict[str, Any]
    completion_status: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        result = {
            'borrower_info': self.borrower_info,
            'documents': self.documents,
            'urla_data': self.urla_data,
            'completion_status': self.completion_status
        }
        if self.income_analysis:
            result['income_analysis'] = self.income_analysis.to_dict()
        return result
    
    def to_json(self, file_path: str):
        """Save application to JSON file"""
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


class MortgageAssistant:
    """AI Assistant for mortgage application processing"""
    
    def __init__(self, api_key: Optional[str] = None, freddie_rules: str = "freddie_income_guides.json"):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.classifier = DocumentClassifier(self.api_key)
        self.extractor = DocumentExtractor(self.api_key)
        self.underwriting_engine = FreddieUnderwritingEngine(freddie_rules)
        self.urla_analyzer = URLAFormAnalyzer()
        self.mismo_generator = MISMOGenerator()
        self.gap_analyzer = GapAnalyzer()
        
        self.processed_documents = []
        self.extracted_data = {}
    
    def process_document_folder(self, folder_path: str, file_pattern: str = "*.pdf") -> List[Dict]:
        """
        Process all documents in a folder
        Returns list of processed documents with classification and extracted data
        """
        
        folder = Path(folder_path)
        pdf_files = list(folder.glob(file_pattern))
        
        print(f"Found {len(pdf_files)} PDF files to process\n")
        
        results = []
        
        for pdf_file in pdf_files:
            print(f"Processing: {pdf_file.name}")
            
            try:
                # Parse PDF
                parser = PDFParser(str(pdf_file))
                extracted_text = parser.extract_text()
                
                # Classify
                classification = self.classifier.classify_document(extracted_text)
                print(f"  → Classified as: {classification.document_type} ({classification.confidence:.0%} confidence)")
                
                # Extract data
                extracted_data = self.extractor.extract(extracted_text, classification.document_type)
                print(f"  → Extracted {len(extracted_data.extracted_fields)} fields")
                
                result = {
                    'filename': pdf_file.name,
                    'file_path': str(pdf_file),
                    'classification': classification.to_dict(),
                    'extracted_data': extracted_data.to_dict()
                }
                
                results.append(result)
                self.processed_documents.append(result)
                
                # Organize by document type
                doc_type = classification.document_type
                if doc_type not in self.extracted_data:
                    self.extracted_data[doc_type] = []
                self.extracted_data[doc_type].append(extracted_data.extracted_fields)
                
                print("  ✓ Complete\n")
                
            except Exception as e:
                print(f"  ✗ Error: {e}\n")
                results.append({
                    'filename': pdf_file.name,
                    'error': str(e)
                })
        
        return results
    
    def analyze_income(self) -> Optional[IncomeAnalysis]:
        """
        Analyze income using Freddie Mac underwriting rules
        """
        
        print("\n" + "=" * 70)
        print("INCOME ANALYSIS")
        print("=" * 70 + "\n")
        
        # Gather W-2 data
        w2_data = self.extracted_data.get('W2', [])
        if not w2_data:
            print("⚠ No W-2 documents found")
            return None
        
        print(f"Found {len(w2_data)} W-2 document(s)")
        
        # Get most recent paystub
        paystub_data = None
        paystubs = self.extracted_data.get('PAYSTUB', [])
        if paystubs:
            paystub_data = paystubs[0]  # Most recent
            print(f"Found paystub data")
        
        # Get VOE
        voe_data = None
        voes = self.extracted_data.get('VOE', [])
        if voes:
            voe_data = voes[0]
            print(f"Found VOE data")
        
        # Perform analysis
        analysis = self.underwriting_engine.analyze_w2_income(w2_data, paystub_data, voe_data)
        
        # Print worksheet
        worksheet = self.underwriting_engine.generate_income_calculation_worksheet(analysis)
        print("\n" + worksheet)
        
        return analysis
    
    def map_to_urla(self) -> Dict[str, Any]:
        """
        Map extracted document data to URLA form fields
        """
        
        print("\n" + "=" * 70)
        print("MAPPING TO URLA FORM")
        print("=" * 70 + "\n")
        
        # Prepare data for mapping
        mapping_data = {}
        
        # Include all extracted document data
        for doc_type, data_list in self.extracted_data.items():
            if data_list:
                if doc_type in ['W2', 'PAYSTUB', 'VOE']:
                    mapping_data[f'{doc_type.lower()}_data'] = data_list[0] if len(data_list) == 1 else data_list
        
        # Map to URLA
        urla_data = self.urla_analyzer.get_field_mapping_from_docs(mapping_data)
        
        print(f"Mapped {len(urla_data)} fields to URLA form")
        
        return urla_data
    
    def generate_urla_report(self, urla_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate URLA completion report
        """
        
        print("\n" + "=" * 70)
        print("URLA FORM COMPLETION STATUS")
        print("=" * 70 + "\n")
        
        report = self.urla_analyzer.generate_completion_report(urla_data)
        
        print(f"Total Fields: {report['total_fields']}")
        print(f"Filled Fields: {report['filled_fields']} ({report['completion_percentage']}%)")
        print(f"Required Fields: {report['required_fields']}")
        print(f"Required Filled: {report['required_filled']} ({report['required_percentage']}%)")
        
        if report['missing_required']:
            print(f"\n⚠ Missing Required Fields ({len(report['missing_required'])}):")
            for field in report['missing_required'][:10]:  # Show first 10
                print(f"  - {field}")
            if len(report['missing_required']) > 10:
                print(f"  ... and {len(report['missing_required']) - 10} more")
        
        if report['validation_errors']:
            print(f"\n⚠ Validation Errors:")
            for error in report['validation_errors']:
                print(f"  - {error}")
        
        if report['is_ready_to_submit']:
            print("\n✓ Form is ready to submit!")
        else:
            print("\n✗ Form is not ready to submit - please complete missing fields")
        
        return report
    
    def create_application(self) -> MortgageApplication:
        """
        Create a complete mortgage application from processed documents
        """
        
        # Analyze income
        income_analysis = self.analyze_income()
        
        # Map to URLA
        urla_data = self.map_to_urla()
        
        # Generate completion report
        completion_status = self.generate_urla_report(urla_data)
        
        # Extract borrower info
        borrower_info = {
            'name': urla_data.get('borrower_first_name', '') + ' ' + urla_data.get('borrower_last_name', ''),
            'ssn': urla_data.get('borrower_ssn'),
            'employer': urla_data.get('employer_name'),
        }
        
        application = MortgageApplication(
            borrower_info=borrower_info,
            documents=self.processed_documents,
            income_analysis=income_analysis,
            urla_data=urla_data,
            completion_status=completion_status
        )
        
        return application
    
    def generate_summary_report(self, application: MortgageApplication) -> str:
        """
        Generate a human-readable summary report
        """
        
        lines = []
        lines.append("=" * 70)
        lines.append("MORTGAGE APPLICATION SUMMARY")
        lines.append("=" * 70)
        lines.append("")
        
        # Borrower Info
        lines.append("BORROWER INFORMATION:")
        lines.append("-" * 70)
        for key, value in application.borrower_info.items():
            if value:
                lines.append(f"  {key.replace('_', ' ').title()}: {value}")
        lines.append("")
        
        # Documents Processed
        lines.append(f"DOCUMENTS PROCESSED: {len(application.documents)}")
        lines.append("-" * 70)
        doc_types = {}
        for doc in application.documents:
            if 'classification' in doc:
                doc_type = doc['classification']['document_type']
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
        
        for doc_type, count in doc_types.items():
            lines.append(f"  {doc_type}: {count}")
        lines.append("")
        
        # Income Summary
        if application.income_analysis:
            lines.append("INCOME SUMMARY:")
            lines.append("-" * 70)
            lines.append(f"  Total Monthly Income: ${application.income_analysis.total_monthly_income:,.2f}")
            lines.append(f"  Income Sources: {len(application.income_analysis.income_sources)}")
            lines.append(f"  Meets Freddie Mac Requirements: {'YES' if application.income_analysis.meets_requirements else 'NO'}")
            lines.append("")
        
        # URLA Status
        lines.append("URLA FORM STATUS:")
        lines.append("-" * 70)
        status = application.completion_status
        lines.append(f"  Overall Completion: {status['completion_percentage']}%")
        lines.append(f"  Required Fields Completion: {status['required_percentage']}%")
        lines.append(f"  Ready to Submit: {'YES' if status['is_ready_to_submit'] else 'NO'}")
        lines.append("")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    def generate_mismo_xml(self, income_analysis: Optional[IncomeAnalysis] = None) -> str:
        """
        Generate MISMO XML from extracted data
        """
        
        print("\n" + "=" * 70)
        print("GENERATING MISMO XML")
        print("=" * 70 + "\n")
        
        # Generate MISMO XML from extracted data
        mismo_xml = self.mismo_generator.generate_from_extracted_data(
            self.extracted_data,
            income_analysis
        )
        
        print("✓ MISMO XML generated successfully")
        
        return mismo_xml
    
    def analyze_gaps(self, mismo_xml: str) -> str:
        """
        Analyze application for information gaps
        """
        
        print("\n" + "=" * 70)
        print("ANALYZING INFORMATION GAPS")
        print("=" * 70 + "\n")
        
        # Parse the generated MISMO XML
        from mismo_parser import MISMOParser
        parser = MISMOParser(None)  # Pass None for xml_file since we'll use parse_string
        mismo_data = parser.parse_string(mismo_xml)
        
        # Analyze gaps
        gaps = self.gap_analyzer.analyze_all(mismo_data, self.extracted_data)
        
        # Generate report
        gap_report = self.gap_analyzer.generate_report(gaps)
        
        return gap_report
    
    def save_results(self, output_dir: str = "output", mismo_xml: Optional[str] = None, gap_report: Optional[str] = None):
        """
        Save all results to output directory
        """
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save processed documents
        with open(output_path / "processed_documents.json", 'w') as f:
            json.dump(self.processed_documents, f, indent=2)
        
        # Save extracted data
        with open(output_path / "extracted_data.json", 'w') as f:
            json.dump(self.extracted_data, f, indent=2)
        
        # Save MISMO XML
        if mismo_xml:
            with open(output_path / "mortgage_application.xml", 'w', encoding='utf-8') as f:
                f.write(mismo_xml)
            print(f"✓ MISMO XML saved to {output_dir}/mortgage_application.xml")
        
        # Save gap report
        if gap_report:
            with open(output_path / "gap_analysis_report.txt", 'w', encoding='utf-8') as f:
                f.write(gap_report)
            print(f"✓ Gap analysis report saved to {output_dir}/gap_analysis_report.txt")
        
        print(f"✓ Results saved to {output_dir}/")


def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python mortgage_assistant.py <folder_path>")
        print("Example: python mortgage_assistant.py /path/to/documents")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    
    if not Path(folder_path).exists():
        print(f"Error: Folder not found: {folder_path}")
        sys.exit(1)
    
    print("=" * 70)
    print("MORTGAGE APPLICATION ASSISTANT")
    print("AI-Powered URLA Form Filling System")
    print("=" * 70)
    print("")
    
    # Initialize assistant
    assistant = MortgageAssistant()
    
    # Process documents
    print("STEP 1: Processing Documents")
    print("-" * 70)
    assistant.process_document_folder(folder_path)
    
    # Create application
    print("\nSTEP 2: Creating Mortgage Application")
    print("-" * 70)
    application = assistant.create_application()
    
    # Generate MISMO XML
    print("\nSTEP 3: Generating MISMO XML")
    print("-" * 70)
    mismo_xml = assistant.generate_mismo_xml(application.income_analysis)
    
    # Analyze gaps
    print("\nSTEP 4: Analyzing Information Gaps")
    print("-" * 70)
    gap_report = assistant.analyze_gaps(mismo_xml)
    print(gap_report)
    
    # Generate summary
    print("\n" + assistant.generate_summary_report(application))
    
    # Save results
    assistant.save_results(mismo_xml=mismo_xml, gap_report=gap_report)
    
    # Save application
    application.to_json("output/mortgage_application.json")
    print("✓ Complete application saved to output/mortgage_application.json")


if __name__ == "__main__":
    main()
