"""
Pydantic models for the API
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class DocumentType(str, Enum):
    """Document types that can be processed"""
    W2 = "W2"
    PAYSTUB = "PAYSTUB"
    VOE = "VOE"
    BANK_STATEMENT = "BANK_STATEMENT"
    CREDIT_REPORT = "CREDIT_REPORT"
    MORTGAGE_STATEMENT = "MORTGAGE_STATEMENT"
    TAX_RETURN = "TAX_RETURN"
    OTHER = "OTHER"


class ProcessingStatus(str, Enum):
    """Status of document processing"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ValueSource(str, Enum):
    """Source of a field value"""
    DOCUMENT_AI = "document_ai"
    DOCUMENT_RULE = "document_rule"
    USER_INPUT = "user_input"
    CALCULATED = "calculated"
    DEFAULT = "default"


class SessionCreate(BaseModel):
    """Request to create a new session"""
    borrower_email: Optional[str] = None
    borrower_name: Optional[str] = None


class SessionResponse(BaseModel):
    """Response with session information"""
    session_id: str
    created_at: datetime
    last_updated: datetime
    current_section: str = "1a"
    completion_percentage: float = 0.0


class DocumentUploadResponse(BaseModel):
    """Response after document upload"""
    document_id: str
    filename: str
    message: str


class DocumentInfo(BaseModel):
    """Information about a document"""
    document_id: str
    filename: str
    file_size: int
    upload_timestamp: datetime
    processing_status: ProcessingStatus
    document_type: Optional[str] = None
    confidence: Optional[float] = None
    extracted_fields_count: int = 0


class FieldValue(BaseModel):
    """A field value with metadata"""
    field_name: str
    value: Any
    value_source: ValueSource
    confidence: float = 1.0
    contributing_documents: List[str] = Field(default_factory=list)


class URLAFieldInfo(BaseModel):
    """Information about a URLA field"""
    field_name: str
    field_type: str
    required: bool
    description: str
    current_value: Optional[Any] = None
    value_source: Optional[ValueSource] = None
    confidence: Optional[float] = None
    contributing_documents: List[str] = Field(default_factory=list)


class URLASectionResponse(BaseModel):
    """Response with URLA section data"""
    section_id: str
    section_name: str
    description: str
    fields: List[URLAFieldInfo]
    completion_percentage: float
    missing_required_fields: List[str]


class FieldUpdateRequest(BaseModel):
    """Request to update a field value"""
    field_name: str
    value: Any
    section_id: str


class IncomeSourceInfo(BaseModel):
    """Information about an income source"""
    source_type: str
    employer_name: Optional[str] = None
    amount: float
    frequency: str = "monthly"
    is_stable: bool
    has_continuance: bool
    notes: Optional[str] = None


class IncomeAnalysisResponse(BaseModel):
    """Response with income analysis"""
    total_monthly_income: float
    income_sources: List[IncomeSourceInfo]
    meets_freddie_requirements: bool
    compliance_checks: Dict[str, bool]
    issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    potential_income_increases: List[Dict[str, Any]] = Field(default_factory=list)


class InformationGap(BaseModel):
    """An information gap"""
    field_name: str
    section: str
    severity: str  # "critical", "warning", "info"
    description: str
    recommendation: str
    mismo_path: Optional[str] = None


class GapAnalysisResponse(BaseModel):
    """Response with gap analysis"""
    total_gaps: int
    critical_gaps: int
    warning_gaps: int
    info_gaps: int
    gaps: List[InformationGap]
    completion_percentage: float
    suggested_documents: List[str] = Field(default_factory=list)


class MISMOExportResponse(BaseModel):
    """Response with MISMO XML"""
    xml_content: str
    file_size: int
    generated_at: datetime
