from pathlib import Path
import sys

sys.path.insert(0, str((Path(__file__).parent).resolve()))
sys.path.insert(0, str((Path(__file__).parent / "src").resolve()))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from typing import List, Optional
import os
import uuid
from datetime import datetime

from models import (
    SessionCreate, SessionResponse, DocumentUploadResponse, DocumentInfo,
    URLASectionResponse, URLAFieldInfo, FieldUpdateRequest, IncomeAnalysisResponse,
    IncomeSourceInfo, GapAnalysisResponse, InformationGap, MISMOExportResponse,
    ProcessingStatus, ValueSource
)
from session_manager import session_manager
from mortgage_assistant import MortgageAssistant
from urla_analyzer import URLAFormAnalyzer
from pdf_parser import PDFParser
from document_extractor import DocumentClassifier, DocumentExtractor
from ai_pipeline import AIDocumentPipeline

app = FastAPI(title="Mortgage Application API")

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/config")
async def get_config():
    """Get system configuration including AI extraction status"""
    openai_key = os.getenv("OPENAI_API_KEY")
    return {
        "ai_enabled": bool(openai_key),
        "provider": "openai" if openai_key else "rule_only",
        "extraction_mode": "AI-powered" if openai_key else "Rule-based (reduced accuracy)"
    }


@app.post("/sessions", response_model=SessionResponse)
async def create_session(request: SessionCreate):
    """Create a new mortgage application session"""
    session = session_manager.create_session()
    return SessionResponse(
        session_id=session.session_id,
        created_at=session.created_at,
        last_updated=session.last_updated,
        current_section=session.current_section,
        completion_percentage=0.0
    )


@app.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get session information"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Calculate completion percentage
    urla_analyzer = URLAFormAnalyzer()
    all_fields = urla_analyzer.get_all_fields()
    filled_count = len([f for f in session.field_values.values() if f["value"] is not None])
    completion_percentage = (filled_count / len(all_fields)) * 100 if all_fields else 0
    
    return SessionResponse(
        session_id=session.session_id,
        created_at=session.created_at,
        last_updated=session.last_updated,
        current_section=session.current_section,
        completion_percentage=round(completion_percentage, 1)
    )


@app.post("/sessions/{session_id}/documents", response_model=DocumentUploadResponse)
async def upload_document(session_id: str, file: UploadFile = File(...)):
    """Upload a document to a session"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    document_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{session_id}_{document_id}_{file.filename}"
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    session.add_document(document_id, file.filename, len(content))
    
    return DocumentUploadResponse(
        document_id=document_id,
        filename=file.filename,
        message="Document uploaded successfully"
    )


@app.get("/sessions/{session_id}/documents", response_model=List[DocumentInfo])
async def list_documents(session_id: str):
    """List all documents in a session"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return [DocumentInfo(**doc) for doc in session.documents.values()]


