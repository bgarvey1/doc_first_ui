"""
Step 3: Final Comprehensive Analysis using GPT-5

This script:
1. Loads all semantic JSON files
2. Uses full gpt-5-2025-08-07 model for comprehensive analysis
3. Applies Freddie Mac underwriting guidelines
4. Generates MISMO 3.4 XML
5. Produces detailed gap analysis report
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from openai import OpenAI
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()


class MortgageUnderwritingAnalyzer:
    """Comprehensive mortgage underwriting analysis using GPT-5"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-5-2025-08-07"  # Full model for final analysis
        self.semantic_dir = Path("semantic_json")
        self.output_dir = Path("final_output")
        self.output_dir.mkdir(exist_ok=True)
        
        print(f"✓ Initialized with model: {self.model}")
    
    def load_all_semantic_files(self) -> Dict[str, Any]:
        """Load all semantic JSON files"""
        
        json_files = sorted(self.semantic_dir.glob("*_semantic.json"))
        
        if not json_files:
            print(f"⚠️  No semantic JSON files found in {self.semantic_dir}/")
            return {}
        
        documents = {}
        
        print(f"\n📁 Loading {len(json_files)} semantic JSON files...\n")
        
        for json_file in json_files:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                doc_type = data.get('document_type', 'UNKNOWN')
                filename = data.get('filename', json_file.stem)
                
                # Group by document type
                if doc_type not in documents:
                    documents[doc_type] = []
                
                documents[doc_type].append(data)
                print(f"  ✓ {doc_type}: {filename}")
        
        print(f"\n✓ Loaded {len(json_files)} documents")
        print(f"✓ Document types: {', '.join(documents.keys())}\n")
        
        return documents
    
    def load_freddie_guidelines(self) -> Dict[str, Any]:
        """Load Freddie Mac underwriting guidelines"""
        
        guidelines_file = Path("freddie_income_guides.json")
        
        if not guidelines_file.exists():
            print("⚠️  Freddie Mac guidelines not found")
            return {}
        
        with open(guidelines_file, 'r', encoding='utf-8') as f:
            guidelines = json.load(f)
        
        print(f"✓ Loaded Freddie Mac guidelines (Sections 5301-5305)")
        
        return guidelines
    
    def create_comprehensive_analysis_prompt(self, documents: Dict[str, Any], guidelines: Dict[str, Any]) -> str:
        """Create a comprehensive prompt for final analysis"""
        
        prompt = f"""You are a senior mortgage underwriter conducting a comprehensive file review for a mortgage application.

BORROWER DOCUMENTS ANALYZED:
{json.dumps(documents, indent=2)}

FREDDIE MAC UNDERWRITING GUIDELINES:
{json.dumps(guidelines, indent=2)}

YOUR TASK:
Perform a complete mortgage underwriting analysis and produce THREE outputs:

1. **BORROWER_PROFILE**: Complete borrower information extracted from all documents
   - Personal information (name, address, SSN)
   - Employment information (employer, position, dates)
   - Income analysis (base salary, YTD earnings, 2-year history from W2s)
   - Asset verification (bank accounts, balances)
   - Liability identification (mortgage, auto loan, credit cards)
   - Credit profile (scores, derogatory items, credit history)

2. **MISMO_DATA**: Structured data ready for MISMO 3.4 XML generation
   - Use MISMO 3.4 field names and structure
   - Include: PARTY (borrower), EMPLOYER, INCOME, ASSET, LIABILITY, CREDIT_SCORE
   - Map all extracted data to appropriate MISMO fields
   - Follow MISMO naming conventions exactly

3. **GAP_ANALYSIS**: Comprehensive gap analysis report
   - CRITICAL gaps: Missing required documents or information
   - WARNING gaps: Inconsistencies or items needing verification
   - INFO gaps: Additional documentation that would strengthen the file
   - Apply Freddie Mac guidelines for each gap identified
   - Specific recommendations for each gap

IMPORTANT ANALYSIS GUIDELINES:
- Calculate qualifying income per Freddie Mac Section 5301 (base salary + overtime/bonus if 2yr history)
- Verify income consistency across paystubs, W2s, and VOE
- Identify all recurring monthly obligations from bank statements
- Calculate debt-to-income ratios (housing + total)
- Flag any discrepancies or red flags
- Note document dates and ensure they meet seasoning requirements
- Identify large deposits that may need sourcing
- Check for sufficient reserves

OUTPUT FORMAT:
Return a JSON object with three top-level keys:
- "borrower_profile": Complete borrower information
- "mismo_data": MISMO 3.4 structured data
- "gap_analysis": Array of gaps with severity, description, recommendation

Be thorough, precise, and apply mortgage underwriting best practices."""

        return prompt
    
    def perform_comprehensive_analysis(self, documents: Dict[str, Any], guidelines: Dict[str, Any]) -> Dict[str, Any]:
        """Send all data to GPT-5 for comprehensive analysis"""
        
        print("\n" + "="*70)
        print("COMPREHENSIVE MORTGAGE UNDERWRITING ANALYSIS")
        print("="*70)
        print(f"Model: {self.model}")
        print(f"Documents: {sum(len(docs) for docs in documents.values())} files")
        print("="*70 + "\n")
        
        prompt = self.create_comprehensive_analysis_prompt(documents, guidelines)
        
        print("🤖 Sending to GPT-5 for analysis...")
        print("   (This may take 30-60 seconds)\n")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a senior mortgage underwriter with expertise in Freddie Mac guidelines, MISMO standards, and comprehensive file review."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                max_completion_tokens=16000
            )
            
            content = response.choices[0].message.content
            
            if not content or content.strip() == "":
                return {
                    "error": "GPT-5 returned empty response",
                    "finish_reason": response.choices[0].finish_reason,
                    "tokens": {
                        "prompt": response.usage.prompt_tokens,
                        "completion": response.usage.completion_tokens,
                        "total": response.usage.total_tokens
                    }
                }
            
            analysis = json.loads(content)
            
            # Add metadata
            analysis["metadata"] = {
                "analysis_date": datetime.now().isoformat(),
                "model_used": self.model,
                "tokens_used": {
                    "prompt": response.usage.prompt_tokens,
                    "completion": response.usage.completion_tokens,
                    "total": response.usage.total_tokens
                },
                "finish_reason": response.choices[0].finish_reason
            }
            
            print("✓ Analysis complete!")
            print(f"✓ Tokens used: {response.usage.total_tokens:,}")
            print(f"✓ Finish reason: {response.choices[0].finish_reason}\n")
            
            return analysis
            
        except json.JSONDecodeError as e:
            return {
                "error": f"JSON parsing error: {e}",
                "raw_response": content if 'content' in locals() else ""
            }
        except Exception as e:
            return {
                "error": f"Analysis error: {str(e)}",
                "error_type": type(e).__name__
            }
    
    def save_analysis_results(self, analysis: Dict[str, Any]):
        """Save the analysis results to multiple output files"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Save complete analysis JSON
        complete_file = self.output_dir / f"complete_analysis_{timestamp}.json"
        with open(complete_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved complete analysis: {complete_file}")
        
        # 2. Save borrower profile
        if "borrower_profile" in analysis:
            profile_file = self.output_dir / f"borrower_profile_{timestamp}.json"
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(analysis["borrower_profile"], f, indent=2, ensure_ascii=False)
            print(f"✓ Saved borrower profile: {profile_file}")
        
        # 3. Save MISMO data
        if "mismo_data" in analysis:
            mismo_file = self.output_dir / f"mismo_data_{timestamp}.json"
            with open(mismo_file, 'w', encoding='utf-8') as f:
                json.dump(analysis["mismo_data"], f, indent=2, ensure_ascii=False)
            print(f"✓ Saved MISMO data: {mismo_file}")
        
        # 4. Save gap analysis as readable report
        if "gap_analysis" in analysis:
            gap_file = self.output_dir / f"gap_analysis_{timestamp}.txt"
            with open(gap_file, 'w', encoding='utf-8') as f:
                f.write("="*70 + "\n")
                f.write("MORTGAGE UNDERWRITING GAP ANALYSIS REPORT\n")
                f.write("="*70 + "\n\n")
                f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Borrower: Elmo James\n\n")
                
                gaps = analysis["gap_analysis"]
                
                # Group by severity
                critical = [g for g in gaps if g.get("severity") == "CRITICAL"]
                warning = [g for g in gaps if g.get("severity") == "WARNING"]
                info = [g for g in gaps if g.get("severity") == "INFO"]
                
                f.write(f"SUMMARY:\n")
                f.write(f"  Critical Issues: {len(critical)}\n")
                f.write(f"  Warnings: {len(warning)}\n")
                f.write(f"  Informational: {len(info)}\n\n")
                
                # Write each section
                for severity, gaps_list in [("CRITICAL", critical), ("WARNING", warning), ("INFO", info)]:
                    if gaps_list:
                        f.write("="*70 + "\n")
                        f.write(f"{severity} ITEMS ({len(gaps_list)})\n")
                        f.write("="*70 + "\n\n")
                        
                        for idx, gap in enumerate(gaps_list, 1):
                            f.write(f"{idx}. {gap.get('item', 'Unknown')}\n")
                            f.write(f"   Description: {gap.get('description', 'N/A')}\n")
                            if 'recommendation' in gap:
                                f.write(f"   Recommendation: {gap.get('recommendation')}\n")
                            if 'guideline_reference' in gap:
                                f.write(f"   Guideline: {gap.get('guideline_reference')}\n")
                            f.write("\n")
            
            print(f"✓ Saved gap analysis report: {gap_file}")
        
        # 5. Save gap analysis JSON
        if "gap_analysis" in analysis:
            gap_json_file = self.output_dir / f"gap_analysis_{timestamp}.json"
            with open(gap_json_file, 'w', encoding='utf-8') as f:
                json.dump(analysis["gap_analysis"], f, indent=2, ensure_ascii=False)
            print(f"✓ Saved gap analysis JSON: {gap_json_file}")
    
    def run(self):
        """Run the complete analysis pipeline"""
        
        print("\n" + "="*70)
        print("FINAL MORTGAGE UNDERWRITING ANALYSIS PIPELINE")
        print("Using GPT-5-2025-08-07 for comprehensive review")
        print("="*70 + "\n")
        
        # Load all semantic JSON files
        documents = self.load_all_semantic_files()
        if not documents:
            print("❌ No documents to analyze. Run pdf_to_json.py and json_to_semantic.py first.")
            return
        
        # Load Freddie Mac guidelines
        guidelines = self.load_freddie_guidelines()
        
        # Perform comprehensive analysis
        analysis = self.perform_comprehensive_analysis(documents, guidelines)
        
        # Check for errors
        if "error" in analysis:
            print(f"\n❌ Analysis failed: {analysis['error']}")
            # Still save the error response
            error_file = self.output_dir / f"error_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2)
            print(f"✓ Error details saved to: {error_file}")
            return
        
        # Save all results
        print("\n" + "="*70)
        print("SAVING RESULTS")
        print("="*70 + "\n")
        
        self.save_analysis_results(analysis)
        
        # Print summary
        print("\n" + "="*70)
        print("✅ ANALYSIS COMPLETE")
        print("="*70)
        print(f"\nOutput directory: {self.output_dir}/")
        print("\nFiles created:")
        print("  • complete_analysis_*.json - Full analysis results")
        print("  • borrower_profile_*.json - Extracted borrower data")
        print("  • mismo_data_*.json - MISMO 3.4 structured data")
        print("  • gap_analysis_*.txt - Human-readable gap report")
        print("  • gap_analysis_*.json - Machine-readable gap data")
        
        # Print gap summary
        if "gap_analysis" in analysis:
            gaps = analysis["gap_analysis"]
            critical = len([g for g in gaps if g.get("severity") == "CRITICAL"])
            warning = len([g for g in gaps if g.get("severity") == "WARNING"])
            info = len([g for g in gaps if g.get("severity") == "INFO"])
            
            print("\n📊 Gap Analysis Summary:")
            print(f"   Critical Issues: {critical}")
            print(f"   Warnings: {warning}")
            print(f"   Informational: {info}")
        
        print("\n" + "="*70 + "\n")


def main():
    """Run the final analysis"""
    analyzer = MortgageUnderwritingAnalyzer()
    analyzer.run()


if __name__ == "__main__":
    main()
