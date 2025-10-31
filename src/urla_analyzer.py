"""
URLA Form Analyzer
Parses and analyzes the Uniform Residential Loan Application (Fannie Mae Form 1003)
"""
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime


@dataclass
class URLAField:
    """Represents a field in the URLA form"""
    section: str
    field_name: str
    field_type: str  # TEXT, NUMBER, DATE, CHECKBOX, DROPDOWN
    required: bool
    description: str
    current_value: Optional[Any] = None
    validation_rules: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class URLASection:
    """Represents a section of the URLA form"""
    section_id: str
    section_name: str
    description: str
    fields: List[URLAField]
    subsections: List['URLASection'] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'section_id': self.section_id,
            'section_name': self.section_name,
            'description': self.description,
            'fields': [f.to_dict() for f in self.fields],
            'subsections': [s.to_dict() for s in self.subsections]
        }


class URLAFormAnalyzer:
    """Analyzes URLA form structure and requirements"""
    
    def __init__(self):
        self.sections = self._define_urla_structure()
    
    def _define_urla_structure(self) -> List[URLASection]:
        """
        Define the URLA form structure based on Fannie Mae Form 1003 (2019 version)
        """
        
        sections = []
        
        # Section 1a: Borrower Information
        section_1a = URLASection(
            section_id='1a',
            section_name='Borrower Information',
            description='Personal information about the borrower',
            fields=[
                URLAField('1a', 'borrower_first_name', 'TEXT', True, 'First Name'),
                URLAField('1a', 'borrower_middle_name', 'TEXT', False, 'Middle Name'),
                URLAField('1a', 'borrower_last_name', 'TEXT', True, 'Last Name'),
                URLAField('1a', 'borrower_suffix', 'TEXT', False, 'Suffix (Jr., Sr., etc.)'),
                URLAField('1a', 'borrower_ssn', 'TEXT', True, 'Social Security Number', validation_rules=['SSN_FORMAT']),
                URLAField('1a', 'borrower_dob', 'DATE', True, 'Date of Birth'),
                URLAField('1a', 'borrower_citizenship', 'DROPDOWN', True, 'Citizenship Status'),
                URLAField('1a', 'borrower_marital_status', 'DROPDOWN', True, 'Marital Status'),
                URLAField('1a', 'borrower_dependents', 'NUMBER', False, 'Number of Dependents'),
                URLAField('1a', 'borrower_email', 'TEXT', False, 'Email Address'),
                URLAField('1a', 'borrower_phone_home', 'TEXT', True, 'Home Phone'),
                URLAField('1a', 'borrower_phone_cell', 'TEXT', False, 'Cell Phone'),
                URLAField('1a', 'borrower_current_address', 'TEXT', True, 'Current Address'),
                URLAField('1a', 'borrower_address_city', 'TEXT', True, 'City'),
                URLAField('1a', 'borrower_address_state', 'TEXT', True, 'State'),
                URLAField('1a', 'borrower_address_zip', 'TEXT', True, 'ZIP Code'),
                URLAField('1a', 'borrower_years_at_address', 'NUMBER', True, 'Years at Address'),
                URLAField('1a', 'borrower_housing_status', 'DROPDOWN', True, 'Housing Status (Own/Rent)'),
            ]
        )
        sections.append(section_1a)
        
        # Section 1b: Current Employment and Income
        section_1b = URLASection(
            section_id='1b',
            section_name='Current Employment/Self-Employment and Income',
            description='Current employment information and income sources',
            fields=[
                URLAField('1b', 'employer_name', 'TEXT', True, 'Employer or Business Name'),
                URLAField('1b', 'employer_phone', 'TEXT', True, 'Employer Phone Number'),
                URLAField('1b', 'employer_address', 'TEXT', True, 'Employer Address'),
                URLAField('1b', 'employer_city', 'TEXT', True, 'City'),
                URLAField('1b', 'employer_state', 'TEXT', True, 'State'),
                URLAField('1b', 'employer_zip', 'TEXT', True, 'ZIP Code'),
                URLAField('1b', 'employment_start_date', 'DATE', True, 'Start Date'),
                URLAField('1b', 'position_title', 'TEXT', True, 'Position/Title'),
                URLAField('1b', 'ownership_percentage', 'NUMBER', False, 'Ownership % (if self-employed)'),
                URLAField('1b', 'monthly_income_base', 'NUMBER', True, 'Base Monthly Income'),
                URLAField('1b', 'monthly_income_overtime', 'NUMBER', False, 'Overtime'),
                URLAField('1b', 'monthly_income_bonus', 'NUMBER', False, 'Bonus'),
                URLAField('1b', 'monthly_income_commission', 'NUMBER', False, 'Commission'),
                URLAField('1b', 'monthly_income_other', 'NUMBER', False, 'Other Income'),
                URLAField('1b', 'total_monthly_income', 'NUMBER', True, 'Total Monthly Income'),
            ]
        )
        sections.append(section_1b)
        
        # Section 1c: Previous Employment (if less than 2 years at current job)
        section_1c = URLASection(
            section_id='1c',
            section_name='Previous Employment/Self-Employment',
            description='Previous employment information (if applicable)',
            fields=[
                URLAField('1c', 'prev_employer_name', 'TEXT', False, 'Previous Employer Name'),
                URLAField('1c', 'prev_employment_start_date', 'DATE', False, 'Start Date'),
                URLAField('1c', 'prev_employment_end_date', 'DATE', False, 'End Date'),
                URLAField('1c', 'prev_position_title', 'TEXT', False, 'Position/Title'),
                URLAField('1c', 'prev_monthly_income', 'NUMBER', False, 'Monthly Income'),
            ]
        )
        sections.append(section_1c)
        
        # Section 2a: Financial Information - Assets
        section_2a = URLASection(
            section_id='2a',
            section_name='Financial Information - Assets',
            description='Bank accounts, investments, and other assets',
            fields=[
                URLAField('2a', 'checking_account_balance', 'NUMBER', False, 'Checking Account Balance'),
                URLAField('2a', 'savings_account_balance', 'NUMBER', False, 'Savings Account Balance'),
                URLAField('2a', 'retirement_accounts', 'NUMBER', False, 'Retirement Accounts (401k, IRA, etc.)'),
                URLAField('2a', 'stocks_bonds', 'NUMBER', False, 'Stocks and Bonds'),
                URLAField('2a', 'other_assets', 'NUMBER', False, 'Other Assets'),
                URLAField('2a', 'total_assets', 'NUMBER', True, 'Total Assets'),
            ]
        )
        sections.append(section_2a)
        
        # Section 2b: Financial Information - Liabilities
        section_2b = URLASection(
            section_id='2b',
            section_name='Financial Information - Liabilities',
            description='Credit cards, loans, and other liabilities',
            fields=[
                URLAField('2b', 'credit_card_debt', 'NUMBER', False, 'Credit Card Debt'),
                URLAField('2b', 'auto_loans', 'NUMBER', False, 'Auto Loans'),
                URLAField('2b', 'student_loans', 'NUMBER', False, 'Student Loans'),
                URLAField('2b', 'other_liabilities', 'NUMBER', False, 'Other Liabilities'),
                URLAField('2b', 'total_liabilities', 'NUMBER', True, 'Total Liabilities'),
            ]
        )
        sections.append(section_2b)
        
        # Section 4a: Loan and Property Information
        section_4a = URLASection(
            section_id='4a',
            section_name='Loan and Property Information',
            description='Details about the loan and property',
            fields=[
                URLAField('4a', 'loan_amount', 'NUMBER', True, 'Loan Amount'),
                URLAField('4a', 'loan_purpose', 'DROPDOWN', True, 'Loan Purpose (Purchase/Refinance)'),
                URLAField('4a', 'property_address', 'TEXT', True, 'Property Address'),
                URLAField('4a', 'property_city', 'TEXT', True, 'City'),
                URLAField('4a', 'property_state', 'TEXT', True, 'State'),
                URLAField('4a', 'property_zip', 'TEXT', True, 'ZIP Code'),
                URLAField('4a', 'property_type', 'DROPDOWN', True, 'Property Type'),
                URLAField('4a', 'occupancy_type', 'DROPDOWN', True, 'Occupancy (Primary/Secondary/Investment)'),
                URLAField('4a', 'property_value', 'NUMBER', True, 'Estimated Property Value'),
                URLAField('4a', 'down_payment', 'NUMBER', True, 'Down Payment Amount'),
            ]
        )
        sections.append(section_4a)
        
        # Section 5a: Declarations
        section_5a = URLASection(
            section_id='5a',
            section_name='Declarations',
            description='Required declarations about borrower circumstances',
            fields=[
                URLAField('5a', 'outstanding_judgments', 'CHECKBOX', True, 'Outstanding Judgments'),
                URLAField('5a', 'bankruptcy_last_7_years', 'CHECKBOX', True, 'Bankruptcy in Last 7 Years'),
                URLAField('5a', 'foreclosure_last_7_years', 'CHECKBOX', True, 'Foreclosure in Last 7 Years'),
                URLAField('5a', 'lawsuit_pending', 'CHECKBOX', True, 'Party to Lawsuit'),
                URLAField('5a', 'loan_delinquency', 'CHECKBOX', True, 'Delinquent on Federal Debt'),
                URLAField('5a', 'alimony_child_support', 'CHECKBOX', True, 'Obligated to Pay Alimony/Child Support'),
                URLAField('5a', 'down_payment_borrowed', 'CHECKBOX', True, 'Down Payment Borrowed'),
                URLAField('5a', 'cosigner_endorser', 'CHECKBOX', True, 'Co-signer/Endorser on Any Loan'),
                URLAField('5a', 'us_citizen', 'CHECKBOX', True, 'U.S. Citizen'),
                URLAField('5a', 'permanent_resident', 'CHECKBOX', True, 'Permanent Resident Alien'),
                URLAField('5a', 'primary_residence', 'CHECKBOX', True, 'Will Occupy as Primary Residence'),
            ]
        )
        sections.append(section_5a)
        
        # Section 7: Military Service
        section_7 = URLASection(
            section_id='7',
            section_name='Military Service',
            description='Military service information',
            fields=[
                URLAField('7', 'military_service', 'CHECKBOX', False, 'Currently Serving or Previously Served'),
                URLAField('7', 'service_member', 'CHECKBOX', False, 'Active Duty'),
                URLAField('7', 'veteran', 'CHECKBOX', False, 'Veteran'),
                URLAField('7', 'surviving_spouse', 'CHECKBOX', False, 'Surviving Spouse'),
            ]
        )
        sections.append(section_7)
        
        # Section 8: Demographic Information (Optional)
        section_8 = URLASection(
            section_id='8',
            section_name='Demographic Information',
            description='Optional demographic information',
            fields=[
                URLAField('8', 'ethnicity', 'CHECKBOX', False, 'Ethnicity'),
                URLAField('8', 'race', 'CHECKBOX', False, 'Race'),
                URLAField('8', 'sex', 'DROPDOWN', False, 'Sex'),
            ]
        )
        sections.append(section_8)
        
        return sections
    
    def get_all_fields(self) -> List[URLAField]:
        """Get a flat list of all URLA fields"""
        all_fields = []
        for section in self.sections:
            all_fields.extend(section.fields)
        return all_fields
    
    def get_required_fields(self) -> List[URLAField]:
        """Get only required fields"""
        return [field for field in self.get_all_fields() if field.required]
    
    def get_section(self, section_id: str) -> Optional[URLASection]:
        """Get a specific section by ID"""
        for section in self.sections:
            if section.section_id == section_id:
                return section
        return None
    
    def validate_field_value(self, field: URLAField, value: Any) -> tuple[bool, Optional[str]]:
        """Validate a field value against its rules"""
        
        if field.required and (value is None or value == ''):
            return False, f"{field.field_name} is required"
        
        if value is None or value == '':
            return True, None
        
        # Type validation
        if field.field_type == 'NUMBER':
            try:
                float(value)
            except (ValueError, TypeError):
                return False, f"{field.field_name} must be a number"
        
        # Custom validation rules
        for rule in field.validation_rules:
            if rule == 'SSN_FORMAT':
                # Basic SSN format check
                ssn_str = str(value).replace('-', '')
                if not (ssn_str.isdigit() and len(ssn_str) == 9):
                    return False, f"{field.field_name} must be a valid SSN format (XXX-XX-XXXX)"
        
        return True, None
    
    def get_field_mapping_from_docs(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map extracted document data to URLA form fields
        """
        
        mapping = {}
        
        # Map W-2 data
        if 'w2_data' in extracted_data:
            w2 = extracted_data['w2_data']
            if isinstance(w2, list) and len(w2) > 0:
                w2 = w2[0]  # Use most recent
            
            mapping['borrower_ssn'] = w2.get('employee_ssn')
            mapping['employer_name'] = w2.get('employer_name')
            
            # Calculate monthly income from W-2
            wages = w2.get('wages', 0)
            if wages:
                mapping['monthly_income_base'] = wages / 12
        
        # Map paystub data
        if 'paystub_data' in extracted_data:
            paystub = extracted_data['paystub_data']
            mapping['employer_name'] = paystub.get('employer_name') or mapping.get('employer_name')
            
            # Use YTD to calculate monthly income
            ytd_gross = paystub.get('ytd_gross', 0)
            if ytd_gross:
                # Estimate monthly (assumes partial year)
                import datetime
                current_month = datetime.datetime.now().month
                if current_month > 0:
                    mapping['monthly_income_base'] = ytd_gross / current_month
        
        # Map VOE data
        if 'voe_data' in extracted_data:
            voe = extracted_data['voe_data']
            mapping['employer_name'] = voe.get('employer_name') or mapping.get('employer_name')
            mapping['position_title'] = voe.get('job_title')
            mapping['employment_start_date'] = voe.get('employment_start_date')
            
            base_salary = voe.get('base_salary', 0)
            if base_salary:
                mapping['monthly_income_base'] = base_salary / 12
        
        return mapping
    
    def generate_completion_report(self, filled_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a report on URLA form completion status
        """
        
        all_fields = self.get_all_fields()
        required_fields = self.get_required_fields()
        
        filled_count = 0
        required_filled = 0
        missing_required = []
        validation_errors = []
        
        for field in all_fields:
            field_value = filled_data.get(field.field_name)
            
            if field_value is not None and field_value != '':
                filled_count += 1
                
                if field.required:
                    required_filled += 1
                
                # Validate
                is_valid, error = self.validate_field_value(field, field_value)
                if not is_valid:
                    validation_errors.append(error)
            else:
                if field.required:
                    missing_required.append(field.field_name)
        
        completion_percentage = (filled_count / len(all_fields)) * 100
        required_percentage = (required_filled / len(required_fields)) * 100 if required_fields else 0
        
        return {
            'total_fields': len(all_fields),
            'filled_fields': filled_count,
            'completion_percentage': round(completion_percentage, 1),
            'required_fields': len(required_fields),
            'required_filled': required_filled,
            'required_percentage': round(required_percentage, 1),
            'missing_required': missing_required,
            'validation_errors': validation_errors,
            'is_ready_to_submit': len(missing_required) == 0 and len(validation_errors) == 0
        }
    
    def export_structure_to_json(self, output_file: str = 'urla_structure.json'):
        """Export URLA structure to JSON file"""
        structure = {
            'form_name': 'Uniform Residential Loan Application (URLA)',
            'form_version': 'Fannie Mae Form 1003 (2019)',
            'sections': [section.to_dict() for section in self.sections]
        }
        
        with open(output_file, 'w') as f:
            json.dump(structure, f, indent=2)
        
        return output_file


if __name__ == "__main__":
    # Test the analyzer
    analyzer = URLAFormAnalyzer()
    
    print("URLA Form Structure Analysis")
    print("=" * 70)
    
    print(f"\nTotal Sections: {len(analyzer.sections)}")
    print(f"Total Fields: {len(analyzer.get_all_fields())}")
    print(f"Required Fields: {len(analyzer.get_required_fields())}")
    
    print("\nSections:")
    for section in analyzer.sections:
        print(f"  - {section.section_id}: {section.section_name} ({len(section.fields)} fields)")
    
    # Export structure
    output_file = analyzer.export_structure_to_json()
    print(f"\nStructure exported to: {output_file}")
