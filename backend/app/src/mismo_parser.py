"""
MISMO XML Parser and Handler
Parses MISMO 3.4 XML format for mortgage data exchange
"""
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json


# MISMO 3.4 Namespace
MISMO_NS = {
    '': 'http://www.mismo.org/residential/2009/schemas',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    'xlink': 'http://www.w3.org/1999/xlink',
    'ULAD': 'http://www.datamodelextension.org/Schema/ULAD',
    'DU': 'http://www.datamodelextension.org/Schema/DU'
}


@dataclass
class MISMOBorrower:
    """MISMO Borrower Information"""
    first_name: str = ""
    middle_name: str = ""
    last_name: str = ""
    suffix: str = ""
    ssn: str = ""
    date_of_birth: str = ""
    marital_status: str = ""
    email: str = ""
    home_phone: str = ""
    current_address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    citizenship_type: str = ""
    dependent_count: int = 0
    
    # Employment
    employer_name: str = ""
    employer_phone: str = ""
    employer_address: str = ""
    position: str = ""
    employment_start_date: str = ""
    self_employed: bool = False
    
    # Income
    base_income: float = 0.0
    overtime_income: float = 0.0
    bonus_income: float = 0.0
    other_income: List[Dict[str, Any]] = field(default_factory=list)
    
    # Assets
    assets: List[Dict[str, Any]] = field(default_factory=list)
    
    # Liabilities
    liabilities: List[Dict[str, Any]] = field(default_factory=list)
    
    # Declarations
    declarations: Dict[str, bool] = field(default_factory=dict)


@dataclass
class MISMOLoan:
    """MISMO Loan Information"""
    loan_identifier: str = ""
    loan_amount: float = 0.0
    loan_purpose: str = ""  # Purchase, Refinance
    loan_type: str = ""  # Conventional, FHA, VA
    interest_rate: float = 0.0
    amortization_type: str = ""
    loan_term_months: int = 360
    
    # Property
    property_address: str = ""
    property_city: str = ""
    property_state: str = ""
    property_zip: str = ""
    property_value: float = 0.0
    property_type: str = ""
    occupancy_type: str = ""
    
    # Closing
    down_payment: float = 0.0
    closing_costs: float = 0.0
    cash_from_borrower: float = 0.0


@dataclass
class MISMOData:
    """Complete MISMO Data Structure"""
    borrower: MISMOBorrower
    loan: MISMOLoan
    application_date: str = ""
    created_date: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'borrower': self.borrower.__dict__,
            'loan': self.loan.__dict__,
            'application_date': self.application_date,
            'created_date': self.created_date
        }


