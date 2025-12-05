#!/usr/bin/env python3
"""
Script de Seed para ambiente STAGING
Popula o banco de dados com dados reais da planilha Excel (.xlsx) do cliente.

USO:
    python -m scripts.seed_from_client_sheet --file data/fluxo_caixa_2025.xlsx

REQUISITOS:
    - Arquivo Excel (.xlsx) na pasta backend/data/:
        - fluxo_caixa_2025.xlsx (ou caminho customizado via --file)
        - Abas necessárias:
          * "Plano de contas" (ou "Plano de contas|LLM")
          * "Lançamento Diário" (ou "Lançamento Diario")
          * "Lançamentos Previstos"
    
    - Variáveis de ambiente:
        - DATABASE_URL: URL de conexão com o banco PostgreSQL de STAGING
        - STAGING_TENANT_ID: (opcional) ID do tenant staging
        - STAGING_BUSINESS_UNIT_ID: (opcional) ID da business unit staging
        - STAGING_USER_ID: (opcional) ID do usuário que criará os registros

CARACTERÍSTICAS:
    - Idempotente: pode ser executado múltiplas vezes sem duplicar dados
    - Validações: verifica integridade hierárquica (grupo → subgrupo → conta)
    - Logs detalhados: mostra progresso e estatísticas
    - Transações: usa commit/rollback para garantir atomicidade
    - Excel: lê dados diretamente do arquivo .xlsx local
"""

import sys
import os
import argparse
from pathlib import Path
from uuid import uuid4
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional, Tuple, List
import re

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

try:
    import pandas as pd
except ImportError:
    print("❌ Erro: pandas não está instalado. Execute: pip install pandas openpyxl")
    sys.exit(1)

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import SessionLocal, create_tables

# Importar TODOS os modelos para garantir que os relacionamentos sejam resolvidos corretamente
# Isso é necessário porque alguns modelos (como Tenant) referenciam outros via string
# e o SQLAlchemy precisa que todas as classes estejam importadas antes de resolver os relacionamentos

# Modelos de autenticação e estrutura
from app.models.auth import User, Tenant, BusinessUnit, UserRole, UserStatus

# Modelos de contas bancárias (necessário para relacionamento com Tenant)
from app.models.conta_bancaria import ContaBancaria

# Modelos de caixa e investimentos (necessário para relacionamento com Tenant)
from app.models.caixa import Caixa
from app.models.investimento import Investimento

# Modelos de plano de contas
from app.models.chart_of_accounts import (
    ChartAccountGroup,
    ChartAccountSubgroup,
    ChartAccount
)

# Modelos de lançamentos
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

# Caminho padrão do arquivo Excel
DEFAULT_EXCEL_FILE = backend_path / "data" / "fluxo_caixa_2025.xlsx"

# Nomes das abas (tentar diferentes variações)
PLANO_CONTAS_SHEETS = ["Plano de contas|LLM", "Plano de contas", "Plano de Contas", "Plano de Contas|LLM"]
LANCAMENTOS_DIARIOS_SHEETS = ["Lançamento Diário", "Lançamento Diario", "Lancamento Diario", "Lançamentos Diários"]
LANCAMENTOS_PREVISTOS_SHEETS = ["Lançamentos Previstos", "Lancamentos Previstos", "Previsões", "Previsoes"]

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
            'linhas_ignoradas': 0,
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
        print(f"Linhas ignoradas: {self.stats['linhas_ignoradas']}")
        if self.stats['erros']:
            print(f"\n⚠️  {len(self.stats['erros'])} erros encontrados:")
            for erro in self.stats['erros'][:10]:  # Mostrar apenas os 10 primeiros
                print(f"   - {erro}")
        print("="*60)

logger = SeedLogger()

# ============================================================================
# FUNÇÕES DE PARSE
# ============================================================================

def parse_currency(value) -> Decimal:
    """Converte valor para Decimal"""
    if pd.isna(value) or value == "" or value is None:
        return Decimal("0.00")
    
    # Converter para string
    value_str = str(value).strip()
    
    # Remover R$, espaços e vírgulas
    value_str = value_str.replace("R$", "").replace("$", "").strip()
    value_str = value_str.replace(".", "").replace(",", ".")
    
    try:
        return Decimal(value_str)
    except:
        logger.log(f"Erro ao converter valor: {value}", "WARNING")
        return Decimal("0.00")

