"""
In-memory session management for mortgage applications
"""
import uuid
from typing import Dict, Optional, Any
from datetime import datetime
from models import ProcessingStatus, ValueSource


class ApplicationSession:
    """Represents a mortgage application session"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        self.current_section = "1a"
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.field_values: Dict[str, Dict[str, Any]] = {}
        self.extracted_data: Dict[str, Any] = {}
        self.income_analysis: Optional[Dict[str, Any]] = None
        self.gap_analysis: Optional[Dict[str, Any]] = None
        self.processed_documents: list = []
    
    def add_document(self, document_id: str, filename: str, file_size: int):
        """Add a document to the session"""
        self.documents[document_id] = {
            "document_id": document_id,
            "filename": filename,
            "file_size": file_size,
            "upload_timestamp": datetime.now(),
            "processing_status": ProcessingStatus.PENDING,
            "document_type": None,
            "confidence": None,
            "extracted_fields_count": 0
        }
        self.last_updated = datetime.now()
    
    def update_document_status(self, document_id: str, status: ProcessingStatus, 
                              document_type: Optional[str] = None,
                              confidence: Optional[float] = None,
                              extracted_fields_count: int = 0):
        """Update document processing status"""
        if document_id in self.documents:
            self.documents[document_id]["processing_status"] = status
            if document_type:
                self.documents[document_id]["document_type"] = document_type
            if confidence is not None:
                self.documents[document_id]["confidence"] = confidence
            self.documents[document_id]["extracted_fields_count"] = extracted_fields_count
            self.last_updated = datetime.now()
    
    def set_field_value(self, field_name: str, value: Any, section_id: str,
                       value_source: ValueSource = ValueSource.USER_INPUT,
                       confidence: float = 1.0,
                       contributing_documents: list = None):
        """Set a field value"""
        self.field_values[field_name] = {
            "field_name": field_name,
            "value": value,
            "section_id": section_id,
            "value_source": value_source,
            "confidence": confidence,
            "contributing_documents": contributing_documents or []
        }
        self.last_updated = datetime.now()
    
    def get_field_value(self, field_name: str) -> Optional[Dict[str, Any]]:
        """Get a field value"""
        return self.field_values.get(field_name)
    
    def get_section_fields(self, section_id: str) -> list:
        """Get all fields for a section"""
        return [fv for fv in self.field_values.values() if fv["section_id"] == section_id]


class SessionManager:
    """Manages application sessions in memory"""
    
    def __init__(self):
        self.sessions: Dict[str, ApplicationSession] = {}
    
    def create_session(self) -> ApplicationSession:
        """Create a new session"""
        session_id = str(uuid.uuid4())
        session = ApplicationSession(session_id)
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[ApplicationSession]:
        """Get a session by ID"""
        return self.sessions.get(session_id)
    
    def delete_session(self, session_id: str):
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]


session_manager = SessionManager()
