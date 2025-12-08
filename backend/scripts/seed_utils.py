"""
Utilitários compartilhados para seed e validação.

Este módulo contém as funções de normalização e filtro usadas tanto no seed
quanto na validação, garantindo consistência entre os dois processos.
"""

import re
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
import pandas as pd

from app.models.lancamento_diario import TransactionType

# Nomes das abas (tentar diferentes variações)
PLANO_CONTAS_SHEETS = ["Plano de contas|LLM", "Plano de contas", "Plano de Contas", "Plano de Contas|LLM"]
LANCAMENTOS_DIARIOS_SHEETS = ["Lançamento Diário", "Lançamento Diario", "Lancamento Diario", "Lançamentos Diários"]
LANCAMENTOS_PREVISTOS_SHEETS = ["Lançamentos Previstos", "Lancamentos Previstos", "Previsões", "Previsoes"]


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
    
    return None


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


def generate_code(name: str, prefix: str = "") -> str:
    """Gera código único baseado no nome"""
    # Remover acentos e caracteres especiais
    name_clean = re.sub(r'[^a-zA-Z0-9\s]', '', name)
    # Pegar primeiras letras de cada palavra
    if prefix:
        return f"{prefix}{name_clean[:3].upper()}"
    return name_clean[:3].upper()


def find_sheet_in_excel(excel_file, sheet_names: List[str]) -> Optional[str]:
    """Encontra a primeira aba que existe no arquivo Excel"""
    try:
        excel = pd.ExcelFile(excel_file)
        available_sheets = excel.sheet_names
        
        for sheet_name in sheet_names:
            if sheet_name in available_sheets:
                return sheet_name
        
        return None
    except Exception:
        return None


def read_excel_sheet(excel_file, sheet_name: str) -> pd.DataFrame:
    """Lê uma aba específica do arquivo Excel"""
    try:
        df = pd.read_excel(excel_file, sheet_name=sheet_name, engine='openpyxl')
        return df
    except Exception:
        return pd.DataFrame()

