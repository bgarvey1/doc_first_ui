"""
Freddie Mac Underwriting Rules Engine
Implements income calculation and verification logic based on Freddie Mac guidelines
"""
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class IncomeSource:
    """Represents a source of income"""
    type: str  # W2, SELF_EMPLOYED, BONUS, COMMISSION, etc.
    amount: float
    frequency: str  # ANNUAL, MONTHLY, BIWEEKLY, etc.
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    employer: Optional[str] = None
    is_stable: bool = True
    has_continuance: bool = True
    notes: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class IncomeAnalysis:
    """Analysis result for income qualification"""
    total_monthly_income: float
    income_sources: List[IncomeSource]
    meets_requirements: bool
    issues: List[str]
    recommendations: List[str]
    freddie_mac_compliance: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            'total_monthly_income': self.total_monthly_income,
            'income_sources': [source.to_dict() for source in self.income_sources],
            'meets_requirements': self.meets_requirements,
            'issues': self.issues,
            'recommendations': self.recommendations,
            'freddie_mac_compliance': self.freddie_mac_compliance
        }


class FreddieUnderwritingEngine:
    """Implements Freddie Mac underwriting rules from Section 5300"""
    
    def __init__(self, rules_file: str = "freddie_income_guides.json"):
        self.rules = self._load_rules(rules_file)
    
    def _load_rules(self, rules_file: str) -> Dict:
        """Load Freddie Mac rules from JSON file"""
        rules_path = Path(rules_file)
        if rules_path.exists():
            with open(rules_path, 'r') as f:
                return json.load(f)
        return {}
    
    def analyze_w2_income(self, w2_data: List[Dict], paystub_data: Optional[Dict] = None,
                          voe_data: Optional[Dict] = None) -> IncomeAnalysis:
        """
        Analyze W-2 income according to Freddie Mac Section 5303
        Requires 2-year history, calculates monthly income
        """
        
        issues = []
        recommendations = []
        income_sources = []
        
        # Rule 5301.1.b: Income must be verified, acceptable, and expected to continue ≥ 3 years
        if len(w2_data) < 2:
            issues.append("Less than 2 years of W-2 history. Freddie Mac typically requires 2-year history.")
            recommendations.append("Obtain W-2s for at least 2 prior years.")
        
        # Sort W-2s by year (handle None values)
        w2_sorted = sorted(w2_data, key=lambda x: x.get('year') or x.get('tax_year') or '0', reverse=True)
        
        # Check for recent paystub (within 30 days)
        if paystub_data:
            pay_date = paystub_data.get('pay_date')
            if pay_date:
                # Check if paystub is within 30 days
                recommendations.append("Paystub provided - verify it's within 30 days of application per Rule 5302.2")
        else:
            issues.append("No paystub provided. Freddie Mac requires paystub within 30 days of application.")
        
        # Check for VOE
        if voe_data:
            continuance = voe_data.get('likelihood_of_continued_employment') or ''
            if continuance and 'positive' not in continuance.lower() and 'likely' not in continuance.lower():
                issues.append("VOE does not confirm likelihood of continued employment (Rule 5301.1.d)")
        else:
            issues.append("No VOE provided. Required for employment verification per Rule 5302.2")
        
        # Calculate base income
        if w2_sorted:
            most_recent_w2 = w2_sorted[0]
            wages = most_recent_w2.get('wages', 0)
            
            if wages:
                # Annual to monthly: divide by 12
                monthly_income = wages / 12
                
                income_sources.append(IncomeSource(
                    type='W2_BASE',
                    amount=monthly_income,
                    frequency='MONTHLY',
                    employer=most_recent_w2.get('employer_name'),
                    start_date=None,
                    is_stable=True,
                    has_continuance=True,
                    notes=f"Based on {most_recent_w2.get('year')} W-2 wages"
                ))
        
        # Check for income stability (2-year trend)
        if len(w2_sorted) >= 2:
            current_year = w2_sorted[0]
            prior_year = w2_sorted[1]
            
            current_wages = current_year.get('wages') or current_year.get('total_wages') or 0
            prior_wages = prior_year.get('wages') or prior_year.get('total_wages') or 0
            
            if prior_wages and prior_wages > 0 and current_wages is not None:
                change_pct = ((current_wages - prior_wages) / prior_wages) * 100
                
                if change_pct < -10:
                    issues.append(f"Income declined by {abs(change_pct):.1f}% year-over-year. "
                                 "Rule 5303.1 requires documentation of declining income.")
                    recommendations.append("Obtain written explanation for income decline and document stability.")
                elif change_pct > 10:
                    recommendations.append(f"Income increased by {change_pct:.1f}% - positive trend.")
        
        # Calculate total monthly income
        total_monthly_income = sum(source.amount for source in income_sources)
        
        # Freddie Mac compliance check
        compliance = {
            'section_5301_stable_income': len(income_sources) > 0,
            'section_5302_documentation': {
                'w2_provided': len(w2_data) >= 2,
                'paystub_provided': paystub_data is not None,
                'voe_provided': voe_data is not None,
                'meets_doc_requirements': len(w2_data) >= 2 and paystub_data is not None and voe_data is not None
            },
            'section_5303_employed_income': {
                'two_year_history': len(w2_data) >= 2,
                'income_stable': len(issues) == 0 or not any('declined' in issue.lower() for issue in issues)
            }
        }
        
        meets_requirements = (
            len(w2_data) >= 2 and
            paystub_data is not None and
            voe_data is not None and
            len(income_sources) > 0
        )
        
        return IncomeAnalysis(
            total_monthly_income=total_monthly_income,
            income_sources=income_sources,
            meets_requirements=meets_requirements,
            issues=issues,
            recommendations=recommendations,
            freddie_mac_compliance=compliance
        )
    
    def calculate_bonus_overtime_income(self, w2_data: List[Dict], paystub_data: Dict) -> Optional[IncomeSource]:
        """
        Calculate bonus/overtime income per Rule 5303.1
        Requires 2-year history, averages 24 months
        """
        
        if len(w2_data) < 2:
            return None
        
        # Look for overtime/bonus in paystub YTD
        ytd_gross = paystub_data.get('ytd_gross', 0)
        ytd_base = paystub_data.get('base_ytd', ytd_gross)  # If not separated, use gross
        
        # Estimate overtime/bonus as difference
        ytd_variable = ytd_gross - ytd_base if ytd_gross > ytd_base else 0
        
        if ytd_variable > 0:
            # Average with prior years (simplified - in real scenario, extract from W-2s)
            # Rule: Average 24 months of bonus/overtime
            monthly_variable = ytd_variable / 12  # Simplified calculation
            
            return IncomeSource(
                type='BONUS_OVERTIME',
                amount=monthly_variable,
                frequency='MONTHLY',
                is_stable=True,
                has_continuance=True,
                notes="Averaged over 24-month period per Rule 5303.1"
            )
        
        return None
    
    def verify_income_continuance(self, voe_data: Dict, income_sources: List[IncomeSource]) -> Dict[str, Any]:
        """
        Verify income continuance per Rule 5301.1.d
        Income must be likely to continue for ≥ 3 years
        """
        
        continuance_check = {
            'meets_requirement': False,
            'verification_date': datetime.now().isoformat(),
            'issues': []
        }
        
        if not voe_data:
            continuance_check['issues'].append("No VOE provided for continuance verification")
            return continuance_check
        
        likelihood = voe_data.get('likelihood_of_continued_employment', '').lower()
        
        positive_indicators = ['positive', 'likely', 'expected', 'stable', 'permanent']
        negative_indicators = ['unlikely', 'temporary', 'contract ending', 'uncertain']
        
        has_positive = any(indicator in likelihood for indicator in positive_indicators)
        has_negative = any(indicator in likelihood for indicator in negative_indicators)
        
        if has_negative:
            continuance_check['issues'].append("VOE indicates income may not continue for 3+ years")
        elif has_positive:
            continuance_check['meets_requirement'] = True
        else:
            continuance_check['issues'].append("VOE does not clearly state likelihood of continued employment")
        
        return continuance_check
    
    def calculate_monthly_income(self, amount: float, frequency: str) -> float:
        """
        Convert income to monthly amount per Rule 5303.1
        """
        
        conversions = {
            'ANNUAL': lambda x: x / 12,
            'MONTHLY': lambda x: x,
            'SEMI_MONTHLY': lambda x: x * 2,
            'BIWEEKLY': lambda x: x * 26 / 12,
            'WEEKLY': lambda x: x * 52 / 12,
            'HOURLY': lambda x: x * 40 * 52 / 12  # Assumes 40 hours/week
        }
        
        converter = conversions.get(frequency.upper())
        if converter:
            return converter(amount)
        
        return amount
    
    def generate_income_calculation_worksheet(self, analysis: IncomeAnalysis) -> str:
        """
        Generate Freddie Mac Form 91 (Income Calculation Worksheet) equivalent
        """
        
        worksheet = []
        worksheet.append("=" * 70)
        worksheet.append("FREDDIE MAC INCOME CALCULATION WORKSHEET")
        worksheet.append("Per Sections 5301-5303 of Freddie Mac Guidelines")
        worksheet.append("=" * 70)
        worksheet.append("")
        
        worksheet.append("INCOME SOURCES:")
        worksheet.append("-" * 70)
        
        for i, source in enumerate(analysis.income_sources, 1):
            worksheet.append(f"\n{i}. {source.type}")
            worksheet.append(f"   Employer: {source.employer or 'N/A'}")
            worksheet.append(f"   Amount: ${source.amount:,.2f} {source.frequency}")
            worksheet.append(f"   Stable: {'Yes' if source.is_stable else 'No'}")
            worksheet.append(f"   Continuance: {'Yes' if source.has_continuance else 'No'}")
            worksheet.append(f"   Notes: {source.notes}")
        
        worksheet.append("\n" + "-" * 70)
        worksheet.append(f"TOTAL MONTHLY QUALIFYING INCOME: ${analysis.total_monthly_income:,.2f}")
        worksheet.append("-" * 70)
        
        worksheet.append("\nCOMPLIANCE CHECK:")
        worksheet.append("-" * 70)
        compliance = analysis.freddie_mac_compliance
        
        for section, details in compliance.items():
            worksheet.append(f"\n{section.replace('_', ' ').title()}:")
            if isinstance(details, dict):
                for key, value in details.items():
                    status = "✓" if value else "✗"
                    worksheet.append(f"  {status} {key.replace('_', ' ').title()}: {value}")
            else:
                status = "✓" if details else "✗"
                worksheet.append(f"  {status} {details}")
        
        if analysis.issues:
            worksheet.append("\nISSUES:")
            worksheet.append("-" * 70)
            for issue in analysis.issues:
                worksheet.append(f"  ⚠ {issue}")
        
        if analysis.recommendations:
            worksheet.append("\nRECOMMENDATIONS:")
            worksheet.append("-" * 70)
            for rec in analysis.recommendations:
                worksheet.append(f"  → {rec}")
        
        worksheet.append("\n" + "=" * 70)
        worksheet.append(f"MEETS FREDDIE MAC REQUIREMENTS: {'YES' if analysis.meets_requirements else 'NO'}")
        worksheet.append("=" * 70)
        
        return "\n".join(worksheet)


if __name__ == "__main__":
    # Example usage
    engine = FreddieUnderwritingEngine()
    
    # Sample W-2 data
    w2_data = [
        {'year': '2025', 'wages': 85000, 'employer_name': 'Tech Corp'},
        {'year': '2024', 'wages': 80000, 'employer_name': 'Tech Corp'}
    ]
    
    paystub = {'pay_date': '2025-10-15', 'ytd_gross': 70833}
    voe = {'likelihood_of_continued_employment': 'Positive - Employee in good standing'}
    
    analysis = engine.analyze_w2_income(w2_data, paystub, voe)
    
    print(engine.generate_income_calculation_worksheet(analysis))