class MISMOParser:
    """Parser for MISMO XML files"""
    
    def __init__(self, xml_file: Optional[str] = None):
        self.xml_file = Path(xml_file) if xml_file else None
        self.tree = None
        self.root = None
        self.ns = MISMO_NS
        
    def parse(self) -> MISMOData:
        """Parse MISMO XML file"""
        self.tree = ET.parse(self.xml_file)
        self.root = self.tree.getroot()
        
        # Extract data
        borrower = self._parse_borrower()
        loan = self._parse_loan()
        
        # Get dates
        created_date = self._get_text('.//CreatedDatetime')
        app_date = self._get_text('.//ApplicationReceivedDate')
        
        return MISMOData(
            borrower=borrower,
            loan=loan,
            application_date=app_date,
            created_date=created_date
        )
    
    def parse_string(self, xml_string: str) -> MISMOData:
        """Parse MISMO XML from string"""
        self.root = ET.fromstring(xml_string)
        
        # Extract data
        borrower = self._parse_borrower()
        loan = self._parse_loan()
        
        # Get dates
        created_date = self._get_text('.//CreatedDatetime')
        app_date = self._get_text('.//ApplicationReceivedDate')
        
        return MISMOData(
            borrower=borrower,
            loan=loan,
            application_date=app_date,
            created_date=created_date
        )
    
    def _parse_borrower(self) -> MISMOBorrower:
        """Parse borrower information"""
        borrower = MISMOBorrower()
        
        # Find borrower party (without namespace since our generated XML may not use them consistently)
        borrower_party = self.root.find('.//PARTY')  # Just find first PARTY for now
        
        if borrower_party:
            # Name
            borrower.first_name = self._get_text_from_element(borrower_party, './/NAME/FirstName')
            borrower.middle_name = self._get_text_from_element(borrower_party, './/NAME/MiddleName')
            borrower.last_name = self._get_text_from_element(borrower_party, './/NAME/LastName')
            borrower.suffix = self._get_text_from_element(borrower_party, './/NAME/SuffixName')
            
            # SSN
            borrower.ssn = self._get_text_from_element(borrower_party, './/TAXPAYER_IDENTIFIER/TaxpayerIdentifierValue')
            
            # Contact
            borrower.email = self._get_text_from_element(borrower_party, './/CONTACT_POINT_EMAIL/ContactPointEmailValue')
            borrower.home_phone = self._get_text_from_element(borrower_party, './/CONTACT_POINT_TELEPHONE/ContactPointTelephoneValue')
            
            # Address
            address_elem = borrower_party.find('.//ADDRESS')
            
            if address_elem is not None:
                borrower.current_address = self._get_text_from_element(address_elem, './AddressLineText')
                borrower.city = self._get_text_from_element(address_elem, './CityName')
                borrower.state = self._get_text_from_element(address_elem, './StateCode')
                borrower.zip_code = self._get_text_from_element(address_elem, './PostalCode')
            
            # Borrower details
            borrower.date_of_birth = self._get_text_from_element(borrower_party, './/BORROWER_DETAIL/BorrowerBirthDate')
            borrower.marital_status = self._get_text_from_element(borrower_party, './/BORROWER_DETAIL/MaritalStatusType')
            borrower.citizenship_type = self._get_text_from_element(borrower_party, './/DECLARATION_DETAIL/CitizenshipResidencyType')
            
            dependent_count = self._get_text_from_element(borrower_party, './/BORROWER_DETAIL/DependentCount')
            if dependent_count:
                borrower.dependent_count = int(dependent_count)
            
            # Employment
            employer = borrower_party.find('.//EMPLOYER')
            if employer:
                borrower.employer_name = self._get_text_from_element(employer, './/LEGAL_ENTITY_DETAIL/FullName')
                borrower.employer_phone = self._get_text_from_element(employer, './/CONTACT_POINT_TELEPHONE/ContactPointTelephoneValue')
                borrower.position = self._get_text_from_element(employer, './/EMPLOYMENT/EmploymentPositionDescription')
                borrower.employment_start_date = self._get_text_from_element(employer, './/EMPLOYMENT/EmploymentStartDate')
                
                self_emp = self._get_text_from_element(employer, './/EMPLOYMENT/EmploymentBorrowerSelfEmployedIndicator')
                borrower.self_employed = self_emp.lower() == 'true' if self_emp else False
            
            # Income
            income_items = borrower_party.findall('.//CURRENT_INCOME_ITEM', self.ns)
            for item in income_items:
                income_type = self._get_text_from_element(item, './/IncomeType')
                amount_str = self._get_text_from_element(item, './/CurrentIncomeMonthlyTotalAmount')
                amount = float(amount_str) if amount_str else 0.0
                
                if income_type == 'Base':
                    borrower.base_income = amount
                elif income_type == 'Overtime':
                    borrower.overtime_income = amount
                elif income_type == 'Bonus':
                    borrower.bonus_income = amount
                else:
                    borrower.other_income.append({
                        'type': income_type,
                        'amount': amount
                    })
            
            # Assets
            assets = self.root.findall('.//ASSET', self.ns)
            for asset in assets:
                asset_data = {
                    'type': self._get_text_from_element(asset, './/AssetType'),
                    'account_id': self._get_text_from_element(asset, './/AssetAccountIdentifier'),
                    'value': float(self._get_text_from_element(asset, './/AssetCashOrMarketValueAmount') or 0),
                    'holder': self._get_text_from_element(asset, './/ASSET_HOLDER/NAME/FullName')
                }
                borrower.assets.append(asset_data)
            
            # Liabilities
            liabilities = self.root.findall('.//LIABILITY', self.ns)
            for liability in liabilities:
                liability_data = {
                    'type': self._get_text_from_element(liability, './/LiabilityType'),
                    'account_id': self._get_text_from_element(liability, './/LiabilityAccountIdentifier'),
                    'balance': float(self._get_text_from_element(liability, './/LiabilityUnpaidBalanceAmount') or 0),
                    'monthly_payment': float(self._get_text_from_element(liability, './/LiabilityMonthlyPaymentAmount') or 0),
                    'holder': self._get_text_from_element(liability, './/LIABILITY_HOLDER/NAME/FullName')
                }
                borrower.liabilities.append(liability_data)
            
            # Declarations
            decl = borrower_party.find('.//DECLARATION_DETAIL')
            if decl is not None:
                borrower.declarations = {
                    'bankruptcy': self._get_bool_from_element(decl, './BankruptcyIndicator'),
                    'outstanding_judgments': self._get_bool_from_element(decl, './OutstandingJudgmentsIndicator'),
                    'lawsuit': self._get_bool_from_element(decl, './PartyToLawsuitIndicator'),
                    'delinquent': self._get_bool_from_element(decl, './PresentlyDelinquentIndicator'),
                    'foreclosure': self._get_bool_from_element(decl, './PriorPropertyForeclosureCompletedIndicator')
                }
        
        return borrower
    
    def _parse_loan(self) -> MISMOLoan:
        """Parse loan information"""
        loan = MISMOLoan()
        
        loan_elem = self.root.find('.//LOAN')  # Find first LOAN element
        
        if loan_elem:
            # Basic loan info
            loan.loan_identifier = self._get_text_from_element(loan_elem, './/LOAN_IDENTIFIER/LoanIdentifier')
            loan.loan_amount = float(self._get_text_from_element(loan_elem, './/TERMS_OF_LOAN/BaseLoanAmount') or 0)
            loan.loan_purpose = self._get_text_from_element(loan_elem, './/TERMS_OF_LOAN/LoanPurposeType')
            loan.loan_type = self._get_text_from_element(loan_elem, './/TERMS_OF_LOAN/MortgageType')
            loan.interest_rate = float(self._get_text_from_element(loan_elem, './/TERMS_OF_LOAN/NoteRatePercent') or 0)
            loan.amortization_type = self._get_text_from_element(loan_elem, './/AMORTIZATION_RULE/AmortizationType')
            
            term_str = self._get_text_from_element(loan_elem, './/AMORTIZATION_RULE/LoanAmortizationPeriodCount')
            loan.loan_term_months = int(term_str) if term_str else 360
            
            # Closing
            loan.closing_costs = float(self._get_text_from_element(loan_elem, './/EstimatedClosingCostsAmount') or 0)
            loan.cash_from_borrower = float(self._get_text_from_element(loan_elem, './/CashFromBorrowerAtClosingAmount') or 0)
        
        # Property
        property_elem = self.root.find('.//SUBJECT_PROPERTY')
        if property_elem:
            loan.property_address = self._get_text_from_element(property_elem, './/ADDRESS/AddressLineText')
            loan.property_city = self._get_text_from_element(property_elem, './/ADDRESS/CityName')
            loan.property_state = self._get_text_from_element(property_elem, './/ADDRESS/StateCode')
            loan.property_zip = self._get_text_from_element(property_elem, './/ADDRESS/PostalCode')
            loan.property_value = float(self._get_text_from_element(property_elem, './/PropertyValuationAmount') or 0)
            loan.property_type = self._get_text_from_element(property_elem, './/PROPERTY_DETAIL/AttachmentType')
            loan.occupancy_type = self._get_text_from_element(property_elem, './/PROPERTY_DETAIL/PropertyUsageType')
            
            # Calculate down payment
            sales_price = float(self._get_text_from_element(property_elem, './/SalesContractAmount') or loan.property_value)
            if sales_price > 0 and loan.loan_amount > 0:
                loan.down_payment = sales_price - loan.loan_amount
        
        return loan
    
    def _get_text(self, xpath: str) -> str:
        """Get text content from XPath"""
        elem = self.root.find(xpath)
        return elem.text if elem is not None else ""
    
    def _get_text_from_element(self, element: ET.Element, xpath: str) -> str:
        """Get text content from element with relative XPath"""
        elem = element.find(xpath)
        return elem.text if elem is not None else ""
    
    def _get_bool_from_element(self, element: ET.Element, xpath: str) -> bool:
        """Get boolean from element xpath"""
        text = self._get_text_from_element(element, xpath)
        return text.lower() == 'true' if text else False
    
    def get_required_fields(self) -> List[str]:
        """Get list of required MISMO fields"""
        return [
            # Borrower
            'FirstName', 'LastName', 'TaxpayerIdentifierValue', 'BorrowerBirthDate',
            'CitizenshipResidencyType', 'MaritalStatusType',
            'AddressLineText', 'CityName', 'StateCode', 'PostalCode',
            # Employment
            'FullName (Employer)', 'EmploymentStartDate', 'EmploymentPositionDescription',
            # Income
            'CurrentIncomeMonthlyTotalAmount (Base)',
            # Loan
            'BaseLoanAmount', 'LoanPurposeType', 'MortgageType', 'NoteRatePercent',
            # Property
            'PropertyValuationAmount', 'PropertyUsageType',
            # Declarations
            'BankruptcyIndicator', 'OutstandingJudgmentsIndicator', 'IntentToOccupyType'
        ]


