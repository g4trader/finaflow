#!/usr/bin/env python3
"""
Script de Validação Profunda - Dashboard vs Planilha vs Banco (Auditoria)

Compara os totais mensais (receita, despesa, custo, saldo) entre:
- Planilha BRUTA do cliente (Excel, sem filtros)
- Planilha FILTRADA (aplicando regras do seed)
- Banco de dados STAGING
- Endpoints de dashboard do backend

USO:
    python -m scripts.validate_dashboard_against_client_sheet --file data/fluxo_caixa_2025.xlsx --year 2025

REQUISITOS:
    - Arquivo Excel (.xlsx) na pasta backend/data/
    - Variável de ambiente DATABASE_URL configurada
    - Variável de ambiente BACKEND_URL configurada (opcional, default: staging)
    - Dependências: pandas, openpyxl, requests
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

try:
    import pandas as pd
    import requests
except ImportError as e:
    print(f"❌ Erro: dependência não instalada: {e}")
    print("Execute: pip install pandas openpyxl requests")
    sys.exit(1)

from sqlalchemy.orm import Session
from app.database import SessionLocal

# Importar TODOS os modelos para garantir que os relacionamentos sejam resolvidos
from app.models.auth import User, Tenant, BusinessUnit, UserRole, UserStatus
from app.models.conta_bancaria import ContaBancaria
from app.models.caixa import Caixa
from app.models.investimento import Investimento
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
from app.models.validation_status import (
    DashboardValidationStatus,
    ValidationStatus
)

# Reutilizar funções do seed_utils
from scripts.seed_utils import (
    parse_currency,
    parse_date,
    determine_transaction_type,
    find_sheet_in_excel,
    read_excel_sheet,
    LANCAMENTOS_DIARIOS_SHEETS,
    LANCAMENTOS_PREVISTOS_SHEETS
)

# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

DEFAULT_EXCEL_FILE = backend_path / "data" / "fluxo_caixa_2025.xlsx"
DEFAULT_BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "https://finaflow-backend-staging-642830139828.us-central1.run.app"
)
TOLERANCE_ABS = Decimal("0.05")  # R$ 0,05
TOLERANCE_PCT = Decimal("0.1")   # 0,1%

# ============================================================================
# ESTRUTURAS DE DADOS
# ============================================================================

# Estrutura de resumo mensal com valores brutos e filtrados
MonthlySummaryWithBruto = Dict[Tuple[int, int], Dict[str, Dict[str, Decimal]]]  # {
#     (ano, mes): {
#         "receita": {"bruto": Decimal, "filtrado": Decimal},
#         "despesa": {"bruto": Decimal, "filtrado": Decimal},
#         "custo": {"bruto": Decimal, "filtrado": Decimal},
#         "saldo": {"bruto": Decimal, "filtrado": Decimal}
#     }
# }

# Estrutura de resumo mensal simples (banco/API)
MonthlySummary = Dict[Tuple[int, int], Dict[str, Decimal]]  # {
#     (ano, mes): {
#         "receita": Decimal,
#         "despesa": Decimal,
#         "custo": Decimal,
#         "saldo": Decimal
#     }
# }

# ============================================================================
# FUNÇÕES DE NORMALIZAÇÃO DA PLANILHA (BRUTA E FILTRADA)
# ============================================================================

def normalize_diarios_bruto(
    df: pd.DataFrame,
    column_map: Dict[str, str],
    year: int
) -> List[Dict]:
    """
    Normaliza lançamentos diários da planilha SEM aplicar filtros do seed.
    Retorna lista de entradas canônicas (BRUTA).
    """
    entries = []
    
    for row_num, row in df.iterrows():
        # Parse dos campos
        data_mov_str = str(row[column_map['data_movimentacao']]) if pd.notna(row[column_map['data_movimentacao']]) else ""
        subgrupo_nome = ""
        grupo_nome = ""
        if 'subgrupo' in column_map:
            subgrupo_nome = str(row[column_map['subgrupo']]).strip() if pd.notna(row[column_map['subgrupo']]) else ""
        if 'grupo' in column_map:
            grupo_nome = str(row[column_map['grupo']]).strip() if pd.notna(row[column_map['grupo']]) else ""
        valor_str = str(row[column_map['valor']]) if pd.notna(row[column_map['valor']]) else ""
        
        # Parse básico (sem filtros)
        data_movimentacao = parse_date(data_mov_str)
        if not data_movimentacao or data_movimentacao.year != year:
            continue
        
        valor = parse_currency(valor_str)
        if valor == 0:
            continue
        
        # Determinar tipo baseado apenas no nome do grupo (sem validação de existência)
        tx_type = determine_transaction_type(grupo_nome, subgrupo_nome)
        tipo_str = "RECEITA" if tx_type == TransactionType.RECEITA else \
                   "DESPESA" if tx_type == TransactionType.DESPESA else \
                   "CUSTO"
        
        entries.append({
            "data": data_movimentacao.date(),
            "ano": data_movimentacao.year,
            "mes": data_movimentacao.month,
            "grupo": grupo_nome or "N/A",
            "subgrupo": subgrupo_nome or "N/A",
            "conta": "N/A",
            "tipo": tipo_str,
            "valor": valor,
            "origem": "DIARIO"
        })
    
    return entries

def normalize_diarios_filtrado(
    df: pd.DataFrame,
    column_map: Dict[str, str],
    tenant_id: str,
    db: Session
) -> List[Dict]:
    """
    Normaliza lançamentos diários da planilha aplicando EXATAMENTE as mesmas regras do seed.
    Retorna lista de entradas canônicas (FILTRADA).
    """
    entries = []
    
    # Pré-carregar grupos e subgrupos do banco
    grupos_map = {}
    grupos_db = db.query(ChartAccountGroup).filter(
        ChartAccountGroup.tenant_id == tenant_id
    ).all()
    for g in grupos_db:
        grupos_map[g.name.lower()] = g
    
    subgrupos_map = {}
    subgrupos_db = db.query(ChartAccountSubgroup).filter(
        ChartAccountSubgroup.tenant_id == tenant_id
    ).all()
    for sg in subgrupos_db:
        key = f"{sg.group_id}::{sg.name.lower()}"
        subgrupos_map[key] = sg
    
    for row_num, row in df.iterrows():
        # Parse dos campos (mesma lógica do seed)
        data_mov_str = str(row[column_map['data_movimentacao']]) if pd.notna(row[column_map['data_movimentacao']]) else ""
        subgrupo_nome = ""
        grupo_nome = ""
        if 'subgrupo' in column_map:
            subgrupo_nome = str(row[column_map['subgrupo']]).strip() if pd.notna(row[column_map['subgrupo']]) else ""
        if 'grupo' in column_map:
            grupo_nome = str(row[column_map['grupo']]).strip() if pd.notna(row[column_map['grupo']]) else ""
        valor_str = str(row[column_map['valor']]) if pd.notna(row[column_map['valor']]) else ""
        
        # REGRA 1: Pular linhas vazias
        if not data_mov_str or not valor_str:
            continue
        
        # REGRA 2: Parse de data
        data_movimentacao = parse_date(data_mov_str)
        if not data_movimentacao:
            continue
        
        # REGRA 3: Parse de valor
        valor = parse_currency(valor_str)
        if valor <= 0:
            continue
        
        # REGRA 4: Buscar grupo e subgrupo
        grupo = None
        subgrupo = None
        
        if grupo_nome:
            grupo_key = grupo_nome.lower()
            grupo = grupos_map.get(grupo_key)
            if not grupo:
                grupo = db.query(ChartAccountGroup).filter(
                    ChartAccountGroup.name == grupo_nome,
                    ChartAccountGroup.tenant_id == tenant_id
                ).first()
        
        if subgrupo_nome and grupo:
            subgrupo_key = f"{grupo.id}::{subgrupo_nome.lower()}"
            subgrupo = subgrupos_map.get(subgrupo_key)
            if not subgrupo:
                subgrupo = db.query(ChartAccountSubgroup).filter(
                    ChartAccountSubgroup.name == subgrupo_nome,
                    ChartAccountSubgroup.group_id == grupo.id,
                    ChartAccountSubgroup.tenant_id == tenant_id
                ).first()
        
        if not grupo or not subgrupo:
            continue
        
        # REGRA 5: Buscar primeira conta do subgrupo
        conta = db.query(ChartAccount).filter(
            ChartAccount.subgroup_id == subgrupo.id,
            ChartAccount.tenant_id == tenant_id
        ).first()
        
        if not conta:
            continue
        
        # Determinar tipo de transação
        tx_type = determine_transaction_type(grupo_nome, subgrupo_nome)
        tipo_str = "RECEITA" if tx_type == TransactionType.RECEITA else \
                   "DESPESA" if tx_type == TransactionType.DESPESA else \
                   "CUSTO"
        
        entries.append({
            "data": data_movimentacao.date(),
            "ano": data_movimentacao.year,
            "mes": data_movimentacao.month,
            "grupo": grupo.name,
            "subgrupo": subgrupo.name,
            "conta": conta.name,
            "tipo": tipo_str,
            "valor": valor,
            "origem": "DIARIO"
        })
    
    return entries

def normalize_previstos_bruto(
    df: pd.DataFrame,
    column_map: Dict[str, str],
    year: int
) -> List[Dict]:
    """
    Normaliza lançamentos previstos da planilha SEM aplicar filtros do seed.
    Retorna lista de entradas canônicas (BRUTA).
    """
    entries = []
    
    for row_num, row in df.iterrows():
        mes_str = str(row[column_map['data_prevista']]) if pd.notna(row[column_map['data_prevista']]) else ""
        conta_nome = str(row[column_map['conta']]).strip() if pd.notna(row[column_map['conta']]) else ""
        subgrupo_nome = ""
        grupo_nome = ""
        if 'subgrupo' in column_map:
            subgrupo_nome = str(row[column_map['subgrupo']]).strip() if pd.notna(row[column_map['subgrupo']]) else ""
        if 'grupo' in column_map:
            grupo_nome = str(row[column_map['grupo']]).strip() if pd.notna(row[column_map['grupo']]) else ""
        valor_str = str(row[column_map['valor']]) if pd.notna(row[column_map['valor']]) else ""
        
        # Parse básico (sem filtros)
        data_prevista = parse_date(mes_str)
        if not data_prevista or data_prevista.year != year:
            continue
        
        valor = parse_currency(valor_str)
        if valor == 0:
            continue
        
        # Determinar tipo baseado apenas no nome do grupo
        tx_type = determine_transaction_type(grupo_nome, subgrupo_nome)
        tipo_str = "RECEITA" if tx_type == TransactionType.RECEITA else \
                   "DESPESA" if tx_type == TransactionType.DESPESA else \
                   "CUSTO"
        
        entries.append({
            "data": data_prevista.date(),
            "ano": data_prevista.year,
            "mes": data_prevista.month,
            "grupo": grupo_nome or "N/A",
            "subgrupo": subgrupo_nome or "N/A",
            "conta": conta_nome or "N/A",
            "tipo": tipo_str,
            "valor": valor,
            "origem": "PREVISTO"
        })
    
    return entries

def normalize_previstos_filtrado(
    df: pd.DataFrame,
    column_map: Dict[str, str],
    tenant_id: str,
    db: Session
) -> List[Dict]:
    """
    Normaliza lançamentos previstos da planilha aplicando EXATAMENTE as mesmas regras do seed.
    Retorna lista de entradas canônicas (FILTRADA).
    """
    entries = []
    
    # Pré-carregar grupos, subgrupos e contas do banco
    grupos_map = {}
    grupos_db = db.query(ChartAccountGroup).filter(
        ChartAccountGroup.tenant_id == tenant_id
    ).all()
    for g in grupos_db:
        grupos_map[g.name.lower()] = g
    
    subgrupos_map = {}
    subgrupos_db = db.query(ChartAccountSubgroup).filter(
        ChartAccountSubgroup.tenant_id == tenant_id
    ).all()
    for sg in subgrupos_db:
        key = f"{sg.group_id}::{sg.name.lower()}"
        subgrupos_map[key] = sg
    
    contas_map = {}
    contas_db = db.query(ChartAccount).filter(
        ChartAccount.tenant_id == tenant_id
    ).all()
    for c in contas_db:
        contas_map[c.name.lower()] = c
    
    for row_num, row in df.iterrows():
        mes_str = str(row[column_map['data_prevista']]) if pd.notna(row[column_map['data_prevista']]) else ""
        conta_nome = str(row[column_map['conta']]).strip() if pd.notna(row[column_map['conta']]) else ""
        subgrupo_nome = ""
        grupo_nome = ""
        if 'subgrupo' in column_map:
            subgrupo_nome = str(row[column_map['subgrupo']]).strip() if pd.notna(row[column_map['subgrupo']]) else ""
        if 'grupo' in column_map:
            grupo_nome = str(row[column_map['grupo']]).strip() if pd.notna(row[column_map['grupo']]) else ""
        valor_str = str(row[column_map['valor']]) if pd.notna(row[column_map['valor']]) else ""
        
        # REGRA 1: Pular linhas vazias
        if not mes_str or not conta_nome or not valor_str:
            continue
        
        # REGRA 2: Parse de data
        data_prevista = parse_date(mes_str)
        if not data_prevista:
            continue
        
        # REGRA 3: Parse de valor
        valor = parse_currency(valor_str)
        if valor <= 0:
            continue
        
        # REGRA 4: Buscar conta
        conta = None
        if conta_nome:
            conta = contas_map.get(conta_nome.lower())
            if not conta:
                conta = db.query(ChartAccount).filter(
                    ChartAccount.name.ilike(f"%{conta_nome}%"),
                    ChartAccount.tenant_id == tenant_id
                ).first()
        
        if not conta:
            continue
        
        # Buscar subgrupo e grupo da conta
        if not subgrupo_nome:
            subgrupo_db = db.query(ChartAccountSubgroup).filter(
                ChartAccountSubgroup.id == conta.subgroup_id
            ).first()
            if subgrupo_db:
                subgrupo_nome = subgrupo_db.name
                grupo_nome = subgrupo_db.group.name if subgrupo_db.group else ""
        
        # REGRA 5: Buscar grupo e subgrupo
        grupo = None
        subgrupo = None
        
        if grupo_nome:
            grupo_key = grupo_nome.lower()
            grupo = grupos_map.get(grupo_key)
            if not grupo:
                grupo = db.query(ChartAccountGroup).filter(
                    ChartAccountGroup.name == grupo_nome,
                    ChartAccountGroup.tenant_id == tenant_id
                ).first()
        
        if subgrupo_nome and grupo:
            subgrupo_key = f"{grupo.id}::{subgrupo_nome.lower()}"
            subgrupo = subgrupos_map.get(subgrupo_key)
            if not subgrupo:
                subgrupo = db.query(ChartAccountSubgroup).filter(
                    ChartAccountSubgroup.name == subgrupo_nome,
                    ChartAccountSubgroup.group_id == grupo.id,
                    ChartAccountSubgroup.tenant_id == tenant_id
                ).first()
        
        if not subgrupo:
            subgrupo = db.query(ChartAccountSubgroup).filter(
                ChartAccountSubgroup.id == conta.subgroup_id
            ).first()
        
        if not grupo and subgrupo:
            grupo = db.query(ChartAccountGroup).filter(
                ChartAccountGroup.id == subgrupo.group_id
            ).first()
        
        if not grupo or not subgrupo:
            continue
        
        # Determinar tipo de transação
        tx_type = determine_transaction_type(grupo_nome, subgrupo_nome)
        tipo_str = "RECEITA" if tx_type == TransactionType.RECEITA else \
                   "DESPESA" if tx_type == TransactionType.DESPESA else \
                   "CUSTO"
        
        entries.append({
            "data": data_prevista.date(),
            "ano": data_prevista.year,
            "mes": data_prevista.month,
            "grupo": grupo.name,
            "subgrupo": subgrupo.name,
            "conta": conta.name,
            "tipo": tipo_str,
            "valor": valor,
            "origem": "PREVISTO"
        })
    
    return entries

def agregar_planilha_bruta_e_filtrada(
    entries_bruto: List[Dict],
    entries_filtrado: List[Dict],
    year: int
) -> MonthlySummaryWithBruto:
    """
    Agrega entradas brutas e filtradas por mês e tipo.
    Retorna dicionário com valores brutos e filtrados.
    """
    summary = defaultdict(lambda: {
        "receita": {"bruto": Decimal("0"), "filtrado": Decimal("0")},
        "despesa": {"bruto": Decimal("0"), "filtrado": Decimal("0")},
        "custo": {"bruto": Decimal("0"), "filtrado": Decimal("0")},
        "saldo": {"bruto": Decimal("0"), "filtrado": Decimal("0")}
    })
    
    # Agregar valores brutos
    for entry in entries_bruto:
        if entry["ano"] != year:
            continue
        
        key = (entry["ano"], entry["mes"])
        tipo = entry["tipo"].upper()
        valor = entry["valor"]
        
        if tipo == "RECEITA":
            summary[key]["receita"]["bruto"] += valor
        elif tipo == "DESPESA":
            summary[key]["despesa"]["bruto"] += valor
        elif tipo == "CUSTO":
            summary[key]["custo"]["bruto"] += valor
    
    # Agregar valores filtrados
    for entry in entries_filtrado:
        if entry["ano"] != year:
            continue
        
        key = (entry["ano"], entry["mes"])
        tipo = entry["tipo"].upper()
        valor = entry["valor"]
        
        if tipo == "RECEITA":
            summary[key]["receita"]["filtrado"] += valor
        elif tipo == "DESPESA":
            summary[key]["despesa"]["filtrado"] += valor
        elif tipo == "CUSTO":
            summary[key]["custo"]["filtrado"] += valor
    
    # Calcular saldo para cada mês
    for key in summary:
        summary[key]["saldo"]["bruto"] = (
            summary[key]["receita"]["bruto"] -
            summary[key]["despesa"]["bruto"] -
            summary[key]["custo"]["bruto"]
        )
        summary[key]["saldo"]["filtrado"] = (
            summary[key]["receita"]["filtrado"] -
            summary[key]["despesa"]["filtrado"] -
            summary[key]["custo"]["filtrado"]
        )
    
    return dict(summary)

# ============================================================================
# FUNÇÕES DE AGREGAÇÃO DO BANCO
# ============================================================================

def agregar_banco(
    db: Session,
    tenant_id: str,
    business_unit_id: str,
    year: int
) -> MonthlySummary:
    """
    Agrega lançamentos do banco por mês e tipo.
    Retorna dicionário: {(ano, mes): {"receita": Decimal, "despesa": Decimal, "custo": Decimal, "saldo": Decimal}}
    """
    summary = defaultdict(lambda: {
        "receita": Decimal("0"),
        "despesa": Decimal("0"),
        "custo": Decimal("0"),
        "saldo": Decimal("0")
    })
    
    start_dt = datetime(year, 1, 1)
    end_dt = datetime(year, 12, 31, 23, 59, 59)
    
    # Consultar lançamentos diários
    query = db.query(LancamentoDiario).filter(
        LancamentoDiario.tenant_id == tenant_id,
        LancamentoDiario.business_unit_id == business_unit_id,
        LancamentoDiario.is_active.is_(True),
        LancamentoDiario.data_movimentacao >= start_dt,
        LancamentoDiario.data_movimentacao <= end_dt
    )
    
    lancamentos = query.all()
    
    for lanc in lancamentos:
        if lanc.transaction_type is None:
            continue
        
        ano = lanc.data_movimentacao.year
        mes = lanc.data_movimentacao.month
        key = (ano, mes)
        valor = lanc.valor
        
        if lanc.transaction_type == TransactionType.RECEITA:
            summary[key]["receita"] += valor
        elif lanc.transaction_type == TransactionType.DESPESA:
            summary[key]["despesa"] += valor
        elif lanc.transaction_type == TransactionType.CUSTO:
            summary[key]["custo"] += valor
    
    # Calcular saldo para cada mês
    for key in summary:
        summary[key]["saldo"] = (
            summary[key]["receita"] -
            summary[key]["despesa"] -
            summary[key]["custo"]
        )
    
    return dict(summary)

# ============================================================================
# FUNÇÕES DE CONSUMO DA API
# ============================================================================

def consumir_api(backend_url: str, year: int, token: str) -> MonthlySummary:
    """
    Consome o endpoint /financial/annual-summary e retorna resumo mensal.
    Retorna dicionário: {(ano, mes): {"receita": Decimal, "despesa": Decimal, "custo": Decimal, "saldo": Decimal}}
    """
    summary = defaultdict(lambda: {
        "receita": Decimal("0"),
        "despesa": Decimal("0"),
        "custo": Decimal("0"),
        "saldo": Decimal("0")
    })
    
    try:
        response = requests.get(
            f"{backend_url}/api/v1/financial/annual-summary",
            params={"year": year},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        # O endpoint retorna monthly como lista de 12 objetos (mes 1-12)
        monthly_list = data.get("monthly", [])
        
        for month_data in monthly_list:
            month = month_data.get("month", 0)
            if month < 1 or month > 12:
                continue
            
            key = (year, month)
            summary[key]["receita"] = Decimal(str(month_data.get("revenue", 0)))
            summary[key]["despesa"] = Decimal(str(month_data.get("expense", 0)))
            summary[key]["custo"] = Decimal(str(month_data.get("cost", 0)))
            summary[key]["saldo"] = (
                summary[key]["receita"] -
                summary[key]["despesa"] -
                summary[key]["custo"]
            )
        
    except Exception as e:
        print(f"❌ Erro ao consumir API: {e}")
        return {}
    
    return dict(summary)

def login_api(backend_url: str) -> Optional[str]:
    """
    Faz login na API e retorna o access_token.
    """
    try:
        response = requests.post(
            f"{backend_url}/api/v1/auth/login",
            json={
                "username": "qa@finaflow.test",
                "password": "QaFinaflow123!"
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return data.get("access_token")
    except Exception as e:
        print(f"❌ Erro ao fazer login na API: {e}")
        return None

# ============================================================================
# FUNÇÕES DE COMPARAÇÃO
# ============================================================================

def comparar_totais(
    sheet_summary: MonthlySummaryWithBruto,
    db_summary: MonthlySummary,
    api_summary: MonthlySummary,
    year: int
) -> Tuple[bool, List[Dict], Dict[str, int]]:
    """
    Compara os três resumos e retorna (ok, lista_de_inconsistencias, estatisticas).
    """
    inconsistencies = []
    stats = {
        "mismatch_bruta_filtro": 0,
        "mismatch_filtro_banco": 0,
        "mismatch_banco_api": 0
    }
    all_ok = True
    
    # Coletar todos os meses presentes em qualquer resumo
    all_months = set()
    for key in sheet_summary.keys():
        if key[0] == year:
            all_months.add(key[1])
    for key in db_summary.keys():
        if key[0] == year:
            all_months.add(key[1])
    for key in api_summary.keys():
        if key[0] == year:
            all_months.add(key[1])
    
    for mes in sorted(all_months):
        key = (year, mes)
        
        # Obter valores (default 0 se não existir)
        sheet = sheet_summary.get(key, {
            "receita": {"bruto": Decimal("0"), "filtrado": Decimal("0")},
            "despesa": {"bruto": Decimal("0"), "filtrado": Decimal("0")},
            "custo": {"bruto": Decimal("0"), "filtrado": Decimal("0")},
            "saldo": {"bruto": Decimal("0"), "filtrado": Decimal("0")}
        })
        db = db_summary.get(key, {
            "receita": Decimal("0"),
            "despesa": Decimal("0"),
            "custo": Decimal("0"),
            "saldo": Decimal("0")
        })
        api = api_summary.get(key, {
            "receita": Decimal("0"),
            "despesa": Decimal("0"),
            "custo": Decimal("0"),
            "saldo": Decimal("0")
        })
        
        # Comparar cada tipo
        for tipo in ["receita", "despesa", "custo", "saldo"]:
            sheet_bruto = sheet[tipo]["bruto"]
            sheet_filtrado = sheet[tipo]["filtrado"]
            db_val = db[tipo]
            api_val = api[tipo]
            
            # Comparar BRUTA→FILTRO
            delta_bruta_filtro = abs(sheet_filtrado - sheet_bruto)
            delta_pct_bruta_filtro = None
            if sheet_bruto != 0:
                delta_pct_bruta_filtro = (delta_bruta_filtro / abs(sheet_bruto)) * 100
            
            mismatch_bruta_filtro = (
                delta_bruta_filtro > TOLERANCE_ABS or
                (delta_pct_bruta_filtro is not None and delta_pct_bruta_filtro > TOLERANCE_PCT)
            )
            
            # Comparar FILTRO→BANCO
            delta_filtro_banco = abs(db_val - sheet_filtrado)
            delta_pct_filtro_banco = None
            if sheet_filtrado != 0:
                delta_pct_filtro_banco = (delta_filtro_banco / abs(sheet_filtrado)) * 100
            
            mismatch_filtro_banco = (
                delta_filtro_banco > TOLERANCE_ABS or
                (delta_pct_filtro_banco is not None and delta_pct_filtro_banco > TOLERANCE_PCT)
            )
            
            # Comparar BANCO→API
            delta_banco_api = abs(api_val - db_val)
            delta_pct_banco_api = None
            if db_val != 0:
                delta_pct_banco_api = (delta_banco_api / abs(db_val)) * 100
            
            mismatch_banco_api = (
                delta_banco_api > TOLERANCE_ABS or
                (delta_pct_banco_api is not None and delta_pct_banco_api > TOLERANCE_PCT)
            )
            
            if mismatch_bruta_filtro:
                stats["mismatch_bruta_filtro"] += 1
                all_ok = False
            
            if mismatch_filtro_banco:
                stats["mismatch_filtro_banco"] += 1
                all_ok = False
            
            if mismatch_banco_api:
                stats["mismatch_banco_api"] += 1
                all_ok = False
            
            if mismatch_bruta_filtro or mismatch_filtro_banco or mismatch_banco_api:
                inconsistencies.append({
                    "ano": year,
                    "mes": mes,
                    "tipo": tipo,
                    "sheet_bruto": sheet_bruto,
                    "sheet_filtrado": sheet_filtrado,
                    "db": db_val,
                    "api": api_val,
                    "delta_bruta_filtro": delta_bruta_filtro,
                    "delta_pct_bruta_filtro": delta_pct_bruta_filtro,
                    "delta_filtro_banco": delta_filtro_banco,
                    "delta_pct_filtro_banco": delta_pct_filtro_banco,
                    "delta_banco_api": delta_banco_api,
                    "delta_pct_banco_api": delta_pct_banco_api
                })
    
    return all_ok, inconsistencies, stats

# ============================================================================
# FUNÇÕES DE DRILL DOWN (DEBUG)
# ============================================================================

def gerar_csv_planilha_filtrada(
    entries_filtrado: List[Dict],
    year: int,
    month: int,
    tipo: str,
    log_dir: Path
) -> Path:
    """
    Gera CSV com entradas filtradas da planilha para um mês/tipo específico.
    """
    tipo_upper = tipo.upper()
    filtered_entries = [
        e for e in entries_filtrado
        if e["ano"] == year and e["mes"] == month and e["tipo"].upper() == tipo_upper
    ]
    
    csv_path = log_dir / f"debug_{year}_{month:02d}_{tipo_upper}_planilha.csv"
    
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write("ano,mes,grupo,subgrupo,conta,tipo,origem,valor\n")
        for entry in filtered_entries:
            f.write(f"{entry['ano']},{entry['mes']},"
                   f'"{entry["grupo"]}","{entry["subgrupo"]}","{entry["conta"]}",'
                   f"{entry['tipo']},{entry['origem']},{float(entry['valor']):.2f}\n")
    
    return csv_path

def gerar_csv_banco(
    db: Session,
    tenant_id: str,
    business_unit_id: str,
    year: int,
    month: int,
    tipo: str,
    log_dir: Path
) -> Path:
    """
    Gera CSV com lançamentos do banco para um mês/tipo específico.
    """
    tipo_upper = tipo.upper()
    
    # Mapear tipo string para TransactionType
    tipo_map = {
        "RECEITA": TransactionType.RECEITA,
        "DESPESA": TransactionType.DESPESA,
        "CUSTO": TransactionType.CUSTO
    }
    transaction_type = tipo_map.get(tipo_upper)
    if not transaction_type:
        raise ValueError(f"Tipo inválido: {tipo}")
    
    start_dt = datetime(year, month, 1)
    if month == 12:
        end_dt = datetime(year, 12, 31, 23, 59, 59)
    else:
        end_dt = datetime(year, month + 1, 1) - timedelta(seconds=1)
    
    query = db.query(LancamentoDiario).join(
        ChartAccount
    ).join(
        ChartAccountSubgroup
    ).join(
        ChartAccountGroup
    ).filter(
        LancamentoDiario.tenant_id == tenant_id,
        LancamentoDiario.business_unit_id == business_unit_id,
        LancamentoDiario.is_active.is_(True),
        LancamentoDiario.data_movimentacao >= start_dt,
        LancamentoDiario.data_movimentacao <= end_dt,
        LancamentoDiario.transaction_type == transaction_type
    )
    
    lancamentos = query.all()
    
    csv_path = log_dir / f"debug_{year}_{month:02d}_{tipo_upper}_banco.csv"
    
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write("ano,mes,grupo,subgrupo,conta,tipo,valor\n")
        for lanc in lancamentos:
            grupo = lanc.conta.subgroup.group.name if lanc.conta and lanc.conta.subgroup and lanc.conta.subgroup.group else "N/A"
            subgrupo = lanc.conta.subgroup.name if lanc.conta and lanc.conta.subgroup else "N/A"
            conta = lanc.conta.name if lanc.conta else "N/A"
            f.write(f"{lanc.data_movimentacao.year},{lanc.data_movimentacao.month},"
                   f'"{grupo}","{subgrupo}","{conta}",'
                   f"{tipo_upper},{float(lanc.valor):.2f}\n")
    
    return csv_path

def gerar_csv_comparativo(
    entries_filtrado: List[Dict],
    db: Session,
    tenant_id: str,
    business_unit_id: str,
    year: int,
    month: int,
    tipo: str,
    log_dir: Path
) -> Path:
    """
    Gera CSV comparativo entre planilha filtrada e banco para um mês/tipo específico.
    """
    tipo_upper = tipo.upper()
    
    # Agregar planilha por grupo/subgrupo/conta
    planilha_agg = defaultdict(lambda: Decimal("0"))
    for entry in entries_filtrado:
        if entry["ano"] == year and entry["mes"] == month and entry["tipo"].upper() == tipo_upper:
            key = (entry["grupo"], entry["subgrupo"], entry["conta"])
            planilha_agg[key] += entry["valor"]
    
    # Agregar banco por grupo/subgrupo/conta
    tipo_map = {
        "RECEITA": TransactionType.RECEITA,
        "DESPESA": TransactionType.DESPESA,
        "CUSTO": TransactionType.CUSTO
    }
    transaction_type = tipo_map.get(tipo_upper)
    if not transaction_type:
        raise ValueError(f"Tipo inválido: {tipo}")
    
    start_dt = datetime(year, month, 1)
    if month == 12:
        end_dt = datetime(year, 12, 31, 23, 59, 59)
    else:
        end_dt = datetime(year, month + 1, 1) - timedelta(seconds=1)
    
    query = db.query(LancamentoDiario).join(
        ChartAccount
    ).join(
        ChartAccountSubgroup
    ).join(
        ChartAccountGroup
    ).filter(
        LancamentoDiario.tenant_id == tenant_id,
        LancamentoDiario.business_unit_id == business_unit_id,
        LancamentoDiario.is_active.is_(True),
        LancamentoDiario.data_movimentacao >= start_dt,
        LancamentoDiario.data_movimentacao <= end_dt,
        LancamentoDiario.transaction_type == transaction_type
    )
    
    lancamentos = query.all()
    
    banco_agg = defaultdict(lambda: Decimal("0"))
    for lanc in lancamentos:
        grupo = lanc.conta.subgroup.group.name if lanc.conta and lanc.conta.subgroup and lanc.conta.subgroup.group else "N/A"
        subgrupo = lanc.conta.subgroup.name if lanc.conta and lanc.conta.subgroup else "N/A"
        conta = lanc.conta.name if lanc.conta else "N/A"
        key = (grupo, subgrupo, conta)
        banco_agg[key] += lanc.valor
    
    # Criar conjunto de todas as chaves
    all_keys = set(planilha_agg.keys()) | set(banco_agg.keys())
    
    # Criar lista de comparação
    comparativo = []
    for key in all_keys:
        grupo, subgrupo, conta = key
        valor_planilha = planilha_agg.get(key, Decimal("0"))
        valor_banco = banco_agg.get(key, Decimal("0"))
        delta_abs = abs(valor_banco - valor_planilha)
        delta_pct = None
        if valor_planilha != 0:
            delta_pct = (delta_abs / abs(valor_planilha)) * 100
        
        status = "AMBOS"
        if valor_planilha == 0 and valor_banco != 0:
            status = "SO_BANCO"
        elif valor_planilha != 0 and valor_banco == 0:
            status = "SO_PLANILHA"
        
        comparativo.append({
            "grupo": grupo,
            "subgrupo": subgrupo,
            "conta": conta,
            "valor_planilha": valor_planilha,
            "valor_banco": valor_banco,
            "delta_abs": delta_abs,
            "delta_pct": delta_pct,
            "status": status
        })
    
    # Ordenar por delta_abs desc
    comparativo.sort(key=lambda x: x["delta_abs"], reverse=True)
    
    csv_path = log_dir / f"debug_{year}_{month:02d}_{tipo_upper}_comparativo.csv"
    
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write("grupo,subgrupo,conta,valor_planilha,valor_banco,delta_abs,delta_pct,status\n")
        for item in comparativo:
            delta_pct_str = f"{float(item['delta_pct']):.2f}" if item['delta_pct'] is not None else "N/A"
            f.write(f'"{item["grupo"]}","{item["subgrupo"]}","{item["conta"]}",'
                   f"{float(item['valor_planilha']):.2f},{float(item['valor_banco']):.2f},"
                   f"{float(item['delta_abs']):.2f},{delta_pct_str},{item['status']}\n")
    
    return csv_path

# ============================================================================
# FUNÇÕES DE IMPRESSÃO
# ============================================================================

def imprimir_tabela_comparacao(
    sheet_summary: MonthlySummaryWithBruto,
    db_summary: MonthlySummary,
    api_summary: MonthlySummary,
    year: int
):
    """
    Imprime tabela de comparação expandida.
    """
    print("\n" + "="*140)
    print("TABELA DE COMPARAÇÃO")
    print("="*140)
    print(f"{'ANO-MÊS':<10} {'TIPO':<10} {'PLAN_BRUTA':>15} {'PLAN_FILTRO':>15} {'BANCO':>15} {'API':>15} "
          f"{'Δ BRUT→FILT':>12} {'Δ%':>8} {'Δ FILT→BAN':>12} {'Δ%':>8} {'Δ BAN→API':>12} {'Δ%':>8}")
    print("-"*140)
    
    all_months = set()
    for key in sheet_summary.keys():
        if key[0] == year:
            all_months.add(key[1])
    for key in db_summary.keys():
        if key[0] == year:
            all_months.add(key[1])
    for key in api_summary.keys():
        if key[0] == year:
            all_months.add(key[1])
    
    for mes in sorted(all_months):
        key = (year, mes)
        sheet = sheet_summary.get(key, {
            "receita": {"bruto": Decimal("0"), "filtrado": Decimal("0")},
            "despesa": {"bruto": Decimal("0"), "filtrado": Decimal("0")},
            "custo": {"bruto": Decimal("0"), "filtrado": Decimal("0")},
            "saldo": {"bruto": Decimal("0"), "filtrado": Decimal("0")}
        })
        db = db_summary.get(key, {
            "receita": Decimal("0"),
            "despesa": Decimal("0"),
            "custo": Decimal("0"),
            "saldo": Decimal("0")
        })
        api = api_summary.get(key, {
            "receita": Decimal("0"),
            "despesa": Decimal("0"),
            "custo": Decimal("0"),
            "saldo": Decimal("0")
        })
        
        for tipo in ["receita", "despesa", "custo", "saldo"]:
            sheet_bruto = sheet[tipo]["bruto"]
            sheet_filtrado = sheet[tipo]["filtrado"]
            db_val = db[tipo]
            api_val = api[tipo]
            
            # Calcular deltas
            delta_bruta_filtro = abs(sheet_filtrado - sheet_bruto)
            delta_pct_bruta_filtro = (delta_bruta_filtro / abs(sheet_bruto) * 100) if sheet_bruto != 0 else None
            delta_filtro_banco = abs(db_val - sheet_filtrado)
            delta_pct_filtro_banco = (delta_filtro_banco / abs(sheet_filtrado) * 100) if sheet_filtrado != 0 else None
            delta_banco_api = abs(api_val - db_val)
            delta_pct_banco_api = (delta_banco_api / abs(db_val) * 100) if db_val != 0 else None
            
            # Marcar warnings
            status = ""
            if delta_bruta_filtro > TOLERANCE_ABS or (delta_pct_bruta_filtro and delta_pct_bruta_filtro > TOLERANCE_PCT):
                status += "⚠️ "
            if delta_filtro_banco > TOLERANCE_ABS or (delta_pct_filtro_banco and delta_pct_filtro_banco > TOLERANCE_PCT):
                status += "⚠️ "
            if delta_banco_api > TOLERANCE_ABS or (delta_pct_banco_api and delta_pct_banco_api > TOLERANCE_PCT):
                status += "⚠️ "
            
            print(f"{year}-{mes:02d}  {tipo.upper():<10} "
                  f"{float(sheet_bruto):>15,.2f} {float(sheet_filtrado):>15,.2f} {float(db_val):>15,.2f} {float(api_val):>15,.2f} "
                  f"{float(delta_bruta_filtro):>12,.2f} "
                  f"{f'{float(delta_pct_bruta_filtro):.2f}%' if delta_pct_bruta_filtro is not None else 'N/A':>8} "
                  f"{float(delta_filtro_banco):>12,.2f} "
                  f"{f'{float(delta_pct_filtro_banco):.2f}%' if delta_pct_filtro_banco is not None else 'N/A':>8} "
                  f"{float(delta_banco_api):>12,.2f} "
                  f"{f'{float(delta_pct_banco_api):.2f}%' if delta_pct_banco_api is not None else 'N/A':>8} "
                  f"{status}")

# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def carregar_e_normalizar_planilha(
    excel_file: Path,
    tenant_id: str,
    year: int,
    db: Session
) -> Tuple[List[Dict], List[Dict]]:
    """
    Carrega e normaliza a planilha, retornando entradas brutas e filtradas.
    """
    entries_bruto = []
    entries_filtrado = []
    
    # Ler lançamentos diários
    sheet_name_diarios = find_sheet_in_excel(excel_file, LANCAMENTOS_DIARIOS_SHEETS)
    if not sheet_name_diarios:
        print("❌ Aba de Lançamentos Diários não encontrada")
        return entries_bruto, entries_filtrado
    
    df_diarios = read_excel_sheet(excel_file, sheet_name_diarios)
    df_diarios.columns = df_diarios.columns.str.strip()
    
    # Mapear colunas
    column_map_diarios = {}
    for col in df_diarios.columns:
        col_lower = col.lower()
        if 'data' in col_lower and ('movimentação' in col_lower or 'movimentacao' in col_lower):
            column_map_diarios['data_movimentacao'] = col
        elif 'data' in col_lower and 'data_movimentacao' not in column_map_diarios:
            column_map_diarios['data_movimentacao'] = col
        if 'subgrupo' in col_lower and 'subgrupo' not in column_map_diarios:
            column_map_diarios['subgrupo'] = col
        if 'grupo' in col_lower and 'subgrupo' not in col_lower and 'grupo' not in column_map_diarios:
            column_map_diarios['grupo'] = col
        if 'valor' in col_lower and 'valor' not in column_map_diarios:
            column_map_diarios['valor'] = col
    
    if 'data_movimentacao' not in column_map_diarios or 'valor' not in column_map_diarios:
        print("❌ Colunas necessárias não encontradas em Lançamentos Diários")
        return entries_bruto, entries_filtrado
    
    # Normalizar (bruto e filtrado)
    entries_bruto.extend(normalize_diarios_bruto(df_diarios, column_map_diarios, year))
    entries_filtrado.extend(normalize_diarios_filtrado(df_diarios, column_map_diarios, tenant_id, db))
    
    # Ler lançamentos previstos
    sheet_name_previstos = find_sheet_in_excel(excel_file, LANCAMENTOS_PREVISTOS_SHEETS)
    if sheet_name_previstos:
        df_previstos = read_excel_sheet(excel_file, sheet_name_previstos)
        df_previstos.columns = df_previstos.columns.str.strip()
        
        # Mapear colunas
        column_map_previstos = {}
        for col in df_previstos.columns:
            col_lower = col.lower()
            if ('mês' in col_lower or 'mes' in col_lower or 'data' in col_lower) and 'prevista' in col_lower:
                column_map_previstos['data_prevista'] = col
            elif ('mês' in col_lower or 'mes' in col_lower) and 'data_prevista' not in column_map_previstos:
                column_map_previstos['data_prevista'] = col
            if 'conta' in col_lower and 'conta' not in column_map_previstos:
                column_map_previstos['conta'] = col
            if 'subgrupo' in col_lower and 'subgrupo' not in column_map_previstos:
                column_map_previstos['subgrupo'] = col
            if 'grupo' in col_lower and 'subgrupo' not in col_lower and 'grupo' not in column_map_previstos:
                column_map_previstos['grupo'] = col
            if 'valor' in col_lower and 'valor' not in column_map_previstos:
                column_map_previstos['valor'] = col
        
        if 'data_prevista' in column_map_previstos and 'conta' in column_map_previstos and 'valor' in column_map_previstos:
            entries_bruto.extend(normalize_previstos_bruto(df_previstos, column_map_previstos, year))
            entries_filtrado.extend(normalize_previstos_filtrado(df_previstos, column_map_previstos, tenant_id, db))
    
    return entries_bruto, entries_filtrado

def main():
    parser = argparse.ArgumentParser(
        description="Validar dashboard contra planilha e banco (auditoria profunda)"
    )
    parser.add_argument(
        '--file',
        type=str,
        default=str(DEFAULT_EXCEL_FILE),
        help=f'Caminho do arquivo Excel (default: {DEFAULT_EXCEL_FILE})'
    )
    parser.add_argument(
        '--year',
        type=int,
        default=2025,
        help='Ano para validação (default: 2025)'
    )
    parser.add_argument(
        '--log-file',
        type=str,
        default=None,
        help='Caminho do arquivo de log (opcional)'
    )
    parser.add_argument(
        '--backend-url',
        type=str,
        default=DEFAULT_BACKEND_URL,
        help=f'URL do backend (default: {DEFAULT_BACKEND_URL})'
    )
    parser.add_argument(
        '--debug-month',
        type=int,
        default=None,
        help='Mês para drill down detalhado (1-12, opcional)'
    )
    parser.add_argument(
        '--debug-type',
        type=str,
        default=None,
        choices=['RECEITA', 'DESPESA', 'CUSTO'],
        help='Tipo para drill down detalhado (RECEITA, DESPESA, CUSTO, opcional)'
    )
    
    args = parser.parse_args()
    
    # Validar parâmetros de debug
    if (args.debug_month is not None and args.debug_type is None) or \
       (args.debug_month is None and args.debug_type is not None):
        print("❌ --debug-month e --debug-type devem ser fornecidos juntos")
        sys.exit(1)
    
    if args.debug_month is not None and (args.debug_month < 1 or args.debug_month > 12):
        print("❌ --debug-month deve estar entre 1 e 12")
        sys.exit(1)
    
    excel_file = Path(args.file)
    if not excel_file.exists():
        print(f"❌ Arquivo não encontrado: {excel_file}")
        sys.exit(1)
    
    # Configurar logging
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = backend_path / "logs"
    log_dir.mkdir(exist_ok=True)
    
    if args.log_file:
        log_file = Path(args.log_file)
    else:
        log_file = log_dir / f"validate_dashboard_{timestamp}.log"
    
    # Redirecionar stdout para arquivo e terminal
    class Tee:
        def __init__(self, *files):
            self.files = files
        def write(self, obj):
            for f in self.files:
                f.write(obj)
                f.flush()
        def flush(self):
            for f in self.files:
                f.flush()
    
    log_f = open(log_file, 'w', encoding='utf-8')
    original_stdout = sys.stdout
    sys.stdout = Tee(original_stdout, log_f)
    
    try:
        print("="*80)
        print("🔍 VALIDAÇÃO PROFUNDA - DASHBOARD vs PLANILHA vs BANCO (AUDITORIA)")
        print("="*80)
        print(f"📁 Arquivo Excel: {excel_file}")
        print(f"📅 Ano: {args.year}")
        print(f"🌐 Backend URL: {args.backend_url}")
        print(f"📝 Log: {log_file}")
        print()
        
        # Conectar ao banco
        print("🔗 Conectando ao banco de dados...")
        try:
            db = SessionLocal()
            # Testar conexão
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
            print("✅ Conexão com banco estabelecida")
        except Exception as e:
            print(f"❌ Erro ao conectar ao banco: {e}")
            print("")
            print("💡 Dicas:")
            print("   1. Verifique se Cloud SQL Proxy está rodando:")
            print("      ps aux | grep cloud_sql_proxy")
            print("   2. Verifique se DATABASE_URL está configurado:")
            print(f"      echo $DATABASE_URL")
            print("   3. Para iniciar proxy:")
            print("      ./cloud_sql_proxy -instances=trivihair:us-central1:finaflow-db-staging=tcp:5432 &")
            print("   4. Use o script helper:")
            print("      ./scripts/run_validation_with_proxy.sh")
            sys.exit(1)
        
        try:
            # Obter tenant e business unit
            tenant = db.query(Tenant).filter(Tenant.name == "FinaFlow Staging").first()
            if not tenant:
                print("❌ Tenant 'FinaFlow Staging' não encontrado")
                sys.exit(1)
            
            business_unit = db.query(BusinessUnit).filter(
                BusinessUnit.tenant_id == tenant.id,
                BusinessUnit.name == "Matriz"
            ).first()
            if not business_unit:
                print("❌ Business Unit 'Matriz' não encontrada")
                sys.exit(1)
            
            print(f"✅ Tenant: {tenant.name} (ID: {tenant.id})")
            print(f"✅ Business Unit: {business_unit.name} (ID: {business_unit.id})")
            print()
            
            # 1. Carregar e normalizar planilha (bruto e filtrado)
            print("="*80)
            print("1. CARREGANDO E NORMALIZANDO PLANILHA (BRUTA E FILTRADA)")
            print("="*80)
            entries_bruto, entries_filtrado = carregar_e_normalizar_planilha(
                excel_file, tenant.id, args.year, db
            )
            print(f"✅ Entradas brutas: {len(entries_bruto)}")
            print(f"✅ Entradas filtradas: {len(entries_filtrado)}")
            
            # 2. Agregar planilha (bruto e filtrado)
            print("\n" + "="*80)
            print("2. AGREGANDO PLANILHA (BRUTA E FILTRADA)")
            print("="*80)
            sheet_summary = agregar_planilha_bruta_e_filtrada(
                entries_bruto, entries_filtrado, args.year
            )
            print(f"✅ Resumo da planilha: {len(sheet_summary)} meses")
            
            # 3. Agregar banco
            print("\n" + "="*80)
            print("3. AGREGANDO DADOS DO BANCO")
            print("="*80)
            db_summary = agregar_banco(db, tenant.id, business_unit.id, args.year)
            print(f"✅ Resumo do banco: {len(db_summary)} meses")
            
            # 4. Consumir API
            print("\n" + "="*80)
            print("4. CONSUMINDO API DE DASHBOARD")
            print("="*80)
            token = login_api(args.backend_url)
            if not token:
                print("❌ Falha ao fazer login na API")
                sys.exit(1)
            print("✅ Login realizado com sucesso")
            
            api_summary = consumir_api(args.backend_url, args.year, token)
            print(f"✅ Resumo da API: {len(api_summary)} meses")
            
            # 5. Comparar
            print("\n" + "="*80)
            print("5. COMPARANDO RESULTADOS")
            print("="*80)
            
            all_ok, inconsistencies, stats = comparar_totais(
                sheet_summary, db_summary, api_summary, args.year
            )
            
            # Imprimir tabela de comparação
            imprimir_tabela_comparacao(sheet_summary, db_summary, api_summary, args.year)
            
            # Modo de drill down (se solicitado)
            if args.debug_month and args.debug_type:
                print("\n" + "="*80)
                print(f"🔍 MODO DRILL DOWN - {args.year}-{args.debug_month:02d} | {args.debug_type}")
                print("="*80)
                
                print(f"\n📊 Gerando CSVs de drill down...")
                
                csv_planilha = gerar_csv_planilha_filtrada(
                    entries_filtrado, args.year, args.debug_month, args.debug_type, log_dir
                )
                print(f"✅ CSV da planilha filtrada: {csv_planilha}")
                
                csv_banco = gerar_csv_banco(
                    db, tenant.id, business_unit.id, args.year, args.debug_month, args.debug_type, log_dir
                )
                print(f"✅ CSV do banco: {csv_banco}")
                
                csv_comparativo = gerar_csv_comparativo(
                    entries_filtrado, db, tenant.id, business_unit.id,
                    args.year, args.debug_month, args.debug_type, log_dir
                )
                print(f"✅ CSV comparativo: {csv_comparativo}")
                
                print(f"\n📁 CSVs salvos em: {log_dir}")
                print(f"   - {csv_planilha.name}")
                print(f"   - {csv_banco.name}")
                print(f"   - {csv_comparativo.name}")
            
            # Resumo final
            print("\n" + "="*80)
            print("📊 RESUMO FINAL")
            print("="*80)
            
            # Contar meses únicos com mismatch
            meses_bruta_filtro = set()
            meses_filtro_banco = set()
            meses_banco_api = set()
            
            for inc in inconsistencies:
                key = (inc['ano'], inc['mes'])
                if inc['delta_bruta_filtro'] > TOLERANCE_ABS or \
                   (inc['delta_pct_bruta_filtro'] and inc['delta_pct_bruta_filtro'] > TOLERANCE_PCT):
                    meses_bruta_filtro.add(key)
                if inc['delta_filtro_banco'] > TOLERANCE_ABS or \
                   (inc['delta_pct_filtro_banco'] and inc['delta_pct_filtro_banco'] > TOLERANCE_PCT):
                    meses_filtro_banco.add(key)
                if inc['delta_banco_api'] > TOLERANCE_ABS or \
                   (inc['delta_pct_banco_api'] and inc['delta_pct_banco_api'] > TOLERANCE_PCT):
                    meses_banco_api.add(key)
            
            print(f"\n📈 Estatísticas de Mismatches (por mês/tipo):")
            print(f"  - BRUTA→FILTRO: {stats['mismatch_bruta_filtro']} ocorrências em {len(meses_bruta_filtro)} meses distintos")
            print(f"    (Diferenças explicadas por regras do seed - linhas filtradas/ignoradas)")
            print(f"  - FILTRO→BANCO: {stats['mismatch_filtro_banco']} ocorrências em {len(meses_filtro_banco)} meses distintos")
            print(f"    (Possível bug no seed - dados não foram persistidos corretamente)")
            print(f"  - BANCO→API: {stats['mismatch_banco_api']} ocorrências em {len(meses_banco_api)} meses distintos")
            print(f"    (Possível bug no dashboard/endpoint - cálculo incorreto na API)")
            
            if all_ok:
                print("\n✅ TODOS OS TOTAIS ESTÃO CONSISTENTES (planilha, banco, API)")
                print("✅ Todas as regras do seed estão sendo respeitadas no dashboard.")
                print("✅ As diferenças entre planilha bruta e sistema são exclusivamente de linhas filtradas/ignoradas pelo seed.")
            else:
                print(f"\n❌ FORAM ENCONTRADOS {len(inconsistencies)} MISMATCHES DE TOTAIS")
                print("\nInconsistências (primeiras 20):")
                for inc in inconsistencies[:20]:
                    print(f"  - {inc['ano']}-{inc['mes']:02d} | {inc['tipo'].upper()} | "
                          f"Bruto: R$ {float(inc['sheet_bruto']):,.2f} | "
                          f"Filtrado: R$ {float(inc['sheet_filtrado']):,.2f} | "
                          f"Banco: R$ {float(inc['db']):,.2f} | "
                          f"API: R$ {float(inc['api']):,.2f}")
                    if inc['delta_filtro_banco'] > TOLERANCE_ABS:
                        print(f"    ⚠️  Δ FILTRO→BANCO: R$ {float(inc['delta_filtro_banco']):,.2f} "
                              f"({float(inc['delta_pct_filtro_banco']):.2f}%)" if inc['delta_pct_filtro_banco'] else "")
                    if inc['delta_banco_api'] > TOLERANCE_ABS:
                        print(f"    ⚠️  Δ BANCO→API: R$ {float(inc['delta_banco_api']):,.2f} "
                              f"({float(inc['delta_pct_banco_api']):.2f}%)" if inc['delta_pct_banco_api'] else "")
            
            # Atualizar status de validação (BLOCO 4)
            print("\n" + "="*80)
            print("💾 ATUALIZANDO STATUS DE VALIDAÇÃO")
            print("="*80)
            try:
                import json
                validation_details = {
                    "mismatches_count": len(inconsistencies),
                    "stats": stats,
                    "all_ok": all_ok
                }
                
                # Buscar ou criar registro de validação
                validation_record = db.query(DashboardValidationStatus).filter(
                    DashboardValidationStatus.tenant_id == tenant.id,
                    DashboardValidationStatus.business_unit_id == business_unit.id,
                    DashboardValidationStatus.year == str(args.year)
                ).first()
                
                if not validation_record:
                    validation_record = DashboardValidationStatus(
                        tenant_id=tenant.id,
                        business_unit_id=business_unit.id,
                        year=str(args.year),
                        status=ValidationStatus.SUCCESS if all_ok else ValidationStatus.FAILED,
                        last_validation_at=datetime.utcnow(),
                        validation_details=json.dumps(validation_details)
                    )
                    db.add(validation_record)
                else:
                    validation_record.status = ValidationStatus.SUCCESS if all_ok else ValidationStatus.FAILED
                    validation_record.last_validation_at = datetime.utcnow()
                    validation_record.validation_details = json.dumps(validation_details)
                
                db.commit()
                print(f"✅ Status de validação atualizado: {validation_record.status.value}")
            except Exception as e:
                print(f"⚠️  Erro ao atualizar status de validação: {e}")
                db.rollback()
            
            print("\n" + "="*80)
            
            sys.stdout = original_stdout
            log_f.close()
            
            sys.exit(0 if all_ok else 1)
            
        finally:
            db.close()
    
    except Exception as e:
        import traceback
        error_msg = f"❌ Erro durante validação: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        sys.stdout = original_stdout
        log_f.close()
        sys.exit(1)

if __name__ == "__main__":
    main()
