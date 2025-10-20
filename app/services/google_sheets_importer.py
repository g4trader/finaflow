"""
Serviço de importação de dados do Google Sheets
"""

import json
import os
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session
from decimal import Decimal
import logging

from app.database import get_db
from app.models.financial import AccountGroup, AccountSubgroup, Account, Transaction
from app.models.auth import User

logger = logging.getLogger(__name__)

class GoogleSheetsImporter:
    def __init__(self, credentials_path: str = "google_credentials.json"):
        """Inicializar importador com credenciais do Google Sheets"""
        self.credentials_path = credentials_path
        self.service = None
        self.credentials = None
        
    def authenticate(self) -> bool:
        """Autenticar com Google Sheets API"""
        try:
            if not os.path.exists(self.credentials_path):
                logger.error(f"❌ Arquivo de credenciais não encontrado: {self.credentials_path}")
                return False
                
            self.credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
            self.service = build('sheets', 'v4', credentials=self.credentials)
            logger.info("✅ Autenticação com Google Sheets API bem-sucedida")
            return True
        except Exception as e:
            logger.error(f"❌ Erro na autenticação: {e}")
            return False
    
    def import_from_spreadsheet(self, spreadsheet_id: str, tenant_id: str, user_id: str) -> Dict[str, Any]:
        """
        Importar dados de uma planilha Google Sheets
        
        Args:
            spreadsheet_id: ID da planilha Google Sheets
            tenant_id: ID do tenant
            user_id: ID do usuário que está fazendo a importação
            
        Returns:
            Dict com resultado da importação
        """
        if not self.service:
            if not self.authenticate():
                return {"success": False, "error": "Falha na autenticação"}
        
        try:
            # Obter informações da planilha
            spreadsheet_info = self._get_spreadsheet_info(spreadsheet_id)
            if not spreadsheet_info:
                return {"success": False, "error": "Não foi possível obter informações da planilha"}
            
            result = {
                "success": True,
                "spreadsheet_id": spreadsheet_id,
                "spreadsheet_title": spreadsheet_info.get("title", ""),
                "sheets_processed": [],
                "data_imported": {
                    "account_groups": 0,
                    "account_subgroups": 0,
                    "accounts": 0,
                    "transactions": 0
                },
                "errors": []
            }
            
            # Processar cada aba
            for sheet_name in spreadsheet_info.get("sheets", []):
                try:
                    sheet_result = self._process_sheet(spreadsheet_id, sheet_name, tenant_id, user_id)
                    result["sheets_processed"].append(sheet_result)
                    
                    # Somar dados importados
                    if sheet_result.get("success"):
                        for key, value in sheet_result.get("data_imported", {}).items():
                            result["data_imported"][key] += value
                    else:
                        result["errors"].append(f"Aba '{sheet_name}': {sheet_result.get('error', 'Erro desconhecido')}")
                        
                except Exception as e:
                    error_msg = f"Erro ao processar aba '{sheet_name}': {str(e)}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
            
            logger.info(f"✅ Importação concluída: {result['data_imported']}")
            return result
            
        except Exception as e:
            error_msg = f"Erro geral na importação: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def _get_spreadsheet_info(self, spreadsheet_id: str) -> Optional[Dict[str, Any]]:
        """Obter informações básicas da planilha"""
        try:
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            sheets = []
            
            for sheet in spreadsheet.get('sheets', []):
                properties = sheet.get('properties', {})
                sheets.append({
                    'name': properties.get('title', ''),
                    'id': properties.get('sheetId', 0),
                    'row_count': properties.get('gridProperties', {}).get('rowCount', 0),
                    'column_count': properties.get('gridProperties', {}).get('columnCount', 0)
                })
            
            return {
                "title": spreadsheet.get("properties", {}).get("title", ""),
                "sheets": [sheet["name"] for sheet in sheets]
            }
            
        except HttpError as e:
            logger.error(f"❌ Erro ao obter informações da planilha: {e}")
            return None
    
    def _process_sheet(self, spreadsheet_id: str, sheet_name: str, tenant_id: str, user_id: str) -> Dict[str, Any]:
        """Processar uma aba específica da planilha"""
        try:
            # Obter dados da aba
            data = self._get_sheet_data(spreadsheet_id, sheet_name)
            if not data:
                return {"success": False, "error": "Aba vazia ou inacessível"}
            
            # Determinar tipo de aba e processar
            sheet_type = self._determine_sheet_type(sheet_name, data)
            
            result = {
                "sheet_name": sheet_name,
                "sheet_type": sheet_type,
                "success": True,
                "data_imported": {
                    "account_groups": 0,
                    "account_subgroups": 0,
                    "accounts": 0,
                    "transactions": 0
                },
                "error": None
            }
            
            if sheet_type == "account_structure":
                import_result = self._import_account_structure(data, tenant_id, user_id)
            elif sheet_type == "transactions":
                import_result = self._import_transactions(data, tenant_id, user_id)
            elif sheet_type == "cash_flow":
                import_result = self._import_cash_flow(data, tenant_id, user_id, sheet_name)
            else:
                import_result = {"success": False, "error": "Tipo de aba não suportado"}
            
            if import_result.get("success"):
                result["data_imported"] = import_result.get("data_imported", {})
            else:
                result["success"] = False
                result["error"] = import_result.get("error", "Erro desconhecido")
            
            return result
            
        except Exception as e:
            error_msg = f"Erro ao processar aba '{sheet_name}': {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def _get_sheet_data(self, spreadsheet_id: str, sheet_name: str) -> List[List[str]]:
        """Obter dados de uma aba específica"""
        try:
            range_name = f"{sheet_name}!A:Z"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            return result.get('values', [])
            
        except HttpError as e:
            logger.error(f"❌ Erro ao obter dados da aba '{sheet_name}': {e}")
            return []
    
    def _determine_sheet_type(self, sheet_name: str, data: List[List[str]]) -> str:
        """Determinar tipo de aba baseado no nome e dados"""
        sheet_name_lower = sheet_name.lower()
        
        if "plano de contas" in sheet_name_lower or "conta" in sheet_name_lower:
            return "account_structure"
        elif "lançamento" in sheet_name_lower or "movimento" in sheet_name_lower:
            return "transactions"
        elif "fluxo" in sheet_name_lower or "caixa" in sheet_name_lower:
            return "cash_flow"
        elif "resultado" in sheet_name_lower or "dre" in sheet_name_lower:
            return "reports"
        else:
            # Analisar cabeçalhos para determinar tipo
            if data and len(data) > 0:
                headers = [str(h).lower() for h in data[0]]
                if any("conta" in h for h in headers) and any("grupo" in h for h in headers):
                    return "account_structure"
                elif any("data" in h for h in headers) and any("valor" in h for h in headers):
                    return "transactions"
                elif any("fluxo" in h for h in headers):
                    return "cash_flow"
            
            return "unknown"
    
    def _import_account_structure(self, data: List[List[str]], tenant_id: str, user_id: str) -> Dict[str, Any]:
        """Importar estrutura de contas (grupos, subgrupos, contas)"""
        if not data or len(data) < 2:
            return {"success": False, "error": "Dados insuficientes para importar estrutura de contas"}
        
        headers = data[0]
        rows = data[1:]
        
        # Mapear colunas
        column_mapping = self._map_columns(headers, {
            "conta": ["conta", "account"],
            "subgrupo": ["subgrupo", "subgroup"],
            "grupo": ["grupo", "group"],
            "escolha": ["escolha", "choice", "tipo", "type"]
        })
        
        if not all(key in column_mapping for key in ["conta", "subgrupo", "grupo"]):
            return {"success": False, "error": "Colunas obrigatórias não encontradas: Conta, Subgrupo, Grupo"}
        
        db = next(get_db())
        try:
            groups_created = set()
            subgroups_created = set()
            accounts_created = 0
            
            for row in rows:
                if len(row) < len(headers):
                    continue
                
                conta = row[column_mapping["conta"]].strip() if column_mapping["conta"] < len(row) else ""
                subgrupo = row[column_mapping["subgrupo"]].strip() if column_mapping["subgrupo"] < len(row) else ""
                grupo = row[column_mapping["grupo"]].strip() if column_mapping["grupo"] < len(row) else ""
                escolha = row[column_mapping["escolha"]].strip() if column_mapping.get("escolha") and column_mapping["escolha"] < len(row) else ""
                
                if not conta or not subgrupo or not grupo:
                    continue
                
                # Criar grupo se não existir
                group_key = f"{grupo}_{tenant_id}"
                if group_key not in groups_created:
                    existing_group = db.query(AccountGroup).filter(
                        AccountGroup.tenant_id == tenant_id,
                        AccountGroup.name == grupo
                    ).first()
                    
                    if not existing_group:
                        group = AccountGroup(
                            tenant_id=tenant_id,
                            name=grupo,
                            code=f"GRP_{len(groups_created) + 1:03d}",
                            description=f"Grupo: {grupo}"
                        )
                        db.add(group)
                        db.commit()
                        db.refresh(group)
                        groups_created.add(group_key)
                    else:
                        groups_created.add(group_key)
                
                # Criar subgrupo se não existir
                subgroup_key = f"{subgrupo}_{grupo}_{tenant_id}"
                if subgroup_key not in subgroups_created:
                    existing_subgroup = db.query(AccountSubgroup).filter(
                        AccountSubgroup.tenant_id == tenant_id,
                        AccountSubgroup.name == subgrupo
                    ).first()
                    
                    if not existing_subgroup:
                        group = db.query(AccountGroup).filter(
                            AccountGroup.tenant_id == tenant_id,
                            AccountGroup.name == grupo
                        ).first()
                        
                        if group:
                            subgroup = AccountSubgroup(
                                tenant_id=tenant_id,
                                group_id=group.id,
                                name=subgrupo,
                                code=f"SUB_{len(subgroups_created) + 1:03d}",
                                description=f"Subgrupo: {subgrupo}"
                            )
                            db.add(subgroup)
                            db.commit()
                            db.refresh(subgroup)
                            subgroups_created.add(subgroup_key)
                    else:
                        subgroups_created.add(subgroup_key)
                
                # Criar conta específica
                existing_account = db.query(Account).filter(
                    Account.tenant_id == tenant_id,
                    Account.name == conta
                ).first()
                
                if not existing_account:
                    subgroup = db.query(AccountSubgroup).filter(
                        AccountSubgroup.tenant_id == tenant_id,
                        AccountSubgroup.name == subgrupo
                    ).first()
                    
                    if subgroup:
                        account_type = self._determine_account_type(grupo, subgrupo, conta, escolha)
                        account = Account(
                            tenant_id=tenant_id,
                            subgroup_id=subgroup.id,
                            name=conta,
                            code=f"ACC_{accounts_created + 1:03d}",
                            account_type=account_type,
                            description=f"Conta: {conta}"
                        )
                        db.add(account)
                        accounts_created += 1
            
            db.commit()
            
            return {
                "success": True,
                "data_imported": {
                    "account_groups": len(groups_created),
                    "account_subgroups": len(subgroups_created),
                    "accounts": accounts_created,
                    "transactions": 0
                }
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Erro ao importar estrutura de contas: {e}")
            return {"success": False, "error": str(e)}
        finally:
            db.close()
    
    def _import_transactions(self, data: List[List[str]], tenant_id: str, user_id: str) -> Dict[str, Any]:
        """Importar transações financeiras"""
        if not data or len(data) < 2:
            return {"success": False, "error": "Dados insuficientes para importar transações"}
        
        headers = data[0]
        rows = data[1:]
        
        # Mapear colunas
        column_mapping = self._map_columns(headers, {
            "data": ["data", "date", "data movimentação"],
            "descricao": ["descrição", "description", "desc"],
            "conta": ["conta", "account"],
            "subgrupo": ["subgrupo", "subgroup"],
            "grupo": ["grupo", "group"],
            "valor": ["valor", "value", "amount"]
        })
        
        if not all(key in column_mapping for key in ["data", "valor"]):
            return {"success": False, "error": "Colunas obrigatórias não encontradas: Data, Valor"}
        
        db = next(get_db())
        try:
            transactions_created = 0
            
            for row in rows:
                if len(row) < len(headers):
                    continue
                
                # Extrair dados da linha
                data_str = row[column_mapping["data"]].strip() if column_mapping["data"] < len(row) else ""
                valor_str = row[column_mapping["valor"]].strip() if column_mapping["valor"] < len(row) else ""
                descricao = row[column_mapping["descricao"]].strip() if column_mapping.get("descricao") and column_mapping["descricao"] < len(row) else ""
                
                if not data_str or not valor_str:
                    continue
                
                # Converter data
                try:
                    transaction_date = self._parse_date(data_str)
                except:
                    continue
                
                # Converter valor
                try:
                    amount = self._parse_amount(valor_str)
                except:
                    continue
                
                # Encontrar conta
                account = None
                if column_mapping.get("conta"):
                    conta_name = row[column_mapping["conta"]].strip() if column_mapping["conta"] < len(row) else ""
                    if conta_name:
                        account = db.query(Account).filter(
                            Account.tenant_id == tenant_id,
                            Account.name.ilike(f"%{conta_name}%")
                        ).first()
                
                if not account and column_mapping.get("subgrupo"):
                    subgrupo_name = row[column_mapping["subgrupo"]].strip() if column_mapping["subgrupo"] < len(row) else ""
                    if subgrupo_name:
                        subgroup = db.query(AccountSubgroup).filter(
                            AccountSubgroup.tenant_id == tenant_id,
                            AccountSubgroup.name.ilike(f"%{subgrupo_name}%")
                        ).first()
                        if subgroup:
                            account = db.query(Account).filter(
                                Account.tenant_id == tenant_id,
                                Account.subgroup_id == subgroup.id
                            ).first()
                
                if not account:
                    continue
                
                # Criar transação
                transaction_type = "credit" if amount > 0 else "debit"
                transaction = Transaction(
                    tenant_id=tenant_id,
                    account_id=account.id,
                    transaction_date=transaction_date,
                    description=descricao or f"Transação importada - {account.name}",
                    amount=abs(amount),
                    transaction_type=transaction_type,
                    created_by=user_id,
                    is_approved=True
                )
                db.add(transaction)
                transactions_created += 1
            
            db.commit()
            
            return {
                "success": True,
                "data_imported": {
                    "account_groups": 0,
                    "account_subgroups": 0,
                    "accounts": 0,
                    "transactions": transactions_created
                }
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Erro ao importar transações: {e}")
            return {"success": False, "error": str(e)}
        finally:
            db.close()
    
    def _import_cash_flow(self, data: List[List[str]], tenant_id: str, user_id: str, sheet_name: str) -> Dict[str, Any]:
        """Importar dados de fluxo de caixa"""
        # Por enquanto, apenas log dos dados de fluxo de caixa
        logger.info(f"📊 Dados de fluxo de caixa encontrados na aba '{sheet_name}': {len(data)} linhas")
        
        return {
            "success": True,
            "data_imported": {
                "account_groups": 0,
                "account_subgroups": 0,
                "accounts": 0,
                "transactions": 0
            }
        }
    
    def _map_columns(self, headers: List[str], mapping: Dict[str, List[str]]) -> Dict[str, int]:
        """Mapear nomes de colunas para índices"""
        column_mapping = {}
        
        for key, possible_names in mapping.items():
            for i, header in enumerate(headers):
                header_lower = str(header).lower().strip()
                if any(name.lower() in header_lower for name in possible_names):
                    column_mapping[key] = i
                    break
        
        return column_mapping
    
    def _determine_account_type(self, grupo: str, subgrupo: str, conta: str, escolha: str) -> str:
        """Determinar tipo de conta baseado nas informações"""
        grupo_lower = grupo.lower()
        subgrupo_lower = subgrupo.lower()
        conta_lower = conta.lower()
        
        if "receita" in grupo_lower or "receita" in subgrupo_lower or "venda" in conta_lower:
            return "revenue"
        elif "despesa" in grupo_lower or "despesa" in subgrupo_lower or "custo" in subgrupo_lower:
            return "expense"
        elif "ativo" in grupo_lower or "caixa" in conta_lower or "banco" in conta_lower:
            return "asset"
        elif "passivo" in grupo_lower or "dívida" in conta_lower or "emprestimo" in conta_lower:
            return "liability"
        else:
            return "expense"  # Default
    
    def _parse_date(self, date_str: str) -> date:
        """Converter string de data para objeto date"""
        date_str = date_str.strip()
        
        # Tentar diferentes formatos
        formats = [
            "%d/%m/%Y",
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d-%m-%Y"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        # Se não conseguir converter, usar data atual
        return date.today()
    
    def _parse_amount(self, amount_str: str) -> Decimal:
        """Converter string de valor monetário para Decimal"""
        amount_str = amount_str.strip()
        
        # Remover formatação brasileira
        amount_str = amount_str.replace("R$", "").replace(" ", "")
        
        # Se tem ponto e vírgula (formato brasileiro: 1.234,56)
        if "," in amount_str and "." in amount_str:
            # Separar parte inteira e decimal
            parts = amount_str.split(",")
            integer_part = parts[0].replace(".", "")
            decimal_part = parts[1]
            amount_str = f"{integer_part}.{decimal_part}"
        elif "," in amount_str:
            # Apenas vírgula (1,56 ou 1234,56)
            amount_str = amount_str.replace(",", ".")
        
        try:
            return Decimal(amount_str)
        except:
            return Decimal("0")

# Instância global do importador
google_sheets_importer = GoogleSheetsImporter()







