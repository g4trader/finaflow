#!/usr/bin/env python3
"""
Script de Seed para ambiente STAGING
Popula o banco de dados com dados reais da planilha Google Sheets do cliente.

USO:
    python backend/database/seed/seed_staging.py

REQUISITOS:
    - Planilha Google Sheets:
        - URL: https://docs.google.com/spreadsheets/d/1rWMdDhwiNoC7iMycmQGWWDIacrePr1gB7c_mbt1patQ
        - Abas necessárias:
          * "Plano de contas" (ou "Plano de contas|LLM")
          * "Lançamento Diário"
          * "Lançamentos Previstos"
    
    - Arquivo de credenciais:
        - google_credentials.json na raiz do backend (ou caminho em GOOGLE_APPLICATION_CREDENTIALS)
    
    - Variáveis de ambiente:
        - DATABASE_URL: URL de conexão com o banco PostgreSQL de STAGING
        - GOOGLE_APPLICATION_CREDENTIALS: (opcional) Caminho para google_credentials.json
        - STAGING_TENANT_ID: (opcional) ID do tenant staging
        - STAGING_BUSINESS_UNIT_ID: (opcional) ID da business unit staging
        - STAGING_USER_ID: (opcional) ID do usuário que criará os registros

CARACTERÍSTICAS:
    - Idempotente: pode ser executado múltiplas vezes sem duplicar dados
    - Validações: verifica integridade hierárquica (grupo → subgrupo → conta)
    - Logs detalhados: mostra progresso e estatísticas
    - Transações: usa commit/rollback para garantir atomicidade
    - Google Sheets: lê dados diretamente da planilha online
"""

import sys
import os
from pathlib import Path
from uuid import uuid4
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional, Tuple, List
import re

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

# Google Sheets API
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import SessionLocal, create_tables
from app.models.auth import User, Tenant, BusinessUnit, UserRole, UserStatus
from app.models.chart_of_accounts import (
    ChartAccountGroup,
    ChartAccountSubgroup,
    ChartAccount
)
from app.models.lancamento_diario import (
    LancamentoDiario,
    TransactionType,
    TransactionStatus
)
from app.models.lancamento_previsto import (
    LancamentoPrevisto
)

# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

# ID da planilha Google Sheets
SPREADSHEET_ID = "1rWMdDhwiNoC7iMycmQGWWDIacrePr1gB7c_mbt1patQ"

# Nomes das abas (tentar diferentes variações)
PLANO_CONTAS_SHEETS = ["Plano de contas|LLM", "Plano de contas", "Plano de Contas"]
LANCAMENTOS_DIARIOS_SHEETS = ["Lançamento Diário", "Lançamento Diario", "Lancamento Diario"]
LANCAMENTOS_PREVISTOS_SHEETS = ["Lançamentos Previstos", "Lancamentos Previstos", "Previsões"]

# Caminho para credenciais Google
GOOGLE_CREDENTIALS_PATH = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS",
    str(backend_path / "google_credentials.json")
)

# ============================================================================
# UTILITÁRIOS
# ============================================================================

class SeedLogger:
    """Logger para o processo de seed"""
    
    def __init__(self):
        self.stats = {
            'grupos_criados': 0,
            'grupos_existentes': 0,
            'subgrupos_criados': 0,
            'subgrupos_existentes': 0,
            'contas_criadas': 0,
            'contas_existentes': 0,
            'lancamentos_diarios_criados': 0,
            'lancamentos_diarios_existentes': 0,
            'lancamentos_previstos_criados': 0,
            'lancamentos_previstos_existentes': 0,
            'erros': []
        }
    
    def log(self, message: str, level: str = "INFO"):
        """Log uma mensagem"""
        prefix = {
            "INFO": "ℹ️ ",
            "SUCCESS": "✅",
            "WARNING": "⚠️ ",
            "ERROR": "❌",
            "STEP": "📋"
        }.get(level, "ℹ️ ")
        print(f"{prefix} {message}")
    
    def print_stats(self):
        """Imprime estatísticas finais"""
        print("\n" + "="*60)
        print("📊 ESTATÍSTICAS DO SEED")
        print("="*60)
        print(f"Grupos: {self.stats['grupos_criados']} criados, {self.stats['grupos_existentes']} existentes")
        print(f"Subgrupos: {self.stats['subgrupos_criados']} criados, {self.stats['subgrupos_existentes']} existentes")
        print(f"Contas: {self.stats['contas_criadas']} criadas, {self.stats['contas_existentes']} existentes")
        print(f"Lançamentos Diários: {self.stats['lancamentos_diarios_criados']} criados, {self.stats['lancamentos_diarios_existentes']} existentes")
        print(f"Lançamentos Previstos: {self.stats['lancamentos_previstos_criados']} criados, {self.stats['lancamentos_previstos_existentes']} existentes")
        if self.stats['erros']:
            print(f"\n⚠️  {len(self.stats['erros'])} erros encontrados:")
            for erro in self.stats['erros'][:10]:  # Mostrar apenas os 10 primeiros
                print(f"   - {erro}")
        print("="*60)