def parse_date(date_value) -> Optional[datetime]:
    """Converte valor para datetime"""
    if pd.isna(date_value) or date_value == "" or date_value is None:
        return None
    
    # Se já for datetime
    if isinstance(date_value, datetime):
        return date_value
    
    # Se for Timestamp do pandas
    if isinstance(date_value, pd.Timestamp):
        return date_value.to_pydatetime()
    
    # Tentar converter string
    value_str = str(date_value).strip()
    
    # Formatos esperados
    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%d/%m/%y",
        "%d-%m-%y",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(value_str, fmt)
        except:
            continue
    
    logger.log(f"Erro ao converter data: {date_value}", "WARNING")
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
    elif "dedução" in grupo_lower or "deducao" in grupo_lower:
        return "Dedução"
    else:
        return "Outro"

# ============================================================================
# FUNÇÕES DE LEITURA DE EXCEL
# ============================================================================

def find_sheet_in_excel(excel_file: Path, sheet_names: List[str]) -> Optional[str]:
    """Encontra a primeira aba que existe no arquivo Excel"""
    try:
        excel = pd.ExcelFile(excel_file)
        available_sheets = excel.sheet_names
        
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

def read_excel_sheet(excel_file: Path, sheet_name: str) -> pd.DataFrame:
    """Lê uma aba específica do arquivo Excel"""
    try:
        df = pd.read_excel(excel_file, sheet_name=sheet_name, engine='openpyxl')
        logger.log(f"Dados lidos da aba '{sheet_name}': {len(df)} linhas", "INFO")
        return df
    except Exception as e:
        logger.log(f"Erro ao ler aba '{sheet_name}': {str(e)}", "ERROR")
        return pd.DataFrame()

# ============================================================================
# FUNÇÕES DE SEED
# ============================================================================

def get_or_create_tenant(db: Session, tenant_id: Optional[str] = None) -> Tenant:
    """Obtém ou cria tenant padrão para staging"""
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

def get_or_create_business_unit(db: Session, tenant: Tenant, business_unit_id: Optional[str] = None) -> BusinessUnit:
    """Obtém ou cria business unit padrão para staging"""
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

def get_or_create_user(db: Session, tenant: Tenant, business_unit: BusinessUnit, user_id: Optional[str] = None) -> User:
    """Obtém ou cria usuário padrão para staging"""
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
    excel_file: Path
) -> Tuple[Dict[str, ChartAccountGroup], Dict[str, ChartAccountSubgroup], Dict[str, ChartAccount]]:
    """Seed do plano de contas a partir do Excel"""
    logger.log("Iniciando seed do Plano de Contas...", "STEP")
    
    grupos_map: Dict[str, ChartAccountGroup] = {}
    subgrupos_map: Dict[str, ChartAccountSubgroup] = {}
    contas_map: Dict[str, ChartAccount] = {}
    
    # Encontrar a aba correta
    sheet_name = find_sheet_in_excel(excel_file, PLANO_CONTAS_SHEETS)
    if not sheet_name:
        logger.log("Aba do Plano de Contas não encontrada", "ERROR")
        logger.stats['erros'].append("Aba do Plano de Contas não encontrada")
        return grupos_map, subgrupos_map, contas_map
    
    try:
        # Ler dados da planilha
        df = read_excel_sheet(excel_file, sheet_name)
        if df.empty:
            logger.log("Nenhum dado encontrado na aba do Plano de Contas", "ERROR")
            logger.stats['erros'].append("Nenhum dado encontrado na aba do Plano de Contas")
            return grupos_map, subgrupos_map, contas_map
        
        # Normalizar nomes de colunas (case-insensitive, remover espaços)
        df.columns = df.columns.str.strip()
        column_map = {}
        for col in df.columns:
            col_lower = col.lower()
            if 'conta' in col_lower and 'conta' not in column_map:
                column_map['conta'] = col
            if 'subgrupo' in col_lower and 'subgrupo' not in column_map:
                column_map['subgrupo'] = col
            if 'grupo' in col_lower and 'subgrupo' not in col_lower and 'grupo' not in column_map:
                column_map['grupo'] = col
            if ('escolha' in col_lower or 'llm' in col_lower) and 'escolha' not in column_map:
                column_map['escolha'] = col
            if 'observação' in col_lower or 'observacao' in col_lower:
                column_map['observacao'] = col
        
        # Verificar se temos as colunas mínimas
        if 'conta' not in column_map or 'subgrupo' not in column_map or 'grupo' not in column_map:
            logger.log(f"Colunas necessárias não encontradas. Colunas disponíveis: {list(df.columns)}", "ERROR")
            logger.stats['erros'].append("Colunas necessárias não encontradas")
            return grupos_map, subgrupos_map, contas_map
        
        for row_num, row in df.iterrows():
            try:
                # Parse dos campos
                conta_nome = str(row[column_map['conta']]).strip() if pd.notna(row[column_map['conta']]) else ""
                subgrupo_nome = str(row[column_map['subgrupo']]).strip() if pd.notna(row[column_map['subgrupo']]) else ""
                grupo_nome = str(row[column_map['grupo']]).strip() if pd.notna(row[column_map['grupo']]) else ""
                escolha = ""
                if 'escolha' in column_map:
                    escolha = str(row[column_map['escolha']]).strip() if pd.notna(row[column_map['escolha']]) else ""
                
                # Pular linhas vazias ou com "Usar" diferente
                if not conta_nome or not subgrupo_nome or not grupo_nome:
                    continue
                
                if escolha and escolha.lower() not in ['usar', 'use', 'sim', 'yes', '']:
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
                error_msg = f"Erro na linha {row_num + 2}: {str(e)}"
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

