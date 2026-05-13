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
import json
import time
from pathlib import Path
from uuid import uuid4
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple, List
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
from sqlalchemy import func
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

# Modelos de contas de liquidação
from app.models.liquidation_accounts import (
    LiquidationAccount,
    LiquidationAccountType
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
FLUXO_CAIXA_SHEETS_REGEX = re.compile(r"(?:Fluxo de caixa|Previsão Fluxo de caixa)-(\d{4})", re.IGNORECASE)

MONTH_LABELS = [
    "JANEIRO",
    "FEVEREIRO",
    "MARÇO",
    "ABRIL",
    "MAIO",
    "JUNHO",
    "JULHO",
    "AGOSTO",
    "SETEMBRO",
    "OUTUBRO",
    "NOVEMBRO",
    "DEZEMBRO",
]

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
        print(f"{prefix} {message}", flush=True)  # flush=True para aparecer imediatamente

    def print_stats(self):
        """Imprime estatísticas do seed"""
        print("\n📊 Estatísticas do Seed:", flush=True)
        for key, value in self.stats.items():
            if key == "erros":
                continue
            print(f"  - {key}: {value}", flush=True)
        if self.stats.get("erros"):
            print("\n❌ Erros encontrados:", flush=True)
            for err in self.stats["erros"][:20]:
                print(f"  - {err}", flush=True)


def _normalize_name(value: str) -> str:
    return (value or "").strip()


def _is_numeric_label(value: str) -> bool:
    if not value:
        return False
    stripped = value.strip()
    if not re.search(r"\d", stripped):
        return False
    return re.fullmatch(r"[-\d\.,]+", stripped) is not None


def get_or_create_group(
    db: Session,
    tenant: Tenant,
    grupos_map: Dict[str, ChartAccountGroup],
    grupo_nome: str,
) -> ChartAccountGroup:
    grupo_nome = _normalize_name(grupo_nome)
    if not grupo_nome:
        raise ValueError("Grupo vazio não pode ser criado")
    grupo_key = grupo_nome.lower()
    grupo = grupos_map.get(grupo_key)
    if grupo:
        return grupo
    grupo = db.query(ChartAccountGroup).filter(
        func.trim(func.lower(ChartAccountGroup.name)) == grupo_key,
        ChartAccountGroup.tenant_id == tenant.id,
    ).first()
    if not grupo:
        grupo = ChartAccountGroup(
            id=str(uuid4()),
            tenant_id=tenant.id,
            code=generate_code(grupo_nome, "G"),
            name=grupo_nome,
            description=f"Grupo: {grupo_nome}",
            is_active=True,
        )
        db.add(grupo)
        db.commit()
        db.refresh(grupo)
        logger.stats['grupos_criados'] += 1
        logger.log(f"Grupo criado: {grupo_nome}", "SUCCESS")
    else:
        logger.stats['grupos_existentes'] += 1
    grupos_map[grupo_key] = grupo
    return grupo


def get_or_create_subgroup(
    db: Session,
    tenant: Tenant,
    subgrupos_map: Dict[str, ChartAccountSubgroup],
    grupo: ChartAccountGroup,
    subgrupo_nome: str,
) -> ChartAccountSubgroup:
    subgrupo_nome = _normalize_name(subgrupo_nome)
    if not subgrupo_nome:
        raise ValueError("Subgrupo vazio não pode ser criado")
    subgrupo_key = f"{grupo.name.lower()}::{subgrupo_nome.lower()}"
    subgrupo = subgrupos_map.get(subgrupo_key)
    if subgrupo:
        return subgrupo
    subgrupo = db.query(ChartAccountSubgroup).filter(
        func.trim(func.lower(ChartAccountSubgroup.name)) == subgrupo_nome.lower(),
        ChartAccountSubgroup.group_id == grupo.id,
        ChartAccountSubgroup.tenant_id == tenant.id,
    ).first()
    if not subgrupo:
        subgrupo = ChartAccountSubgroup(
            id=str(uuid4()),
            tenant_id=tenant.id,
            code=generate_code(subgrupo_nome, "SG"),
            name=subgrupo_nome,
            description=f"Subgrupo: {subgrupo_nome}",
            group_id=grupo.id,
            is_active=True,
        )
        db.add(subgrupo)
        db.commit()
        db.refresh(subgrupo)
        logger.stats['subgrupos_criados'] += 1
        logger.log(f"Subgrupo criado: {subgrupo_nome} (Grupo: {grupo.name})", "SUCCESS")
    else:
        logger.stats['subgrupos_existentes'] += 1
    subgrupos_map[subgrupo_key] = subgrupo
    return subgrupo


def get_or_create_account(
    db: Session,
    tenant: Tenant,
    contas_map: Dict[str, ChartAccount],
    subgrupo: ChartAccountSubgroup,
    conta_nome: str,
    grupo_nome: str,
) -> ChartAccount:
    conta_nome = _normalize_name(conta_nome)
    if not conta_nome:
        raise ValueError("Conta vazia não pode ser criada")
    conta_key = f"{subgrupo.group_id}::{subgrupo.id}::{conta_nome.lower()}"
    conta = contas_map.get(conta_key)
    if conta:
        return conta
    conta = db.query(ChartAccount).filter(
        func.trim(func.lower(ChartAccount.name)) == conta_nome.lower(),
        ChartAccount.subgroup_id == subgrupo.id,
        ChartAccount.tenant_id == tenant.id,
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
            is_active=True,
        )
        db.add(conta)
        db.commit()
        db.refresh(conta)
        logger.stats['contas_criadas'] += 1
        logger.log(f"Conta criada: {conta_nome} (Subgrupo: {subgrupo.name})", "SUCCESS")
    else:
        logger.stats['contas_existentes'] += 1
    contas_map[conta_key] = conta
    return conta
    
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
    """Converte valor monetário (BRL) para Decimal sem inflar valores.

    Regras:
    - Se tiver "." e ",": assume "." como milhar e "," como decimal (ex: 1.234,56).
    - Se tiver só ",": assume "," como decimal (ex: 1234,56).
    - Se tiver só ".": assume "." como decimal (ex: 1234.56).
    """
    if pd.isna(value) or value == "" or value is None:
        return Decimal("0")

    s = str(value).strip()
    s = s.replace("R$", "").replace("$", "").replace(" ", "")
    if s == "":
        return Decimal("0")

    has_dot = "." in s
    has_comma = "," in s

    try:
        if has_dot and has_comma:
            s_clean = s.replace(".", "").replace(",", ".")
        elif has_comma:
            s_clean = s.replace(",", ".")
        else:
            s_clean = s
        return Decimal(s_clean)
    except Exception:
        logger.log(f"Erro ao converter valor: {value}", "WARNING")
        return Decimal("0")

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
    
    # Remover microsegundos se existirem
    if '.' in value_str and ' ' in value_str:
        # Formato: "2025-09-01 00:00:00.000000"
        parts = value_str.split('.')
        value_str = parts[0]
    
    # Formatos esperados (com e sem hora)
    formats = [
        "%Y-%m-%d %H:%M:%S",  # 2025-09-01 00:00:00
        "%Y-%m-%d",           # 2025-09-01
        "%d/%m/%Y %H:%M:%S",  # 01/09/2025 00:00:00
        "%d/%m/%Y",           # 01/09/2025
        "%d-%m-%Y %H:%M:%S",  # 01-09-2025 00:00:00
        "%d-%m-%Y",           # 01-09-2025
        "%d/%m/%y",           # 01/09/25
        "%d-%m-%y",           # 01-09-25
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

# Importar determine_transaction_type de seed_utils (versão corrigida)
from scripts.seed_utils import determine_transaction_type

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
# FUNÇÕES DE LEITURA DO FLUXO DE CAIXA (SALDO INICIAL E ORDEM)
# ============================================================================

def _find_month_header_row(df: pd.DataFrame) -> Optional[int]:
    max_scan = min(10, len(df))
    for idx in range(max_scan):
        row = df.iloc[idx].astype(str).str.strip().str.upper()
        if "JANEIRO" in row.values and "FEVEREIRO" in row.values:
            return idx
    return None

def _detect_label_column(df: pd.DataFrame, start_row: int) -> int:
    best_col = 1
    best_count = -1
    for col in df.columns:
        series = df.iloc[start_row:, col]
        count = int(series.apply(lambda v: isinstance(v, str) and v.strip() != "").sum())
        if count > best_count:
            best_count = count
            best_col = int(col)
    return best_col

def _parse_numeric(value) -> float:
    if value is None:
        return 0.0
    try:
        if isinstance(value, float) and pd.isna(value):
            return 0.0
    except Exception:
        pass
    if isinstance(value, (int, float, Decimal)):
        return float(value)
    if isinstance(value, str):
        cleaned = (
            value.replace("R$", "")
            .replace(" ", "")
            .replace(".", "")
            .replace(",", ".")
            .strip()
        )
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    return 0.0

def extract_cash_flow_settings(excel_file: Path) -> Dict[int, Dict[str, Any]]:
    """
    Extrai ordem das linhas e saldo do ano anterior a partir das abas de fluxo de caixa.
    Retorna: {year: {"line_order": [...], "saldo_ano_anterior": float}}
    """
    settings: Dict[int, Dict[str, any]] = {}
    try:
        excel = pd.ExcelFile(excel_file)
    except Exception as e:
        logger.log(f"Erro ao abrir arquivo para extrair fluxo de caixa: {str(e)}", "ERROR")
        return settings

    for sheet_name in excel.sheet_names:
        match = FLUXO_CAIXA_SHEETS_REGEX.search(sheet_name or "")
        if not match:
            continue
        try:
            year = int(match.group(1))
        except ValueError:
            continue

        try:
            df = pd.read_excel(excel, sheet_name=sheet_name, header=None, engine="openpyxl")
        except Exception as e:
            logger.log(f"Erro ao ler aba '{sheet_name}': {str(e)}", "ERROR")
            continue

        header_row_idx = _find_month_header_row(df)
        if header_row_idx is None:
            logger.log(f"Não foi possível localizar cabeçalhos de meses em '{sheet_name}'", "WARNING")
            continue

        header_row = df.iloc[header_row_idx].astype(str).str.strip().str.upper()
        month_columns = {month: idx for idx, month in enumerate(header_row) if month in MONTH_LABELS}
        data_start = header_row_idx + 2
        label_col = _detect_label_column(df, data_start)

        labels: List[str] = []
        saldo_ano_anterior = 0.0
        ignore_labels = {"previsão de fluxo de caixa", "ano do fluxo:"}

        for row_idx in range(data_start, len(df)):
            raw_label = df.iloc[row_idx, label_col]
            if raw_label is None or (isinstance(raw_label, float) and pd.isna(raw_label)):
                continue
            label = str(raw_label).strip()
            if not label:
                continue
            lower_label = label.lower()
            if lower_label in ignore_labels:
                continue
            if label.isdigit() and int(label) == year:
                continue

            labels.append(label)

            if lower_label == "saldo do ano anterior":
                for month in MONTH_LABELS:
                    col_idx = month_columns.get(month)
                    if col_idx is None:
                        continue
                    previsto_val = _parse_numeric(df.iloc[row_idx, col_idx])
                    realizado_val = _parse_numeric(df.iloc[row_idx, col_idx + 1]) if col_idx + 1 < len(df.columns) else 0.0
                    if previsto_val:
                        saldo_ano_anterior = previsto_val
                        break
                    if realizado_val:
                        saldo_ano_anterior = realizado_val
                        break

        settings[year] = {
            "line_order": labels,
            "saldo_ano_anterior": saldo_ano_anterior,
        }
        logger.log(
            f"Fluxo de caixa extraído: {sheet_name} (ano {year}) com {len(labels)} linhas",
            "INFO",
        )

    return settings


def extract_cash_flow_forecast_values(excel_file: Path) -> Dict[int, Dict[str, Dict[str, float]]]:
    """
    Extrai valores previstos por linha/mês da aba de previsão do fluxo de caixa.
    Retorna: {year: {label: {MONTH_LABEL: value}}}
    """
    results: Dict[int, Dict[str, Dict[str, float]]] = {}
    try:
        excel = pd.ExcelFile(excel_file)
    except Exception as e:
        logger.log(f"Erro ao abrir arquivo para extrair valores previstos: {str(e)}", "ERROR")
        return results

    for sheet_name in excel.sheet_names:
        match = FLUXO_CAIXA_SHEETS_REGEX.search(sheet_name or "")
        if not match:
            continue
        try:
            year = int(match.group(1))
        except ValueError:
            continue

        try:
            df = pd.read_excel(excel, sheet_name=sheet_name, header=None, engine="openpyxl")
        except Exception as e:
            logger.log(f"Erro ao ler aba '{sheet_name}': {str(e)}", "ERROR")
            continue

        header_row_idx = _find_month_header_row(df)
        if header_row_idx is None:
            logger.log(f"Não foi possível localizar cabeçalhos de meses em '{sheet_name}'", "WARNING")
            continue

        header_row = df.iloc[header_row_idx].astype(str).str.strip().str.upper()
        month_columns = {month: idx for idx, month in enumerate(header_row) if month in MONTH_LABELS}
        data_start = header_row_idx + 2
        label_col = _detect_label_column(df, data_start)

        year_values: Dict[str, Dict[str, float]] = {}
        ignore_labels = {"previsão de fluxo de caixa", "ano do fluxo:"}

        for row_idx in range(data_start, len(df)):
            raw_label = df.iloc[row_idx, label_col]
            if raw_label is None or (isinstance(raw_label, float) and pd.isna(raw_label)):
                continue
            label = str(raw_label).strip()
            if not label:
                continue
            lower_label = label.lower()
            if lower_label in ignore_labels:
                continue
            if label.isdigit() and int(label) == year:
                continue

            months: Dict[str, float] = {}
            for month in MONTH_LABELS:
                col_idx = month_columns.get(month)
                value = df.iloc[row_idx, col_idx] if col_idx is not None else 0
                months[month] = _parse_numeric(value)

            year_values[label] = months

        if year_values:
            results[year] = year_values
            logger.log(
                f"Valores previstos extraídos: {sheet_name} (ano {year}) com {len(year_values)} linhas",
                "INFO",
            )

    return results

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
            col_lower = str(col).lower().strip()
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
        
        last_grupo_nome = ""
        last_subgrupo_nome = ""
        for row_num, row in df.iterrows():
            try:
                # Parse dos campos
                conta_nome = str(row[column_map['conta']]).strip() if pd.notna(row[column_map['conta']]) else ""
                subgrupo_nome = str(row[column_map['subgrupo']]).strip() if pd.notna(row[column_map['subgrupo']]) else ""
                grupo_nome = str(row[column_map['grupo']]).strip() if pd.notna(row[column_map['grupo']]) else ""
                escolha = ""
                if 'escolha' in column_map:
                    escolha = str(row[column_map['escolha']]).strip() if pd.notna(row[column_map['escolha']]) else ""

                if _is_numeric_label(grupo_nome) or _is_numeric_label(subgrupo_nome) or _is_numeric_label(conta_nome):
                    continue

                if not grupo_nome:
                    grupo_nome = last_grupo_nome
                if not subgrupo_nome:
                    subgrupo_nome = last_subgrupo_nome

                if not grupo_nome:
                    continue

                if escolha and escolha.lower() not in ['usar', 'use', 'sim', 'yes', '']:
                    continue

                grupo = get_or_create_group(db, tenant, grupos_map, grupo_nome)

                if subgrupo_nome:
                    subgrupo = get_or_create_subgroup(db, tenant, subgrupos_map, grupo, subgrupo_nome)
                    last_subgrupo_nome = subgrupo_nome
                else:
                    subgrupo = None

                last_grupo_nome = grupo_nome

                if conta_nome and subgrupo:
                    get_or_create_account(db, tenant, contas_map, subgrupo, conta_nome, grupo_nome)
                
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
    """
    Seed de lançamentos previstos a partir do Excel
    
    REGRAS DE EXCLUSÃO DE LINHA (linhas ignoradas):
    - data_prevista (mês) vazia ou inválida (parse_date retorna None)
    - conta vazia ou não encontrada no banco
    - valor vazia ou inválida (parse_currency retorna 0 ou <= 0)
    - grupo não encontrado (quando necessário)
    - subgrupo não encontrado (quando necessário)
    - lançamento já existe (idempotência - mesma data, conta, valor, tenant, BU)
    - exceção durante processamento da linha
    """
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
            col_lower = str(col).lower().strip()
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

        # Heurística: preferir coluna com datas completas (dia != 1) quando houver
        date_candidates = []
        for col in df.columns:
            try:
                series = pd.to_datetime(df[col], errors='coerce')
            except Exception:
                continue
            valid_ratio = series.notna().mean()
            if valid_ratio >= 0.6:
                day_not_one_ratio = (series.dt.day != 1).mean()
                date_candidates.append((day_not_one_ratio, col))
        if date_candidates:
            date_candidates.sort(reverse=True, key=lambda x: x[0])
            best_ratio, best_col = date_candidates[0]
            # Se pelo menos 10% das datas não são dia 1, assumir que é a coluna correta
            if best_ratio >= 0.1:
                column_map['data_prevista'] = best_col
        
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

                if _is_numeric_label(grupo_nome):
                    grupo_nome = ""
                if _is_numeric_label(subgrupo_nome):
                    subgrupo_nome = ""
                if _is_numeric_label(conta_nome):
                    conta_nome = ""
                
                # Pular linhas vazias
                if not mes_str or not valor_str:
                    logger.stats['linhas_ignoradas'] += 1
                    continue
                
                # Parse de data e valor
                data_prevista = parse_date(mes_str)
                if not data_prevista:
                    logger.stats['linhas_ignoradas'] += 1
                    continue
                
                valor = parse_currency(valor_str)
                
                conta = None
                if conta_nome:
                    for _, c in contas_map.items():
                        if c.name.lower() == conta_nome.lower():
                            conta = c
                            break

                # Fallback: tentar casar conta por aproximação quando grupo/subgrupo vierem vazios
                if conta is None and conta_nome and not subgrupo_nome and not grupo_nome:
                    conta_lower = conta_nome.lower()
                    for _, c in contas_map.items():
                        c_lower = c.name.lower()
                        if conta_lower in c_lower or c_lower in conta_lower:
                            conta = c
                            break

                if conta and not subgrupo_nome:
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
                    grupo = get_or_create_group(db, tenant, grupos_map, grupo_nome)
                else:
                    grupo = None
                if subgrupo_nome and grupo:
                    subgrupo = get_or_create_subgroup(db, tenant, subgrupos_map, grupo, subgrupo_nome)
                
                # Usar subgrupo e grupo da conta se não encontrou
                if not subgrupo and conta:
                    subgrupo = db.query(ChartAccountSubgroup).filter(
                        ChartAccountSubgroup.id == conta.subgroup_id
                    ).first()
                if not grupo and subgrupo:
                    grupo = db.query(ChartAccountGroup).filter(
                        ChartAccountGroup.id == subgrupo.group_id
                    ).first()
                # Se ainda não tem grupo/subgrupo, usar fallback para "Despesas Administrativas"
                if not subgrupo and not grupo:
                    fallback_subgrupo = None
                    for key, sg in subgrupos_map.items():
                        if key.strip().lower() == "despesas administrativas":
                            fallback_subgrupo = sg
                            break
                    if fallback_subgrupo:
                        subgrupo = fallback_subgrupo
                        grupo = db.query(ChartAccountGroup).filter(
                            ChartAccountGroup.id == subgrupo.group_id
                        ).first()
                if not grupo or not subgrupo:
                    raise ValueError(
                        f"Grupo/Subgrupo não encontrado para conta '{conta_nome}' (linha {row_num + 2})"
                    )

                if conta_nome:
                    conta = get_or_create_account(db, tenant, contas_map, subgrupo, conta_nome, grupo.name)
                else:
                    raise ValueError(f"Conta vazia na linha {row_num + 2}")
                
                # Verificar se já existe (idempotência)
                import_ref = f"previsto:{row_num + 2}"
                existing = db.query(LancamentoPrevisto).filter(
                    LancamentoPrevisto.import_ref == import_ref,
                    LancamentoPrevisto.tenant_id == tenant.id,
                    LancamentoPrevisto.business_unit_id == business_unit.id,
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
                    import_ref=import_ref,
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
                logger.stats['lancamentos_previstos_criados'] += 1
                
                # Commit em batch a cada 50 registros para melhor performance
                if logger.stats['lancamentos_previstos_criados'] % 50 == 0:
                    db.commit()
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

def get_or_create_liquidation_account(
    db: Session,
    tenant: Tenant,
    business_unit: BusinessUnit,
    codigo: str
) -> Optional[LiquidationAccount]:
    """
    Cria ou obtém uma conta de liquidação baseada no código (scb, cef, cx, etc.)
    """
    if not codigo:
        return None
    
    codigo_upper = codigo.upper().strip()
    
    # Buscar existente
    liquidation_account = db.query(LiquidationAccount).filter(
        LiquidationAccount.code == codigo_upper,
        LiquidationAccount.tenant_id == tenant.id
    ).first()
    
    if liquidation_account:
        return liquidation_account
    
    # Determinar tipo baseado no código
    account_type = LiquidationAccountType.OTHER
    name = codigo_upper
    
    if codigo_upper in ["SCB", "CEF", "BANCO", "BANC"]:
        account_type = LiquidationAccountType.BANK_ACCOUNT
        if codigo_upper == "SCB":
            name = "SCB - Conta Bancária"
        elif codigo_upper == "CEF":
            name = "CEF - Caixa Econômica Federal"
        else:
            name = f"{codigo_upper} - Conta Bancária"
    elif codigo_upper in ["CX", "CAIXA", "CASH"]:
        account_type = LiquidationAccountType.CASH
        name = "Caixa Físico"
    elif codigo_upper in ["INV", "INVESTIMENTO", "APLICAÇÃO", "APLICACAO"]:
        account_type = LiquidationAccountType.INVESTMENT
        name = "Investimentos"
    
    # Criar nova conta de liquidação
    liquidation_account = LiquidationAccount(
        id=str(uuid4()),
        tenant_id=tenant.id,
        business_unit_id=business_unit.id,
        code=codigo_upper,
        name=name,
        description=f"Conta de liquidação: {codigo_upper}",
        account_type=account_type,
        is_active=True,
        is_default=False
    )
    
    db.add(liquidation_account)
    db.commit()
    db.refresh(liquidation_account)
    
    return liquidation_account

def _get_classification_reason(grupo_nome: str, subgrupo_nome: str, transaction_type) -> str:
    """Retorna motivo da classificação para logging"""
    grupo_lower = (grupo_nome or "").lower().strip()
    subgrupo_lower = (subgrupo_nome or "").lower().strip()
    tipo_value = transaction_type.value if hasattr(transaction_type, 'value') else str(transaction_type)
    
    if tipo_value == "RECEITA":
        if any(kw in grupo_lower for kw in ["receita", "venda", "renda", "faturamento", "vendas"]):
            return "mapeamento_por_grupo_receita"
        return "mapeamento_por_subgrupo_receita"
    
    if tipo_value == "CUSTO":
        if any(kw in grupo_lower for kw in ["custo", "custos"]):
            return "mapeamento_por_grupo_custo"
        if subgrupo_lower and any(kw in subgrupo_lower for kw in ["custo", "custos", "mercadoria", "produto", "mão de obra", "mao de obra", "serviços prestados", "servicos prestados"]):
            return "mapeamento_por_subgrupo_custo"
        return "mapeamento_por_subgrupo_custo_palavras_chave"
    
    if tipo_value == "DESPESA":
        if any(kw in grupo_lower for kw in ["despesa", "gasto", "operacional", "administrativa"]):
            return "mapeamento_por_grupo_despesa"
        if subgrupo_lower and any(kw in subgrupo_lower for kw in ["despesa", "gasto", "marketing", "administrativa"]):
            return "mapeamento_por_subgrupo_despesa"
        return "default_despesa"
    
    return "desconhecido"

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
    """
    Seed de lançamentos diários a partir do Excel
    
    REGRAS DE EXCLUSÃO DE LINHA (linhas ignoradas):
    - data_movimentacao vazia ou inválida (parse_date retorna None)
    - valor vazia ou inválida (parse_currency retorna 0 ou <= 0)
    - grupo não encontrado no banco/planilha
    - subgrupo não encontrado no banco/planilha
    - conta não encontrada no subgrupo
    - lançamento já existe (idempotência - mesma data, conta, valor, tenant, BU)
    - exceção durante processamento da linha
    """
    logger.log("Iniciando seed de Lançamentos Diários...", "STEP")
    print(f"🔍 [SEED] Iniciando seed_lancamentos_diarios")
    print(f"   Arquivo: {excel_file}")
    print(f"   Existe: {excel_file.exists()}")
    
    # Encontrar a aba correta
    sheet_name = find_sheet_in_excel(excel_file, LANCAMENTOS_DIARIOS_SHEETS)
    if not sheet_name:
        error_msg = "Aba de Lançamentos Diários não encontrada"
        logger.log(error_msg, "ERROR")
        logger.stats['erros'].append(error_msg)
        print(f"❌ [SEED] {error_msg}")
        print(f"   Abas procuradas: {LANCAMENTOS_DIARIOS_SHEETS}")
        try:
            excel_file_obj = pd.ExcelFile(excel_file)
            print(f"   Abas disponíveis: {excel_file_obj.sheet_names}")
        except Exception as e:
            print(f"   Erro ao ler abas: {e}")
        return
    
    print(f"✅ [SEED] Aba encontrada: '{sheet_name}'")
    
    try:
        # Ler dados da planilha
        print(f"📖 [SEED] Lendo dados da aba '{sheet_name}'...")
        df = read_excel_sheet(excel_file, sheet_name)
        print(f"📊 [SEED] DataFrame lido: {len(df)} linhas, {len(df.columns)} colunas")
        print(f"   Colunas: {list(df.columns)[:10]}...")
        
        if df.empty:
            error_msg = "Nenhum dado encontrado na aba de Lançamentos Diários"
            logger.log(error_msg, "ERROR")
            logger.stats['erros'].append(error_msg)
            print(f"❌ [SEED] {error_msg}")
            return
        
        # Normalizar nomes de colunas
        df.columns = df.columns.str.strip()
        column_map = {}
        for col in df.columns:
            col_lower = str(col).lower().strip()
            if 'data' in col_lower and 'movimentação' in col_lower or 'movimentacao' in col_lower:
                column_map['data_movimentacao'] = col
            elif 'data' in col_lower and 'data_movimentacao' not in column_map:
                column_map['data_movimentacao'] = col
            if 'subgrupo' in col_lower and 'subgrupo' not in column_map:
                column_map['subgrupo'] = col
            if 'grupo' in col_lower and 'subgrupo' not in col_lower and 'grupo' not in column_map:
                column_map['grupo'] = col
            if 'conta' in col_lower and 'subgrupo' not in col_lower and 'grupo' not in col_lower and 'conta' not in column_map:
                column_map['conta'] = col
            if 'valor' in col_lower and 'valor' not in column_map:
                column_map['valor'] = col
            if ('observação' in col_lower or 'observacao' in col_lower) and 'observacoes' not in column_map:
                column_map['observacoes'] = col
            if 'liquidação' in col_lower or 'liquidacao' in col_lower:
                column_map['liquidacao'] = col
        
        # Verificar colunas mínimas
        if 'data_movimentacao' not in column_map or 'valor' not in column_map:
            logger.log(f"Colunas necessárias não encontradas. Colunas disponíveis: {list(df.columns)}", "ERROR")
            logger.stats['erros'].append("Colunas necessárias não encontradas em Lançamentos Diários")
            return
        
        # Mapas auxiliares para fallback quando grupo estiver vazio na planilha
        group_by_id = {g.id: g for g in grupos_map.values()}
        subgroup_by_id = {sg.id: sg for sg in subgrupos_map.values()}
        subgroups_by_name = {}
        for sg in subgrupos_map.values():
            key = sg.name.strip().lower()
            subgroups_by_name.setdefault(key, []).append(sg)
        accounts_by_name = {}
        for acc in contas_map.values():
            key = acc.name.strip().lower()
            accounts_by_name.setdefault(key, []).append(acc)

        # Processar em lotes para melhor performance
        BATCH_SIZE = 50  # Reduzir tamanho do lote para commits mais frequentes
        lancamentos_batch = []
        total_rows = len(df)
        logger.log(f"Processando {total_rows} linhas de lançamentos diários...", "INFO")
        logger.log(f"Progresso será mostrado a cada {BATCH_SIZE} lançamentos criados", "INFO")
        
        processed_count = 0
        last_log_time = time.time()
        start_time = time.time()
        for row_num, row in df.iterrows():
            processed_count += 1
            # Mostrar progresso a cada 50 linhas processadas OU a cada 10 segundos
            current_time = time.time()
            if processed_count % 50 == 0 or (current_time - last_log_time) >= 10:
                created_count = logger.stats['lancamentos_diarios_criados']
                skipped_count = logger.stats['linhas_ignoradas']
                elapsed = current_time - start_time
                rate = processed_count / elapsed if elapsed > 0 else 0
                remaining = (total_rows - processed_count) / rate if rate > 0 else 0
                progress_pct = (processed_count / total_rows) * 100 if total_rows > 0 else 0
                logger.log(f"📊 Progresso: {processed_count}/{total_rows} ({progress_pct:.1f}%) | {created_count} criados | {skipped_count} ignorados | Velocidade: {rate:.1f} linhas/s | Tempo restante: {remaining/60:.1f} min", "INFO")
                last_log_time = current_time
            try:
                # Parse dos campos
                data_mov_str = str(row[column_map['data_movimentacao']]) if pd.notna(row[column_map['data_movimentacao']]) else ""
                subgrupo_nome = ""
                grupo_nome = ""
                conta_nome = ""  # CORREÇÃO: Buscar conta específica da planilha
                if 'subgrupo' in column_map:
                    subgrupo_nome = str(row[column_map['subgrupo']]).strip() if pd.notna(row[column_map['subgrupo']]) else ""
                if 'grupo' in column_map:
                    grupo_nome = str(row[column_map['grupo']]).strip() if pd.notna(row[column_map['grupo']]) else ""
                if 'conta' in column_map:
                    conta_nome = str(row[column_map['conta']]).strip() if pd.notna(row[column_map['conta']]) else ""
                valor_str = str(row[column_map['valor']]) if pd.notna(row[column_map['valor']]) else ""
                observacoes = ""
                if 'observacoes' in column_map:
                    observacoes = str(row[column_map['observacoes']]).strip() if pd.notna(row[column_map['observacoes']]) else ""
                
                # CORREÇÃO CRÍTICA: Remover espaços extras no final (problema comum em Excel)
                grupo_nome = grupo_nome.rstrip()
                subgrupo_nome = subgrupo_nome.rstrip()
                conta_nome = conta_nome.rstrip()

                if _is_numeric_label(grupo_nome):
                    grupo_nome = ""
                if _is_numeric_label(subgrupo_nome):
                    subgrupo_nome = ""
                if _is_numeric_label(conta_nome):
                    conta_nome = ""
                
                # Ler coluna de liquidação (código da conta: scb, cef, cx, etc.)
                liquidacao_codigo = None
                if 'liquidacao' in column_map:
                    liquidacao_val = row[column_map['liquidacao']] if pd.notna(row[column_map['liquidacao']]) else None
                    if liquidacao_val is not None:
                        liquidacao_codigo = str(liquidacao_val).strip().lower()
                        if not liquidacao_codigo or liquidacao_codigo == 'nan':
                            liquidacao_codigo = None
                
                # Pular linhas vazias
                if not data_mov_str or not valor_str:
                    if os.getenv("COST_DEBUG") == "1":
                        log_entry = {
                            "excel_row": row_num + 2,
                            "group": grupo_nome,
                            "subgroup": subgrupo_nome,
                            "description": "",
                            "month": None,
                            "year": None,
                            "value": 0,
                            "tipo_resultante": None,
                            "motivo": "dados_vazios",
                            "action": "SKIPPED",
                            "skip_reason": "data_mov ou valor vazio"
                        }
                        log_file = backend_path / "artifacts" / "seed_classification_2025.jsonl"
                        log_file.parent.mkdir(exist_ok=True)
                        with open(log_file, "a", encoding="utf-8") as f:
                            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                    logger.stats['linhas_ignoradas'] += 1
                    continue
                
                # Parse de data e valor
                data_movimentacao = parse_date(data_mov_str)
                if not data_movimentacao:
                    if os.getenv("COST_DEBUG") == "1":
                        log_entry = {
                            "excel_row": row_num + 2,
                            "group": grupo_nome,
                            "subgroup": subgrupo_nome,
                            "description": "",
                            "month": None,
                            "year": None,
                            "value": float(parse_currency(valor_str)),
                            "tipo_resultante": None,
                            "motivo": "data_invalida",
                            "action": "SKIPPED",
                            "skip_reason": "data não parseada"
                        }
                        log_file = backend_path / "artifacts" / "seed_classification_2025.jsonl"
                        log_file.parent.mkdir(exist_ok=True)
                        with open(log_file, "a", encoding="utf-8") as f:
                            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                    logger.stats['linhas_ignoradas'] += 1
                    continue
                
                valor = parse_currency(valor_str)
                
                # Buscar grupo e subgrupo
                grupo = None
                subgrupo = None
                conta = None
                
                if grupo_nome:
                    grupo = get_or_create_group(db, tenant, grupos_map, grupo_nome)
                
                if subgrupo_nome and grupo:
                    subgrupo = get_or_create_subgroup(db, tenant, subgrupos_map, grupo, subgrupo_nome)

                # Fallback: se grupo não veio na planilha, tentar inferir pelo subgrupo/conta
                if not grupo:
                    if subgrupo_nome:
                        candidates = subgroups_by_name.get(subgrupo_nome.lower().strip(), [])
                        if len(candidates) == 1:
                            subgrupo = candidates[0]
                            grupo = group_by_id.get(subgrupo.group_id)
                    if not grupo and conta_nome:
                        acc_candidates = accounts_by_name.get(conta_nome.lower().strip(), [])
                        if len(acc_candidates) == 1:
                            conta = acc_candidates[0]
                            subgrupo = subgroup_by_id.get(conta.subgroup_id)
                            if subgrupo:
                                grupo = group_by_id.get(subgrupo.group_id)

                if grupo and not grupo_nome:
                    grupo_nome = grupo.name
                if subgrupo and not subgrupo_nome:
                    subgrupo_nome = subgrupo.name
                
                if not grupo or not subgrupo:
                    raise ValueError(
                        f"Grupo/Subgrupo não encontrado na linha {row_num + 2}. Grupo='{grupo_nome}', Subgrupo='{subgrupo_nome}'"
                    )
                
                if conta is None and conta_nome:
                    conta = get_or_create_account(db, tenant, contas_map, subgrupo, conta_nome, grupo.name)
                if conta is None and not conta_nome and subgrupo:
                    conta = next(
                        (c for c in contas_map.values() if getattr(c, "subgroup_id", None) == subgrupo.id),
                        None
                    )
                    if conta is None:
                        conta = get_or_create_account(db, tenant, contas_map, subgrupo, subgrupo.name, grupo.name)
                if not conta:
                    raise ValueError(f"Conta não encontrada na linha {row_num + 2}")
                
                # Verificar se já existe (idempotência)
                # Usar referência de importação por linha para permitir duplicidades legítimas
                import_ref = f"diario:{row_num + 2}"

                existing = db.query(LancamentoDiario).filter(
                    LancamentoDiario.import_ref == import_ref,
                    LancamentoDiario.tenant_id == tenant.id,
                    LancamentoDiario.business_unit_id == business_unit.id
                ).first()
                
                if existing:
                    if os.getenv("COST_DEBUG") == "1" and data_movimentacao.year == 2025:
                        log_entry = {
                            "excel_row": row_num + 2,
                            "group": grupo_nome,
                            "subgroup": subgrupo_nome,
                            "description": observacoes or f"Lançamento de {subgrupo_nome}",
                            "month": data_movimentacao.month,
                            "year": data_movimentacao.year,
                            "value": float(valor),
                            "tipo_resultante": existing.transaction_type.value if existing.transaction_type else None,
                            "motivo": "ja_existe",
                            "action": "SKIPPED",
                            "skip_reason": "lançamento já existe (idempotência)"
                        }
                        log_file = backend_path / "artifacts" / "seed_classification_2025.jsonl"
                        log_file.parent.mkdir(exist_ok=True)
                        with open(log_file, "a", encoding="utf-8") as f:
                            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                    logger.stats['lancamentos_diarios_existentes'] += 1
                    continue
                
                # Determinar tipo de transação
                transaction_type = determine_transaction_type(grupo_nome, subgrupo_nome)
                
                # Criar ou obter conta de liquidação se houver código
                liquidation_account_id = None
                if liquidacao_codigo:
                    liquidation_account = get_or_create_liquidation_account(
                        db, tenant, business_unit, liquidacao_codigo
                    )
                    if liquidation_account:
                        liquidation_account_id = liquidation_account.id
                
                # Logging de classificação (se COST_DEBUG=1)
                if os.getenv("COST_DEBUG") == "1" and data_movimentacao.year == 2025:
                    log_entry = {
                        "excel_row": row_num + 2,
                        "group": grupo_nome,
                        "subgroup": subgrupo_nome,
                        "description": observacoes or f"Lançamento de {subgrupo_nome}",
                        "month": data_movimentacao.month,
                        "year": data_movimentacao.year,
                        "value": float(valor),
                        "tipo_resultante": transaction_type.value,
                        "motivo": _get_classification_reason(grupo_nome, subgrupo_nome, transaction_type),
                        "action": "INSERTED"
                    }
                    
                    log_file = backend_path / "artifacts" / "seed_classification_2025.jsonl"
                    log_file.parent.mkdir(exist_ok=True)
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                
                # Criar lançamento (adicionar ao lote)
                # CORREÇÃO: Se não há observações, usar número da linha do Excel para diferenciar
                # Isso permite múltiplos lançamentos legítimos sem observações
                if observacoes and observacoes.strip():
                    obs_final = observacoes
                else:
                    # Usar número da linha como identificador único para permitir múltiplos lançamentos
                    obs_final = f"Lançamento linha {row_num + 2}"
                
                lancamento = LancamentoDiario(
                    id=str(uuid4()),
                    data_movimentacao=data_movimentacao,
                    valor=valor,
                    liquidacao=None,  # Campo DateTime - manter None por enquanto
                    liquidation_account_id=liquidation_account_id,  # Conta de liquidação (scb, cef, cx, etc.)
                    observacoes=obs_final,
                    import_ref=import_ref,
                    conta_id=conta.id,
                    subgrupo_id=subgrupo.id,
                    grupo_id=grupo.id,
                    transaction_type=transaction_type,
                    status=TransactionStatus.LIQUIDADO,
                    tenant_id=tenant.id,
                    business_unit_id=business_unit.id,
                    created_by=user.id,
                    is_active=True
                )
                
                lancamentos_batch.append(lancamento)
                logger.stats['lancamentos_diarios_criados'] += 1
                
                # Commit em lotes
                if len(lancamentos_batch) >= BATCH_SIZE:
                    try:
                        logger.log(f"💾 Committing lote de {len(lancamentos_batch)} lançamentos...", "INFO")
                        db.add_all(lancamentos_batch)
                        db.commit()
                        logger.log(f"✅ Lote commitado: {logger.stats['lancamentos_diarios_criados']} lançamentos criados (linha {row_num + 2}/{total_rows})", "INFO")
                        lancamentos_batch = []
                    except Exception as e:
                        db.rollback()
                        logger.log(f"Erro ao commitar lote: {str(e)}", "ERROR")
                        # Tentar commit individual para o lote
                        for lanc in lancamentos_batch:
                            try:
                                db.add(lanc)
                                db.commit()
                            except:
                                db.rollback()
                                logger.stats['linhas_ignoradas'] += 1
                        lancamentos_batch = []
            
            except Exception as e:
                error_msg = f"Erro na linha {row_num + 2}: {str(e)}"
                logger.log(error_msg, "ERROR")
                logger.stats['erros'].append(error_msg)
                logger.stats['linhas_ignoradas'] += 1
                continue
        
        # Commit do lote final
        if lancamentos_batch:
            try:
                db.add_all(lancamentos_batch)
                db.commit()
                logger.log(f"✅ Lote final commitado: {len(lancamentos_batch)} lançamentos", "INFO")
            except Exception as e:
                db.rollback()
                logger.log(f"Erro ao commitar lote final: {str(e)}", "ERROR")
                # Tentar commit individual
                for lanc in lancamentos_batch:
                    try:
                        db.add(lanc)
                        db.commit()
                    except:
                        db.rollback()
                        logger.stats['linhas_ignoradas'] += 1
        
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
    parser.add_argument(
        '--reset-data',
        action='store_true',
        help='Apaga lançamentos diários e previstos do tenant antes de semear (use em staging).'
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

            # Opcional: reset de dados anteriores (corrige seeds inflados)
            if args.reset_data:
                logger.log("\n" + "-"*60, "STEP")
                logger.log("⚠️  Resetando lançamentos existentes do tenant antes de semear...", "WARNING")
                # CORREÇÃO: Filtrar apenas ano 2025 para não deletar dados de outros anos
                # IMPORTANTE: Deletar TODOS os lançamentos de 2025, independente de observações
                from datetime import date
                from sqlalchemy import and_
                
                # Deletar lançamentos diários de 2025
                deleted_diarios = db.query(LancamentoDiario).filter(
                    and_(
                        LancamentoDiario.tenant_id == tenant.id,
                        LancamentoDiario.data_movimentacao >= date(2025, 1, 1),
                        LancamentoDiario.data_movimentacao <= date(2025, 12, 31)
                    )
                ).delete(synchronize_session=False)
                
                # Deletar lançamentos previstos de 2025
                deleted_prev = db.query(LancamentoPrevisto).filter(
                    and_(
                        LancamentoPrevisto.tenant_id == tenant.id,
                        LancamentoPrevisto.data_prevista >= date(2025, 1, 1),
                        LancamentoPrevisto.data_prevista <= date(2025, 12, 31)
                    )
                ).delete(synchronize_session=False)
                
                db.commit()
                logger.log(f"✅ Removidos {deleted_diarios} lançamentos diários de 2025 e {deleted_prev} lançamentos previstos de 2025.", "SUCCESS")
                
                # Verificar se realmente foram deletados
                remaining_diarios = db.query(LancamentoDiario).filter(
                    and_(
                        LancamentoDiario.tenant_id == tenant.id,
                        LancamentoDiario.data_movimentacao >= date(2025, 1, 1),
                        LancamentoDiario.data_movimentacao <= date(2025, 12, 31)
                    )
                ).count()
                
                if remaining_diarios > 0:
                    logger.log(f"⚠️  ATENÇÃO: Ainda existem {remaining_diarios} lançamentos diários de 2025 após reset!", "WARNING")
                else:
                    logger.log(f"✅ Confirmado: Nenhum lançamento diário de 2025 restante após reset.", "SUCCESS")
            
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

            if logger.stats.get('erros'):
                raise RuntimeError("Seed finalizado com erros. Corrija a planilha e execute novamente.")
            
            logger.log("\n" + "="*60, "STEP")
            logger.log("✅ SEED CONCLUÍDO COM SUCESSO!", "SUCCESS")
            logger.log("="*60, "STEP")
            
            # Retornar exit code 0 em caso de sucesso
            sys.exit(0)
            
        except Exception as e:
            db.rollback()
            error_msg = f"Erro durante o seed: {str(e)}"
            logger.log(error_msg, "ERROR")
            logger.stats['erros'].append(error_msg)
            import traceback
            traceback.print_exc()
            sys.exit(1)
        finally:
            db.close()
    
    except Exception as e:
        logger.log(f"❌ Erro fatal: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
