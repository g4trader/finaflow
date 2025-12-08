#!/usr/bin/env python3
"""
Script de Validação Profunda - Dashboard vs Planilha vs Banco

Compara os totais mensais (receita, despesa, custo, saldo) entre:
- Planilha do cliente (Excel)
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
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import re

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
from sqlalchemy import func, extract
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

# Reutilizar funções do seed
from scripts.seed_from_client_sheet import (
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

# Estrutura canônica de um lançamento
CanonicalEntry = Dict[str, any]  # {
#     "data": date,
#     "ano": int,
#     "mes": int,
#     "grupo": str,
#     "subgrupo": str,
#     "conta": str,
#     "tipo": "RECEITA" | "DESPESA" | "CUSTO",
#     "valor": Decimal,
#     "origem": "DIARIO" | "PREVISTO"
# }

# Estrutura de resumo mensal
MonthlySummary = Dict[Tuple[int, int], Dict[str, Decimal]]  # {
#     (ano, mes): {
#         "receita": Decimal,
#         "despesa": Decimal,
#         "custo": Decimal,
#         "saldo": Decimal
#     }
# }

# ============================================================================
# FUNÇÕES DE NORMALIZAÇÃO DA PLANILHA
# ============================================================================

def normalize_diarios_from_sheet(
    df: pd.DataFrame,
    column_map: Dict[str, str],
    tenant_id: str,
    db: Session
) -> List[Dict]:
    """
    Normaliza lançamentos diários da planilha aplicando EXATAMENTE as mesmas regras do seed.
    Retorna lista de entradas canônicas.
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
        
        # Criar entrada canônica
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

