"""
Interactive CLI for Mortgage Application Assistant
Provides a user-friendly interface for processing documents and filling out URLA
"""
import os
import sys
from pathlib import Path
from typing import Optional

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, SpinnerColumn, TextColumn
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from mortgage_assistant import MortgageAssistant, MortgageApplication


class InteractiveCLI:
    """Interactive command-line interface for mortgage processing"""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.assistant = None
        self.application = None
    
    def print(self, text: str, style: Optional[str] = None):
        """Print with or without Rich formatting"""
        if self.console:
            self.console.print(text, style=style)
        else:
            print(text)
    
    def print_header(self, title: str):
        """Print section header"""
        if self.console:
            self.console.print(Panel(title, style="bold blue"))
        else:
            print("\n" + "=" * 70)
            print(title)
            print("=" * 70)
    
    def prompt(self, message: str, default: Optional[str] = None) -> str:
        """Prompt for user input"""
        if self.console:
            return Prompt.ask(message, default=default)
        else:
            if default:
                message = f"{message} [{default}]"
            response = input(f"{message}: ")
            return response if response else default
    
    def confirm(self, message: str, default: bool = True) -> bool:
        """Confirm yes/no"""
        if self.console:
            return Confirm.ask(message, default=default)
        else:
            response = input(f"{message} [{'Y/n' if default else 'y/N'}]: ").lower()
            if not response:
                return default
            return response in ['y', 'yes']
    
    def show_welcome(self):
        """Show welcome screen"""
        self.print_header("🏠 MORTGAGE APPLICATION ASSISTANT")
        self.print("\nAI-Powered System for Processing Mortgage Documents and Filling URLA Forms")
        self.print("\nFeatures:")
        self.print("  • Automatically classify and extract data from PDFs")
        self.print("  • Verify income using Freddie Mac underwriting guidelines")
        self.print("  • Intelligently map data to URLA form fields")
        self.print("  • Generate compliance reports")
        self.print("\n")
    
    def select_folder(self) -> Optional[str]:
        """Select document folder"""
        self.print_header("📁 SELECT DOCUMENT FOLDER")
        
        default_folder = os.getcwd()
        folder = self.prompt("\nEnter path to folder containing borrower documents", default=default_folder)
        
        folder_path = Path(folder)
        if not folder_path.exists():
            self.print(f"\n❌ Error: Folder not found: {folder}", style="bold red")
            return None
        
        # Count PDFs
        pdf_files = list(folder_path.glob("*.pdf"))
        self.print(f"\n✓ Found {len(pdf_files)} PDF file(s) in folder", style="green")
        
        if len(pdf_files) == 0:
            self.print("⚠ No PDF files found", style="yellow")
            return None
        
        # Show files
        if self.confirm("\nShow file list?", default=False):
            for pdf in pdf_files:
                self.print(f"  • {pdf.name}")
        
        return folder
    
    def process_documents(self, folder: str):
        """Process all documents in folder"""
        self.print_header("📄 PROCESSING DOCUMENTS")
        
        # Initialize assistant
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            self.print("\n⚠ Warning: OPENAI_API_KEY not set. AI features will be limited.", style="yellow")
            self.print("Set your API key in .env file for full functionality\n")
        
        self.assistant = MortgageAssistant(api_key=api_key)
        
        # Process documents
        self.print("\nProcessing documents...")
        results = self.assistant.process_document_folder(folder)
        
        # Show results in table
        if self.console and RICH_AVAILABLE:
            table = Table(title="Document Processing Results")
            table.add_column("File", style="cyan")
            table.add_column("Type", style="magenta")
            table.add_column("Confidence", justify="right", style="green")
            table.add_column("Fields", justify="right")
            
            for result in results:
                if 'error' in result:
                    table.add_row(result['filename'], "ERROR", "-", "-")
                else:
                    classification = result['classification']
                    extracted = result['extracted_data']
                    table.add_row(
                        result['filename'],
                        classification['document_type'],
                        f"{classification['confidence']:.0%}",
                        str(len(extracted['extracted_fields']))
                    )
            
            self.console.print(table)
        else:
            self.print("\nProcessing complete!")
            for result in results:
                if 'error' not in result:
                    self.print(f"  ✓ {result['filename']}")
        
        self.print("")
    
    def analyze_income(self):
        """Analyze income"""
        self.print_header("💰 INCOME ANALYSIS")
        
        if not self.assistant:
            self.print("❌ No documents processed yet", style="bold red")
            return
        
        income_analysis = self.assistant.analyze_income()
        
        if not income_analysis:
            self.print("\n⚠ Could not perform income analysis - missing required documents", style="yellow")
        
        self.print("")
    
    def map_to_urla(self):
        """Map extracted data to URLA"""
        self.print_header("📋 URLA FORM MAPPING")
        
        if not self.assistant:
            self.print("❌ No documents processed yet", style="bold red")
            return
        
        urla_data = self.assistant.map_to_urla()
        
        # Show mapped fields
        if self.console and RICH_AVAILABLE:
            table = Table(title="Mapped URLA Fields")
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="green")
            
            for field, value in list(urla_data.items())[:15]:  # Show first 15
                table.add_row(field, str(value))
            
            if len(urla_data) > 15:
                table.add_row("...", f"... and {len(urla_data) - 15} more fields")
            
            self.console.print(table)
        else:
            self.print(f"\n✓ Mapped {len(urla_data)} fields")
        
        self.print("")
        return urla_data
    
    def show_completion_status(self, urla_data: dict):
        """Show URLA completion status"""
        self.print_header("✅ COMPLETION STATUS")
        
        if not self.assistant:
            return
        
        report = self.assistant.generate_urla_report(urla_data)
        self.print("")
    
    def create_application(self):
        """Create complete application"""
        self.print_header("📦 CREATING APPLICATION")
        
        if not self.assistant:
            self.print("❌ No documents processed yet", style="bold red")
            return
        
        self.print("\nGenerating mortgage application...")
        self.application = self.assistant.create_application()
        
        # Show summary
        summary = self.assistant.generate_summary_report(self.application)
        self.print("\n" + summary)
        
        self.print("")
    
    def save_results(self):
        """Save results"""
        self.print_header("💾 SAVE RESULTS")
        
        if not self.assistant or not self.application:
            self.print("❌ No application to save", style="bold red")
            return
        
        output_dir = self.prompt("\nOutput directory", default="output")
        
        # Create output directory
        Path(output_dir).mkdir(exist_ok=True)
        
        # Save results
        self.assistant.save_results(output_dir)
        self.application.to_json(f"{output_dir}/mortgage_application.json")
        
        # Export URLA structure
        self.assistant.urla_analyzer.export_structure_to_json(f"{output_dir}/urla_structure.json")
        
        self.print(f"\n✓ All results saved to {output_dir}/", style="bold green")
        self.print("\nFiles created:")
        self.print(f"  • {output_dir}/processed_documents.json")
        self.print(f"  • {output_dir}/extracted_data.json")
        self.print(f"  • {output_dir}/mortgage_application.json")
        self.print(f"  • {output_dir}/urla_structure.json")
        self.print("")
    
    def show_menu(self) -> str:
        """Show main menu"""
        self.print("\n" + "-" * 70)
        self.print("MENU:")
        self.print("  1. Select Document Folder")
        self.print("  2. Process Documents")
        self.print("  3. Analyze Income")
        self.print("  4. Map to URLA Form")
        self.print("  5. View Completion Status")
        self.print("  6. Create Application")
        self.print("  7. Save Results")
        self.print("  8. Run Full Pipeline")
        self.print("  9. Exit")
        self.print("-" * 70)
        
        choice = self.prompt("\nSelect option", default="8")
        return choice
    
    def run_full_pipeline(self):
        """Run complete pipeline"""
        self.print_header("🚀 RUNNING FULL PIPELINE")
        
        # 1. Select folder
        folder = self.select_folder()
        if not folder:
            return
        
        # 2. Process documents
        self.process_documents(folder)
        
        # 3. Analyze income
        self.analyze_income()
        
        # 4. Map to URLA
        urla_data = self.map_to_urla()
        
        # 5. Show completion
        if urla_data:
            self.show_completion_status(urla_data)
        
        # 6. Create application
        self.create_application()
        
        # 7. Save results
        if self.confirm("\nSave results?", default=True):
            self.save_results()
    
    def run(self):
        """Main run loop"""
        self.show_welcome()
        
        folder = None
        
        while True:
            choice = self.show_menu()
            
            if choice == "1":
                folder = self.select_folder()
            
            elif choice == "2":
                if folder:
                    self.process_documents(folder)
                else:
                    self.print("\n❌ Please select a folder first", style="bold red")
            
            elif choice == "3":
                self.analyze_income()
            
            elif choice == "4":
                urla_data = self.map_to_urla()
            
            elif choice == "5":
                if self.assistant:
                    urla_data = self.assistant.map_to_urla()
                    self.show_completion_status(urla_data)
                else:
                    self.print("\n❌ No data available", style="bold red")
            
            elif choice == "6":
                self.create_application()
            
            elif choice == "7":
                self.save_results()
            
            elif choice == "8":
                self.run_full_pipeline()
            
            elif choice == "9":
                self.print("\n👋 Goodbye!", style="bold blue")
                break
            
            else:
                self.print("\n❌ Invalid option", style="bold red")


def main():
    """Main entry point"""
    cli = InteractiveCLI()
    
    # Check if folder provided as argument
    if len(sys.argv) > 1:
        folder = sys.argv[1]
        if Path(folder).exists():
            cli.show_welcome()
            cli.process_documents(folder)
            cli.run_full_pipeline()
            return
    
    # Otherwise run interactive mode
    cli.run()


if __name__ == "__main__":
    main()