@app.post("/sessions/{session_id}/process")
async def process_documents(session_id: str):
    """Process all documents in a session using AI-first pipeline"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    try:
        pipeline = AIDocumentPipeline(api_key)
        
        documents_to_process = []
        for doc_id, doc in session.documents.items():
            if doc["processing_status"] != ProcessingStatus.PENDING:
                continue
            
            file_path = None
            for f in UPLOAD_DIR.glob(f"{session_id}_{doc_id}_*"):
                file_path = str(f)
                break
            
            if file_path:
                documents_to_process.append((doc_id, file_path))
                session.update_document_status(doc_id, ProcessingStatus.PROCESSING)
        
        if not documents_to_process:
            return {"message": "No pending documents to process", "total_documents": 0}
        
        result = pipeline.process_session(documents_to_process)
        
        session.extracted_data['semantic_docs'] = result['semantic_docs']
        session.extracted_data['section_1b'] = result['section_1b']
        session.extracted_data['gaps'] = result['gaps']
        
        for doc_id, _ in documents_to_process:
            session.update_document_status(
                doc_id,
                ProcessingStatus.COMPLETED,
                "processed",
                0.95,
                1
            )
        
        section_1b = result['section_1b']
        for income_source in section_1b.get('income_sources', []):
            # Extract employer name
            employer = income_source.get('employer_name', {})
            if employer and employer.get('value') and employer['value'] != 'unknown':
                session.set_field_value(
                    'employer_name',
                    employer['value'],
                    '1b',
                    ValueSource.DOCUMENT_AI,
                    employer.get('confidence', 0.9),
                    income_source.get('source_doc_ids', [])
                )
            
            # Extract job title
            job_title = income_source.get('job_title', {})
            if job_title and job_title.get('value') and job_title['value'] != 'unknown':
                session.set_field_value(
                    'job_title',
                    job_title['value'],
                    '1b',
                    ValueSource.DOCUMENT_AI,
                    job_title.get('confidence', 0.9),
                    income_source.get('source_doc_ids', [])
                )
            
            # Extract monthly income
            total_income = income_source.get('total_monthly_income', {})
            if total_income and total_income.get('value') and total_income['value'] != 'unknown':
                session.set_field_value(
                    'monthly_income',
                    total_income['value'],
                    '1b',
                    ValueSource.DOCUMENT_AI,
                    total_income.get('confidence', 0.9),
                    income_source.get('source_doc_ids', [])
                )
        
        session.income_analysis = {
            'total_monthly_income': section_1b.get('total_monthly_income', 0),
            'freddie_analysis': section_1b.get('freddie_analysis', ''),
            'income_sources': section_1b.get('income_sources', [])
        }
        
        session.gap_analysis = result['gaps']
        
        return {
            "message": "Documents processed successfully using AI pipeline",
            "total_documents": len(documents_to_process),
            "total_monthly_income": section_1b.get('total_monthly_income', 0),
            "gaps_found": len(result['gaps'].get('gaps', []))
        }
    
    except Exception as e:
        for doc_id, doc in session.documents.items():
            if doc["processing_status"] == ProcessingStatus.PROCESSING:
                session.update_document_status(doc_id, ProcessingStatus.FAILED)
        
        import traceback
        error_detail = f"Error processing documents: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}/urla/{section_id}", response_model=URLASectionResponse)
async def get_urla_section(session_id: str, section_id: str):
    """Get URLA section data"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    urla_analyzer = URLAFormAnalyzer()
    section = urla_analyzer.get_section(section_id)
    
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    
    fields = []
    missing_required = []
    
    for field in section.fields:
        field_value = session.get_field_value(field.field_name)
        
        if field_value:
            fields.append(URLAFieldInfo(
                field_name=field.field_name,
                field_type=field.field_type,
                required=field.required,
                description=field.description,
                current_value=field_value["value"],
                value_source=field_value["value_source"],
                confidence=field_value["confidence"],
                contributing_documents=field_value["contributing_documents"]
            ))
        else:
            fields.append(URLAFieldInfo(
                field_name=field.field_name,
                field_type=field.field_type,
                required=field.required,
                description=field.description,
                current_value=None
            ))
            if field.required:
                missing_required.append(field.field_name)
    
    filled = len([f for f in fields if f.current_value is not None])
    completion = (filled / len(fields)) * 100 if fields else 0
    
    return URLASectionResponse(
        section_id=section.section_id,
        section_name=section.section_name,
        description=section.description,
        fields=fields,
        completion_percentage=round(completion, 1),
        missing_required_fields=missing_required
    )


