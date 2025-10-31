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
    """Process all documents in a session"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    api_key = os.getenv('OPENAI_API_KEY')
    classifier = DocumentClassifier(api_key)
    extractor = DocumentExtractor(api_key)
    
    for doc_id, doc in session.documents.items():
        if doc["processing_status"] != ProcessingStatus.PENDING:
            continue
        
        try:
            session.update_document_status(doc_id, ProcessingStatus.PROCESSING)
            
            file_path = None
            for f in UPLOAD_DIR.glob(f"{session_id}_{doc_id}_*"):
                file_path = f
                break
            
            if not file_path:
                session.update_document_status(doc_id, ProcessingStatus.FAILED)
                continue
            
            # Parse PDF
            parser = PDFParser(str(file_path))
            extracted_text = parser.extract_text()
            
            # Classify
            classification = classifier.classify_document(extracted_text)
            
            # Extract data
            extracted_data = extractor.extract(extracted_text, classification.document_type)
            
            doc_type = classification.document_type
            if doc_type not in session.extracted_data:
                session.extracted_data[doc_type] = []
            session.extracted_data[doc_type].append(extracted_data.extracted_fields)
            
            session.update_document_status(
                doc_id,
                ProcessingStatus.COMPLETED,
                doc_type,
                classification.confidence,
                len(extracted_data.extracted_fields)
            )
            
            urla_analyzer = URLAFormAnalyzer()
            mapping_data = {}
            if doc_type == 'W2':
                mapping_data['w2_data'] = extracted_data.extracted_fields
            elif doc_type == 'PAYSTUB':
                mapping_data['paystub_data'] = extracted_data.extracted_fields
            elif doc_type == 'VOE':
                mapping_data['voe_data'] = extracted_data.extracted_fields
            
            if mapping_data:
                urla_fields = urla_analyzer.get_field_mapping_from_docs(mapping_data)
                
                for field_name, value in urla_fields.items():
                    if value is not None:
                        section_id = "1b"  # Default to employment section
                        if "borrower" in field_name:
                            section_id = "1a"
                        elif "property" in field_name or "loan" in field_name:
                            section_id = "4a"
                        
                        session.set_field_value(
                            field_name,
                            value,
                            section_id,
                            ValueSource.DOCUMENT_RULE,
                            classification.confidence,
                            [doc_id]
                        )
        
        except Exception as e:
            session.update_document_status(doc_id, ProcessingStatus.FAILED)
            print(f"Error processing document {doc_id}: {e}")
    
    return {"message": "Documents processed", "total_documents": len(session.documents)}


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
    """Calculate income using Freddie Mac rules"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    from underwriting_engine import FreddieUnderwritingEngine
    engine = FreddieUnderwritingEngine("app/freddie_income_guides.json")
    
    w2_data = session.extracted_data.get('W2', [])
    paystub_data = session.extracted_data.get('PAYSTUB', [{}])[0] if session.extracted_data.get('PAYSTUB') else None
    voe_data = session.extracted_data.get('VOE', [{}])[0] if session.extracted_data.get('VOE') else None
    
    if not w2_data:
        raise HTTPException(status_code=400, detail="No W-2 documents found")
    
    # Analyze income
    analysis = engine.analyze_w2_income(w2_data, paystub_data, voe_data)
    
    session.income_analysis = analysis.to_dict()
    
    income_sources = [
        IncomeSourceInfo(
            source_type=src.source_type,
            employer_name=src.employer_name,
            amount=src.amount,
            frequency=src.frequency,
            is_stable=src.is_stable,
            has_continuance=src.has_continuance,
            notes=src.notes
        )
        for src in analysis.income_sources
    ]
    
    potential_increases = []
    if len(w2_data) < 2:
        potential_increases.append({
            "suggestion": "Upload prior year W-2 for 2-year income history",
            "potential_benefit": "May increase qualifying income through bonus/overtime averaging"
        })
    
    return IncomeAnalysisResponse(
        total_monthly_income=analysis.total_monthly_income,
        income_sources=income_sources,
        meets_freddie_requirements=analysis.meets_requirements,
        compliance_checks=analysis.freddie_mac_compliance,
        issues=analysis.issues,
        recommendations=analysis.recommendations,
        potential_income_increases=potential_increases
    )


@app.get("/sessions/{session_id}/gaps", response_model=GapAnalysisResponse)
async def get_gap_analysis(session_id: str):
    """Get gap analysis for the application"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    from gap_analyzer import GapAnalyzer
    from mismo_generator import MISMOGenerator
    
    # Generate MISMO XML
    mismo_gen = MISMOGenerator()
    mismo_xml = mismo_gen.generate_from_extracted_data(
        session.extracted_data,
        session.income_analysis
    )
    
    from mismo_parser import MISMOParser
    parser = MISMOParser(None)
    mismo_data = parser.parse_string(mismo_xml)
    
    analyzer = GapAnalyzer()
    gaps = analyzer.analyze_all(mismo_data, session.extracted_data)
    
    session.gap_analysis = {
        "gaps": [g.__dict__ for g in gaps],
        "completion": analyzer.get_completion_percentage()
    }
    
    gap_list = [
        InformationGap(
            field_name=g.field_name,
            section=g.section,
            severity=g.severity.value,
            description=g.description,
            recommendation=g.recommendation,
            mismo_path=g.mismo_path
        )
        for g in gaps
    ]
    
    critical = len([g for g in gaps if g.severity.value == "critical"])
    warning = len([g for g in gaps if g.severity.value == "warning"])
    info = len([g for g in gaps if g.severity.value == "info"])
    
    suggested_documents = []
    if critical > 0:
        suggested_documents.append("Upload borrower identification documents (ID, SSN card)")
    if not session.extracted_data.get('W2'):
        suggested_documents.append("Upload W-2 forms for the last 2 years")
    if not session.extracted_data.get('PAYSTUB'):
        suggested_documents.append("Upload most recent paystub (within 30 days)")
    if not session.extracted_data.get('BANK_STATEMENT'):
        suggested_documents.append("Upload bank statements for asset verification")
    
    return GapAnalysisResponse(
        total_gaps=len(gaps),
        critical_gaps=critical,
        warning_gaps=warning,
        info_gaps=info,
        gaps=gap_list,
        completion_percentage=analyzer.get_completion_percentage(),
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
