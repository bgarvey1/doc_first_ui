"""
AI-First Document Processing Pipeline

This module implements a pure AI approach to document processing:
1. PDF → Structural JSON (text, tables, layout)
2. Structural JSON → Semantic JSON via GPT-5-mini (W-2, paystub, VOE schemas)
3. All Semantic JSONs → 1003 Answers via GPT-5 (with Freddie Mac guidelines)

No rule-based extraction logic - everything is handled by the AI models.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import fitz  # PyMuPDF
from openai import OpenAI
from pydantic import ValidationError

from ai_schemas import (
    DocumentType, W2Semantic, PaystubSemantic, VOESemantic,
    Section1bOutput, GapAnalysis, FieldValue, Evidence
)

logger = logging.getLogger(__name__)


class AIDocumentPipeline:
    """AI-first document processing pipeline"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with OpenAI API key"""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for AI-first pipeline")
        
        self.client = OpenAI(api_key=self.api_key)
        
        self.semantic_model = "gpt-5-mini-2025-08-07"  # For per-document extraction
        self.analysis_model = "gpt-5-2025-08-07"  # For income analysis
        
        self.freddie_guidelines = self._load_freddie_guidelines()
    
    def _load_freddie_guidelines(self) -> Dict[str, Any]:
        """Load Freddie Mac guidelines JSON"""
        guidelines_path = Path(__file__).parent.parent / "freddie_income_guides.json"
        try:
            with open(guidelines_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load Freddie Mac guidelines: {e}")
            return {}
    
    
    def pdf_to_structural_json(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract text, tables, and layout from PDF into structural JSON.
        Uses PyMuPDF for fast, accurate text extraction.
        
        Returns:
            {
                "pages": [
                    {
                        "page_num": 1,
                        "text": "full page text",
                        "blocks": [
                            {"type": "text", "bbox": [x0,y0,x1,y1], "text": "..."},
                            {"type": "table", "bbox": [...], "rows": [[...]]}
                        ]
                    }
                ],
                "metadata": {"num_pages": 1, "filename": "..."}
            }
        """
        try:
            doc = fitz.open(pdf_path)
            structural_json = {
                "pages": [],
                "metadata": {
                    "num_pages": len(doc),
                    "filename": Path(pdf_path).name
                }
            }
            
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text("text")
                
                blocks = []
                for block in page.get_text("dict")["blocks"]:
                    if block["type"] == 0:  # Text block
                        block_text = ""
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                block_text += span.get("text", "")
                            block_text += "\n"
                        
                        blocks.append({
                            "type": "text",
                            "bbox": block["bbox"],
                            "text": block_text.strip()
                        })
                
                
                structural_json["pages"].append({
                    "page_num": page_num,
                    "text": text,
                    "blocks": blocks
                })
            
            doc.close()
            return structural_json
            
        except Exception as e:
            logger.error(f"Error extracting structural JSON from PDF: {e}")
            raise
    
    
    def identify_document_type(self, structural_json: Dict[str, Any]) -> DocumentType:
        """
        Use GPT-5-mini to identify document type from structural JSON.
        """
        text_sample = ""
        for page in structural_json["pages"][:2]:  # First 2 pages only
            text_sample += page["text"][:1000]  # First 1000 chars per page
        
        prompt = f"""Analyze this document and identify its type.

Document text sample:
{text_sample}

Identify the document type as one of:
- w2: IRS Form W-2 (Wage and Tax Statement)
- paystub: Employee paystub/paycheck stub
- voe: Verification of Employment form
- bank_statement: Bank account statement
- tax_return: Tax return (1040, etc.)
- credit_report: Credit report
- unknown: Cannot determine type

Also identify the year if applicable (e.g., tax year for W-2, statement year).

Return your answer as JSON with this exact structure:
{{
    "doc_type": "w2|paystub|voe|bank_statement|tax_return|credit_report|unknown",
    "confidence": 0.95,
    "year": 2024
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.semantic_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            return DocumentType(**result)
            
        except Exception as e:
            logger.error(f"Error identifying document type: {e}")
            return DocumentType(doc_type="unknown", confidence=0.0)
    
    def extract_w2_semantic(self, doc_id: str, structural_json: Dict[str, Any]) -> W2Semantic:
        """Extract W-2 data into semantic JSON using GPT-5-mini"""
        
        full_text = "\n\n".join([p["text"] for p in structural_json["pages"]])
        
        prompt = f"""Extract W-2 form data from this document into structured JSON.

Document text:
{full_text}

Extract the following fields. For each field, provide:
- value: the extracted value (or "unknown" if not found)
- confidence: 0.0-1.0 confidence score
- evidence: array of {{"page": page_number, "snippet": "relevant text", "location": "Box 1"}}

Required fields:
- employee_name, employee_ssn, employee_address
- employer_name, employer_ein, employer_address
- box_1_wages (Box 1: Wages, tips, other compensation)
- box_2_federal_tax (Box 2: Federal income tax withheld)
- box_3_ss_wages (Box 3: Social security wages)
- box_5_medicare_wages (Box 5: Medicare wages and tips)
- tax_year (e.g., 2024)

Optional fields:
- state_wages, state_tax

Return JSON matching this schema structure. Use "unknown" for values you cannot find.
Include page numbers (1-indexed) and text snippets as evidence for each field."""

        try:
            response = self.client.chat.completions.create(
                model=self.semantic_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            result["doc_id"] = doc_id
            result["doc_type"] = "w2"
            
            return W2Semantic(**result)
            
        except ValidationError as e:
            logger.error(f"Validation error in W-2 extraction: {e}")
            raise
        except Exception as e:
            logger.error(f"Error extracting W-2 semantic data: {e}")
            raise
    
    def extract_paystub_semantic(self, doc_id: str, structural_json: Dict[str, Any]) -> PaystubSemantic:
        """Extract paystub data into semantic JSON using GPT-5-mini"""
        
        full_text = "\n\n".join([p["text"] for p in structural_json["pages"]])
        
        prompt = f"""Extract paystub data from this document into structured JSON.

Document text:
{full_text}

Extract the following fields with value, confidence (0.0-1.0), and evidence:

Required fields:
- employee_name, employer_name
- pay_period_start, pay_period_end, pay_date (dates in YYYY-MM-DD format)
- current_gross_pay (gross pay for this pay period)
- ytd_gross_pay (year-to-date gross pay)

Optional fields:
- employee_id
- current_regular_hours, current_regular_rate
- current_overtime_hours, current_overtime_pay
- current_bonus, current_commission
- ytd_federal_tax, ytd_ss_tax, ytd_medicare_tax
- current_net_pay

Return JSON with evidence (page numbers and text snippets) for each field.
Use "unknown" for values not found."""

        try:
            response = self.client.chat.completions.create(
                model=self.semantic_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            result["doc_id"] = doc_id
            result["doc_type"] = "paystub"
            
            return PaystubSemantic(**result)
            
        except ValidationError as e:
            logger.error(f"Validation error in paystub extraction: {e}")
            raise
        except Exception as e:
            logger.error(f"Error extracting paystub semantic data: {e}")
            raise
    
    def extract_voe_semantic(self, doc_id: str, structural_json: Dict[str, Any]) -> VOESemantic:
        """Extract VOE data into semantic JSON using GPT-5-mini"""
        
        full_text = "\n\n".join([p["text"] for p in structural_json["pages"]])
        
        prompt = f"""Extract Verification of Employment (VOE) data from this document into structured JSON.

Document text:
{full_text}

Extract the following fields with value, confidence (0.0-1.0), and evidence:

Required fields:
- employee_name, employer_name
- job_title, hire_date (YYYY-MM-DD), employment_status (full-time/part-time)
- base_salary (annual salary or hourly rate with unit)
- pay_frequency (weekly/bi-weekly/semi-monthly/monthly)
- probability_continued (likelihood employment will continue)
- verification_date (YYYY-MM-DD)

Optional fields:
- employee_ssn, employer_address, employer_phone
- hours_per_week
- overtime_typical, bonus_typical, commission_typical

Return JSON with evidence for each field. Use "unknown" for values not found."""

        try:
            response = self.client.chat.completions.create(
                model=self.semantic_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            result["doc_id"] = doc_id
            result["doc_type"] = "voe"
            
            return VOESemantic(**result)
            
        except ValidationError as e:
            logger.error(f"Validation error in VOE extraction: {e}")
            raise
        except Exception as e:
            logger.error(f"Error extracting VOE semantic data: {e}")
            raise
    
    def structural_to_semantic(self, doc_id: str, structural_json: Dict[str, Any]) -> Optional[Any]:
        """
        Convert structural JSON to semantic JSON based on document type.
        Returns W2Semantic, PaystubSemantic, VOESemantic, or None.
        """
        doc_type = self.identify_document_type(structural_json)
        logger.info(f"Identified document {doc_id} as {doc_type.doc_type} (confidence: {doc_type.confidence})")
        
        if doc_type.doc_type == "w2":
            return self.extract_w2_semantic(doc_id, structural_json)
        elif doc_type.doc_type == "paystub":
            return self.extract_paystub_semantic(doc_id, structural_json)
        elif doc_type.doc_type == "voe":
            return self.extract_voe_semantic(doc_id, structural_json)
        else:
            logger.warning(f"Unsupported document type: {doc_type.doc_type}")
            return None
    
    
    def aggregate_to_1003_section_1b(
        self,
        semantic_docs: List[Any]
    ) -> Section1bOutput:
        """
        Aggregate semantic JSONs into 1003 Section 1b using GPT-5.
        Applies Freddie Mac guidelines for income calculation.
        """
        
        docs_json = []
        for doc in semantic_docs:
            docs_json.append(doc.model_dump())
        
        freddie_summary = {
            "income_requirements": self.freddie_guidelines.get("5301", {}),
            "documentation": self.freddie_guidelines.get("5302", {}),
            "employed_income": self.freddie_guidelines.get("5303", {}),
            "calculation_framework": self.freddie_guidelines.get("calculation_framework", {})
        }
        
        prompt = f"""You are a mortgage underwriter analyzing employment and income documents to complete Section 1b of the URLA (1003) form.

SEMANTIC DOCUMENTS:
{json.dumps(docs_json, indent=2)}

FREDDIE MAC GUIDELINES:
{json.dumps(freddie_summary, indent=2)}

TASK:
1. Identify all income sources from the documents
2. For each income source, calculate:
   - Base monthly income (use appropriate conversion: weekly×52÷12, bi-weekly×26÷12, etc.)
   - Variable income (overtime, bonus, commission) - average over available period
   - Total qualifying monthly income
3. Apply Freddie Mac rules:
   - Verify 2-year history (or justify shorter period)
   - Verify 3-year continuance likelihood
   - For variable income: analyze trend (stable/increasing/declining)
   - If declining >10%, document reason
4. Identify gaps and recommend additional documents that could increase qualifying income

OUTPUT REQUIREMENTS:
Return JSON matching this structure:
{{
    "section": "1b",
    "income_sources": [
        {{
            "employer_name": {{"value": "...", "confidence": 0.95, "evidence": [...], "notes": "..."}},
            "job_title": {{"value": "...", "confidence": 0.9, "evidence": [...]}},
            "hire_date": {{"value": "2020-01-15", "confidence": 0.95, "evidence": [...]}},
            "employment_status": {{"value": "full-time", "confidence": 1.0, "evidence": [...]}},
            "base_monthly_income": {{"value": "5000.00", "confidence": 0.95, "evidence": [...], "notes": "Calculated from bi-weekly pay: $2307.69 × 26 ÷ 12"}},
            "overtime_monthly": {{"value": "200.00", "confidence": 0.8, "evidence": [...], "notes": "Average from available paystubs"}},
            "bonus_monthly": null,
            "commission_monthly": null,
            "total_monthly_income": {{"value": "5200.00", "confidence": 0.9, "evidence": [...], "notes": "Base + overtime"}},
            "source_doc_ids": ["doc1", "doc2"],
            "freddie_compliant": true,
            "freddie_notes": "Meets 2-year history requirement. Employment verified via VOE. Overtime shows stable pattern."
        }}
    ],
    "total_monthly_income": 5200.00,
    "freddie_analysis": "Detailed analysis of Freddie Mac compliance...",
    "gaps": ["Missing W-2 for 2023", "Paystub older than 30 days"],
    "recommendations": ["Provide most recent paystub (within 30 days)", "Provide 2023 W-2 to complete 2-year history"]
}}

IMPORTANT:
- Show your calculations and reasoning
- Cite evidence with page numbers
- Use "unknown" for values you cannot determine
- Be conservative with confidence scores
- Explain any Freddie Mac compliance issues"""

        try:
            response = self.client.chat.completions.create(
                model=self.analysis_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            return Section1bOutput(**result)
            
        except ValidationError as e:
            logger.error(f"Validation error in 1003 aggregation: {e}")
            raise
        except Exception as e:
            logger.error(f"Error aggregating to 1003 Section 1b: {e}")
            raise
    
    
    def analyze_gaps(
        self,
        semantic_docs: List[Any],
        section_1b: Section1bOutput
    ) -> GapAnalysis:
        """
        Analyze gaps and provide recommendations using GPT-5.
        """
        
        docs_json = [doc.model_dump() for doc in semantic_docs]
        section_json = section_1b.model_dump()
        
        prompt = f"""Analyze the gaps in this mortgage application and provide recommendations.

AVAILABLE DOCUMENTS:
{json.dumps(docs_json, indent=2)}

CURRENT 1003 SECTION 1B:
{json.dumps(section_json, indent=2)}

FREDDIE MAC GUIDELINES:
{json.dumps(self.freddie_guidelines, indent=2)}

TASK:
Identify all gaps in documentation and information. For each gap:
1. Classify severity: critical (blocks approval), warning (may impact approval), info (nice to have)
2. Describe the gap and its impact on qualification
3. Recommend specific actions to resolve
4. Estimate potential monthly income increase if resolved

Focus on:
- Missing documents (W-2s, paystubs, VOE, tax returns)
- Incomplete 2-year history
- Missing variable income documentation (overtime, bonus, commission)
- Paystubs older than 30 days
- Missing continuance verification
- Opportunities to increase qualifying income

Return JSON:
{{
    "gaps": [
        {{
            "severity": "critical|warning|info",
            "category": "missing_document|incomplete_data|outdated_document|missing_verification",
            "description": "...",
            "impact": "...",
            "recommendation": "...",
            "potential_income_increase": 500.00
        }}
    ],
    "total_potential_increase": 1200.00,
    "priority_actions": ["Action 1", "Action 2", "Action 3"]
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.analysis_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            return GapAnalysis(**result)
            
        except ValidationError as e:
            logger.error(f"Validation error in gap analysis: {e}")
            raise
        except Exception as e:
            logger.error(f"Error analyzing gaps: {e}")
            raise
    
    
    def process_document(self, doc_id: str, pdf_path: str) -> Optional[Any]:
        """
        Complete pipeline for a single document:
        PDF → Structural JSON → Semantic JSON
        
        Returns: W2Semantic, PaystubSemantic, VOESemantic, or None
        """
        logger.info(f"Processing document {doc_id}: {pdf_path}")
        
        structural_json = self.pdf_to_structural_json(pdf_path)
        
        semantic_json = self.structural_to_semantic(doc_id, structural_json)
        
        return semantic_json
    
    def process_session(
        self,
        documents: List[Tuple[str, str]]  # List of (doc_id, pdf_path)
    ) -> Dict[str, Any]:
        """
        Complete pipeline for a session:
        1. Process each document → semantic JSON
        2. Aggregate → 1003 Section 1b
        3. Analyze gaps
        
        Returns:
            {
                "semantic_docs": [...],
                "section_1b": Section1bOutput,
                "gaps": GapAnalysis
            }
        """
        logger.info(f"Processing session with {len(documents)} documents")
        
        # Step 1: Process all documents
        semantic_docs = []
        for doc_id, pdf_path in documents:
            try:
                semantic = self.process_document(doc_id, pdf_path)
                if semantic:
                    semantic_docs.append(semantic)
            except Exception as e:
                logger.error(f"Failed to process document {doc_id}: {e}")
        
        if not semantic_docs:
            raise ValueError("No documents were successfully processed")
        
        section_1b = self.aggregate_to_1003_section_1b(semantic_docs)
        
        gaps = self.analyze_gaps(semantic_docs, section_1b)
        
        return {
            "semantic_docs": [doc.model_dump() for doc in semantic_docs],
            "section_1b": section_1b.model_dump(),
            "gaps": gaps.model_dump()
        }