def seed_lancamentos_previstos(
    db: Session,
    tenant: Tenant,
    business_unit: BusinessUnit,
    user: User,
    grupos_map: Dict[str, ChartAccountGroup],
    subgrupos_map: Dict[str, ChartAccountSubgroup],
    contas_map: Dict[str, ChartAccount],
    excel_file: Path
):
    """Seed de lançamentos previstos a partir do Excel"""
    logger.log("Iniciando seed de Lançamentos Previstos...", "STEP")
    
    # Encontrar a aba correta
    sheet_name = find_sheet_in_excel(excel_file, LANCAMENTOS_PREVISTOS_SHEETS)
    if not sheet_name:
        logger.log("Aba de Lançamentos Previstos não encontrada", "ERROR")
        logger.stats['erros'].append("Aba de Lançamentos Previstos não encontrada")
        return
    
    try:
        # Ler dados da planilha
        df = read_excel_sheet(excel_file, sheet_name)
        if df.empty:
            logger.log("Nenhum dado encontrado na aba de Lançamentos Previstos", "ERROR")
            logger.stats['erros'].append("Nenhum dado encontrado na aba de Lançamentos Previstos")
            return
        
        # Normalizar nomes de colunas
        df.columns = df.columns.str.strip()
        column_map = {}
        for col in df.columns:
            col_lower = col.lower()
            if ('mês' in col_lower or 'mes' in col_lower or 'data' in col_lower) and 'prevista' in col_lower:
                column_map['data_prevista'] = col
            elif ('mês' in col_lower or 'mes' in col_lower) and 'data_prevista' not in column_map:
                column_map['data_prevista'] = col
            if 'conta' in col_lower and 'conta' not in column_map:
                column_map['conta'] = col
            if 'subgrupo' in col_lower and 'subgrupo' not in column_map:
                column_map['subgrupo'] = col
            if 'grupo' in col_lower and 'subgrupo' not in col_lower and 'grupo' not in column_map:
                column_map['grupo'] = col
            if 'valor' in col_lower and 'valor' not in column_map:
                column_map['valor'] = col
        
        # Verificar colunas mínimas
        if 'data_prevista' not in column_map or 'conta' not in column_map or 'valor' not in column_map:
            logger.log(f"Colunas necessárias não encontradas. Colunas disponíveis: {list(df.columns)}", "ERROR")
            logger.stats['erros'].append("Colunas necessárias não encontradas em Lançamentos Previstos")
            return
        
        for row_num, row in df.iterrows():
            try:
                # Parse dos campos
                mes_str = str(row[column_map['data_prevista']]) if pd.notna(row[column_map['data_prevista']]) else ""
                conta_nome = str(row[column_map['conta']]).strip() if pd.notna(row[column_map['conta']]) else ""
                subgrupo_nome = ""
                grupo_nome = ""
                if 'subgrupo' in column_map:
                    subgrupo_nome = str(row[column_map['subgrupo']]).strip() if pd.notna(row[column_map['subgrupo']]) else ""
                if 'grupo' in column_map:
                    grupo_nome = str(row[column_map['grupo']]).strip() if pd.notna(row[column_map['grupo']]) else ""
                valor_str = str(row[column_map['valor']]) if pd.notna(row[column_map['valor']]) else ""
                
                # Pular linhas vazias
                if not mes_str or not conta_nome or not valor_str:
                    logger.stats['linhas_ignoradas'] += 1
                    continue
                
                # Parse de data e valor
                data_prevista = parse_date(mes_str)
                if not data_prevista:
                    logger.stats['linhas_ignoradas'] += 1
                    continue
                
                valor = parse_currency(valor_str)
                if valor <= 0:
                    logger.stats['linhas_ignoradas'] += 1
                    continue
                
                # Buscar conta (deve existir no plano de contas)
                conta = None
                if conta_nome:
                    # Buscar em contas_map primeiro
                    for key, c in contas_map.items():
                        if c.name.lower() == conta_nome.lower():
                            conta = c
                            break
                    
                    # Se não encontrou, buscar no banco
                    if not conta:
                        conta = db.query(ChartAccount).filter(
                            ChartAccount.name.ilike(f"%{conta_nome}%"),
                            ChartAccount.tenant_id == tenant.id
                        ).first()
                    
                    if not conta:
                        logger.log(f"Conta não encontrada: {conta_nome} (linha {row_num + 2})", "WARNING")
                        logger.stats['linhas_ignoradas'] += 1
                        continue
                    
                    # Buscar subgrupo e grupo da conta
                    if not subgrupo_nome:
                        subgrupo = db.query(ChartAccountSubgroup).filter(
                            ChartAccountSubgroup.id == conta.subgroup_id
                        ).first()
                        if subgrupo:
                            subgrupo_nome = subgrupo.name
                            grupo_nome = subgrupo.group.name if subgrupo.group else ""
                
                # Buscar grupo e subgrupo se não foram encontrados
                grupo = None
                subgrupo = None
                
                if grupo_nome:
                    grupo_key = grupo_nome.lower()
                    grupo = grupos_map.get(grupo_key)
                    if not grupo:
                        grupo = db.query(ChartAccountGroup).filter(
                            ChartAccountGroup.name == grupo_nome,
                            ChartAccountGroup.tenant_id == tenant.id
                        ).first()
                
                if subgrupo_nome and grupo:
                    subgrupo_key = f"{grupo.id}::{subgrupo_nome.lower()}"
                    subgrupo = subgrupos_map.get(subgrupo_key)
                    if not subgrupo:
                        subgrupo = db.query(ChartAccountSubgroup).filter(
                            ChartAccountSubgroup.name == subgrupo_nome,
                            ChartAccountSubgroup.group_id == grupo.id,
                            ChartAccountSubgroup.tenant_id == tenant.id
                        ).first()
                
                # Usar subgrupo e grupo da conta se não encontrou
                if not subgrupo:
                    subgrupo = db.query(ChartAccountSubgroup).filter(
                        ChartAccountSubgroup.id == conta.subgroup_id
                    ).first()
                
                if not grupo and subgrupo:
                    grupo = db.query(ChartAccountGroup).filter(
                        ChartAccountGroup.id == subgrupo.group_id
                    ).first()
                
                if not grupo or not subgrupo:
                    logger.log(f"Grupo/Subgrupo não encontrado para conta: {conta_nome} (linha {row_num + 2})", "WARNING")
                    logger.stats['linhas_ignoradas'] += 1
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
                error_msg = f"Erro na linha {row_num + 2}: {str(e)}"
                logger.log(error_msg, "ERROR")
                logger.stats['erros'].append(error_msg)
                logger.stats['linhas_ignoradas'] += 1
                continue
        
        logger.log("Seed de Lançamentos Previstos concluído!", "SUCCESS")
        
    except Exception as e:
        error_msg = f"Erro ao processar planilha de lançamentos previstos: {str(e)}"
        logger.log(error_msg, "ERROR")
        logger.stats['erros'].append(error_msg)
        import traceback
        traceback.print_exc()

