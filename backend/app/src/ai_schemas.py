"""
Pydantic schemas for AI-first document processing pipeline.
Defines strict JSON schemas for semantic extraction and 1003 aggregation.
"""

from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from datetime import date



class Evidence(BaseModel):
    """Evidence citation with page number and text snippet"""
    page: int = Field(..., description="Page number where evidence was found (1-indexed)")
    text: str = Field(..., description="Relevant text snippet from the document")
    location: Optional[str] = Field(None, description="Location on page (e.g., 'Box 1', 'Line 3')")


class FieldValue(BaseModel):
    """A field value with evidence and confidence"""
    value: Optional[str] = Field(None, description="Extracted value, or 'unknown' if not found")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    evidence: List[Evidence] = Field(default_factory=list, description="Evidence citations")
    notes: Optional[str] = Field(None, description="Additional notes or rationale")



class DocumentType(BaseModel):
    """Identified document type with confidence"""
    doc_type: Literal["w2", "paystub", "voe", "bank_statement", "tax_return", "credit_report", "unknown"] = Field(
        ..., description="Identified document type"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in classification")
    year: Optional[int] = Field(None, description="Tax year or document year if applicable")



class W2Semantic(BaseModel):
    """Semantic JSON schema for W-2 forms"""
    doc_type: Literal["w2"] = "w2"
    doc_id: str = Field(..., description="Unique document identifier")
    
    employee_name: FieldValue
    employee_ssn: FieldValue
    employee_address: FieldValue
    
    employer_name: FieldValue
    employer_ein: FieldValue
    employer_address: FieldValue
    
    box_1_wages: FieldValue = Field(..., description="Box 1: Wages, tips, other compensation")
    box_2_federal_tax: FieldValue = Field(..., description="Box 2: Federal income tax withheld")
    box_3_ss_wages: FieldValue = Field(..., description="Box 3: Social security wages")
    box_5_medicare_wages: FieldValue = Field(..., description="Box 5: Medicare wages and tips")
    
    tax_year: FieldValue = Field(..., description="Tax year for this W-2")
    
    state_wages: Optional[FieldValue] = None
    state_tax: Optional[FieldValue] = None



class PaystubSemantic(BaseModel):
    """Semantic JSON schema for paystubs"""
    doc_type: Literal["paystub"] = "paystub"
    doc_id: str = Field(..., description="Unique document identifier")
    
    employee_name: FieldValue
    employee_id: Optional[FieldValue] = None
    
    employer_name: FieldValue
    
    pay_period_start: FieldValue = Field(..., description="Pay period start date")
    pay_period_end: FieldValue = Field(..., description="Pay period end date")
    pay_date: FieldValue = Field(..., description="Date of payment")
    
    current_gross_pay: FieldValue = Field(..., description="Gross pay for current period")
    current_regular_hours: Optional[FieldValue] = None
    current_regular_rate: Optional[FieldValue] = None
    current_overtime_hours: Optional[FieldValue] = None
    current_overtime_pay: Optional[FieldValue] = None
    current_bonus: Optional[FieldValue] = None
    current_commission: Optional[FieldValue] = None
    
    ytd_gross_pay: FieldValue = Field(..., description="Year-to-date gross pay")
    ytd_federal_tax: Optional[FieldValue] = None
    ytd_ss_tax: Optional[FieldValue] = None
    ytd_medicare_tax: Optional[FieldValue] = None
    
    current_net_pay: Optional[FieldValue] = None



class VOESemantic(BaseModel):
    """Semantic JSON schema for Verification of Employment"""
    doc_type: Literal["voe"] = "voe"
    doc_id: str = Field(..., description="Unique document identifier")
    
    employee_name: FieldValue
    employee_ssn: Optional[FieldValue] = None
    
    employer_name: FieldValue
    employer_address: Optional[FieldValue] = None
    employer_phone: Optional[FieldValue] = None
    
    job_title: FieldValue
    hire_date: FieldValue = Field(..., description="Date of hire")
    employment_status: FieldValue = Field(..., description="Full-time, part-time, etc.")
    
    base_salary: FieldValue = Field(..., description="Base salary or hourly rate")
    pay_frequency: FieldValue = Field(..., description="Weekly, bi-weekly, monthly, etc.")
    hours_per_week: Optional[FieldValue] = None
    
    overtime_typical: Optional[FieldValue] = Field(None, description="Typical overtime pay")
    bonus_typical: Optional[FieldValue] = Field(None, description="Typical bonus amount")
    commission_typical: Optional[FieldValue] = Field(None, description="Typical commission")
    
    probability_continued: FieldValue = Field(..., description="Likelihood employment will continue")
    
    verification_date: FieldValue = Field(..., description="Date VOE was completed")



class IncomeSource(BaseModel):
    """A single income source for Section 1b"""
    employer_name: FieldValue
    job_title: Optional[FieldValue] = None
    hire_date: Optional[FieldValue] = None
    employment_status: Optional[FieldValue] = None
    
    base_monthly_income: FieldValue = Field(..., description="Calculated base monthly income")
    
    overtime_monthly: Optional[FieldValue] = Field(None, description="Average monthly overtime")
    bonus_monthly: Optional[FieldValue] = Field(None, description="Average monthly bonus")
    commission_monthly: Optional[FieldValue] = Field(None, description="Average monthly commission")
    
    total_monthly_income: FieldValue = Field(..., description="Total qualifying monthly income")
    
    source_doc_ids: List[str] = Field(..., description="Document IDs used for this income source")
    
    freddie_compliant: bool = Field(..., description="Whether income meets Freddie Mac requirements")
    freddie_notes: str = Field(..., description="Notes on Freddie Mac compliance")


class Section1bOutput(BaseModel):
    """1003 Section 1b: Employment and Income"""
    section: Literal["1b"] = "1b"
    
    income_sources: List[IncomeSource] = Field(..., description="All identified income sources")
    
    total_monthly_income: float = Field(..., description="Total qualifying monthly income across all sources")
    
    freddie_analysis: str = Field(..., description="Detailed Freddie Mac compliance analysis")
    
    gaps: List[str] = Field(default_factory=list, description="Missing information or documents")
    recommendations: List[str] = Field(default_factory=list, description="Documents that could increase qualifying income")



class Gap(BaseModel):
    """A gap in documentation or information"""
    severity: Literal["critical", "warning", "info"] = Field(..., description="Severity level")
    category: str = Field(..., description="Category (e.g., 'missing_document', 'incomplete_data')")
    description: str = Field(..., description="Description of the gap")
    impact: str = Field(..., description="Impact on qualification or income")
    recommendation: str = Field(..., description="What to do to resolve this gap")
    potential_income_increase: Optional[float] = Field(None, description="Potential monthly income increase if resolved")


class GapAnalysis(BaseModel):
    """Complete gap analysis output"""
    gaps: List[Gap] = Field(..., description="All identified gaps")
    total_potential_increase: float = Field(..., description="Total potential monthly income increase")
    priority_actions: List[str] = Field(..., description="Prioritized list of actions to take")