@app.patch("/sessions/{session_id}/urla")
async def update_urla_field(session_id: str, update: FieldUpdateRequest):
    """Update a URLA field value"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.set_field_value(
        update.field_name,
        update.value,
        update.section_id,
        ValueSource.USER_INPUT,
        1.0,
        []
    )
    
    return {"message": "Field updated successfully"}


@app.post("/sessions/{session_id}/income", response_model=IncomeAnalysisResponse)
async def calculate_income(session_id: str):
    """Get income analysis from AI pipeline results"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    section_1b = session.extracted_data.get('section_1b')
    if not section_1b:
        raise HTTPException(status_code=400, detail="No income data available. Please process documents first.")
    
    income_sources = []
    for src in section_1b.get('income_sources', []):
        employer_name = src.get('employer_name', {}).get('value', 'Unknown')
        total_income = src.get('total_monthly_income', {})
        
        income_sources.append(IncomeSourceInfo(
            source_type="Employment",
            employer_name=employer_name,
            amount=float(total_income.get('value', 0)) if total_income.get('value') != 'unknown' else 0,
            frequency="Monthly",
            is_stable=src.get('freddie_compliant', False),
            has_continuance=src.get('freddie_compliant', False),
            notes=src.get('freddie_notes', '')
        ))
    
    # Extract recommendations from gaps
    gaps_data = session.extracted_data.get('gaps', {})
    recommendations = gaps_data.get('priority_actions', [])
    
    potential_increases = []
    for gap in gaps_data.get('gaps', []):
        if gap.get('potential_income_increase'):
            potential_increases.append({
                "suggestion": gap.get('recommendation', ''),
                "potential_benefit": f"Could increase income by ${gap['potential_income_increase']:.2f}/month"
            })
    
    return IncomeAnalysisResponse(
        total_monthly_income=section_1b.get('total_monthly_income', 0),
        income_sources=income_sources,
        meets_freddie_requirements=all(src.get('freddie_compliant', False) for src in section_1b.get('income_sources', [])),
        compliance_checks=[section_1b.get('freddie_analysis', '')],
        issues=section_1b.get('gaps', []),
        recommendations=recommendations,
        potential_income_increases=potential_increases
    )


@app.get("/sessions/{session_id}/gaps", response_model=GapAnalysisResponse)
async def get_gap_analysis(session_id: str):
    """Get gap analysis from AI pipeline results"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    gaps_data = session.extracted_data.get('gaps')
    if not gaps_data:
        raise HTTPException(status_code=400, detail="No gap analysis available. Please process documents first.")
    
    gap_list = []
    critical = 0
    warning = 0
    info = 0
    
    for gap in gaps_data.get('gaps', []):
        severity = gap.get('severity', 'info')
        if severity == 'critical':
            critical += 1
        elif severity == 'warning':
            warning += 1
        else:
            info += 1
        
        gap_list.append(InformationGap(
            field_name=gap.get('category', 'unknown'),
            section="1b",  # Default to employment section
            severity=severity,
            description=gap.get('description', ''),
            recommendation=gap.get('recommendation', ''),
            mismo_path=""
        ))
    
    # Extract suggested documents from recommendations
    suggested_documents = gaps_data.get('priority_actions', [])
    
    # Calculate completion percentage (inverse of gaps)
    total_possible_fields = 77  # Total URLA fields
    completion = max(0, 100 - (len(gap_list) / total_possible_fields * 100))
    
    return GapAnalysisResponse(
        total_gaps=len(gap_list),
        critical_gaps=critical,
        warning_gaps=warning,
        info_gaps=info,
        gaps=gap_list,
        completion_percentage=round(completion, 1),
        suggested_documents=suggested_documents
    )


@app.post("/sessions/{session_id}/mismo", response_model=MISMOExportResponse)
async def generate_mismo(session_id: str):
    """Generate MISMO XML for the application"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    from mismo_generator import MISMOGenerator
    
    mismo_gen = MISMOGenerator()
    mismo_xml = mismo_gen.generate_from_extracted_data(
        session.extracted_data,
        session.income_analysis
    )
    
    return MISMOExportResponse(
        xml_content=mismo_xml,
        file_size=len(mismo_xml),
        generated_at=datetime.now()
    )


@app.get("/urla/sections")
async def get_all_sections():
    """Get all URLA sections"""
    urla_analyzer = URLAFormAnalyzer()
    return {
        "sections": [
            {
                "section_id": s.section_id,
                "section_name": s.section_name,
                "description": s.description,
                "field_count": len(s.fields)
            }
            for s in urla_analyzer.sections
        ]
    }