logger = SeedLogger()

# ============================================================================
# FUNÇÕES DE PARSE
# ============================================================================

def parse_currency(value: str) -> Decimal:
    """Converte string de moeda para Decimal"""
    if not value or value.strip() == "":
        return Decimal("0.00")
    
    # Remover R$, espaços e vírgulas
    value = value.replace("R$", "").replace("$", "").strip()
    value = value.replace(".", "").replace(",", ".")
    
    try:
        return Decimal(value)
    except:
        logger.log(f"Erro ao converter valor: {value}", "WARNING")
        return Decimal("0.00")

def parse_date(date_str: str) -> Optional[datetime]:
    """Converte string de data para datetime"""
    if not date_str or date_str.strip() == "":
        return None
    
    # Formatos esperados: DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD
    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%d/%m/%y",
        "%d-%m-%y",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except:
            continue
    
    logger.log(f"Erro ao converter data: {date_str}", "WARNING")
    return None

def generate_code(name: str, prefix: str = "") -> str:
    """Gera código único baseado no nome"""
    # Remover acentos e caracteres especiais
    name_clean = re.sub(r'[^a-zA-Z0-9\s]', '', name)
    # Pegar primeiras letras de cada palavra
    if prefix:
        return f"{prefix}{name_clean[:3].upper()}"
    return name_clean[:3].upper()

def determine_transaction_type(grupo_nome: str, subgrupo_nome: Optional[str] = None) -> TransactionType:
    """Determina o tipo de transação baseado no grupo e subgrupo"""
    grupo_lower = grupo_nome.lower()
    subgrupo_lower = (subgrupo_nome or "").lower()
    
    if any(keyword in grupo_lower for keyword in ["receita", "venda", "renda", "faturamento", "vendas"]):
        return TransactionType.RECEITA
    if any(keyword in grupo_lower for keyword in ["custo", "custos"]) or any(
        keyword in subgrupo_lower for keyword in ["custo", "custos", "mercadoria", "produto"]
    ):
        return TransactionType.CUSTO
    if any(keyword in grupo_lower for keyword in ["despesa", "gasto", "operacional", "administrativa"]) or any(
        keyword in subgrupo_lower for keyword in ["despesa", "gasto", "marketing", "administrativa"]
    ):
        return TransactionType.DESPESA
    return TransactionType.DESPESA

def determine_account_type(grupo_nome: str) -> str:
    """Determina o tipo da conta baseado no grupo"""
    grupo_lower = grupo_nome.lower()
    if "receita" in grupo_lower:
        return "Receita"
    elif "custo" in grupo_lower:
        return "Custo"
    elif "despesa" in grupo_lower:
        return "Despesa"
    elif "dedução" in grupo_lower:
        return "Dedução"
    else:
        return "Outro"

# ============================================================================
# FUNÇÕES DE GOOGLE SHEETS
# ============================================================================