def parse_mismo_file(file_path: str) -> MISMOData:
    """Convenience function to parse MISMO XML"""
    parser = MISMOParser(file_path)
    return parser.parse()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        mismo_file = sys.argv[1]
    else:
        mismo_file = "mismo-sample.xml"
    
    print(f"Parsing MISMO file: {mismo_file}\n")
    
    parser = MISMOParser(mismo_file)
    data = parser.parse()
    
    print("=" * 70)
    print("MISMO DATA EXTRACTED")
    print("=" * 70)
    
    print("\nBORROWER:")
    print(f"  Name: {data.borrower.first_name} {data.borrower.last_name}")
    print(f"  SSN: {data.borrower.ssn}")
    print(f"  DOB: {data.borrower.date_of_birth}")
    print(f"  Address: {data.borrower.current_address}, {data.borrower.city}, {data.borrower.state}")
    
    print("\nEMPLOYMENT:")
    print(f"  Employer: {data.borrower.employer_name}")
    print(f"  Position: {data.borrower.position}")
    print(f"  Start Date: {data.borrower.employment_start_date}")
    
    print("\nINCOME:")
    print(f"  Base: ${data.borrower.base_income:,.2f}/month")
    print(f"  Overtime: ${data.borrower.overtime_income:,.2f}/month")
    print(f"  Bonus: ${data.borrower.bonus_income:,.2f}/month")
    total_income = data.borrower.base_income + data.borrower.overtime_income + data.borrower.bonus_income
    print(f"  Total: ${total_income:,.2f}/month")
    
    print(f"\nASSETS: {len(data.borrower.assets)}")
    total_assets = sum(a['value'] for a in data.borrower.assets)
    print(f"  Total Value: ${total_assets:,.2f}")
    
    print(f"\nLIABILITIES: {len(data.borrower.liabilities)}")
    total_liabilities = sum(l['balance'] for l in data.borrower.liabilities)
    print(f"  Total Balance: ${total_liabilities:,.2f}")
    
    print("\nLOAN:")
    print(f"  Amount: ${data.loan.loan_amount:,.2f}")
    print(f"  Purpose: {data.loan.loan_purpose}")
    print(f"  Type: {data.loan.loan_type}")
    print(f"  Rate: {data.loan.interest_rate}%")
    print(f"  Term: {data.loan.loan_term_months} months")
    
    print("\nPROPERTY:")
    print(f"  Address: {data.loan.property_address}")
    print(f"  City: {data.loan.property_city}, {data.loan.property_state}")
    print(f"  Value: ${data.loan.property_value:,.2f}")
    print(f"  Down Payment: ${data.loan.down_payment:,.2f}")
    
    print("\n" + "=" * 70)
    
    # Export to JSON
    with open('mismo_parsed.json', 'w') as f:
        json.dump(data.to_dict(), f, indent=2)
    
    print("\n✓ Data exported to mismo_parsed.json")