def normalize_previstos_from_sheet(
    df: pd.DataFrame,
    column_map: Dict[str, str],
    tenant_id: str,
    db: Session
) -> List[Dict]:
    """
    Normaliza lançamentos previstos da planilha aplicando EXATAMENTE as mesmas regras do seed.
    Retorna lista de entradas canônicas.
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
        # Parse dos campos (mesma lógica do seed)
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
        
        # Criar entrada canônica
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

def build_sheet_summary(entries: List[Dict], year: int) -> MonthlySummary:
    """
    Agrega entradas canônicas por mês e tipo.
    Retorna dicionário: {(ano, mes): {"receita": Decimal, "despesa": Decimal, "custo": Decimal, "saldo": Decimal}}
    """
    summary = defaultdict(lambda: {
        "receita": Decimal("0"),
        "despesa": Decimal("0"),
        "custo": Decimal("0"),
        "saldo": Decimal("0")
    })
    
    for entry in entries:
        if entry["ano"] != year:
            continue
        
        key = (entry["ano"], entry["mes"])
        tipo = entry["tipo"].upper()
        valor = entry["valor"]
        
        if tipo == "RECEITA":
            summary[key]["receita"] += valor
        elif tipo == "DESPESA":
            summary[key]["despesa"] += valor
        elif tipo == "CUSTO":
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
# FUNÇÕES DE AGREGAÇÃO DO BANCO
# ============================================================================

def build_db_summary(
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

def build_api_summary(backend_url: str, year: int, token: str) -> MonthlySummary:
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

# ============================================================================
# FUNÇÕES DE COMPARAÇÃO
# ============================================================================

def compare_summaries(
    sheet_summary: MonthlySummary,
    db_summary: MonthlySummary,
    api_summary: MonthlySummary,
    year: int
) -> Tuple[bool, List[Dict]]:
    """
    Compara os três resumos e retorna (ok, lista_de_inconsistencias).
    """
    inconsistencies = []
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
            "receita": Decimal("0"),
            "despesa": Decimal("0"),
            "custo": Decimal("0"),
            "saldo": Decimal("0")
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
            sheet_val = sheet[tipo]
            db_val = db[tipo]
            api_val = api[tipo]
            
            # Comparar planilha vs banco
            delta_sheet_db = abs(db_val - sheet_val)
            delta_pct_sheet_db = None
            if sheet_val != 0:
                delta_pct_sheet_db = (delta_sheet_db / abs(sheet_val)) * 100
            
            # Comparar banco vs API
            delta_db_api = abs(api_val - db_val)
            delta_pct_db_api = None
            if db_val != 0:
                delta_pct_db_api = (delta_db_api / abs(db_val)) * 100
            
            # Verificar tolerâncias
            mismatch_sheet_db = (
                delta_sheet_db > TOLERANCE_ABS or
                (delta_pct_sheet_db is not None and delta_pct_sheet_db > TOLERANCE_PCT)
            )
            mismatch_db_api = (
                delta_db_api > TOLERANCE_ABS or
                (delta_pct_db_api is not None and delta_pct_db_api > TOLERANCE_PCT)
            )
            
            if mismatch_sheet_db or mismatch_db_api:
                all_ok = False
                inconsistencies.append({
                    "ano": year,
                    "mes": mes,
                    "tipo": tipo,
                    "sheet": sheet_val,
                    "db": db_val,
                    "api": api_val,
                    "delta_sheet_db": delta_sheet_db,
                    "delta_pct_sheet_db": delta_pct_sheet_db,
                    "delta_db_api": delta_db_api,
                    "delta_pct_db_api": delta_pct_db_api
                })
    
    return all_ok, inconsistencies

# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Validar dashboard contra planilha e banco"
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
    
    args = parser.parse_args()
    
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
        print("🔍 VALIDAÇÃO PROFUNDA - DASHBOARD vs PLANILHA vs BANCO")
        print("="*80)
        print(f"📁 Arquivo Excel: {excel_file}")
        print(f"📅 Ano: {args.year}")
        print(f"🌐 Backend URL: {args.backend_url}")
        print(f"📝 Log: {log_file}")
        print()
        
        # Conectar ao banco
        db = SessionLocal()
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
            
            # 1. Normalizar planilha
            print("="*80)
            print("1. NORMALIZANDO PLANILHA")
            print("="*80)
            
            # Ler lançamentos diários
            sheet_name_diarios = find_sheet_in_excel(excel_file, LANCAMENTOS_DIARIOS_SHEETS)
            if not sheet_name_diarios:
                print("❌ Aba de Lançamentos Diários não encontrada")
                sys.exit(1)
            
            df_diarios = read_excel_sheet(excel_file, sheet_name_diarios)
            df_diarios.columns = df_diarios.columns.str.strip()
            
            # Mapear colunas (mesma lógica do seed)
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
                sys.exit(1)
            
            entries_diarios = normalize_diarios_from_sheet(
                df_diarios, column_map_diarios, tenant.id, db
            )
            print(f"✅ Lançamentos diários normalizados: {len(entries_diarios)}")
            
            # Ler lançamentos previstos
            entries_previstos = []
            sheet_name_previstos = find_sheet_in_excel(excel_file, LANCAMENTOS_PREVISTOS_SHEETS)
            if sheet_name_previstos:
                df_previstos = read_excel_sheet(excel_file, sheet_name_previstos)
                df_previstos.columns = df_previstos.columns.str.strip()
                
                # Mapear colunas (mesma lógica do seed)
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
                    entries_previstos = normalize_previstos_from_sheet(
                        df_previstos, column_map_previstos, tenant.id, db
                    )
                    print(f"✅ Lançamentos previstos normalizados: {len(entries_previstos)}")
            
            # Agregar planilha
            all_entries = entries_diarios + entries_previstos
            sheet_summary = build_sheet_summary(all_entries, args.year)
            print(f"✅ Resumo da planilha: {len(sheet_summary)} meses")
            
            # 2. Agregar banco
            print("\n" + "="*80)
            print("2. AGREGANDO DADOS DO BANCO")
            print("="*80)
            db_summary = build_db_summary(db, tenant.id, business_unit.id, args.year)
            print(f"✅ Resumo do banco: {len(db_summary)} meses")
            
            # 3. Consumir API
            print("\n" + "="*80)
            print("3. CONSUMINDO API DE DASHBOARD")
            print("="*80)
            token = login_api(args.backend_url)
            if not token:
                print("❌ Falha ao fazer login na API")
                sys.exit(1)
            print("✅ Login realizado com sucesso")
            
            api_summary = build_api_summary(args.backend_url, args.year, token)
            print(f"✅ Resumo da API: {len(api_summary)} meses")
            
            # 4. Comparar
            print("\n" + "="*80)
            print("4. COMPARANDO RESULTADOS")
            print("="*80)
            
            all_ok, inconsistencies = compare_summaries(
                sheet_summary, db_summary, api_summary, args.year
            )
            
            # Imprimir tabela de comparação
            print("\n" + "-"*80)
            print("TABELA DE COMPARAÇÃO")
            print("-"*80)
            print(f"{'ANO-MÊS':<10} {'TIPO':<10} {'PLANILHA':>15} {'BANCO':>15} {'API':>15} "
                  f"{'Δ PLAN→BAN':>12} {'Δ%':>8} {'Δ BAN→API':>12} {'Δ%':>8}")
            print("-"*80)
            
            all_months = set()
            for key in sheet_summary.keys():
                if key[0] == args.year:
                    all_months.add(key[1])
            for key in db_summary.keys():
                if key[0] == args.year:
                    all_months.add(key[1])
            for key in api_summary.keys():
                if key[0] == args.year:
                    all_months.add(key[1])
            
            for mes in sorted(all_months):
                key = (args.year, mes)
                sheet = sheet_summary.get(key, {"receita": Decimal("0"), "despesa": Decimal("0"), "custo": Decimal("0"), "saldo": Decimal("0")})
                db_val = db_summary.get(key, {"receita": Decimal("0"), "despesa": Decimal("0"), "custo": Decimal("0"), "saldo": Decimal("0")})
                api = api_summary.get(key, {"receita": Decimal("0"), "despesa": Decimal("0"), "custo": Decimal("0"), "saldo": Decimal("0")})
                
                for tipo in ["receita", "despesa", "custo", "saldo"]:
                    sheet_val = sheet[tipo]
                    db_val_tipo = db_val[tipo]
                    api_val = api[tipo]
                    
                    delta_sheet_db = abs(db_val_tipo - sheet_val)
                    delta_pct_sheet_db = (delta_sheet_db / abs(sheet_val) * 100) if sheet_val != 0 else None
                    delta_db_api = abs(api_val - db_val_tipo)
                    delta_pct_db_api = (delta_db_api / abs(db_val_tipo) * 100) if db_val_tipo != 0 else None
                    
                    status = ""
                    if delta_sheet_db > TOLERANCE_ABS or (delta_pct_sheet_db and delta_pct_sheet_db > TOLERANCE_PCT):
                        status += "⚠️ "
                    if delta_db_api > TOLERANCE_ABS or (delta_pct_db_api and delta_pct_db_api > TOLERANCE_PCT):
                        status += "⚠️ "
                    
                    print(f"{args.year}-{mes:02d}  {tipo.upper():<10} "
                          f"{float(sheet_val):>15,.2f} {float(db_val_tipo):>15,.2f} {float(api_val):>15,.2f} "
                          f"{float(delta_sheet_db):>12,.2f} "
                          f"{f'{float(delta_pct_sheet_db):.2f}%' if delta_pct_sheet_db is not None else 'N/A':>8} "
                          f"{float(delta_db_api):>12,.2f} "
                          f"{f'{float(delta_pct_db_api):.2f}%' if delta_pct_db_api is not None else 'N/A':>8} "
                          f"{status}")
            
            # Resumo final
            print("\n" + "="*80)
            print("📊 RESUMO FINAL")
            print("="*80)
            
            if all_ok:
                print("✅ TODOS OS TOTAIS ESTÃO CONSISTENTES (planilha, banco, API)")
            else:
                print(f"❌ FORAM ENCONTRADOS {len(inconsistencies)} MISMATCHES DE TOTAIS")
                print("\nInconsistências:")
                for inc in inconsistencies[:20]:  # Mostrar apenas as 20 primeiras
                    print(f"  - {inc['ano']}-{inc['mes']:02d} | {inc['tipo'].upper()} | "
                          f"Planilha: R$ {float(inc['sheet']):,.2f} | "
                          f"Banco: R$ {float(inc['db']):,.2f} | "
                          f"API: R$ {float(inc['api']):,.2f} | "
                          f"Δ Plan→Ban: R$ {float(inc['delta_sheet_db']):,.2f} | "
                          f"Δ Ban→API: R$ {float(inc['delta_db_api']):,.2f}")
            
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

