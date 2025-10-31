"""
MISMO XML Generator
Creates MISMO 3.4 XML files from extracted mortgage data
"""
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from mismo_parser import MISMOData, MISMOBorrower, MISMOLoan, MISMO_NS


class MISMOGenerator:
    """Generates MISMO 3.4 XML files"""
    
    def __init__(self, template_file: Optional[str] = None):
        self.template_file = template_file
        self.ns = MISMO_NS
    
    def generate_from_extracted_data(self, extracted_data: Dict[str, Any],
                                     income_analysis: Optional[Any] = None) -> str:
        """
        Generate MISMO XML from extracted document data
        
        Args:
            extracted_data: Dictionary with keys like 'W2', 'PAYSTUB', 'VOE', etc.
            income_analysis: IncomeAnalysis object from underwriting engine
        
        Returns:
            MISMO XML as string
        """
        
        # Build MISMO data structure from extracted data
        borrower = self._build_borrower_from_data(extracted_data, income_analysis)
        loan = self._build_loan_from_data(extracted_data)
        
        mismo_data = MISMOData(
            borrower=borrower,
            loan=loan,
            application_date=datetime.now().strftime('%Y-%m-%d'),
            created_date=datetime.now().isoformat()
        )
        
        return self.generate(mismo_data)
    
    def generate(self, mismo_data: MISMOData) -> str:
        """Generate MISMO XML from MISMOData object"""
        
        # Create root MESSAGE element
        root = ET.Element('MESSAGE')
        root.set('xmlns', self.ns[''])
        root.set('xmlns:xsi', self.ns['xsi'])
        root.set('xmlns:xlink', self.ns['xlink'])
        root.set('xmlns:ULAD', self.ns['ULAD'])
        root.set('xmlns:DU', self.ns['DU'])
        root.set('MISMOReferenceModelIdentifier', '3.4.032420160128')
        
        # Add ABOUT_VERSIONS
        about_versions = ET.SubElement(root, 'ABOUT_VERSIONS')
        about_version = ET.SubElement(about_versions, 'ABOUT_VERSION')
        created_dt = ET.SubElement(about_version, 'CreatedDatetime')
        created_dt.text = mismo_data.created_date or datetime.now().isoformat()
        
        # Add DEAL_SETS
        deal_sets = ET.SubElement(root, 'DEAL_SETS')
        deal_set = ET.SubElement(deal_sets, 'DEAL_SET')
        deals = ET.SubElement(deal_set, 'DEALS')
        deal = ET.SubElement(deals, 'DEAL')
        
        # Add sections
        self._add_assets(deal, mismo_data.borrower)
        self._add_collateral(deal, mismo_data.loan)
        self._add_liabilities(deal, mismo_data.borrower)
        self._add_loans(deal, mismo_data.loan)
        self._add_parties(deal, mismo_data.borrower)
        
        # Convert to string with pretty printing
        xml_str = ET.tostring(root, encoding='utf-8')
        dom = minidom.parseString(xml_str)
        return dom.toprettyxml(indent='  ', encoding='UTF-8').decode('utf-8')
    
    def _build_borrower_from_data(self, extracted_data: Dict, income_analysis) -> MISMOBorrower:
        """Build MISMOBorrower from extracted document data"""
        borrower = MISMOBorrower()
        
        # Get W-2 data (most recent)
        w2_list = extracted_data.get('W2', [])
        if w2_list:
            w2 = w2_list[0] if isinstance(w2_list, list) else w2_list
            borrower.ssn = w2.get('employee_ssn', '')
            borrower.employer_name = w2.get('employer_name', '')
            
            # Try to extract name from employee_name
            emp_name = w2.get('employee_name', '')
            if emp_name:
                parts = emp_name.split()
                if len(parts) >= 2:
                    borrower.first_name = parts[0]
                    borrower.last_name = parts[-1]
                    if len(parts) > 2:
                        borrower.middle_name = parts[1]
        
        # Get paystub data
        paystub_list = extracted_data.get('PAYSTUB', [])
        if paystub_list:
            paystub = paystub_list[0] if isinstance(paystub_list, list) else paystub_list
            if not borrower.employer_name:
                borrower.employer_name = paystub.get('employer_name', '')
            if not borrower.first_name:
                emp_name = paystub.get('employee_name', '')
                if emp_name:
                    parts = emp_name.split()
                    if len(parts) >= 2:
                        borrower.first_name = parts[0]
                        borrower.last_name = parts[-1]
        
        # Get VOE data
        voe_list = extracted_data.get('VOE', [])
        if voe_list:
            voe = voe_list[0] if isinstance(voe_list, list) else voe_list
            if not borrower.employer_name:
                borrower.employer_name = voe.get('employer_name', '')
            borrower.position = voe.get('job_title', '')
            borrower.employment_start_date = voe.get('employment_start_date', '')
            if not borrower.first_name:
                emp_name = voe.get('employee_name', '')
                if emp_name:
                    parts = emp_name.split()
                    if len(parts) >= 2:
                        borrower.first_name = parts[0]
                        borrower.last_name = parts[-1]
        
        # Get income from analysis
        if income_analysis:
            for income_source in income_analysis.income_sources:
                if income_source.type == 'W2_BASE':
                    borrower.base_income = income_source.amount
                elif income_source.type == 'BONUS_OVERTIME':
                    # Split evenly for demo (in real scenario, would separate)
                    borrower.overtime_income = income_source.amount / 2
                    borrower.bonus_income = income_source.amount / 2
        
        # Default values
        if not borrower.citizenship_type:
            borrower.citizenship_type = 'USCitizen'
        if not borrower.marital_status:
            borrower.marital_status = 'Unmarried'
        
        return borrower
    
    def _build_loan_from_data(self, extracted_data: Dict) -> MISMOLoan:
        """Build MISMOLoan from extracted data"""
        loan = MISMOLoan()
        
        # Set defaults for purchase loan
        loan.loan_purpose = 'Purchase'
        loan.loan_type = 'Conventional'
        loan.amortization_type = 'Fixed'
        loan.loan_term_months = 360
        loan.interest_rate = 4.0  # Default
        
        # These would typically come from loan application data
        # For now, use placeholder values
        loan.loan_identifier = f"LOAN-{datetime.now().strftime('%Y%m%d')}"
        
        return loan
    
    def _add_assets(self, deal: ET.Element, borrower: MISMOBorrower):
        """Add ASSETS section"""
        if not borrower.assets:
            return
        
        assets_elem = ET.SubElement(deal, 'ASSETS')
        
        for i, asset in enumerate(borrower.assets, 1):
            asset_elem = ET.SubElement(assets_elem, 'ASSET', {
                'SequenceNumber': str(i),
                '{http://www.w3.org/1999/xlink}label': f'ASSET_{i}'
            })
            
            asset_detail = ET.SubElement(asset_elem, 'ASSET_DETAIL')
            
            if asset.get('account_id'):
                account = ET.SubElement(asset_detail, 'AssetAccountIdentifier')
                account.text = str(asset['account_id'])
            
            value = ET.SubElement(asset_detail, 'AssetCashOrMarketValueAmount')
            value.text = f"{asset.get('value', 0):.2f}"
            
            asset_type = ET.SubElement(asset_detail, 'AssetType')
            asset_type.text = asset.get('type', 'CheckingAccount')
            
            if asset.get('holder'):
                holder = ET.SubElement(asset_elem, 'ASSET_HOLDER')
                name = ET.SubElement(holder, 'NAME')
                full_name = ET.SubElement(name, 'FullName')
                full_name.text = asset['holder']
    
    def _add_collateral(self, deal: ET.Element, loan: MISMOLoan):
        """Add COLLATERAL section (property)"""
        collaterals = ET.SubElement(deal, 'COLLATERALS')
        collateral = ET.SubElement(collaterals, 'COLLATERAL')
        subject_property = ET.SubElement(collateral, 'SUBJECT_PROPERTY')
        
        # Address
        if loan.property_address:
            address = ET.SubElement(subject_property, 'ADDRESS')
            addr_line = ET.SubElement(address, 'AddressLineText')
            addr_line.text = loan.property_address
            city = ET.SubElement(address, 'CityName')
            city.text = loan.property_city
            state = ET.SubElement(address, 'StateCode')
            state.text = loan.property_state
            zip_code = ET.SubElement(address, 'PostalCode')
            zip_code.text = loan.property_zip
        
        # Property detail
        prop_detail = ET.SubElement(subject_property, 'PROPERTY_DETAIL')
        usage = ET.SubElement(prop_detail, 'PropertyUsageType')
        usage.text = loan.occupancy_type or 'PrimaryResidence'
        
        # Valuation
        if loan.property_value > 0:
            valuations = ET.SubElement(subject_property, 'PROPERTY_VALUATIONS')
            valuation = ET.SubElement(valuations, 'PROPERTY_VALUATION')
            val_detail = ET.SubElement(valuation, 'PROPERTY_VALUATION_DETAIL')
            val_amount = ET.SubElement(val_detail, 'PropertyValuationAmount')
            val_amount.text = f"{loan.property_value:.2f}"
    
    def _add_liabilities(self, deal: ET.Element, borrower: MISMOBorrower):
        """Add LIABILITIES section"""
        if not borrower.liabilities:
            return
        
        liabilities_elem = ET.SubElement(deal, 'LIABILITIES')
        
        for i, liability in enumerate(borrower.liabilities, 1):
            liab_elem = ET.SubElement(liabilities_elem, 'LIABILITY', {
                'SequenceNumber': str(i),
                '{http://www.w3.org/1999/xlink}label': f'LIABILITY_{i}'
            })
            
            liab_detail = ET.SubElement(liab_elem, 'LIABILITY_DETAIL')
            
            if liability.get('account_id'):
                account = ET.SubElement(liab_detail, 'LiabilityAccountIdentifier')
                account.text = str(liability['account_id'])
            
            balance = ET.SubElement(liab_detail, 'LiabilityUnpaidBalanceAmount')
            balance.text = f"{liability.get('balance', 0):.2f}"
            
            payment = ET.SubElement(liab_detail, 'LiabilityMonthlyPaymentAmount')
            payment.text = f"{liability.get('monthly_payment', 0):.2f}"
            
            liab_type = ET.SubElement(liab_detail, 'LiabilityType')
            liab_type.text = liability.get('type', 'Revolving')
            
            if liability.get('holder'):
                holder = ET.SubElement(liab_elem, 'LIABILITY_HOLDER')
                name = ET.SubElement(holder, 'NAME')
                full_name = ET.SubElement(name, 'FullName')
                full_name.text = liability['holder']
    
    def _add_loans(self, deal: ET.Element, loan: MISMOLoan):
        """Add LOANS section"""
        loans_elem = ET.SubElement(deal, 'LOANS')
        loan_elem = ET.SubElement(loans_elem, 'LOAN', {
            'LoanRoleType': 'SubjectLoan',
            '{http://www.w3.org/1999/xlink}label': 'LOAN_1'
        })
        
        # Amortization
        amort = ET.SubElement(loan_elem, 'AMORTIZATION')
        amort_rule = ET.SubElement(amort, 'AMORTIZATION_RULE')
        amort_type = ET.SubElement(amort_rule, 'AmortizationType')
        amort_type.text = loan.amortization_type
        period_count = ET.SubElement(amort_rule, 'LoanAmortizationPeriodCount')
        period_count.text = str(loan.loan_term_months)
        period_type = ET.SubElement(amort_rule, 'LoanAmortizationPeriodType')
        period_type.text = 'Month'
        
        # Loan detail
        loan_detail = ET.SubElement(loan_elem, 'LOAN_DETAIL')
        app_date = ET.SubElement(loan_detail, 'ApplicationReceivedDate')
        app_date.text = datetime.now().strftime('%Y-%m-%d')
        
        # Loan identifier
        loan_ids = ET.SubElement(loan_elem, 'LOAN_IDENTIFIERS')
        loan_id = ET.SubElement(loan_ids, 'LOAN_IDENTIFIER')
        id_val = ET.SubElement(loan_id, 'LoanIdentifier')
        id_val.text = loan.loan_identifier
        id_type = ET.SubElement(loan_id, 'LoanIdentifierType')
        id_type.text = 'LenderLoan'
        
        # Terms of loan
        terms = ET.SubElement(loan_elem, 'TERMS_OF_LOAN')
        base_amount = ET.SubElement(terms, 'BaseLoanAmount')
        base_amount.text = f"{loan.loan_amount:.2f}"
        purpose = ET.SubElement(terms, 'LoanPurposeType')
        purpose.text = loan.loan_purpose
        mort_type = ET.SubElement(terms, 'MortgageType')
        mort_type.text = loan.loan_type
        rate = ET.SubElement(terms, 'NoteRatePercent')
        rate.text = f"{loan.interest_rate:.3f}"
    
    def _add_parties(self, deal: ET.Element, borrower: MISMOBorrower):
        """Add PARTIES section"""
        parties_elem = ET.SubElement(deal, 'PARTIES')
        party = ET.SubElement(parties_elem, 'PARTY')
        individual = ET.SubElement(party, 'INDIVIDUAL')
        
        # Name
        name = ET.SubElement(individual, 'NAME')
        if borrower.first_name:
            first = ET.SubElement(name, 'FirstName')
            first.text = borrower.first_name
        if borrower.last_name:
            last = ET.SubElement(name, 'LastName')
            last.text = borrower.last_name
        if borrower.middle_name:
            middle = ET.SubElement(name, 'MiddleName')
            middle.text = borrower.middle_name
        
        # Contact points
        if borrower.email or borrower.home_phone:
            contact_points = ET.SubElement(individual, 'CONTACT_POINTS')
            
            if borrower.email:
                cp = ET.SubElement(contact_points, 'CONTACT_POINT')
                cp_email = ET.SubElement(cp, 'CONTACT_POINT_EMAIL')
                email = ET.SubElement(cp_email, 'ContactPointEmailValue')
                email.text = borrower.email
            
            if borrower.home_phone:
                cp = ET.SubElement(contact_points, 'CONTACT_POINT')
                cp_phone = ET.SubElement(cp, 'CONTACT_POINT_TELEPHONE')
                phone = ET.SubElement(cp_phone, 'ContactPointTelephoneValue')
                phone.text = borrower.home_phone
        
        # Roles
        roles = ET.SubElement(party, 'ROLES')
        role = ET.SubElement(roles, 'ROLE', {
            'SequenceNumber': '1',
            '{http://www.w3.org/1999/xlink}label': 'BORROWER_1'
        })
        
        borrower_elem = ET.SubElement(role, 'BORROWER')
        
        # Borrower detail
        borr_detail = ET.SubElement(borrower_elem, 'BORROWER_DETAIL')
        if borrower.date_of_birth:
            dob = ET.SubElement(borr_detail, 'BorrowerBirthDate')
            dob.text = borrower.date_of_birth
        if borrower.marital_status:
            marital = ET.SubElement(borr_detail, 'MaritalStatusType')
            marital.text = borrower.marital_status
        if borrower.dependent_count is not None:
            dep = ET.SubElement(borr_detail, 'DependentCount')
            dep.text = str(borrower.dependent_count)
        
        # Current income
        if borrower.base_income > 0 or borrower.overtime_income > 0 or borrower.bonus_income > 0:
            curr_income = ET.SubElement(borrower_elem, 'CURRENT_INCOME')
            curr_items = ET.SubElement(curr_income, 'CURRENT_INCOME_ITEMS')
            
            seq = 1
            if borrower.base_income > 0:
                self._add_income_item(curr_items, seq, 'Base', borrower.base_income)
                seq += 1
            if borrower.overtime_income > 0:
                self._add_income_item(curr_items, seq, 'Overtime', borrower.overtime_income)
                seq += 1
            if borrower.bonus_income > 0:
                self._add_income_item(curr_items, seq, 'Bonus', borrower.bonus_income)
                seq += 1
        
        # Declaration
        if borrower.declarations:
            decl = ET.SubElement(borrower_elem, 'DECLARATION')
            decl_detail = ET.SubElement(decl, 'DECLARATION_DETAIL')
            
            if 'bankruptcy' in borrower.declarations:
                bankruptcy = ET.SubElement(decl_detail, 'BankruptcyIndicator')
                bankruptcy.text = 'true' if borrower.declarations['bankruptcy'] else 'false'
            if borrower.citizenship_type:
                citizenship = ET.SubElement(decl_detail, 'CitizenshipResidencyType')
                citizenship.text = borrower.citizenship_type
        
        # Employers
        if borrower.employer_name:
            employers = ET.SubElement(borrower_elem, 'EMPLOYERS')
            employer = ET.SubElement(employers, 'EMPLOYER', {'SequenceNumber': '1'})
            legal_entity = ET.SubElement(employer, 'LEGAL_ENTITY')
            le_detail = ET.SubElement(legal_entity, 'LEGAL_ENTITY_DETAIL')
            full_name = ET.SubElement(le_detail, 'FullName')
            full_name.text = borrower.employer_name
            
            employment = ET.SubElement(employer, 'EMPLOYMENT')
            if borrower.self_employed:
                self_emp = ET.SubElement(employment, 'EmploymentBorrowerSelfEmployedIndicator')
                self_emp.text = 'true'
            if borrower.position:
                position = ET.SubElement(employment, 'EmploymentPositionDescription')
                position.text = borrower.position
            if borrower.employment_start_date:
                start = ET.SubElement(employment, 'EmploymentStartDate')
                start.text = borrower.employment_start_date
        
        # Role detail
        role_detail = ET.SubElement(role, 'ROLE_DETAIL')
        role_type = ET.SubElement(role_detail, 'PartyRoleType')
        role_type.text = 'Borrower'
        
        # Taxpayer identifier
        if borrower.ssn:
            taxpayer_ids = ET.SubElement(party, 'TAXPAYER_IDENTIFIERS')
            taxpayer_id = ET.SubElement(taxpayer_ids, 'TAXPAYER_IDENTIFIER')
            id_type = ET.SubElement(taxpayer_id, 'TaxpayerIdentifierType')
            id_type.text = 'SocialSecurityNumber'
            id_value = ET.SubElement(taxpayer_id, 'TaxpayerIdentifierValue')
            # Remove dashes from SSN
            id_value.text = borrower.ssn.replace('-', '')
    
    def _add_income_item(self, parent: ET.Element, seq: int, income_type: str, amount: float):
        """Add income item"""
        item = ET.SubElement(parent, 'CURRENT_INCOME_ITEM', {
            'SequenceNumber': str(seq),
            '{http://www.w3.org/1999/xlink}label': f'CURRENT_INCOME_ITEM_{seq}'
        })
        detail = ET.SubElement(item, 'CURRENT_INCOME_ITEM_DETAIL')
        amt = ET.SubElement(detail, 'CurrentIncomeMonthlyTotalAmount')
        amt.text = f"{amount:.2f}"
        emp_ind = ET.SubElement(detail, 'EmploymentIncomeIndicator')
        emp_ind.text = 'true'
        inc_type = ET.SubElement(detail, 'IncomeType')
        inc_type.text = income_type
    
    def save_to_file(self, xml_content: str, output_file: str):
        """Save MISMO XML to file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)


if __name__ == "__main__":
    # Test generation
    from mismo_parser import MISMOBorrower, MISMOLoan, MISMOData
    
    # Create sample data
    borrower = MISMOBorrower(
        first_name="Elmo",
        last_name="James",
        ssn="123-45-6789",
        date_of_birth="1980-01-15",
        marital_status="Unmarried",
        employer_name="Tech Company",
        position="Software Engineer",
        employment_start_date="2020-01-01",
        base_income=10000.00,
        bonus_income=1000.00
    )
    
    loan = MISMOLoan(
        loan_identifier="LOAN-TEST-001",
        loan_amount=300000.00,
        loan_purpose="Purchase",
        loan_type="Conventional",
        interest_rate=4.25,
        property_value=350000.00
    )
    
    data = MISMOData(
        borrower=borrower,
        loan=loan,
        application_date="2025-10-30",
        created_date=datetime.now().isoformat()
    )
    
    # Generate MISMO XML
    generator = MISMOGenerator()
    xml = generator.generate(data)
    
    # Save to file
    generator.save_to_file(xml, 'generated_mismo.xml')
    
    print("Generated MISMO XML file: generated_mismo.xml")
    print("\nFirst 1000 characters:")
    print(xml[:1000])
