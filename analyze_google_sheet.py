#!/usr/bin/env python3
"""
Analisador da planilha Google Sheets da metodologia Ana Paula
"""

import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# ID da planilha da metodologia Ana Paula
SPREADSHEET_ID = "1yyHuP6qjnK2Rd26yPPzaOqi_OJVeRjAJnewRIOJvFVY"

class GoogleSheetsAnalyzer:
    def __init__(self, credentials_path="google_credentials.json"):
        """Inicializar o analisador com credenciais do Google Sheets"""
        self.credentials_path = credentials_path
        self.service = None
        self.spreadsheet_id = SPREADSHEET_ID
        self.analysis_result = {
            "timestamp": datetime.now().isoformat(),
            "spreadsheet_id": self.spreadsheet_id,
            "sheets": {},
            "data_structure": {},
            "import_mapping": {},
            "recommendations": []
        }
    
    def authenticate(self):
        """Autenticar com Google Sheets API"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
            self.service = build('sheets', 'v4', credentials=credentials)
            logger.info("✅ Autenticação com Google Sheets API bem-sucedida")
            return True
        except Exception as e:
            logger.error(f"❌ Erro na autenticação: {e}")
            return False
    
    def get_sheet_names(self):
        """Obter lista de todas as abas da planilha"""
        try:
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            sheets = spreadsheet.get('sheets', [])
            sheet_names = []
            
            for sheet in sheets:
                properties = sheet.get('properties', {})
                sheet_name = properties.get('title', '')
                sheet_id = properties.get('sheetId', 0)
                sheet_names.append({
                    'name': sheet_name,
                    'id': sheet_id,
                    'row_count': properties.get('gridProperties', {}).get('rowCount', 0),
                    'column_count': properties.get('gridProperties', {}).get('columnCount', 0)
                })
            
            logger.info(f"📊 Encontradas {len(sheet_names)} abas na planilha")
            return sheet_names
        except HttpError as e:
            logger.error(f"❌ Erro ao obter abas: {e}")
            return []
    
    def get_sheet_data(self, sheet_name, range_name=None):
        """Obter dados de uma aba específica"""
        try:
            if range_name is None:
                range_name = f"{sheet_name}!A:Z"  # Pegar todas as colunas até Z
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            return values
        except HttpError as e:
            logger.error(f"❌ Erro ao obter dados da aba '{sheet_name}': {e}")
            return []
    
    def analyze_sheet_structure(self, sheet_name, data):
        """Analisar estrutura de uma aba"""
        if not data:
            return {
                "status": "empty",
                "rows": 0,
                "columns": 0,
                "headers": [],
                "data_types": {},
                "sample_data": []
            }
        
        # Analisar estrutura
        rows = len(data)
        columns = len(data[0]) if data else 0
        headers = data[0] if data else []
        
        # Analisar tipos de dados nas colunas
        data_types = {}
        sample_data = []
        
        for col_idx in range(min(columns, 10)):  # Analisar até 10 colunas
            col_data = []
            for row_idx in range(1, min(rows, 21)):  # Pegar até 20 linhas de dados
                if row_idx < len(data) and col_idx < len(data[row_idx]):
                    value = data[row_idx][col_idx]
                    col_data.append(value)
            
            # Determinar tipo de dados
            data_type = self._determine_data_type(col_data)
            data_types[headers[col_idx] if col_idx < len(headers) else f"Col_{col_idx}"] = data_type
            
            # Amostra de dados
            sample_data.append({
                "column": headers[col_idx] if col_idx < len(headers) else f"Col_{col_idx}",
                "type": data_type,
                "sample_values": col_data[:5]
            })
        
        return {
            "status": "analyzed",
            "rows": rows,
            "columns": columns,
            "headers": headers,
            "data_types": data_types,
            "sample_data": sample_data
        }
    
    def _determine_data_type(self, values):
        """Determinar tipo de dados de uma coluna"""
        if not values:
            return "empty"
        
        numeric_count = 0
        date_count = 0
        text_count = 0
        
        for value in values:
            if not value or value.strip() == "":
                continue
                
            # Tentar converter para número
            try:
                # Remover formatação brasileira (R$ 1.234,56)
                clean_value = str(value).replace("R$", "").replace(".", "").replace(",", ".").strip()
                float(clean_value)
                numeric_count += 1
            except:
                # Tentar converter para data
                try:
                    datetime.strptime(str(value), "%d/%m/%Y")
                    date_count += 1
                except:
                    try:
                        datetime.strptime(str(value), "%Y-%m-%d")
                        date_count += 1
                    except:
                        text_count += 1
        
        total = numeric_count + date_count + text_count
        if total == 0:
            return "empty"
        
        if numeric_count / total > 0.7:
            return "numeric"
        elif date_count / total > 0.5:
            return "date"
        else:
            return "text"
    
    def analyze_all_sheets(self):
        """Analisar todas as abas da planilha"""
        if not self.service:
            logger.error("❌ Serviço não inicializado. Execute authenticate() primeiro.")
            return False
        
        sheet_names = self.get_sheet_names()
        logger.info(f"🔍 Analisando {len(sheet_names)} abas...")
        
        for sheet_info in sheet_names:
            sheet_name = sheet_info['name']
            logger.info(f"📋 Analisando aba: {sheet_name}")
            
            # Obter dados da aba
            data = self.get_sheet_data(sheet_name)
            
            # Analisar estrutura
            structure = self.analyze_sheet_structure(sheet_name, data)
            
            # Salvar análise
            self.analysis_result["sheets"][sheet_name] = {
                "info": sheet_info,
                "structure": structure,
                "data_preview": data[:10] if data else []  # Primeiras 10 linhas
            }
            
            logger.info(f"✅ Aba '{sheet_name}' analisada: {structure['rows']} linhas, {structure['columns']} colunas")
        
        return True
    
    def generate_import_mapping(self):
        """Gerar mapeamento para importação de dados"""
        logger.info("🗺️ Gerando mapeamento de importação...")
        
        # Mapear abas para funcionalidades do sistema
        import_mapping = {
            "account_structure": {
                "description": "Estrutura de contas (grupos, subgrupos, contas específicas)",
                "sheets": [],
                "fields": {
                    "groups": ["Grupo", "Código", "Descrição"],
                    "subgroups": ["Subgrupo", "Grupo", "Código", "Descrição"],
                    "accounts": ["Conta", "Subgrupo", "Código", "Tipo"]
                }
            },
            "transactions": {
                "description": "Transações financeiras",
                "sheets": [],
                "fields": {
                    "date": "Data",
                    "description": "Descrição",
                    "account": "Conta",
                    "amount": "Valor",
                    "type": "Tipo"
                }
            },
            "reports": {
                "description": "Relatórios financeiros (DRE, Fluxo de Caixa)",
                "sheets": [],
                "fields": {
                    "period": "Período",
                    "revenue": "Receitas",
                    "expenses": "Despesas",
                    "profit": "Lucro"
                }
            }
        }
        
        # Analisar cada aba e mapear para funcionalidades
        for sheet_name, sheet_data in self.analysis_result["sheets"].items():
            structure = sheet_data["structure"]
            headers = structure["headers"]
            
            # Detectar tipo de aba baseado nos cabeçalhos
            if any("receita" in str(h).lower() for h in headers) or any("venda" in str(h).lower() for h in headers):
                if "transações" in sheet_name.lower() or "movimento" in sheet_name.lower():
                    import_mapping["transactions"]["sheets"].append(sheet_name)
                else:
                    import_mapping["account_structure"]["sheets"].append(sheet_name)
            elif any("despesa" in str(h).lower() for h in headers) or any("custo" in str(h).lower() for h in headers):
                import_mapping["account_structure"]["sheets"].append(sheet_name)
            elif any("dre" in str(h).lower() for h in headers) or any("resultado" in str(h).lower() for h in headers):
                import_mapping["reports"]["sheets"].append(sheet_name)
            elif any("fluxo" in str(h).lower() for h in headers) or any("caixa" in str(h).lower() for h in headers):
                import_mapping["reports"]["sheets"].append(sheet_name)
            else:
                # Aba genérica - tentar mapear baseado na estrutura
                if structure["columns"] >= 3 and any("valor" in str(h).lower() for h in headers):
                    import_mapping["transactions"]["sheets"].append(sheet_name)
        
        self.analysis_result["import_mapping"] = import_mapping
        
        # Gerar recomendações
        self._generate_recommendations()
        
        return import_mapping
    
    def _generate_recommendations(self):
        """Gerar recomendações baseadas na análise"""
        recommendations = []
        
        # Analisar estrutura de dados
        total_sheets = len(self.analysis_result["sheets"])
        sheets_with_data = sum(1 for s in self.analysis_result["sheets"].values() 
                             if s["structure"]["status"] == "analyzed" and s["structure"]["rows"] > 1)
        
        recommendations.append({
            "priority": "HIGH",
            "category": "Data Structure",
            "issue": f"Planilha com {total_sheets} abas, {sheets_with_data} com dados",
            "recommendation": "Implementar importação por aba para cada tipo de dados"
        })
        
        # Recomendações por tipo de dados
        if self.analysis_result["import_mapping"]["transactions"]["sheets"]:
            recommendations.append({
                "priority": "HIGH",
                "category": "Transactions",
                "issue": "Abas de transações identificadas",
                "recommendation": "Criar endpoint para importação de transações com validação de dados"
            })
        
        if self.analysis_result["import_mapping"]["reports"]["sheets"]:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Reports",
                "issue": "Abas de relatórios identificadas",
                "recommendation": "Implementar geração automática de relatórios baseados nos dados da planilha"
            })
        
        # Recomendação de validação
        recommendations.append({
            "priority": "HIGH",
            "category": "Validation",
            "issue": "Validação de dados necessária",
            "recommendation": "Implementar validação de tipos de dados e consistência antes da importação"
        })
        
        self.analysis_result["recommendations"] = recommendations
    
    def save_analysis(self, filename="google_sheet_analysis.json"):
        """Salvar análise em arquivo JSON"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.analysis_result, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Análise salva em: {filename}")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao salvar análise: {e}")
            return False
    
    def print_summary(self):
        """Imprimir resumo da análise"""
        print("\n" + "="*80)
        print("📊 RESUMO DA ANÁLISE - PLANILHA METODOLOGIA ANA PAULA")
        print("="*80)
        
        print(f"📋 Total de abas: {len(self.analysis_result['sheets'])}")
        
        print("\n📄 ABAS ENCONTRADAS:")
        for sheet_name, sheet_data in self.analysis_result["sheets"].items():
            structure = sheet_data["structure"]
            print(f"  • {sheet_name}: {structure['rows']} linhas, {structure['columns']} colunas")
            if structure["headers"]:
                print(f"    Cabeçalhos: {', '.join(structure['headers'][:5])}")
        
        print("\n🗺️ MAPEAMENTO DE IMPORTAÇÃO:")
        for category, mapping in self.analysis_result["import_mapping"].items():
            if mapping["sheets"]:
                print(f"  • {category.upper()}: {mapping['description']}")
                print(f"    Abas: {', '.join(mapping['sheets'])}")
        
        print("\n💡 RECOMENDAÇÕES:")
        for rec in self.analysis_result["recommendations"]:
            print(f"  {rec['priority']}. [{rec['category']}] {rec['issue']}")
            print(f"     → {rec['recommendation']}")
        
        print("\n" + "="*80)

def main():
    """Função principal"""
    analyzer = GoogleSheetsAnalyzer()
    
    # Autenticar
    if not analyzer.authenticate():
        return False
    
    # Analisar todas as abas
    if not analyzer.analyze_all_sheets():
        return False
    
    # Gerar mapeamento de importação
    analyzer.generate_import_mapping()
    
    # Salvar análise
    analyzer.save_analysis()
    
    # Imprimir resumo
    analyzer.print_summary()
    
    return True

if __name__ == "__main__":
    main()







