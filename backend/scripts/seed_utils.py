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
            # Formato brasileiro típico: milhar com ponto, decimal com vírgula
            s_clean = s.replace(".", "").replace(",", ".")
        elif has_comma:
            # Apenas vírgula, tratar como decimal
            s_clean = s.replace(",", ".")
        else:
            # Apenas ponto ou número puro, tratar ponto como decimal
            s_clean = s
        return Decimal(s_clean)
    except Exception:
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
    
    return None


def determine_transaction_type(grupo_nome: str, subgrupo_nome: Optional[str] = None) -> TransactionType:
    """
    Determina o tipo de transação baseado no grupo e subgrupo.
    
    REGRA CRÍTICA: Grupos com "Custos" (singular ou plural) devem ser CUSTO.
    Ordem de verificação:
    1. EXCLUSÕES (Deduções, Movimentações Não Operacionais)
    2. RECEITA (palavras-chave: receita, venda, renda, faturamento, vendas)
    3. CUSTO (palavras-chave: custo, custos - no grupo OU subgrupo)
    4. DESPESA (padrão)
    """
    if not grupo_nome:
        return TransactionType.DESPESA
    
    grupo_lower = grupo_nome.lower().strip()
    subgrupo_lower = (subgrupo_nome or "").lower().strip()
    
    # 0. EXCLUSÕES EXPLÍCITAS - Não devem ser classificadas como DESPESA/CUSTO/RECEITA
    # "Deduções" não são despesas - são reduções de receita
    if "dedução" in grupo_lower or "deducao" in grupo_lower or "deduções" in grupo_lower or "deducoes" in grupo_lower:
        # Deduções devem ser tratadas separadamente ou como RECEITA negativa
        # Por enquanto, retornar DESPESA mas será filtrado no cálculo
        # TODO: Criar tipo DEDUCAO ou tratar como receita negativa
        return TransactionType.DESPESA  # Temporário - será filtrado
    
    # "Movimentações Não Operacionais" não são despesas operacionais
    if "movimentações não operacionais" in grupo_lower or "movimentacoes nao operacionais" in grupo_lower or \
       "movimentações nao operacionais" in grupo_lower or "movimentacoes não operacionais" in grupo_lower:
        # Movimentações não operacionais não devem entrar no cálculo de despesas operacionais
        # Por enquanto, retornar DESPESA mas será filtrado no cálculo
        return TransactionType.DESPESA  # Temporário - será filtrado
    
    # 1. Verificar RECEITA
    receita_keywords = ["receita", "venda", "renda", "faturamento", "vendas"]
    if any(keyword in grupo_lower for keyword in receita_keywords):
        return TransactionType.RECEITA
    
    # 2. Verificar CUSTO (PRIORIDADE: grupo contém "custo" ou "custos")
    # CORREÇÃO CRÍTICA: "Custos" no nome do grupo deve ser CUSTO
    custo_keywords_grupo = ["custo", "custos"]
    custo_keywords_subgrupo = ["custo", "custos", "mercadoria", "produto", "mão de obra", "mao de obra", "serviços prestados", "servicos prestados"]
    
    # Se o grupo contém "custo" ou "custos", é CUSTO (sem exceções)
    if any(keyword in grupo_lower for keyword in custo_keywords_grupo):
        return TransactionType.CUSTO
    
    # Se o subgrupo contém palavras-chave de custo, também é CUSTO
    if subgrupo_lower and any(keyword in subgrupo_lower for keyword in custo_keywords_subgrupo):
        return TransactionType.CUSTO
    
    # 3. Verificar DESPESA
    despesa_keywords_grupo = ["despesa", "gasto", "operacional", "administrativa"]
    despesa_keywords_subgrupo = ["despesa", "gasto", "marketing", "administrativa"]
    
    if any(keyword in grupo_lower for keyword in despesa_keywords_grupo) or \
       (subgrupo_lower and any(keyword in subgrupo_lower for keyword in despesa_keywords_subgrupo)):
        return TransactionType.DESPESA
    
    # 4. Padrão: DESPESA
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

