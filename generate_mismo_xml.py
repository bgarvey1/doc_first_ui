"""
Generate MISMO 3.4 XML from the MISMO data JSON produced by final_analysis.py
"""

import json
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom


class MISMOXMLGenerator:
    """Generate MISMO 3.4 XML from structured JSON data"""
    
    def __init__(self):
        self.ns = {
            '': 'http://www.mismo.org/residential/2009/schemas',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
        
        # Register namespaces
        for prefix, uri in self.ns.items():
            if prefix:
                ET.register_namespace(prefix, uri)
            else:
                ET.register_namespace('', uri)
    
    def create_xml_root(self) -> ET.Element:
        """Create MISMO XML root element with proper namespaces"""
        
        root = ET.Element('MESSAGE')
        root.set('xmlns', self.ns[''])
        root.set('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation',
                'http://www.mismo.org/residential/2009/schemas https://www.mismo.org/schemas/MISMO3_4.xsd')
        root.set('MISMOVersionID', '3.4')
        
        return root
    
    def add_parties(self, deal_sets: ET.Element, parties_data: list):
        """Add PARTY elements to DEAL_SETS"""
        
        parties = ET.SubElement(deal_sets, 'PARTIES')
        
        for party_data in parties_data:
            party = ET.SubElement(parties, 'PARTY')
            party.set('SequenceNumber', '1')
            
            # INDIVIDUAL
            if 'INDIVIDUAL' in party_data:
                individual = ET.SubElement(party, 'INDIVIDUAL')
                ind_data = party_data['INDIVIDUAL']
                
                # NAME
                if 'NAME' in ind_data:
                    name = ET.SubElement(individual, 'NAME')
                    name_data = ind_data['NAME']
                    
                    if 'FirstName' in name_data:
                        first = ET.SubElement(name, 'FirstName')
                        first.text = name_data['FirstName']
                    
                    if 'LastName' in name_data:
                        last = ET.SubElement(name, 'LastName')
                        last.text = name_data['LastName']
                
                # TAXPAYER_IDENTIFIER (SSN)
                if 'TAXPAYER_IDENTIFIER' in ind_data:
                    taxpayer_ids = ET.SubElement(individual, 'TAXPAYER_IDENTIFIERS')
                    taxpayer_id = ET.SubElement(taxpayer_ids, 'TAXPAYER_IDENTIFIER')
                    tid_data = ind_data['TAXPAYER_IDENTIFIER']
                    
                    if 'IdentifierType' in tid_data:
                        id_type = ET.SubElement(taxpayer_id, 'TaxpayerIdentifierType')
                        id_type.text = tid_data['IdentifierType']
                    
                    if 'IdentifierValue' in tid_data:
                        id_value = ET.SubElement(taxpayer_id, 'TaxpayerIdentifierValue')
                        id_value.text = tid_data['IdentifierValue']
                
                # RESIDENCES
                if 'Residences' in ind_data:
                    residences = ET.SubElement(individual, 'RESIDENCES')
                    
                    for res_data in ind_data['Residences']:
                        residence = ET.SubElement(residences, 'RESIDENCE')
                        res = res_data['RESIDENCE']
                        
                        if 'BORROWER_RESIDENCE_TYPE' in res:
                            res_type = ET.SubElement(residence, 'BorrowerResidencyType')
                            res_type.text = res['BORROWER_RESIDENCE_TYPE']
                        
                        if 'ADDRESS' in res:
                            address = ET.SubElement(residence, 'ADDRESS')
                            addr_data = res['ADDRESS']
                            
                            if 'AddressLineText' in addr_data:
                                addr_line = ET.SubElement(address, 'AddressLineText')
                                addr_line.text = addr_data['AddressLineText']
                            
                            if 'CityName' in addr_data:
                                city = ET.SubElement(address, 'CityName')
                                city.text = addr_data['CityName']
                            
                            if 'StateCode' in addr_data:
                                state = ET.SubElement(address, 'StateCode')
                                state.text = addr_data['StateCode']
                            
                            if 'PostalCode' in addr_data:
                                postal = ET.SubElement(address, 'PostalCode')
                                postal.text = addr_data['PostalCode']
            
            # ROLES
            roles = ET.SubElement(party, 'ROLES')
            role = ET.SubElement(roles, 'ROLE')
            
            borrower = ET.SubElement(role, 'BORROWER')
            
            # EMPLOYMENTS
            if 'EMPLOYMENTS' in party_data:
                employments = ET.SubElement(borrower, 'EMPLOYMENTS')
                
                for emp_data in party_data['EMPLOYMENTS']:
                    employment = ET.SubElement(employments, 'EMPLOYMENT')
                    emp = emp_data['EMPLOYMENT']
                    
                    if 'EMPLOYMENT_STATUS_TYPE' in emp:
                        status = ET.SubElement(employment, 'EmploymentStatusType')
                        status.text = emp['EMPLOYMENT_STATUS_TYPE']
                    
                    if 'EMPLOYMENT_START_DATE' in emp:
                        start = ET.SubElement(employment, 'EmploymentStartDate')
                        start.text = emp['EMPLOYMENT_START_DATE']
                    
                    if 'POSITION_TITLE' in emp:
                        position = ET.SubElement(employment, 'EmploymentPositionDescription')
                        position.text = emp['POSITION_TITLE']
                    
                    # EMPLOYER
                    if 'EMPLOYER' in emp:
                        employer = ET.SubElement(employment, 'EMPLOYER')
                        emp_detail = emp['EMPLOYER']
                        
                        legal_entity = ET.SubElement(employer, 'LEGAL_ENTITY')
                        
                        if 'FullName' in emp_detail:
                            emp_name = ET.SubElement(legal_entity, 'FullName')
                            emp_name.text = emp_detail['FullName']
                        
                        if 'ADDRESS' in emp_detail:
                            contacts = ET.SubElement(legal_entity, 'CONTACTS')
                            contact = ET.SubElement(contacts, 'CONTACT')
                            contact_points = ET.SubElement(contact, 'CONTACT_POINTS')
                            contact_point = ET.SubElement(contact_points, 'CONTACT_POINT')
                            
                            address = ET.SubElement(contact_point, 'ADDRESS')
                            addr_data = emp_detail['ADDRESS']
                            
                            if 'AddressLineText' in addr_data:
                                addr_line = ET.SubElement(address, 'AddressLineText')
                                addr_line.text = addr_data['AddressLineText']
                            
                            if 'CityName' in addr_data:
                                city = ET.SubElement(address, 'CityName')
                                city.text = addr_data['CityName']
                            
                            if 'StateCode' in addr_data:
                                state = ET.SubElement(address, 'StateCode')
                                state.text = addr_data['StateCode']
                            
                            if 'PostalCode' in addr_data:
                                postal = ET.SubElement(address, 'PostalCode')
                                postal.text = addr_data['PostalCode']
                    
                    # INCOMES
                    if 'INCOMES' in emp:
                        individual_income = ET.SubElement(employment, 'INDIVIDUAL')
                        incomes = ET.SubElement(individual_income, 'CURRENT_INCOMES')
                        
                        for inc_data in emp['INCOMES']:
                            income = ET.SubElement(incomes, 'CURRENT_INCOME')
                            inc = inc_data['INCOME']
                            
                            if 'INCOME_TYPE' in inc:
                                inc_type = ET.SubElement(income, 'CurrentIncomeType')
                                inc_type.text = inc['INCOME_TYPE']
                            
                            if 'PAYMENT_FREQUENCY_TYPE' in inc:
                                freq = ET.SubElement(income, 'CurrentIncomeMonthlyTotalAmount')
                                freq.text = str(inc.get('CURRENT_INCOME_MONTHLY_AMOUNT', ''))
                            
                            if 'EMPLOYMENT_INCOME_INDICATOR' in inc:
                                emp_ind = ET.SubElement(income, 'EmploymentIncomeIndicator')
                                emp_ind.text = str(inc['EMPLOYMENT_INCOME_INDICATOR']).lower()
            
            # ROLE_DETAIL
            role_detail = ET.SubElement(role, 'ROLE_DETAIL')
            party_role_type = ET.SubElement(role_detail, 'PartyRoleType')
            party_role_type.text = party_data.get('PARTY_ROLE_TYPE', 'Borrower')
    
    def add_assets(self, deal_sets: ET.Element, assets_data: list):
        """Add ASSET elements"""
        
        assets = ET.SubElement(deal_sets, 'ASSETS')
        
        for asset_data in assets_data:
            asset = ET.SubElement(assets, 'ASSET')
            
            detail = asset_data.get('ASSET_DETAIL', {})
            
            if 'ASSET_TYPE' in detail:
                asset_type = ET.SubElement(asset, 'AssetType')
                asset_type.text = detail['ASSET_TYPE']
            
            if 'ASSET_CASH_OR_MARKET_VALUE_AMOUNT' in detail:
                value = ET.SubElement(asset, 'AssetCashOrMarketValueAmount')
                value.text = str(detail['ASSET_CASH_OR_MARKET_VALUE_AMOUNT'])
            
            if 'ASSET_ACCOUNT_IDENTIFIER' in detail:
                account = ET.SubElement(asset, 'AssetAccountIdentifier')
                account.text = detail['ASSET_ACCOUNT_IDENTIFIER']
    
    def add_liabilities(self, deal_sets: ET.Element, liabilities_data: list):
        """Add LIABILITY elements"""
        
        liabilities = ET.SubElement(deal_sets, 'LIABILITIES')
        
        for liability_data in liabilities_data:
            liability = ET.SubElement(liabilities, 'LIABILITY')
            
            detail = liability_data.get('LIABILITY_DETAIL', {})
            
            if 'LIABILITY_TYPE' in detail:
                liab_type = ET.SubElement(liability, 'LiabilityType')
                liab_type.text = detail['LIABILITY_TYPE']
            
            if 'LIABILITY_UNPAID_BALANCE_AMOUNT' in detail:
                balance = ET.SubElement(liability, 'LiabilityUnpaidBalanceAmount')
                balance.text = str(detail['LIABILITY_UNPAID_BALANCE_AMOUNT'])
            
            if 'LIABILITY_MONTHLY_PAYMENT_AMOUNT' in detail:
                payment = ET.SubElement(liability, 'LiabilityMonthlyPaymentAmount')
                payment.text = str(detail['LIABILITY_MONTHLY_PAYMENT_AMOUNT'])
    
    def generate_mismo_xml(self, mismo_data: dict) -> str:
        """Generate complete MISMO 3.4 XML from JSON data"""
        
        root = self.create_xml_root()
        
        # DEAL_SETS
        deal_sets = ET.SubElement(root, 'DEAL_SETS')
        deal_set = ET.SubElement(deal_sets, 'DEAL_SET')
        deals = ET.SubElement(deal_set, 'DEALS')
        deal = ET.SubElement(deals, 'DEAL')
        
        # Add PARTIES
        if 'PARTY' in mismo_data:
            self.add_parties(deal, mismo_data['PARTY'])
        
        # Add ASSETS
        if 'ASSET' in mismo_data:
            self.add_assets(deal, mismo_data['ASSET'])
        
        # Add LIABILITIES
        if 'LIABILITY' in mismo_data:
            self.add_liabilities(deal, mismo_data['LIABILITY'])
        
        # Convert to string with pretty printing
        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ")
        
        # Remove extra blank lines
        lines = [line for line in pretty_xml.split('\n') if line.strip()]
        return '\n'.join(lines)
    
    def process_latest_mismo_data(self):
        """Find and process the latest MISMO data JSON file"""
        
        final_output_dir = Path("final_output")
        
        # Find all mismo_data JSON files
        mismo_files = sorted(final_output_dir.glob("mismo_data_*.json"))
        
        if not mismo_files:
            print("❌ No MISMO data JSON files found in final_output/")
            return
        
        # Get the latest file
        latest_file = mismo_files[-1]
        
        print(f"\n📄 Loading MISMO data: {latest_file.name}")
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            mismo_data = json.load(f)
        
        print("✓ Loaded MISMO data\n")
        
        # Generate XML
        print("🔄 Generating MISMO 3.4 XML...")
        xml_content = self.generate_mismo_xml(mismo_data)
        
        # Save XML
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        xml_file = final_output_dir / f"elmo_james_mismo_{timestamp}.xml"
        
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        print(f"✓ Saved MISMO XML: {xml_file}")
        print(f"✓ File size: {xml_file.stat().st_size:,} bytes\n")
        
        # Print summary
        print("="*70)
        print("✅ MISMO 3.4 XML GENERATED")
        print("="*70)
        print(f"Output file: {xml_file}")
        print(f"\nContents:")
        print(f"  • {len(mismo_data.get('PARTY', []))} Borrower(s)")
        print(f"  • {len(mismo_data.get('ASSET', []))} Asset(s)")
        print(f"  • {len(mismo_data.get('LIABILITY', []))} Liability(ies)")
        print("="*70 + "\n")


def main():
    """Generate MISMO XML from the latest analysis"""
    generator = MISMOXMLGenerator()
    generator.process_latest_mismo_data()


if __name__ == "__main__":
    main()