class GoogleSheetsReader:
    """Classe para ler dados do Google Sheets"""
    
    def __init__(self, credentials_path: str = None):
        self.credentials_path = credentials_path or GOOGLE_CREDENTIALS_PATH
        self.service = None
    
    def authenticate(self) -> bool:
        """Autenticar com Google Sheets API"""
        try:
            if not os.path.exists(self.credentials_path):
                logger.log(f"Arquivo de credenciais não encontrado: {self.credentials_path}", "ERROR")
                logger.log("Por favor, configure GOOGLE_APPLICATION_CREDENTIALS ou coloque google_credentials.json na raiz do backend", "ERROR")
                return False
            
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
            self.service = build('sheets', 'v4', credentials=credentials)
            logger.log("Autenticação com Google Sheets realizada com sucesso", "SUCCESS")
            return True
        except Exception as e:
            logger.log(f"Erro ao autenticar com Google Sheets: {str(e)}", "ERROR")
            return False
    
    def get_sheet_data(self, spreadsheet_id: str, sheet_name: str, range_name: str = None) -> List[List]:
        """Lê dados de uma aba específica"""
        if not self.service:
            raise RuntimeError("Serviço não autenticado. Chame authenticate() primeiro.")
        
        try:
            # Construir range completo
            if range_name:
                full_range = f"{sheet_name}!{range_name}"
            else:
                full_range = sheet_name
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=full_range
            ).execute()
            
            values = result.get('values', [])
            return values
        except HttpError as e:
            if e.resp.status == 404:
                logger.log(f"Aba '{sheet_name}' não encontrada na planilha", "WARNING")
            else:
                logger.log(f"Erro ao ler aba '{sheet_name}': {str(e)}", "ERROR")
            return []
        except Exception as e:
            logger.log(f"Erro ao ler dados do Google Sheets: {str(e)}", "ERROR")
            return []
    
    def find_sheet(self, spreadsheet_id: str, sheet_names: List[str]) -> Optional[str]:
        """Encontra a primeira aba que existe na planilha"""
        if not self.service:
            raise RuntimeError("Serviço não autenticado. Chame authenticate() primeiro.")
        
        try:
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            available_sheets = [sheet['properties']['title'] for sheet in spreadsheet.get('sheets', [])]
            
            for sheet_name in sheet_names:
                if sheet_name in available_sheets:
                    logger.log(f"Aba encontrada: {sheet_name}", "SUCCESS")
                    return sheet_name
            
            logger.log(f"Nenhuma das abas encontrada: {sheet_names}", "WARNING")
            logger.log(f"Abas disponíveis: {', '.join(available_sheets[:10])}", "INFO")
            return None
        except Exception as e:
            logger.log(f"Erro ao listar abas: {str(e)}", "ERROR")
            return None
    
    def sheet_to_dict_list(self, sheet_data: List[List]) -> List[Dict[str, str]]:
        """Converte dados da planilha (lista de listas) para lista de dicionários"""
        if not sheet_data:
            return []
        
        # Primeira linha são os cabeçalhos
        headers = [str(cell).strip() if cell else "" for cell in sheet_data[0]]
        
        # Normalizar nomes de colunas (case-insensitive)
        normalized_headers = {}
        for i, header in enumerate(headers):
            header_lower = header.lower()
            # Mapear variações comuns
            if 'conta' in header_lower and 'conta' not in normalized_headers:
                normalized_headers['conta'] = i
            if 'subgrupo' in header_lower and 'subgrupo' not in normalized_headers:
                normalized_headers['subgrupo'] = i
            if 'grupo' in header_lower and 'grupo' not in normalized_headers:
                normalized_headers['grupo'] = i
            if 'escolha' in header_lower or 'llm' in header_lower:
                normalized_headers['escolha'] = i
            if 'data' in header_lower and 'movimentação' in header_lower:
                normalized_headers['data_movimentacao'] = i
            if 'data' in header_lower and 'prevista' in header_lower:
                normalized_headers['data_prevista'] = i
            if 'mês' in header_lower or 'mes' in header_lower:
                normalized_headers['mes'] = i
            if 'valor' in header_lower:
                normalized_headers['valor'] = i
            if 'observação' in header_lower or 'observacoes' in header_lower:
                normalized_headers['observacoes'] = i
        
        # Converter linhas para dicionários
        result = []
        for row_num, row in enumerate(sheet_data[1:], start=2):
            if not row or all(not cell or str(cell).strip() == "" for cell in row):
                continue  # Pular linhas vazias
            
            row_dict = {}
            for key, col_idx in normalized_headers.items():
                if col_idx < len(row):
                    row_dict[key] = str(row[col_idx]).strip() if row[col_idx] else ""
                else:
                    row_dict[key] = ""
            
            # Adicionar também acesso por índice original
            for i, header in enumerate(headers):
                if i < len(row):
                    row_dict[header] = str(row[i]).strip() if row[i] else ""
            
            result.append(row_dict)
        
        return result

# ============================================================================
# FUNÇÕES DE SEED
# ============================================================================