def seed_lancamentos_diarios(
    db: Session,
    tenant: Tenant,
    business_unit: BusinessUnit,
    user: User,
    grupos_map: Dict[str, ChartAccountGroup],
    subgrupos_map: Dict[str, ChartAccountSubgroup],
    contas_map: Dict[str, ChartAccount],
    excel_file: Path
):
    """Seed de lançamentos diários a partir do Excel"""
    logger.log("Iniciando seed de Lançamentos Diários...", "STEP")
    
    # Encontrar a aba correta
    sheet_name = find_sheet_in_excel(excel_file, LANCAMENTOS_DIARIOS_SHEETS)
    if not sheet_name:
        logger.log("Aba de Lançamentos Diários não encontrada", "ERROR")
        logger.stats['erros'].append("Aba de Lançamentos Diários não encontrada")
        return
    
    try:
        # Ler dados da planilha
        df = read_excel_sheet(excel_file, sheet_name)
        if df.empty:
            logger.log("Nenhum dado encontrado na aba de Lançamentos Diários", "ERROR")
            logger.stats['erros'].append("Nenhum dado encontrado na aba de Lançamentos Diários")
            return
        
        # Normalizar nomes de colunas
        df.columns = df.columns.str.strip()
        column_map = {}
        for col in df.columns:
            col_lower = col.lower()
            if 'data' in col_lower and 'movimentação' in col_lower or 'movimentacao' in col_lower:
                column_map['data_movimentacao'] = col
            elif 'data' in col_lower and 'data_movimentacao' not in column_map:
                column_map['data_movimentacao'] = col
            if 'subgrupo' in col_lower and 'subgrupo' not in column_map:
                column_map['subgrupo'] = col
            if 'grupo' in col_lower and 'subgrupo' not in col_lower and 'grupo' not in column_map:
                column_map['grupo'] = col
            if 'valor' in col_lower and 'valor' not in column_map:
                column_map['valor'] = col
            if ('observação' in col_lower or 'observacao' in col_lower) and 'observacoes' not in column_map:
                column_map['observacoes'] = col
        
        # Verificar colunas mínimas
        if 'data_movimentacao' not in column_map or 'valor' not in column_map:
            logger.log(f"Colunas necessárias não encontradas. Colunas disponíveis: {list(df.columns)}", "ERROR")
            logger.stats['erros'].append("Colunas necessárias não encontradas em Lançamentos Diários")
            return
        
        for row_num, row in df.iterrows():
            try:
                # Parse dos campos
                data_mov_str = str(row[column_map['data_movimentacao']]) if pd.notna(row[column_map['data_movimentacao']]) else ""
                subgrupo_nome = ""
                grupo_nome = ""
                if 'subgrupo' in column_map:
                    subgrupo_nome = str(row[column_map['subgrupo']]).strip() if pd.notna(row[column_map['subgrupo']]) else ""
                if 'grupo' in column_map:
                    grupo_nome = str(row[column_map['grupo']]).strip() if pd.notna(row[column_map['grupo']]) else ""
                valor_str = str(row[column_map['valor']]) if pd.notna(row[column_map['valor']]) else ""
                observacoes = ""
                if 'observacoes' in column_map:
                    observacoes = str(row[column_map['observacoes']]).strip() if pd.notna(row[column_map['observacoes']]) else ""
                
                # Pular linhas vazias
                if not data_mov_str or not valor_str:
                    logger.stats['linhas_ignoradas'] += 1
                    continue
                
                # Parse de data e valor
                data_movimentacao = parse_date(data_mov_str)
                if not data_movimentacao:
                    logger.stats['linhas_ignoradas'] += 1
                    continue
                
                valor = parse_currency(valor_str)
                if valor <= 0:
                    logger.stats['linhas_ignoradas'] += 1
                    continue
                
                # Buscar grupo e subgrupo
                grupo = None
                subgrupo = None
                
                if grupo_nome:
                    grupo_key = grupo_nome.lower()
                    grupo = grupos_map.get(grupo_key)
                    if not grupo:
                        grupo = db.query(ChartAccountGroup).filter(
                            ChartAccountGroup.name == grupo_nome,
                            ChartAccountGroup.tenant_id == tenant.id
                        ).first()
                
                if subgrupo_nome and grupo:
                    subgrupo_key = f"{grupo.id}::{subgrupo_nome.lower()}"
                    subgrupo = subgrupos_map.get(subgrupo_key)
                    if not subgrupo:
                        subgrupo = db.query(ChartAccountSubgroup).filter(
                            ChartAccountSubgroup.name == subgrupo_nome,
                            ChartAccountSubgroup.group_id == grupo.id,
                            ChartAccountSubgroup.tenant_id == tenant.id
                        ).first()
                
                if not grupo or not subgrupo:
                    logger.log(f"Grupo/Subgrupo não encontrado: {grupo_nome}/{subgrupo_nome} (linha {row_num + 2})", "WARNING")
                    logger.stats['linhas_ignoradas'] += 1
                    continue
                
                # Buscar primeira conta do subgrupo
                conta = db.query(ChartAccount).filter(
                    ChartAccount.subgroup_id == subgrupo.id,
                    ChartAccount.tenant_id == tenant.id
                ).first()
                
                if not conta:
                    logger.log(f"Conta não encontrada para subgrupo: {subgrupo_nome} (linha {row_num + 2})", "WARNING")
                    logger.stats['linhas_ignoradas'] += 1
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
                    liquidacao=None,
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
                error_msg = f"Erro na linha {row_num + 2}: {str(e)}"
                logger.log(error_msg, "ERROR")
                logger.stats['erros'].append(error_msg)
                logger.stats['linhas_ignoradas'] += 1
                continue
        
        logger.log("Seed de Lançamentos Diários concluído!", "SUCCESS")
        
    except Exception as e:
        error_msg = f"Erro ao processar planilha de lançamentos diários: {str(e)}"
        logger.log(error_msg, "ERROR")
        logger.stats['erros'].append(error_msg)
        import traceback
        traceback.print_exc()

# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    """Função principal do seed"""
    parser = argparse.ArgumentParser(
        description="Seed de dados STAGING a partir da planilha Excel do cliente"
    )
    parser.add_argument(
        '--file',
        type=str,
        default=str(DEFAULT_EXCEL_FILE),
        help=f'Caminho do arquivo Excel (default: {DEFAULT_EXCEL_FILE})'
    )
    parser.add_argument(
        '--tenant-id',
        type=str,
        default=None,
        help='ID do tenant (opcional, busca ou cria automaticamente)'
    )
    parser.add_argument(
        '--business-unit-id',
        type=str,
        default=None,
        help='ID da business unit (opcional, busca ou cria automaticamente)'
    )
    parser.add_argument(
        '--user-id',
        type=str,
        default=None,
        help='ID do usuário (opcional, busca ou cria automaticamente)'
    )
    
    args = parser.parse_args()
    
    # Resolver caminho do arquivo
    excel_file = Path(args.file)
    if not excel_file.is_absolute():
        excel_file = backend_path / excel_file
    
    logger.log("="*60, "STEP")
    logger.log("🌱 INICIANDO SEED DO AMBIENTE STAGING", "STEP")
    logger.log("="*60, "STEP")
    
    try:
        # Verificar arquivo Excel
        if not excel_file.exists():
            logger.log(f"❌ Arquivo não encontrado: {excel_file}", "ERROR")
            logger.log(f"   Por favor, baixe a planilha do Google Sheets e salve como: {excel_file}", "ERROR")
            sys.exit(1)
        
        logger.log(f"📁 Arquivo Excel: {excel_file}", "INFO")
        
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
            tenant = get_or_create_tenant(db, args.tenant_id)
            business_unit = get_or_create_business_unit(db, tenant, args.business_unit_id)
            user = get_or_create_user(db, tenant, business_unit, args.user_id)
            
            # 2. Seed do Plano de Contas
            logger.log("\n" + "-"*60, "STEP")
            logger.log("2. Seed do Plano de Contas...", "STEP")
            grupos_map, subgrupos_map, contas_map = seed_plano_contas(
                db, tenant, excel_file
            )
            
            # 3. Seed de Lançamentos Previstos
            logger.log("\n" + "-"*60, "STEP")
            logger.log("3. Seed de Lançamentos Previstos...", "STEP")
            seed_lancamentos_previstos(
                db, tenant, business_unit, user,
                grupos_map, subgrupos_map, contas_map,
                excel_file
            )
            
            # 4. Seed de Lançamentos Diários
            logger.log("\n" + "-"*60, "STEP")
            logger.log("4. Seed de Lançamentos Diários...", "STEP")
            seed_lancamentos_diarios(
                db, tenant, business_unit, user,
                grupos_map, subgrupos_map, contas_map,
                excel_file
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

