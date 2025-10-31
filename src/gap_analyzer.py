"""
Gap Analysis Engine
Identifies missing or incomplete information in mortgage applications
"""
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class GapSeverity(Enum):
    """Severity levels for information gaps"""
    CRITICAL = "critical"  # Required field, blocks loan processing
    WARNING = "warning"   # Recommended field, may cause delays
    INFO = "info"         # Optional field, helpful but not required


@dataclass
class InformationGap:
    """Represents a missing or incomplete piece of information"""
    field_name: str
    section: str
    severity: GapSeverity
    current_value: Optional[Any]
    description: str
    recommendation: str
    mismo_path: Optional[str] = None


class GapAnalyzer:
    """Analyzes mortgage applications for missing information"""
    
    # Define required MISMO fields by section
    REQUIRED_BORROWER_FIELDS = {
        'first_name': 'Borrower first name',
        'last_name': 'Borrower last name',
        'ssn': 'Social Security Number',
        'date_of_birth': 'Date of birth',
        'citizenship_type': 'Citizenship status',
        'marital_status': 'Marital status',
    }
    
    REQUIRED_EMPLOYMENT_FIELDS = {
        'employer_name': 'Current employer name',
        'position': 'Job title/position',
        'employment_start_date': 'Employment start date',
        'base_income': 'Base monthly income',
    }
    
    REQUIRED_LOAN_FIELDS = {
        'loan_amount': 'Loan amount requested',
        'loan_purpose': 'Loan purpose (Purchase/Refinance)',
        'loan_type': 'Loan type (Conventional/FHA/VA)',
        'property_value': 'Property value/purchase price',
        'property_address': 'Property street address',
        'property_city': 'Property city',
        'property_state': 'Property state',
        'property_zip': 'Property ZIP code',
    }
    
    RECOMMENDED_FIELDS = {
        'middle_name': ('Borrower middle name', 'Helps with identification'),
        'email': ('Email address', 'Required for electronic communication'),
        'home_phone': ('Phone number', 'Required for contact'),
        'current_address': ('Current residential address', 'Required for credit check'),
        'years_at_address': ('Years at current address', 'Stability indicator'),
        'dependent_count': ('Number of dependents', 'Affects DTI calculation'),
        'overtime_income': ('Overtime income', 'Can increase qualifying income'),
        'bonus_income': ('Bonus income', 'Can increase qualifying income'),
        'interest_rate': ('Interest rate', 'Required for payment calculation'),
        'loan_term_months': ('Loan term', 'Required for payment calculation'),
        'down_payment': ('Down payment amount', 'Required for LTV calculation'),
        'occupancy_type': ('Occupancy type', 'Affects rate and requirements'),
    }
    
    OPTIONAL_FIELDS = {
        'commission_income': ('Commission income', 'Additional income source'),
        'rental_income': ('Rental income', 'Additional income source'),
        'self_employment_income': ('Self-employment income', 'If self-employed'),
        'other_income': ('Other income sources', 'Additional income'),
        'assets': ('Asset accounts', 'Required for reserves and down payment'),
        'liabilities': ('Current debts', 'Required for DTI calculation'),
        'credit_score': ('Credit score', 'Affects rate and approval'),
        'previous_address': ('Previous address', 'If less than 2 years at current'),
    }
    
    def __init__(self):
        self.gaps: List[InformationGap] = []
    
    def analyze_borrower(self, borrower: Any) -> List[InformationGap]:
        """Analyze borrower information for gaps"""
        gaps = []
        
        # Check required borrower fields
        for field, desc in self.REQUIRED_BORROWER_FIELDS.items():
            value = getattr(borrower, field, None)
            if not value or (isinstance(value, str) and not value.strip()):
                gaps.append(InformationGap(
                    field_name=field,
                    section='Borrower Information',
                    severity=GapSeverity.CRITICAL,
                    current_value=value,
                    description=f"Missing {desc}",
                    recommendation=f"Provide {desc} to proceed with application",
                    mismo_path=self._get_mismo_path('borrower', field)
                ))
        
        # Check required employment fields
        for field, desc in self.REQUIRED_EMPLOYMENT_FIELDS.items():
            value = getattr(borrower, field, None)
            if not value or (isinstance(value, str) and not value.strip()):
                gaps.append(InformationGap(
                    field_name=field,
                    section='Employment',
                    severity=GapSeverity.CRITICAL,
                    current_value=value,
                    description=f"Missing {desc}",
                    recommendation=f"Provide {desc} for income verification",
                    mismo_path=self._get_mismo_path('employment', field)
                ))
        
        # Check recommended fields
        for field, (desc, reason) in self.RECOMMENDED_FIELDS.items():
            value = getattr(borrower, field, None)
            if not value or (isinstance(value, str) and not value.strip()):
                # Skip income fields if not applicable
                if field in ['overtime_income', 'bonus_income']:
                    if getattr(borrower, 'base_income', 0) > 0:
                        continue  # Optional if base income is present
                
                gaps.append(InformationGap(
                    field_name=field,
                    section='Additional Information',
                    severity=GapSeverity.WARNING,
                    current_value=value,
                    description=f"Missing {desc}",
                    recommendation=reason,
                    mismo_path=self._get_mismo_path('borrower', field)
                ))
        
        # Check assets
        if not borrower.assets or len(borrower.assets) == 0:
            gaps.append(InformationGap(
                field_name='assets',
                section='Assets',
                severity=GapSeverity.WARNING,
                current_value=None,
                description="No asset accounts provided",
                recommendation="Provide bank statements or asset documentation for reserves",
                mismo_path="DEAL/ASSETS"
            ))
        
        # Check liabilities
        if not borrower.liabilities or len(borrower.liabilities) == 0:
            gaps.append(InformationGap(
                field_name='liabilities',
                section='Liabilities',
                severity=GapSeverity.INFO,
                current_value=None,
                description="No liabilities reported",
                recommendation="Confirm zero debts or provide credit report",
                mismo_path="DEAL/LIABILITIES"
            ))
        
        return gaps
    
    def analyze_loan(self, loan: Any) -> List[InformationGap]:
        """Analyze loan information for gaps"""
        gaps = []
        
        # Check required loan fields
        for field, desc in self.REQUIRED_LOAN_FIELDS.items():
            value = getattr(loan, field, None)
            if not value or (isinstance(value, str) and not value.strip()):
                gaps.append(InformationGap(
                    field_name=field,
                    section='Loan Details',
                    severity=GapSeverity.CRITICAL,
                    current_value=value,
                    description=f"Missing {desc}",
                    recommendation=f"Provide {desc} to determine loan eligibility",
                    mismo_path=self._get_mismo_path('loan', field)
                ))
        
        # Check loan amount vs property value
        if loan.loan_amount and loan.property_value:
            ltv = (loan.loan_amount / loan.property_value) * 100
            if ltv > 97:
                gaps.append(InformationGap(
                    field_name='ltv_ratio',
                    section='Loan Details',
                    severity=GapSeverity.WARNING,
                    current_value=f"{ltv:.2f}%",
                    description=f"High LTV ratio: {ltv:.2f}%",
                    recommendation="LTV >97% may require mortgage insurance or additional documentation",
                    mismo_path="DEAL/LOANS/LOAN/TERMS_OF_LOAN"
                ))
        
        # Check for property details
        if not loan.property_address or not loan.property_city:
            gaps.append(InformationGap(
                field_name='property_address',
                section='Property',
                severity=GapSeverity.CRITICAL,
                current_value=None,
                description="Incomplete property address",
                recommendation="Full property address required for title search and appraisal",
                mismo_path="DEAL/COLLATERALS/COLLATERAL/SUBJECT_PROPERTY/ADDRESS"
            ))
        
        return gaps
    
    def analyze_income_documentation(self, extracted_data: Dict) -> List[InformationGap]:
        """Analyze income documentation completeness"""
        gaps = []
        
        # Check for required documents
        doc_types = {
            'W2': ('W-2 forms', 'Required for wage earners (2 most recent years)'),
            'PAYSTUB': ('Recent paystubs', 'Required (most recent 30 days)'),
            'VOE': ('Verification of Employment', 'Recommended for income verification'),
        }
        
        for doc_type, (name, requirement) in doc_types.items():
            docs = extracted_data.get(doc_type, [])
            if not docs or len(docs) == 0:
                severity = GapSeverity.CRITICAL if doc_type in ['W2', 'PAYSTUB'] else GapSeverity.WARNING
                gaps.append(InformationGap(
                    field_name=doc_type.lower(),
                    section='Income Documentation',
                    severity=severity,
                    current_value=None,
                    description=f"Missing {name}",
                    recommendation=requirement,
                    mismo_path="DEAL/PARTIES/PARTY/ROLES/ROLE/BORROWER/CURRENT_INCOME"
                ))
        
        # Check W-2 year coverage
        w2_docs = extracted_data.get('W2', [])
        if w2_docs:
            years = set()
            for doc in w2_docs:
                if isinstance(doc, dict):
                    year = doc.get('tax_year')
                    if year:
                        years.add(year)
            
            if len(years) < 2:
                gaps.append(InformationGap(
                    field_name='w2_coverage',
                    section='Income Documentation',
                    severity=GapSeverity.WARNING,
                    current_value=f"{len(years)} year(s)",
                    description="Insufficient W-2 history",
                    recommendation="Provide W-2 forms for most recent 2 years",
                    mismo_path="DEAL/PARTIES/PARTY/ROLES/ROLE/BORROWER/CURRENT_INCOME"
                ))
        
        # Check for paystub currency
        paystubs = extracted_data.get('PAYSTUB', [])
        if paystubs:
            # In real implementation, would check dates
            # For now, just note if available
            pass
        
        return gaps
    
    def analyze_asset_documentation(self, extracted_data: Dict) -> List[InformationGap]:
        """Analyze asset documentation"""
        gaps = []
        
        bank_statements = extracted_data.get('BANK_STATEMENT', [])
        if not bank_statements or len(bank_statements) == 0:
            gaps.append(InformationGap(
                field_name='bank_statements',
                section='Asset Documentation',
                severity=GapSeverity.WARNING,
                current_value=None,
                description="No bank statements provided",
                recommendation="Provide most recent 2 months of bank statements for all accounts",
                mismo_path="DEAL/ASSETS"
            ))
        
        return gaps
    
    def analyze_credit_documentation(self, extracted_data: Dict) -> List[InformationGap]:
        """Analyze credit documentation"""
        gaps = []
        
        credit_reports = extracted_data.get('CREDIT_REPORT', [])
        if not credit_reports or len(credit_reports) == 0:
            gaps.append(InformationGap(
                field_name='credit_report',
                section='Credit Documentation',
                severity=GapSeverity.INFO,
                current_value=None,
                description="No credit report provided",
                recommendation="Credit report will be pulled during processing",
                mismo_path="DEAL/PARTIES/PARTY/ROLES/ROLE/BORROWER"
            ))
        
        return gaps
    
    def analyze_all(self, mismo_data: Any, extracted_data: Optional[Dict] = None) -> List[InformationGap]:
        """Perform complete gap analysis"""
        all_gaps = []
        
        # Analyze borrower
        if mismo_data.borrower:
            all_gaps.extend(self.analyze_borrower(mismo_data.borrower))
        
        # Analyze loan
        if mismo_data.loan:
            all_gaps.extend(self.analyze_loan(mismo_data.loan))
        
        # Analyze documentation if provided
        if extracted_data:
            all_gaps.extend(self.analyze_income_documentation(extracted_data))
            all_gaps.extend(self.analyze_asset_documentation(extracted_data))
            all_gaps.extend(self.analyze_credit_documentation(extracted_data))
        
        self.gaps = all_gaps
        return all_gaps
    
    def generate_report(self, gaps: Optional[List[InformationGap]] = None) -> str:
        """Generate formatted gap analysis report"""
        if gaps is None:
            gaps = self.gaps
        
        if not gaps:
            return "✓ No information gaps identified. Application appears complete."
        
        # Group by severity
        critical = [g for g in gaps if g.severity == GapSeverity.CRITICAL]
        warnings = [g for g in gaps if g.severity == GapSeverity.WARNING]
        info = [g for g in gaps if g.severity == GapSeverity.INFO]
        
        report = []
        report.append("=" * 80)
        report.append("MORTGAGE APPLICATION GAP ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Summary
        report.append("SUMMARY")
        report.append("-" * 80)
        report.append(f"Total Gaps Identified: {len(gaps)}")
        report.append(f"  • Critical (Must Resolve): {len(critical)}")
        report.append(f"  • Warnings (Recommended): {len(warnings)}")
        report.append(f"  • Informational: {len(info)}")
        report.append("")
        
        # Critical gaps
        if critical:
            report.append("🔴 CRITICAL GAPS (Must be resolved before loan processing)")
            report.append("-" * 80)
            for i, gap in enumerate(critical, 1):
                report.append(f"\n{i}. {gap.description}")
                report.append(f"   Section: {gap.section}")
                report.append(f"   Field: {gap.field_name}")
                if gap.current_value:
                    report.append(f"   Current: {gap.current_value}")
                report.append(f"   Action Required: {gap.recommendation}")
                if gap.mismo_path:
                    report.append(f"   MISMO Path: {gap.mismo_path}")
            report.append("")
        
        # Warnings
        if warnings:
            report.append("⚠️  WARNING GAPS (Recommended to resolve)")
            report.append("-" * 80)
            for i, gap in enumerate(warnings, 1):
                report.append(f"\n{i}. {gap.description}")
                report.append(f"   Section: {gap.section}")
                report.append(f"   Field: {gap.field_name}")
                if gap.current_value:
                    report.append(f"   Current: {gap.current_value}")
                report.append(f"   Recommendation: {gap.recommendation}")
            report.append("")
        
        # Info
        if info:
            report.append("ℹ️  INFORMATIONAL (Optional)")
            report.append("-" * 80)
            for i, gap in enumerate(info, 1):
                report.append(f"\n{i}. {gap.description}")
                report.append(f"   Section: {gap.section}")
                report.append(f"   Note: {gap.recommendation}")
            report.append("")
        
        # Next steps
        report.append("NEXT STEPS")
        report.append("-" * 80)
        if critical:
            report.append("1. Resolve all CRITICAL gaps immediately")
            report.append("2. Application cannot proceed until critical information is provided")
        if warnings:
            report.append("3. Address WARNING gaps to avoid processing delays")
        if info:
            report.append("4. Review INFORMATIONAL items for completeness")
        report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def get_completion_percentage(self, gaps: Optional[List[InformationGap]] = None) -> float:
        """Calculate application completion percentage"""
        if gaps is None:
            gaps = self.gaps
        
        # Count total possible fields
        total_fields = (
            len(self.REQUIRED_BORROWER_FIELDS) +
            len(self.REQUIRED_EMPLOYMENT_FIELDS) +
            len(self.REQUIRED_LOAN_FIELDS)
        )
        
        # Count missing critical fields
        missing_critical = len([g for g in gaps if g.severity == GapSeverity.CRITICAL])
        
        if total_fields == 0:
            return 100.0
        
        completion = ((total_fields - missing_critical) / total_fields) * 100
        return max(0.0, min(100.0, completion))
    
    def _get_mismo_path(self, section: str, field: str) -> str:
        """Get MISMO XML path for a field"""
        paths = {
            'borrower': {
                'first_name': 'DEAL/PARTIES/PARTY/INDIVIDUAL/NAME/FirstName',
                'last_name': 'DEAL/PARTIES/PARTY/INDIVIDUAL/NAME/LastName',
                'middle_name': 'DEAL/PARTIES/PARTY/INDIVIDUAL/NAME/MiddleName',
                'ssn': 'DEAL/PARTIES/PARTY/TAXPAYER_IDENTIFIERS/TAXPAYER_IDENTIFIER',
                'date_of_birth': 'DEAL/PARTIES/PARTY/ROLES/ROLE/BORROWER/BORROWER_DETAIL/BorrowerBirthDate',
                'marital_status': 'DEAL/PARTIES/PARTY/ROLES/ROLE/BORROWER/BORROWER_DETAIL/MaritalStatusType',
                'citizenship_type': 'DEAL/PARTIES/PARTY/ROLES/ROLE/BORROWER/DECLARATION/DECLARATION_DETAIL/CitizenshipResidencyType',
                'email': 'DEAL/PARTIES/PARTY/INDIVIDUAL/CONTACT_POINTS/CONTACT_POINT/CONTACT_POINT_EMAIL',
                'home_phone': 'DEAL/PARTIES/PARTY/INDIVIDUAL/CONTACT_POINTS/CONTACT_POINT/CONTACT_POINT_TELEPHONE',
            },
            'employment': {
                'employer_name': 'DEAL/PARTIES/PARTY/ROLES/ROLE/BORROWER/EMPLOYERS/EMPLOYER/LEGAL_ENTITY/LEGAL_ENTITY_DETAIL/FullName',
                'position': 'DEAL/PARTIES/PARTY/ROLES/ROLE/BORROWER/EMPLOYERS/EMPLOYER/EMPLOYMENT/EmploymentPositionDescription',
                'employment_start_date': 'DEAL/PARTIES/PARTY/ROLES/ROLE/BORROWER/EMPLOYERS/EMPLOYER/EMPLOYMENT/EmploymentStartDate',
                'base_income': 'DEAL/PARTIES/PARTY/ROLES/ROLE/BORROWER/CURRENT_INCOME/CURRENT_INCOME_ITEMS/CURRENT_INCOME_ITEM',
            },
            'loan': {
                'loan_amount': 'DEAL/LOANS/LOAN/TERMS_OF_LOAN/BaseLoanAmount',
                'loan_purpose': 'DEAL/LOANS/LOAN/TERMS_OF_LOAN/LoanPurposeType',
                'loan_type': 'DEAL/LOANS/LOAN/TERMS_OF_LOAN/MortgageType',
                'interest_rate': 'DEAL/LOANS/LOAN/TERMS_OF_LOAN/NoteRatePercent',
                'property_value': 'DEAL/COLLATERALS/COLLATERAL/SUBJECT_PROPERTY/PROPERTY_VALUATIONS/PROPERTY_VALUATION',
                'property_address': 'DEAL/COLLATERALS/COLLATERAL/SUBJECT_PROPERTY/ADDRESS',
                'property_city': 'DEAL/COLLATERALS/COLLATERAL/SUBJECT_PROPERTY/ADDRESS/CityName',
                'property_state': 'DEAL/COLLATERALS/COLLATERAL/SUBJECT_PROPERTY/ADDRESS/StateCode',
                'property_zip': 'DEAL/COLLATERALS/COLLATERAL/SUBJECT_PROPERTY/ADDRESS/PostalCode',
            }
        }
        
        return paths.get(section, {}).get(field, f"{section}/{field}")


if __name__ == "__main__":
    # Test gap analysis
    from mismo_parser import MISMOBorrower, MISMOLoan, MISMOData
    from datetime import datetime
    
    # Create incomplete borrower
    borrower = MISMOBorrower(
        first_name="Elmo",
        last_name="James",
        # Missing SSN, DOB
        employer_name="Tech Company",
        base_income=10000.00
        # Missing position, employment_start_date
    )
    
    # Create incomplete loan
    loan = MISMOLoan(
        loan_amount=300000.00,
        # Missing purpose, type, property details
    )
    
    data = MISMOData(
        borrower=borrower,
        loan=loan,
        application_date=datetime.now().strftime('%Y-%m-%d')
    )
    
    # Analyze gaps
    analyzer = GapAnalyzer()
    gaps = analyzer.analyze_all(data)
    
    # Generate report
    report = analyzer.generate_report(gaps)
    print(report)
    
    print(f"\nCompletion: {analyzer.get_completion_percentage(gaps):.1f}%")