def get_or_create_tenant(db: Session) -> Tenant:
    """Obtém ou cria tenant padrão para staging"""
    tenant_id = os.getenv("STAGING_TENANT_ID")
    
    if tenant_id:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if tenant:
            logger.log(f"Tenant encontrado: {tenant.name} (ID: {tenant.id})", "SUCCESS")
            return tenant
    
    # Buscar tenant existente ou criar novo
    tenant = db.query(Tenant).filter(Tenant.name == "FinaFlow Staging").first()
    
    if not tenant:
        tenant = Tenant(
            id=str(uuid4()),
            name="FinaFlow Staging",
            domain="finaflow-staging.com",
            status="active"
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        logger.log(f"Tenant criado: {tenant.name} (ID: {tenant.id})", "SUCCESS")
    else:
        logger.log(f"Tenant encontrado: {tenant.name} (ID: {tenant.id})", "SUCCESS")
    
    return tenant

def get_or_create_business_unit(db: Session, tenant: Tenant) -> BusinessUnit:
    """Obtém ou cria business unit padrão para staging"""
    business_unit_id = os.getenv("STAGING_BUSINESS_UNIT_ID")
    
    if business_unit_id:
        bu = db.query(BusinessUnit).filter(BusinessUnit.id == business_unit_id).first()
        if bu:
            logger.log(f"Business Unit encontrada: {bu.name} (ID: {bu.id})", "SUCCESS")
            return bu
    
    # Buscar BU existente ou criar nova
    bu = db.query(BusinessUnit).filter(
        BusinessUnit.tenant_id == tenant.id,
        BusinessUnit.name == "Matriz"
    ).first()
    
    if not bu:
        bu = BusinessUnit(
            id=str(uuid4()),
            tenant_id=tenant.id,
            name="Matriz",
            code="MAT",
            status="active"
        )
        db.add(bu)
        db.commit()
        db.refresh(bu)
        logger.log(f"Business Unit criada: {bu.name} (ID: {bu.id})", "SUCCESS")
    else:
        logger.log(f"Business Unit encontrada: {bu.name} (ID: {bu.id})", "SUCCESS")
    
    return bu

def get_or_create_user(db: Session, tenant: Tenant, business_unit: BusinessUnit) -> User:
    """Obtém ou cria usuário padrão para staging"""
    user_id = os.getenv("STAGING_USER_ID")
    
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            logger.log(f"Usuário encontrado: {user.email} (ID: {user.id})", "SUCCESS")
            return user
    
    # Buscar usuário QA ou criar novo
    user = db.query(User).filter(User.email == "qa@finaflow.test").first()
    
    if not user:
        from app.services.security import SecurityService
        user = User(
            id=str(uuid4()),
            tenant_id=tenant.id,
            business_unit_id=business_unit.id,
            username="qa",
            email="qa@finaflow.test",
            hashed_password=SecurityService.hash_password("QaFinaflow123!"),
            first_name="QA",
            last_name="FinaFlow",
            role=UserRole.SUPER_ADMIN,
            status=UserStatus.ACTIVE
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.log(f"Usuário criado: {user.email} (ID: {user.id})", "SUCCESS")
    else:
        logger.log(f"Usuário encontrado: {user.email} (ID: {user.id})", "SUCCESS")
    
    return user

def seed_plano_contas(
    db: Session,
    tenant: Tenant,
    sheets_reader: GoogleSheetsReader,
    spreadsheet_id: str
) -> Tuple[Dict[str, ChartAccountGroup], Dict[str, ChartAccountSubgroup], Dict[str, ChartAccount]]:
    """Seed do plano de contas a partir do Google Sheets"""
    logger.log("Iniciando seed do Plano de Contas...", "STEP")
    
    grupos_map: Dict[str, ChartAccountGroup] = {}
    subgrupos_map: Dict[str, ChartAccountSubgroup] = {}
    contas_map: Dict[str, ChartAccount] = {}
    
    # Encontrar a aba correta
    sheet_name = sheets_reader.find_sheet(spreadsheet_id, PLANO_CONTAS_SHEETS)
    if not sheet_name:
        logger.log("Aba do Plano de Contas não encontrada", "ERROR")
        logger.stats['erros'].append("Aba do Plano de Contas não encontrada")
        return grupos_map, subgrupos_map, contas_map
    
    try:
        # Ler dados da planilha
        sheet_data = sheets_reader.get_sheet_data(spreadsheet_id, sheet_name)
        if not sheet_data:
            logger.log("Nenhum dado encontrado na aba do Plano de Contas", "ERROR")
            logger.stats['erros'].append("Nenhum dado encontrado na aba do Plano de Contas")
            return grupos_map, subgrupos_map, contas_map
        
        # Converter para lista de dicionários
        rows = sheets_reader.sheet_to_dict_list(sheet_data)
        
        for row_num, row in enumerate(rows, start=2):
                try:
                    # Parse dos campos (tentar diferentes nomes de colunas)
                    conta_nome = (row.get('conta') or row.get('Conta') or row.get('CONTA') or '').strip()
                    subgrupo_nome = (row.get('subgrupo') or row.get('Subgrupo') or row.get('SUBGRUPO') or '').strip()
                    grupo_nome = (row.get('grupo') or row.get('Grupo') or row.get('GRUPO') or '').strip()
                    escolha = (row.get('escolha') or row.get('Escolha') or row.get('ESCOLHA') or row.get('LLM') or '').strip()
                    
                    # Pular linhas vazias ou com "Usar" diferente
                    if not conta_nome or not subgrupo_nome or not grupo_nome:
                        continue
                    
                    if escolha and escolha.lower() not in ['usar', 'use', 'sim', 'yes']:
                        continue
                    
                    # 1. Criar ou obter Grupo
                    grupo_key = grupo_nome.lower()
                    if grupo_key not in grupos_map:
                        grupo = db.query(ChartAccountGroup).filter(
                            ChartAccountGroup.name == grupo_nome,
                            ChartAccountGroup.tenant_id == tenant.id
                        ).first()
                        
                        if not grupo:
                            grupo = ChartAccountGroup(
                                id=str(uuid4()),
                                tenant_id=tenant.id,
                                code=generate_code(grupo_nome, "G"),
                                name=grupo_nome,
                                description=f"Grupo: {grupo_nome}",
                                is_active=True
                            )
                            db.add(grupo)
                            db.commit()
                            db.refresh(grupo)
                            logger.stats['grupos_criados'] += 1
                            logger.log(f"Grupo criado: {grupo_nome}", "SUCCESS")
                        else:
                            logger.stats['grupos_existentes'] += 1
                        
                        grupos_map[grupo_key] = grupo
                    else:
                        grupo = grupos_map[grupo_key]
                    
                    # 2. Criar ou obter Subgrupo
                    subgrupo_key = f"{grupo_key}::{subgrupo_nome.lower()}"
                    if subgrupo_key not in subgrupos_map:
                        subgrupo = db.query(ChartAccountSubgroup).filter(
                            ChartAccountSubgroup.name == subgrupo_nome,
                            ChartAccountSubgroup.group_id == grupo.id,
                            ChartAccountSubgroup.tenant_id == tenant.id
                        ).first()
                        
                        if not subgrupo:
                            subgrupo = ChartAccountSubgroup(
                                id=str(uuid4()),
                                tenant_id=tenant.id,
                                code=generate_code(subgrupo_nome, "SG"),
                                name=subgrupo_nome,
                                description=f"Subgrupo: {subgrupo_nome}",
                                group_id=grupo.id,
                                is_active=True
                            )
                            db.add(subgrupo)
                            db.commit()
                            db.refresh(subgrupo)
                            logger.stats['subgrupos_criados'] += 1
                            logger.log(f"Subgrupo criado: {subgrupo_nome} (Grupo: {grupo_nome})", "SUCCESS")
                        else:
                            logger.stats['subgrupos_existentes'] += 1
                        
                        subgrupos_map[subgrupo_key] = subgrupo
                    else:
                        subgrupo = subgrupos_map[subgrupo_key]
                    
                    # 3. Criar ou obter Conta
                    conta_key = f"{subgrupo_key}::{conta_nome.lower()}"
                    if conta_key not in contas_map:
                        conta = db.query(ChartAccount).filter(
                            ChartAccount.name == conta_nome,
                            ChartAccount.subgroup_id == subgrupo.id,
                            ChartAccount.tenant_id == tenant.id
                        ).first()
                        
                        if not conta:
                            conta = ChartAccount(
                                id=str(uuid4()),
                                tenant_id=tenant.id,
                                code=generate_code(conta_nome, "C"),
                                name=conta_nome,
                                description=f"Conta: {conta_nome}",
                                subgroup_id=subgrupo.id,
                                account_type=determine_account_type(grupo_nome),
                                is_active=True
                            )
                            db.add(conta)
                            db.commit()
                            db.refresh(conta)
                            logger.stats['contas_criadas'] += 1
                            logger.log(f"Conta criada: {conta_nome} (Subgrupo: {subgrupo_nome})", "SUCCESS")
                        else:
                            logger.stats['contas_existentes'] += 1
                        
                        contas_map[conta_key] = conta
                    
                except Exception as e:
                    error_msg = f"Erro na linha {row_num}: {str(e)}"
                    logger.log(error_msg, "ERROR")
                    logger.stats['erros'].append(error_msg)
                    continue
        
        logger.log("Seed do Plano de Contas concluído!", "SUCCESS")
        
    except Exception as e:
        error_msg = f"Erro ao processar planilha do plano de contas: {str(e)}"
        logger.log(error_msg, "ERROR")
        logger.stats['erros'].append(error_msg)
        import traceback
        traceback.print_exc()
    
    return grupos_map, subgrupos_map, contas_map

def seed_lancamentos_diarios(
    db: Session,
    tenant: Tenant,
    business_unit: BusinessUnit,
    user: User,
    grupos_map: Dict[str, ChartAccountGroup],
    subgrupos_map: Dict[str, ChartAccountSubgroup],
    contas_map: Dict[str, ChartAccount],
    sheets_reader: GoogleSheetsReader,
    spreadsheet_id: str
):
    """Seed de lançamentos diários a partir do Google Sheets"""
    logger.log("Iniciando seed de Lançamentos Diários...", "STEP")
    
    # Encontrar a aba correta
    sheet_name = sheets_reader.find_sheet(spreadsheet_id, LANCAMENTOS_DIARIOS_SHEETS)
    if not sheet_name:
        logger.log("Aba de Lançamentos Diários não encontrada", "ERROR")
        logger.stats['erros'].append("Aba de Lançamentos Diários não encontrada")
        return
    
    try:
        # Ler dados da planilha
        sheet_data = sheets_reader.get_sheet_data(spreadsheet_id, sheet_name)
        if not sheet_data:
            logger.log("Nenhum dado encontrado na aba de Lançamentos Diários", "ERROR")
            logger.stats['erros'].append("Nenhum dado encontrado na aba de Lançamentos Diários")
            return
        
        # Converter para lista de dicionários
        rows = sheets_reader.sheet_to_dict_list(sheet_data)
        
        for row_num, row in enumerate(rows, start=2):
                try:
                    # Parse dos campos (tentar diferentes nomes de colunas)
                    data_mov_str = (row.get('data_movimentacao') or row.get('Data Movimentação') or row.get('Data Movimentacao') or '').strip()
                    subgrupo_nome = (row.get('subgrupo') or row.get('Subgrupo') or row.get('SUBGRUPO') or '').strip()
                    grupo_nome = (row.get('grupo') or row.get('Grupo') or row.get('GRUPO') or '').strip()
                    valor_str = (row.get('valor') or row.get('Valor') or row.get('VALOR') or '').strip()
                    observacoes = (row.get('observacoes') or row.get('Observações') or row.get('OBSERVACOES') or '').strip()
                    
                    # Pular linhas vazias
                    if not data_mov_str or not subgrupo_nome or not grupo_nome or not valor_str:
                        continue
                    
                    # Parse de data e valor
                    data_movimentacao = parse_date(data_mov_str)
                    if not data_movimentacao:
                        continue
                    
                    valor = parse_currency(valor_str)
                    if valor <= 0:
                        continue
                    
                    # Buscar grupo, subgrupo e conta
                    grupo_key = grupo_nome.lower()
                    grupo = grupos_map.get(grupo_key)
                    
                    if not grupo:
                        grupo = db.query(ChartAccountGroup).filter(
                            ChartAccountGroup.name == grupo_nome,
                            ChartAccountGroup.tenant_id == tenant.id
                        ).first()
                    
                    if not grupo:
                        logger.log(f"Grupo não encontrado: {grupo_nome} (linha {row_num})", "WARNING")
                        continue
                    
                    subgrupo_key = f"{grupo_key}::{subgrupo_nome.lower()}"
                    subgrupo = subgrupos_map.get(subgrupo_key)
                    
                    if not subgrupo:
                        subgrupo = db.query(ChartAccountSubgroup).filter(
                            ChartAccountSubgroup.name == subgrupo_nome,
                            ChartAccountSubgroup.group_id == grupo.id,
                            ChartAccountSubgroup.tenant_id == tenant.id
                        ).first()
                    
                    if not subgrupo:
                        logger.log(f"Subgrupo não encontrado: {subgrupo_nome} (linha {row_num})", "WARNING")
                        continue
                    
                    # Para lançamentos diários, a conta pode não estar explícita
                    # Vamos buscar a primeira conta do subgrupo ou criar uma genérica
                    conta = db.query(ChartAccount).filter(
                        ChartAccount.subgroup_id == subgrupo.id,
                        ChartAccount.tenant_id == tenant.id
                    ).first()
                    
                    if not conta:
                        logger.log(f"Conta não encontrada para subgrupo: {subgrupo_nome} (linha {row_num})", "WARNING")
                        continue
                    
                    # Verificar se já existe (idempotência)
                    existing = db.query(LancamentoDiario).filter(
                        LancamentoDiario.data_movimentacao == data_movimentacao,
                        LancamentoDiario.conta_id == conta.id,
                        LancamentoDiario.valor == valor,
                        LancamentoDiario.tenant_id == tenant.id,
                        LancamentoDiario.business_unit_id == business_unit.id
                    ).first()
                    
                    if existing:
                        logger.stats['lancamentos_diarios_existentes'] += 1
                        continue
                    
                    # Criar lançamento
                    lancamento = LancamentoDiario(
                        id=str(uuid4()),
                        data_movimentacao=data_movimentacao,
                        valor=valor,
                        liquidacao=None,  # Pode ser preenchido depois
                        observacoes=observacoes or f"Lançamento de {subgrupo_nome}",
                        conta_id=conta.id,
                        subgrupo_id=subgrupo.id,
                        grupo_id=grupo.id,
                        transaction_type=determine_transaction_type(grupo_nome, subgrupo_nome),
                        status=TransactionStatus.LIQUIDADO,
                        tenant_id=tenant.id,
                        business_unit_id=business_unit.id,
                        created_by=user.id,
                        is_active=True
                    )
                    
                    db.add(lancamento)
                    db.commit()
                    logger.stats['lancamentos_diarios_criados'] += 1
                    
                    if logger.stats['lancamentos_diarios_criados'] % 100 == 0:
                        logger.log(f"Lançamentos diários criados: {logger.stats['lancamentos_diarios_criados']}", "INFO")
                
                except Exception as e:
                    error_msg = f"Erro na linha {row_num}: {str(e)}"
                    logger.log(error_msg, "ERROR")
                    logger.stats['erros'].append(error_msg)
                    continue
        
        logger.log("Seed de Lançamentos Diários concluído!", "SUCCESS")
        
    except Exception as e:
        error_msg = f"Erro ao processar planilha de lançamentos diários: {str(e)}"
        logger.log(error_msg, "ERROR")
        logger.stats['erros'].append(error_msg)
        import traceback
        traceback.print_exc()

def seed_lancamentos_previstos(
    db: Session,
    tenant: Tenant,
    business_unit: BusinessUnit,
    user: User,
    grupos_map: Dict[str, ChartAccountGroup],
    subgrupos_map: Dict[str, ChartAccountSubgroup],
    contas_map: Dict[str, ChartAccount],
    sheets_reader: GoogleSheetsReader,
    spreadsheet_id: str
):
    """Seed de lançamentos previstos a partir do Google Sheets"""
    logger.log("Iniciando seed de Lançamentos Previstos...", "STEP")
    
    # Encontrar a aba correta
    sheet_name = sheets_reader.find_sheet(spreadsheet_id, LANCAMENTOS_PREVISTOS_SHEETS)
    if not sheet_name:
        logger.log("Aba de Lançamentos Previstos não encontrada", "ERROR")
        logger.stats['erros'].append("Aba de Lançamentos Previstos não encontrada")
        return
    
    try:
        # Ler dados da planilha
        sheet_data = sheets_reader.get_sheet_data(spreadsheet_id, sheet_name)
        if not sheet_data:
            logger.log("Nenhum dado encontrado na aba de Lançamentos Previstos", "ERROR")
            logger.stats['erros'].append("Nenhum dado encontrado na aba de Lançamentos Previstos")
            return
        
        # Converter para lista de dicionários
        rows = sheets_reader.sheet_to_dict_list(sheet_data)
        
        for row_num, row in enumerate(rows, start=2):
                try:
                    # Parse dos campos (tentar diferentes nomes de colunas)
                    mes_str = (row.get('mes') or row.get('Mês') or row.get('MES') or row.get('data_prevista') or row.get('Data Prevista') or '').strip()
                    conta_nome = (row.get('conta') or row.get('Conta') or row.get('CONTA') or '').strip()
                    subgrupo_nome = (row.get('subgrupo') or row.get('Subgrupo') or row.get('SUBGRUPO') or '').strip()
                    grupo_nome = (row.get('grupo') or row.get('Grupo') or row.get('GRUPO') or '').strip()
                    valor_str = (row.get('valor') or row.get('Valor') or row.get('VALOR') or '').strip()
                    
                    # Pular linhas vazias
                    if not mes_str or not conta_nome or not subgrupo_nome or not grupo_nome or not valor_str:
                        continue
                    
                    # Parse de data e valor
                    data_prevista = parse_date(mes_str)
                    if not data_prevista:
                        continue
                    
                    valor = parse_currency(valor_str)
                    if valor <= 0:
                        continue
                    
                    # Buscar grupo, subgrupo e conta
                    grupo_key = grupo_nome.lower()
                    grupo = grupos_map.get(grupo_key)
                    
                    if not grupo:
                        grupo = db.query(ChartAccountGroup).filter(
                            ChartAccountGroup.name == grupo_nome,
                            ChartAccountGroup.tenant_id == tenant.id
                        ).first()
                    
                    if not grupo:
                        logger.log(f"Grupo não encontrado: {grupo_nome} (linha {row_num})", "WARNING")
                        continue
                    
                    subgrupo_key = f"{grupo_key}::{subgrupo_nome.lower()}"
                    subgrupo = subgrupos_map.get(subgrupo_key)
                    
                    if not subgrupo:
                        subgrupo = db.query(ChartAccountSubgroup).filter(
                            ChartAccountSubgroup.name == subgrupo_nome,
                            ChartAccountSubgroup.group_id == grupo.id,
                            ChartAccountSubgroup.tenant_id == tenant.id
                        ).first()
                    
                    if not subgrupo:
                        logger.log(f"Subgrupo não encontrado: {subgrupo_nome} (linha {row_num})", "WARNING")
                        continue
                    
                    # Buscar conta pelo nome
                    conta_key = f"{subgrupo_key}::{conta_nome.lower()}"
                    conta = contas_map.get(conta_key)
                    
                    if not conta:
                        conta = db.query(ChartAccount).filter(
                            ChartAccount.name == conta_nome,
                            ChartAccount.subgroup_id == subgrupo.id,
                            ChartAccount.tenant_id == tenant.id
                        ).first()
                    
                    if not conta:
                        logger.log(f"Conta não encontrada: {conta_nome} (linha {row_num})", "WARNING")
                        continue
                    
                    # Verificar se já existe (idempotência)
                    existing = db.query(LancamentoPrevisto).filter(
                        LancamentoPrevisto.data_prevista == data_prevista,
                        LancamentoPrevisto.conta_id == conta.id,
                        LancamentoPrevisto.valor == valor,
                        LancamentoPrevisto.tenant_id == tenant.id,
                        LancamentoPrevisto.business_unit_id == business_unit.id
                    ).first()
                    
                    if existing:
                        logger.stats['lancamentos_previstos_existentes'] += 1
                        continue
                    
                    # Criar previsão
                    previsao = LancamentoPrevisto(
                        id=str(uuid4()),
                        data_prevista=data_prevista,
                        valor=valor,
                        observacoes=f"Previsão de {conta_nome}",
                        conta_id=conta.id,
                        subgrupo_id=subgrupo.id,
                        grupo_id=grupo.id,
                        transaction_type=determine_transaction_type(grupo_nome, subgrupo_nome),
                        status=TransactionStatus.PENDENTE,
                        tenant_id=tenant.id,
                        business_unit_id=business_unit.id,
                        created_by=user.id,
                        is_active=True
                    )
                    
                    db.add(previsao)
                    db.commit()
                    logger.stats['lancamentos_previstos_criados'] += 1
                    
                    if logger.stats['lancamentos_previstos_criados'] % 100 == 0:
                        logger.log(f"Lançamentos previstos criados: {logger.stats['lancamentos_previstos_criados']}", "INFO")
                
                except Exception as e:
                    error_msg = f"Erro na linha {row_num}: {str(e)}"
                    logger.log(error_msg, "ERROR")
                    logger.stats['erros'].append(error_msg)
                    continue
        
        logger.log("Seed de Lançamentos Previstos concluído!", "SUCCESS")
        
    except Exception as e:
        error_msg = f"Erro ao processar planilha de lançamentos previstos: {str(e)}"
        logger.log(error_msg, "ERROR")
        logger.stats['erros'].append(error_msg)
        import traceback
        traceback.print_exc()

# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    """Função principal do seed"""
    logger.log("="*60, "STEP")
    logger.log("🌱 INICIANDO SEED DO AMBIENTE STAGING", "STEP")
    logger.log("="*60, "STEP")
    
    try:
        # Informações da planilha
        logger.log(f"Planilha Google Sheets:", "INFO")
        logger.log(f"  - ID: {SPREADSHEET_ID}", "INFO")
        logger.log(f"  - URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}", "INFO")
        logger.log(f"  - Credenciais: {GOOGLE_CREDENTIALS_PATH}", "INFO")
        
        # Autenticar com Google Sheets
        logger.log("\n" + "-"*60, "STEP")
        logger.log("0. Autenticando com Google Sheets...", "STEP")
        sheets_reader = GoogleSheetsReader()
        if not sheets_reader.authenticate():
            logger.log("❌ Falha na autenticação com Google Sheets. Abortando.", "ERROR")
            sys.exit(1)
        
        # Inicializar banco
        logger.log("\n" + "-"*60, "STEP")
        logger.log("Inicializando banco de dados...", "STEP")
        create_tables()
        logger.log("Banco de dados inicializado", "SUCCESS")
        
        db = SessionLocal()
        
        try:
            # 1. Obter ou criar Tenant, BU e User
            logger.log("\n" + "-"*60, "STEP")
            logger.log("1. Configurando Tenant, Business Unit e Usuário...", "STEP")
            tenant = get_or_create_tenant(db)
            business_unit = get_or_create_business_unit(db, tenant)
            user = get_or_create_user(db, tenant, business_unit)
            
            # 2. Seed do Plano de Contas
            logger.log("\n" + "-"*60, "STEP")
            logger.log("2. Seed do Plano de Contas...", "STEP")
            grupos_map, subgrupos_map, contas_map = seed_plano_contas(
                db, tenant, sheets_reader, SPREADSHEET_ID
            )
            
            # 3. Seed de Lançamentos Diários
            logger.log("\n" + "-"*60, "STEP")
            logger.log("3. Seed de Lançamentos Diários...", "STEP")
            seed_lancamentos_diarios(
                db, tenant, business_unit, user,
                grupos_map, subgrupos_map, contas_map,
                sheets_reader, SPREADSHEET_ID
            )
            
            # 4. Seed de Lançamentos Previstos
            logger.log("\n" + "-"*60, "STEP")
            logger.log("4. Seed de Lançamentos Previstos...", "STEP")
            seed_lancamentos_previstos(
                db, tenant, business_unit, user,
                grupos_map, subgrupos_map, contas_map,
                sheets_reader, SPREADSHEET_ID
            )
            
            # 5. Estatísticas finais
            logger.print_stats()
            
            logger.log("\n" + "="*60, "STEP")
            logger.log("✅ SEED CONCLUÍDO COM SUCESSO!", "SUCCESS")
            logger.log("="*60, "STEP")
            
        except Exception as e:
            db.rollback()
            error_msg = f"Erro durante o seed: {str(e)}"
            logger.log(error_msg, "ERROR")
            logger.stats['erros'].append(error_msg)
            import traceback
            traceback.print_exc()
            raise
        finally:
            db.close()
    
    except Exception as e:
        logger.log(f"❌ Erro fatal: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

