"""
Importador específico para a planilha LLM Lavanderia
Importa: Plano de Contas, Lançamentos Diários, Previsões
"""

import json
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any
from google.oauth2 import service_account
from googleapiclient.discovery import build
from sqlalchemy.orm import Session
import re

class LLMSheetImporter:
    def __init__(self, credentials_path="google_credentials.json"):
        """Inicializar importador"""
        self.credentials_path = credentials_path
        self.service = None
        
    def authenticate(self):
        """Autenticar com Google Sheets API"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
            self.service = build('sheets', 'v4', credentials=credentials)
            return True
        except Exception as e:
            print(f"[IMPORT ERROR] Auth failed: {str(e)}")
            return False
    
    def import_complete_data(self, spreadsheet_id: str, tenant_id, business_unit_id, db: Session, user_id=None):
        """
        Importar TODOS os dados da planilha LLM
        
        Importa:
        1. Plano de Contas (já existe)
        2. Lançamentos Diários (transações reais)
        3. Lançamentos Previstos (previsões)
        """
        if not self.service:
            if not self.authenticate():
                return {"success": False, "error": "Falha na autenticação"}
        
        result = {
            "success": True,
            "data_imported": {
                "chart_accounts": 0,
                "daily_transactions": 0,
                "forecasts": 0
            },
            "errors": []
        }
        
        try:
            # 1. Importar Lançamentos Diários (Aba 6)
            print("[IMPORT] Importando Lançamento Diário...")
            daily_result = self._import_daily_transactions(
                spreadsheet_id, 
                "Lançamento Diário",
                tenant_id,
                business_unit_id,
                db,
                user_id
            )
            
            if daily_result.get("success"):
                result["data_imported"]["daily_transactions"] = daily_result.get("count", 0)
                print(f"[IMPORT] ✅ {daily_result.get('count', 0)} lançamentos diários importados")
            else:
                result["errors"].append(f"Lançamentos: {daily_result.get('error')}")
            
            # 2. Importar Lançamentos Previstos (Aba 4)
            print("[IMPORT] Importando Lançamentos Previstos...")
            forecast_result = self._import_forecast_transactions(
                spreadsheet_id,
                "Lançamentos Previstos",
                tenant_id,
                business_unit_id,
                db
            )
            
            if forecast_result.get("success"):
                result["data_imported"]["forecasts"] = forecast_result.get("count", 0)
                print(f"[IMPORT] ✅ {forecast_result.get('count', 0)} previsões importadas")
            else:
                result["errors"].append(f"Previsões: {forecast_result.get('error')}")
            
            return result
            
        except Exception as e:
            print(f"[IMPORT ERROR] {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _import_daily_transactions(self, spreadsheet_id, sheet_name, tenant_id, business_unit_id, db, user_id=None):
        """Importar lançamentos diários"""
        try:
            # Obter dados da aba - ler mais colunas para pegar a coluna F (valor)
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=f"'{sheet_name}'!A:Z"  # Até coluna Z para garantir que pegue a coluna F
            ).execute()
            
            values = result.get('values', [])
            
            if not values or len(values) < 2:
                return {"success": False, "error": "Aba vazia"}
            
            headers = values[0]
            rows = values[1:]
            
            print(f"[IMPORT] Encontradas {len(rows)} linhas de lançamentos")
            print(f"[IMPORT] Cabeçalhos: {headers[:8]}")
            
            # Mapear colunas baseado na estrutura real da planilha LLM
            # B: Data Movimentação, C: Conta, D: Subgrupo, E: Grupo, F: Valor, G: Código, H: Observação
            col_data = self._find_column(headers, ["data movimentação", "data", "date"])
            col_conta = self._find_column(headers, ["conta", "account"])
            col_subgrupo = self._find_column(headers, ["subgrupo", "subgroup"])
            col_grupo = self._find_column(headers, ["grupo", "group"])
            
            # Corrigir mapeamento - se grupo e subgrupo estão na mesma posição, ajustar
            if col_grupo == col_subgrupo and col_subgrupo is not None:
                col_grupo = col_subgrupo + 1  # Próxima coluna
                print(f"[IMPORT] Corrigindo mapeamento: grupo={col_grupo}")
            col_valor = self._find_column(headers, ["valor", "value", "amount"])
            
            # Se não encontrou coluna de valor por nome, usar posição fixa (coluna F = índice 5)
            if col_valor is None:
                col_valor = 5  # Coluna F (índice 5)
                print(f"[IMPORT] Usando coluna F (índice 5) como valor (sem header)")
            col_observacao = self._find_column(headers, ["observação", "observacao", "description", "descrição"])
            
            print(f"[IMPORT] Estrutura real detectada:")
            print(f"[IMPORT] Headers: {headers}")
            print(f"[IMPORT] Mapeamento: data={col_data}, conta={col_conta}, subgrupo={col_subgrupo}, grupo={col_grupo}, valor={col_valor}")
            
            # Verificar se encontrou as colunas essenciais
            if col_data is None:
                return {"success": False, "error": "Coluna 'Data Movimentação' não encontrada"}
            if col_valor is None:
                return {"success": False, "error": "Coluna de valor não encontrada"}
            if col_conta is None:
                return {"success": False, "error": "Coluna 'Conta' não encontrada"}
            
            # Importar lançamentos diários
            from app.models.lancamento_diario import LancamentoDiario, TransactionType, TransactionStatus
            from app.models.chart_of_accounts import ChartAccount, ChartAccountSubgroup, ChartAccountGroup
            
            transactions_created = 0
            
            for row in rows:
                if len(row) <= max(filter(lambda x: x is not None, [col_data, col_valor, col_conta or 0])):
                    continue
                
                # Extrair dados da linha
                data_str = row[col_data].strip() if col_data < len(row) and row[col_data] else ""
                valor_str = row[col_valor].strip() if col_valor < len(row) and row[col_valor] else ""
                conta_name = row[col_conta].strip() if col_conta is not None and col_conta < len(row) and row[col_conta] else ""
                
                if not data_str or not valor_str or not conta_name:
                    continue
                
                # Parsear data
                transaction_date = self._parse_date(data_str)
                if not transaction_date:
                    continue
                
                # Parsear valor
                amount = self._parse_amount(valor_str)
                if amount == 0:
                    continue
                
                # Buscar conta por nome
                import uuid
                tenant_uuid = uuid.UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id
                
                # Buscar conta por nome exato primeiro
                account = db.query(ChartAccount).filter(
                    ChartAccount.name == conta_name,
                    (ChartAccount.tenant_id == tenant_uuid) | (ChartAccount.tenant_id == None)
                ).first()
                
                # Se não encontrou por nome exato, buscar por similaridade
                if not account:
                    account = db.query(ChartAccount).filter(
                        ChartAccount.name.ilike(f"%{conta_name}%"),
                        (ChartAccount.tenant_id == tenant_uuid) | (ChartAccount.tenant_id == None)
                    ).first()
                
                if not account:
                    # Tentar buscar por subgrupo
                    if col_subgrupo is not None and col_subgrupo < len(row) and row[col_subgrupo]:
                        subgrupo_name = row[col_subgrupo].strip()
                        
                        from app.models.chart_of_accounts import ChartAccountSubgroup
                        subgroup = db.query(ChartAccountSubgroup).filter(
                            ChartAccountSubgroup.name.ilike(f"%{subgrupo_name}%"),
                            (ChartAccountSubgroup.tenant_id == tenant_uuid) | (ChartAccountSubgroup.tenant_id == None)
                        ).first()
                        
                        if subgroup:
                            account = db.query(ChartAccount).filter(
                                ChartAccount.subgroup_id == subgroup.id,
                                (ChartAccount.tenant_id == tenant_uuid) | (ChartAccount.tenant_id == None)
                            ).first()
                
                if not account:
                    # Usar primeira conta do tenant como fallback
                    account = db.query(ChartAccount).filter(
                        ChartAccount.tenant_id == tenant_uuid
                    ).first()
                
                if not account:
                    continue
                
                # Descrição/observação
                descricao = ""
                if col_observacao is not None and col_observacao < len(row) and row[col_observacao]:
                    descricao = row[col_observacao].strip()
                
                if not descricao:
                    descricao = f"Lançamento - {conta_name}"
                
                # Criar lançamento diário
                from app.models.lancamento_diario import LancamentoDiario
                
                # Determinar tipo baseado no nome do grupo e subgrupo com lógica completa
                transaction_type_enum = TransactionType.DESPESA  # Default
                
                if account.subgroup and account.subgroup.group:
                    grupo_nome = account.subgroup.group.name.lower()
                    subgrupo_nome = account.subgroup.name.lower()
                    
                    # Lógica melhorada de classificação (mesmo do endpoint POST)
                    if any(keyword in grupo_nome for keyword in ['receita', 'venda', 'renda', 'faturamento', 'vendas']):
                        transaction_type_enum = TransactionType.RECEITA
                    elif any(keyword in grupo_nome for keyword in ['custo', 'custos']) or any(keyword in subgrupo_nome for keyword in ['custo', 'custos', 'mercadoria', 'produto']):
                        transaction_type_enum = TransactionType.CUSTO
                    elif any(keyword in grupo_nome for keyword in ['despesa', 'gasto', 'operacional', 'administrativa']) or any(keyword in subgrupo_nome for keyword in ['despesa', 'gasto', 'marketing', 'administrativa']):
                        transaction_type_enum = TransactionType.DESPESA
                    else:
                        # Default baseado em palavras-chave mais específicas
                        if any(keyword in grupo_nome for keyword in ['ativo', 'passivo', 'patrimonio']):
                            transaction_type_enum = TransactionType.DESPESA
                        else:
                            transaction_type_enum = TransactionType.DESPESA
                
                # Verificar se já existe (evitar duplicatas)
                # Converter para string pois colunas são VARCHAR no banco
                existing = db.query(LancamentoDiario).filter(
                    LancamentoDiario.data_movimentacao == transaction_date,
                    LancamentoDiario.conta_id == account.id,
                    LancamentoDiario.valor == abs(amount),
                    LancamentoDiario.tenant_id == str(tenant_uuid),
                    LancamentoDiario.business_unit_id == str(business_unit_id)
                ).first()
                
                if not existing:
                    lancamento = LancamentoDiario(
                        tenant_id=str(tenant_uuid),
                        business_unit_id=str(business_unit_id),
                        conta_id=account.id,
                        subgrupo_id=account.subgroup_id,
                        grupo_id=account.subgroup.group_id if account.subgroup else None,
                        data_movimentacao=transaction_date,
                        valor=abs(amount),
                        observacoes=descricao or f"Importado - {account.name}",
                        transaction_type=transaction_type_enum,
                        status=TransactionStatus.PENDENTE,
                        created_by=user_id
                    )
                    db.add(lancamento)
                    transactions_created += 1
                    
                    # Commit a cada 100 transações para evitar timeout
                    if transactions_created % 100 == 0:
                        db.commit()
                        print(f"[IMPORT] Progresso: {transactions_created} transações...")
            
            # Commit final
            db.commit()
            print(f"[IMPORT] ✅ Total: {transactions_created} transações importadas")
            
            return {"success": True, "count": transactions_created}
            
        except Exception as e:
            db.rollback()
            print(f"[IMPORT ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    def _import_forecast_transactions(self, spreadsheet_id, sheet_name, tenant_id, business_unit_id, db, user_id=None):
        """Importar lançamentos previstos (previsões)"""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=f"'{sheet_name}'!A:Z"
            ).execute()
            
            values = result.get('values', [])
            
            if not values or len(values) < 2:
                return {"success": False, "error": "Aba vazia"}
            
            headers = values[0]
            rows = values[1:]
            
            print(f"[IMPORT PREVISÕES] Encontradas {len(rows)} linhas")
            print(f"[IMPORT PREVISÕES] Cabeçalhos: {headers[:8]}")
            
            # Mapear colunas baseado na estrutura real da planilha
            # A: Ano/Mês, B: Mês, C: Conta, D: Subgrupo, E: Grupo, F: Valor, H: DESCRIÇÃO
            col_data = self._find_column(headers, ["mês", "mes", "data", "date"])
            if col_data is None:
                col_data = 1  # Coluna B (Mês)
            
            col_conta = self._find_column(headers, ["conta", "account"])
            if col_conta is None:
                col_conta = 2  # Coluna C
            
            col_subgrupo = self._find_column(headers, ["subgrupo", "subgroup"])
            if col_subgrupo is None:
                col_subgrupo = 3  # Coluna D
            
            col_grupo = self._find_column(headers, ["grupo", "group"])
            if col_grupo is None:
                col_grupo = 4  # Coluna E
            
            col_valor = self._find_column(headers, ["valor", "value", "amount"])
            if col_valor is None:
                col_valor = 5  # Coluna F
            
            col_observacao = self._find_column(headers, ["descrição", "descricao", "description"])
            if col_observacao is None:
                col_observacao = 7  # Coluna H
            
            print(f"[IMPORT PREVISÕES] Mapeamento: data={col_data}(B), conta={col_conta}(C), subgrupo={col_subgrupo}(D), grupo={col_grupo}(E), valor={col_valor}(F), obs={col_observacao}(H)")
            
            if col_data is None or col_valor is None or col_conta is None:
                return {"success": False, "error": "Colunas obrigatórias não encontradas"}
            
            # Importar previsões
            from app.models.lancamento_previsto import LancamentoPrevisto, TransactionType, TransactionStatus
            from app.models.chart_of_accounts import ChartAccount, ChartAccountSubgroup, ChartAccountGroup
            
            forecasts_created = 0
            import uuid
            tenant_uuid = uuid.UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id
            
            for row in rows:
                if len(row) <= max(filter(lambda x: x is not None, [col_data, col_valor, col_conta or 0])):
                    continue
                
                # Extrair dados
                data_str = row[col_data].strip() if col_data < len(row) and row[col_data] else ""
                valor_str = row[col_valor].strip() if col_valor < len(row) and row[col_valor] else ""
                conta_name = row[col_conta].strip() if col_conta is not None and col_conta < len(row) and row[col_conta] else ""
                
                if not data_str or not valor_str or not conta_name:
                    continue
                
                # Parsear
                forecast_date = self._parse_date(data_str)
                if not forecast_date:
                    continue
                
                amount = self._parse_amount(valor_str)
                if amount == 0:
                    continue
                
                # Buscar conta
                account = db.query(ChartAccount).filter(
                    ChartAccount.name == conta_name,
                    (ChartAccount.tenant_id == tenant_uuid) | (ChartAccount.tenant_id == None)
                ).first()
                
                if not account:
                    account = db.query(ChartAccount).filter(
                        ChartAccount.name.ilike(f"%{conta_name}%"),
                        (ChartAccount.tenant_id == tenant_uuid) | (ChartAccount.tenant_id == None)
                    ).first()
                
                if not account or not account.subgroup or not account.subgroup.group:
                    continue
                
                # Descrição
                descricao = ""
                if col_observacao is not None and col_observacao < len(row) and row[col_observacao]:
                    descricao = row[col_observacao].strip()
                if not descricao:
                    descricao = f"Previsão - {conta_name}"
                
                # Determinar tipo (mesma lógica dos lançamentos diários)
                grupo_nome = account.subgroup.group.name.lower()
                subgrupo_nome = account.subgroup.name.lower()
                
                if any(keyword in grupo_nome for keyword in ['receita', 'venda', 'renda', 'faturamento', 'vendas']):
                    transaction_type_enum = TransactionType.RECEITA
                elif any(keyword in grupo_nome for keyword in ['custo', 'custos']) or any(keyword in subgrupo_nome for keyword in ['custo', 'custos', 'mercadoria', 'produto']):
                    transaction_type_enum = TransactionType.CUSTO
                elif any(keyword in grupo_nome for keyword in ['despesa', 'gasto', 'operacional', 'administrativa']) or any(keyword in subgrupo_nome for keyword in ['despesa', 'gasto', 'marketing', 'administrativa']):
                    transaction_type_enum = TransactionType.DESPESA
                else:
                    transaction_type_enum = TransactionType.DESPESA
                
                # Verificar se já existe
                existing = db.query(LancamentoPrevisto).filter(
                    LancamentoPrevisto.data_prevista == forecast_date,
                    LancamentoPrevisto.conta_id == account.id,
                    LancamentoPrevisto.valor == abs(amount),
                    LancamentoPrevisto.tenant_id == str(tenant_uuid),
                    LancamentoPrevisto.business_unit_id == str(business_unit_id)
                ).first()
                
                if not existing:
                    previsao = LancamentoPrevisto(
                        tenant_id=str(tenant_uuid),
                        business_unit_id=str(business_unit_id),
                        conta_id=account.id,
                        subgrupo_id=account.subgroup_id,
                        grupo_id=account.subgroup.group_id,
                        data_prevista=forecast_date,
                        valor=abs(amount),
                        observacoes=descricao,
                        transaction_type=transaction_type_enum,
                        status=TransactionStatus.PENDENTE,
                        created_by=user_id
                    )
                    db.add(previsao)
                    forecasts_created += 1
                    
                    if forecasts_created % 100 == 0:
                        db.commit()
                        print(f"[IMPORT PREVISÕES] Progresso: {forecasts_created}...")
            
            db.commit()
            print(f"[IMPORT PREVISÕES] ✅ Total: {forecasts_created} importadas")
            
            return {"success": True, "count": forecasts_created}
            
        except Exception as e:
            db.rollback()
            print(f"[IMPORT ERROR] {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _find_column(self, headers, possible_names):
        """Encontrar índice da coluna baseado em nomes possíveis"""
        for idx, header in enumerate(headers):
            header_lower = str(header).lower().strip()
            for name in possible_names:
                if name.lower() in header_lower:
                    return idx
        return None
    
    def _parse_date(self, date_str):
        """Parsear data em vários formatos"""
        if not date_str:
            return None
        
        date_str = str(date_str).strip()
        
        # Formatos possíveis
        formats = [
            "%d/%m/%Y",
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%m/%d/%Y",
            "%d/%m/%y",
            "%Y/%m/%d"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except:
                continue
        
        return None
    
    def _parse_amount(self, amount_str):
        """Parsear valor monetário"""
        if not amount_str:
            return Decimal("0")
        
        amount_str = str(amount_str).strip()
        
        # Remover formatação
        amount_str = amount_str.replace("R$", "").replace(" ", "")
        
        # Detectar sinal negativo
        is_negative = "-" in amount_str or "(" in amount_str
        amount_str = amount_str.replace("-", "").replace("(", "").replace(")", "")
        
        # Formato brasileiro: 1.234,56
        if "," in amount_str:
            amount_str = amount_str.replace(".", "").replace(",", ".")
        
        try:
            value = Decimal(amount_str)
            return -value if is_negative else value
        except:
            return Decimal("0")

# Instância global
llm_importer = LLMSheetImporter()

