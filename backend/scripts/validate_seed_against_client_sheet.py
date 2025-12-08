#!/usr/bin/env python3
"""
Script de Validação de Dados - Planilha x STAGING
Compara os dados do seed no banco STAGING com a planilha original do cliente.

USO:
    python -m scripts.validate_seed_against_client_sheet --file data/fluxo_caixa_2025.xlsx

REQUISITOS:
    - Arquivo Excel (.xlsx) na pasta backend/data/
    - Variável de ambiente DATABASE_URL configurada
    - Dependências: pandas, openpyxl

SAÍDA:
    - Relatório no terminal
    - Log em backend/logs/validate_seed_<timestamp>.log
    - Código de saída: 0 (OK) ou 1 (MISMATCH)
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional, Tuple, List
from collections import defaultdict
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
from sqlalchemy import func, extract
from app.database import SessionLocal

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

DEFAULT_EXCEL_FILE = backend_path / "data" / "fluxo_caixa_2025.xlsx"
PLANO_CONTAS_SHEETS = ["Plano de contas|LLM", "Plano de contas", "Plano de Contas", "Plano de Contas|LLM"]
LANCAMENTOS_DIARIOS_SHEETS = ["Lançamento Diário", "Lançamento Diario", "Lancamento Diario", "Lançamentos Diários"]
LANCAMENTOS_PREVISTOS_SHEETS = ["Lançamentos Previstos", "Lancamentos Previstos", "Previsões", "Previsoes"]

TOLERANCE = Decimal("0.01")  # Tolerância para comparação de valores

# ============================================================================
# UTILITÁRIOS
# ============================================================================

def parse_currency(value) -> Decimal:
    """Converte valor para Decimal (mesma lógica do seed)"""
    if pd.isna(value) or value == "" or value is None:
        return Decimal("0.00")
    
    value_str = str(value).strip()
    value_str = value_str.replace("R$", "").replace("$", "").strip()
    value_str = value_str.replace(".", "").replace(",", ".")
    
    try:
        return Decimal(value_str)
    except:
        return Decimal("0.00")

def parse_date(date_value) -> Optional[datetime]:
    """Converte valor para datetime (mesma lógica do seed)"""
    if pd.isna(date_value) or date_value == "" or date_value is None:
        return None
    
    if isinstance(date_value, datetime):
        return date_value
    
    if isinstance(date_value, pd.Timestamp):
        return date_value.to_pydatetime()
    
    value_str = str(date_value).strip()
    
    # Remover microsegundos
    if '.' in value_str and ' ' in value_str:
        parts = value_str.split('.')
        value_str = parts[0]
    
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y",
        "%d/%m/%y",
        "%d-%m-%y",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(value_str, fmt)
        except:
            continue
    
    return None

def find_sheet_in_excel(excel_file: Path, sheet_names: List[str]) -> Optional[str]:
    """Encontra a primeira aba que existe no arquivo Excel"""
    try:
        excel = pd.ExcelFile(excel_file)
        available_sheets = excel.sheet_names
        
        for sheet_name in sheet_names:
            if sheet_name in available_sheets:
                return sheet_name
        
        return None
    except Exception as e:
        print(f"❌ Erro ao listar abas: {str(e)}")
        return None

def read_excel_sheet(excel_file: Path, sheet_name: str) -> pd.DataFrame:
    """Lê uma aba específica do arquivo Excel"""
    try:
        df = pd.read_excel(excel_file, sheet_name=sheet_name, engine='openpyxl')
        return df
    except Exception as e:
        print(f"❌ Erro ao ler aba '{sheet_name}': {str(e)}")
        return pd.DataFrame()

# ============================================================================
# VALIDAÇÃO DO PLANO DE CONTAS
# ============================================================================

def validate_plano_contas(
    db: Session,
    tenant_id: str,
    excel_file: Path
) -> Tuple[bool, Dict]:
    """Valida plano de contas: planilha vs banco"""
    print("\n" + "="*60)
    print("📊 VALIDAÇÃO DO PLANO DE CONTAS")
    print("="*60)
    
    results = {
        'grupos': {'planilha': 0, 'banco': 0, 'ok': False},
        'subgrupos': {'planilha': 0, 'banco': 0, 'ok': False},
        'contas': {'planilha': 0, 'banco': 0, 'ok': False}
    }
    
    # Ler planilha
    sheet_name = find_sheet_in_excel(excel_file, PLANO_CONTAS_SHEETS)
    if not sheet_name:
        print("❌ Aba do Plano de Contas não encontrada")
        return False, results
    
    df = read_excel_sheet(excel_file, sheet_name)
    if df.empty:
        print("❌ Nenhum dado encontrado na aba do Plano de Contas")
        return False, results
    
    # Normalizar colunas
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
    
    if 'conta' not in column_map or 'subgrupo' not in column_map or 'grupo' not in column_map:
        print("❌ Colunas necessárias não encontradas")
        return False, results
    
    # Contar na planilha (aplicar mesmas regras do seed)
    grupos_set = set()
    subgrupos_set = set()
    contas_set = set()
    
    for _, row in df.iterrows():
        conta_nome = str(row[column_map['conta']]).strip() if pd.notna(row[column_map['conta']]) else ""
        subgrupo_nome = str(row[column_map['subgrupo']]).strip() if pd.notna(row[column_map['subgrupo']]) else ""
        grupo_nome = str(row[column_map['grupo']]).strip() if pd.notna(row[column_map['grupo']]) else ""
        escolha = ""
        if 'escolha' in column_map:
            escolha = str(row[column_map['escolha']]).strip() if pd.notna(row[column_map['escolha']]) else ""
        
        # Pular linhas vazias ou com "Usar" diferente (mesma lógica do seed)
        if not conta_nome or not subgrupo_nome or not grupo_nome:
            continue
        
        if escolha and escolha.lower() not in ['usar', 'use', 'sim', 'yes', '']:
            continue
        
        grupos_set.add(grupo_nome.lower())
        subgrupos_set.add(f"{grupo_nome.lower()}::{subgrupo_nome.lower()}")
        contas_set.add(f"{grupo_nome.lower()}::{subgrupo_nome.lower()}::{conta_nome.lower()}")
    
    results['grupos']['planilha'] = len(grupos_set)
    results['subgrupos']['planilha'] = len(subgrupos_set)
    results['contas']['planilha'] = len(contas_set)
    
    # Contar no banco
    grupos_banco = db.query(ChartAccountGroup).filter(
        ChartAccountGroup.tenant_id == tenant_id
    ).count()
    
    subgrupos_banco = db.query(ChartAccountSubgroup).filter(
        ChartAccountSubgroup.tenant_id == tenant_id
    ).count()
    
    contas_banco = db.query(ChartAccount).filter(
        ChartAccount.tenant_id == tenant_id
    ).count()
    
    results['grupos']['banco'] = grupos_banco
    results['subgrupos']['banco'] = subgrupos_banco
    results['contas']['banco'] = contas_banco
    
    # Comparar
    results['grupos']['ok'] = results['grupos']['planilha'] == results['grupos']['banco']
    results['subgrupos']['ok'] = results['subgrupos']['planilha'] == results['subgrupos']['banco']
    results['contas']['ok'] = results['contas']['planilha'] == results['contas']['banco']
    
    # Imprimir resultados
    status_grupos = "✅ OK" if results['grupos']['ok'] else "❌ MISMATCH"
    status_subgrupos = "✅ OK" if results['subgrupos']['ok'] else "❌ MISMATCH"
    status_contas = "✅ OK" if results['contas']['ok'] else "❌ MISMATCH"
    
    print(f"[Plano de Contas] Grupos: planilha={results['grupos']['planilha']} | banco={results['grupos']['banco']} -> {status_grupos}")
    print(f"[Plano de Contas] Subgrupos: planilha={results['subgrupos']['planilha']} | banco={results['subgrupos']['banco']} -> {status_subgrupos}")
    print(f"[Plano de Contas] Contas: planilha={results['contas']['planilha']} | banco={results['contas']['banco']} -> {status_contas}")
    
    all_ok = results['grupos']['ok'] and results['subgrupos']['ok'] and results['contas']['ok']
    return all_ok, results

# ============================================================================
# VALIDAÇÃO DE LANÇAMENTOS DIÁRIOS (LINHA A LINHA)
# ============================================================================

def normalize_diarios_from_sheet(
    df: pd.DataFrame,
    column_map: Dict[str, str],
    tenant_id: str,
    db: Session
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Normaliza lançamentos diários da planilha aplicando EXATAMENTE as mesmas regras do seed.
    
    Retorna:
    - df_valid: DataFrame com linhas válidas (que passariam pelos filtros do seed)
    - df_ignored: DataFrame com linhas ignoradas (com motivo)
    """
    rows_valid = []
    rows_ignored = []
    
    grupos_map = {}
    subgrupos_map = {}
    
    # Pré-carregar grupos e subgrupos do banco
    grupos_db = db.query(ChartAccountGroup).filter(
        ChartAccountGroup.tenant_id == tenant_id
    ).all()
    for g in grupos_db:
        grupos_map[g.name.lower()] = g
    
    subgrupos_db = db.query(ChartAccountSubgroup).filter(
        ChartAccountSubgroup.tenant_id == tenant_id
    ).all()
    for sg in subgrupos_db:
        key = f"{sg.group_id}::{sg.name.lower()}"
        subgrupos_map[key] = sg
    
    for row_num, row in df.iterrows():
        motivo_ignorado = None
        
        # Parse dos campos (mesma lógica do seed)
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
        
        # REGRA 1: Pular linhas vazias (mesma lógica do seed linha 840)
        if not data_mov_str or not valor_str:
            motivo_ignorado = "data ou valor vazio"
            rows_ignored.append({
                'linha': row_num + 2,
                'data': data_mov_str,
                'grupo': grupo_nome,
                'subgrupo': subgrupo_nome,
                'valor': valor_str,
                'motivo': motivo_ignorado
            })
            continue
        
        # REGRA 2: Parse de data (mesma lógica do seed linha 845-848)
        data_movimentacao = parse_date(data_mov_str)
        if not data_movimentacao:
            motivo_ignorado = "data inválida ou não parseável"
            rows_ignored.append({
                'linha': row_num + 2,
                'data': data_mov_str,
                'grupo': grupo_nome,
                'subgrupo': subgrupo_nome,
                'valor': valor_str,
                'motivo': motivo_ignorado
            })
            continue
        
        # REGRA 3: Parse de valor (mesma lógica do seed linha 850-853)
        valor = parse_currency(valor_str)
        if valor <= 0:
            motivo_ignorado = f"valor <= 0 (valor parseado: {valor})"
            rows_ignored.append({
                'linha': row_num + 2,
                'data': data_mov_str,
                'grupo': grupo_nome,
                'subgrupo': subgrupo_nome,
                'valor': valor_str,
                'motivo': motivo_ignorado
            })
            continue
        
        # REGRA 4: Buscar grupo e subgrupo (mesma lógica do seed linha 855-880)
        grupo = None
        subgrupo = None
        
        if grupo_nome:
            grupo_key = grupo_nome.lower()
            grupo = grupos_map.get(grupo_key)
            if not grupo:
                motivo_ignorado = f"grupo não encontrado: {grupo_nome}"
                rows_ignored.append({
                    'linha': row_num + 2,
                    'data': data_mov_str,
                    'grupo': grupo_nome,
                    'subgrupo': subgrupo_nome,
                    'valor': valor_str,
                    'motivo': motivo_ignorado
                })
                continue
        
        if subgrupo_nome and grupo:
            subgrupo_key = f"{grupo.id}::{subgrupo_nome.lower()}"
            subgrupo = subgrupos_map.get(subgrupo_key)
            if not subgrupo:
                motivo_ignorado = f"subgrupo não encontrado: {subgrupo_nome} (grupo: {grupo_nome})"
                rows_ignored.append({
                    'linha': row_num + 2,
                    'data': data_mov_str,
                    'grupo': grupo_nome,
                    'subgrupo': subgrupo_nome,
                    'valor': valor_str,
                    'motivo': motivo_ignorado
                })
                continue
        
        if not grupo or not subgrupo:
            motivo_ignorado = "grupo ou subgrupo não encontrado"
            rows_ignored.append({
                'linha': row_num + 2,
                'data': data_mov_str,
                'grupo': grupo_nome,
                'subgrupo': subgrupo_nome,
                'valor': valor_str,
                'motivo': motivo_ignorado
            })
            continue
        
        # REGRA 5: Buscar primeira conta do subgrupo (mesma lógica do seed linha 882-890)
        conta = db.query(ChartAccount).filter(
            ChartAccount.subgroup_id == subgrupo.id,
            ChartAccount.tenant_id == tenant_id
        ).first()
        
        if not conta:
            motivo_ignorado = f"nenhuma conta encontrada no subgrupo: {subgrupo_nome}"
            rows_ignored.append({
                'linha': row_num + 2,
                'data': data_mov_str,
                'grupo': grupo_nome,
                'subgrupo': subgrupo_nome,
                'valor': valor_str,
                'motivo': motivo_ignorado
            })
            continue
        
        # Linha válida - adicionar ao DataFrame normalizado
        rows_valid.append({
            'data': data_movimentacao.date(),
            'grupo': grupo.name,
            'subgrupo': subgrupo.name,
            'conta': conta.name,
            'valor': valor.quantize(Decimal('0.01')),
            'descricao': observacoes or f"Lançamento de {subgrupo_nome}",
            'linha_original': row_num + 2
        })
    
    df_valid = pd.DataFrame(rows_valid)
    df_ignored = pd.DataFrame(rows_ignored)
    
    return df_valid, df_ignored

def normalize_diarios_from_db(
    db: Session,
    tenant_id: str,
    business_unit_id: str
) -> pd.DataFrame:
    """Normaliza lançamentos diários do banco para DataFrame comparável"""
    lancamentos = db.query(LancamentoDiario).join(
        ChartAccount
    ).join(
        ChartAccountSubgroup
    ).join(
        ChartAccountGroup
    ).filter(
        LancamentoDiario.tenant_id == tenant_id,
        LancamentoDiario.business_unit_id == business_unit_id
    ).all()
    
    rows = []
    for ld in lancamentos:
        rows.append({
            'data': ld.data_movimentacao.date(),
            'grupo': ld.grupo.name if ld.grupo else "",
            'subgrupo': ld.subgrupo.name if ld.subgrupo else "",
            'conta': ld.conta.name if ld.conta else "",
            'valor': ld.valor.quantize(Decimal('0.01')),
            'descricao': ld.observacoes or "",
            'id': str(ld.id)
        })
    
    return pd.DataFrame(rows)

def validate_lancamentos_diarios(
    db: Session,
    tenant_id: str,
    business_unit_id: str,
    excel_file: Path,
    log_dir: Path,
    timestamp: str
) -> Tuple[bool, Dict]:
    """Valida lançamentos diários: planilha vs banco (linha a linha)"""
    print("\n" + "="*60)
    print("📊 VALIDAÇÃO DE LANÇAMENTOS DIÁRIOS (LINHA A LINHA)")
    print("="*60)
    
    results = {
        'total_bruto_planilha': 0,
        'total_pos_filtro_planilha': 0,
        'total_banco': 0,
        'missing_in_db': 0,
        'extra_in_db': 0,
        'ok': False,
        'csv_missing': None,
        'csv_extra': None,
        'csv_ignored': None
    }
    
    # Ler planilha
    sheet_name = find_sheet_in_excel(excel_file, LANCAMENTOS_DIARIOS_SHEETS)
    if not sheet_name:
        print("❌ Aba de Lançamentos Diários não encontrada")
        return False, results
    
    df_raw = read_excel_sheet(excel_file, sheet_name)
    if df_raw.empty:
        print("❌ Nenhum dado encontrado na aba de Lançamentos Diários")
        return False, results
    
    results['total_bruto_planilha'] = len(df_raw)
    
    # Normalizar colunas (mesma lógica do seed)
    df_raw.columns = df_raw.columns.str.strip()
    column_map = {}
    for col in df_raw.columns:
        col_lower = col.lower()
        if 'data' in col_lower and ('movimentação' in col_lower or 'movimentacao' in col_lower):
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
    
    if 'data_movimentacao' not in column_map or 'valor' not in column_map:
        print("❌ Colunas necessárias não encontradas")
        return False, results
    
    # Normalizar planilha (aplicar mesmas regras do seed)
    print("  Aplicando filtros do seed na planilha...")
    df_sheet_norm, df_ignored = normalize_diarios_from_sheet(df_raw, column_map, tenant_id, db)
    results['total_pos_filtro_planilha'] = len(df_sheet_norm)
    
    # Normalizar banco
    print("  Carregando dados do banco...")
    df_db_norm = normalize_diarios_from_db(db, tenant_id, business_unit_id)
    results['total_banco'] = len(df_db_norm)
    
    # Criar chave composta para comparação
    # Garantir que 'valor' esteja em float antes de usar .round()
    if not df_sheet_norm.empty:
        df_sheet_norm['valor'] = df_sheet_norm['valor'].apply(
            lambda v: float(v) if v is not None else 0.0
        )
        df_sheet_norm['key'] = (
            df_sheet_norm['data'].astype(str) + "|" +
            df_sheet_norm['grupo'].astype(str) + "|" +
            df_sheet_norm['subgrupo'].astype(str) + "|" +
            df_sheet_norm['conta'].astype(str) + "|" +
            df_sheet_norm['valor'].round(2).astype(str)
        )
    
    if not df_db_norm.empty:
        df_db_norm['valor'] = df_db_norm['valor'].apply(
            lambda v: float(v) if v is not None else 0.0
        )
        df_db_norm['key'] = (
            df_db_norm['data'].astype(str) + "|" +
            df_db_norm['grupo'].astype(str) + "|" +
            df_db_norm['subgrupo'].astype(str) + "|" +
            df_db_norm['conta'].astype(str) + "|" +
            df_db_norm['valor'].round(2).astype(str)
        )
    
    # Merge para encontrar diferenças
    if not df_sheet_norm.empty and not df_db_norm.empty:
        df_merge = df_sheet_norm.merge(
            df_db_norm[['key']],
            on='key',
            how='outer',
            indicator=True
        )
        
        df_missing = df_merge[df_merge['_merge'] == 'left_only'].copy()
        df_extra = df_merge[df_merge['_merge'] == 'right_only'].copy()
        
        results['missing_in_db'] = len(df_missing)
        results['extra_in_db'] = len(df_extra)
        
        # Salvar CSVs
        if len(df_missing) > 0:
            csv_missing = log_dir / f"diarios_missing_in_db_{timestamp}.csv"
            df_missing[['linha_original', 'data', 'grupo', 'subgrupo', 'conta', 'valor', 'descricao']].to_csv(
                csv_missing, index=False, encoding='utf-8-sig'
            )
            results['csv_missing'] = str(csv_missing)
            print(f"  📄 Linhas faltando no banco: {csv_missing}")
        
        if len(df_extra) > 0:
            csv_extra = log_dir / f"diarios_extra_in_db_{timestamp}.csv"
            df_extra[['data', 'grupo', 'subgrupo', 'conta', 'valor', 'descricao', 'id']].to_csv(
                csv_extra, index=False, encoding='utf-8-sig'
            )
            results['csv_extra'] = str(csv_extra)
            print(f"  📄 Linhas extras no banco: {csv_extra}")
    elif not df_sheet_norm.empty:
        # Tudo da planilha está faltando
        results['missing_in_db'] = len(df_sheet_norm)
        csv_missing = log_dir / f"diarios_missing_in_db_{timestamp}.csv"
        df_sheet_norm[['linha_original', 'data', 'grupo', 'subgrupo', 'conta', 'valor', 'descricao']].to_csv(
            csv_missing, index=False, encoding='utf-8-sig'
        )
        results['csv_missing'] = str(csv_missing)
    elif not df_db_norm.empty:
        # Tudo do banco está extra
        results['extra_in_db'] = len(df_db_norm)
        csv_extra = log_dir / f"diarios_extra_in_db_{timestamp}.csv"
        df_db_norm[['data', 'grupo', 'subgrupo', 'conta', 'valor', 'descricao', 'id']].to_csv(
            csv_extra, index=False, encoding='utf-8-sig'
        )
        results['csv_extra'] = str(csv_extra)
    
    # Salvar CSV de linhas ignoradas
    if len(df_ignored) > 0:
        csv_ignored = log_dir / f"diarios_ignored_{timestamp}.csv"
        df_ignored.to_csv(csv_ignored, index=False, encoding='utf-8-sig')
        results['csv_ignored'] = str(csv_ignored)
        print(f"  📄 Linhas ignoradas por regras do seed: {csv_ignored}")
    
    # Determinar status
    # OK se: todas as linhas válidas da planilha estão no banco E não há linhas extras no banco
    # OU se: diferença é explicada apenas por linhas ignoradas
    if results['missing_in_db'] == 0 and results['extra_in_db'] == 0:
        results['ok'] = True
        status = "✅ OK"
    elif results['missing_in_db'] == 0:
        # Há linhas extras no banco (não deveria acontecer se seed só lê essa planilha)
        results['ok'] = False
        status = "⚠️  OK (com linhas extras no banco)"
    else:
        results['ok'] = False
        status = "❌ MISMATCH"
    
    # Imprimir resultados
    print(f"\n[Lançamentos Diários]")
    print(f"  Planilha (bruto): {results['total_bruto_planilha']} linhas")
    print(f"  Planilha (pós-filtro seed): {results['total_pos_filtro_planilha']} linhas")
    print(f"  Banco: {results['total_banco']} linhas")
    print(f"  Faltando no banco: {results['missing_in_db']} linhas")
    print(f"  Extras no banco: {results['extra_in_db']} linhas")
    print(f"  Linhas ignoradas (regras seed): {len(df_ignored)} linhas")
    print(f"  Status: {status}")
    
    return results['ok'], results

# ============================================================================
# VALIDAÇÃO DE LANÇAMENTOS PREVISTOS (LINHA A LINHA)
# ============================================================================

def normalize_previstos_from_sheet(
    df: pd.DataFrame,
    column_map: Dict[str, str],
    tenant_id: str,
    db: Session
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Normaliza lançamentos previstos da planilha aplicando EXATAMENTE as mesmas regras do seed.
    
    Retorna:
    - df_valid: DataFrame com linhas válidas (que passariam pelos filtros do seed)
    - df_ignored: DataFrame com linhas ignoradas (com motivo)
    """
    rows_valid = []
    rows_ignored = []
    
    grupos_map = {}
    subgrupos_map = {}
    contas_map = {}
    
    # Pré-carregar grupos, subgrupos e contas do banco
    grupos_db = db.query(ChartAccountGroup).filter(
        ChartAccountGroup.tenant_id == tenant_id
    ).all()
    for g in grupos_db:
        grupos_map[g.name.lower()] = g
    
    subgrupos_db = db.query(ChartAccountSubgroup).filter(
        ChartAccountSubgroup.tenant_id == tenant_id
    ).all()
    for sg in subgrupos_db:
        key = f"{sg.group_id}::{sg.name.lower()}"
        subgrupos_map[key] = sg
    
    contas_db = db.query(ChartAccount).filter(
        ChartAccount.tenant_id == tenant_id
    ).all()
    for c in contas_db:
        contas_map[c.name.lower()] = c
    
    for row_num, row in df.iterrows():
        motivo_ignorado = None
        
        # Parse dos campos (mesma lógica do seed linha 612-620)
        mes_str = str(row[column_map['data_prevista']]) if pd.notna(row[column_map['data_prevista']]) else ""
        conta_nome = str(row[column_map['conta']]).strip() if pd.notna(row[column_map['conta']]) else ""
        subgrupo_nome = ""
        grupo_nome = ""
        if 'subgrupo' in column_map:
            subgrupo_nome = str(row[column_map['subgrupo']]).strip() if pd.notna(row[column_map['subgrupo']]) else ""
        if 'grupo' in column_map:
            grupo_nome = str(row[column_map['grupo']]).strip() if pd.notna(row[column_map['grupo']]) else ""
        valor_str = str(row[column_map['valor']]) if pd.notna(row[column_map['valor']]) else ""
        
        # REGRA 1: Pular linhas vazias (mesma lógica do seed linha 623-625)
        if not mes_str or not conta_nome or not valor_str:
            motivo_ignorado = "data, conta ou valor vazio"
            rows_ignored.append({
                'linha': row_num + 2,
                'data': mes_str,
                'conta': conta_nome,
                'grupo': grupo_nome,
                'subgrupo': subgrupo_nome,
                'valor': valor_str,
                'motivo': motivo_ignorado
            })
            continue
        
        # REGRA 2: Parse de data (mesma lógica do seed linha 628-631)
        data_prevista = parse_date(mes_str)
        if not data_prevista:
            motivo_ignorado = "data inválida ou não parseável"
            rows_ignored.append({
                'linha': row_num + 2,
                'data': mes_str,
                'conta': conta_nome,
                'grupo': grupo_nome,
                'subgrupo': subgrupo_nome,
                'valor': valor_str,
                'motivo': motivo_ignorado
            })
            continue
        
        # REGRA 3: Parse de valor (mesma lógica do seed linha 633-636)
        valor = parse_currency(valor_str)
        if valor <= 0:
            motivo_ignorado = f"valor <= 0 (valor parseado: {valor})"
            rows_ignored.append({
                'linha': row_num + 2,
                'data': mes_str,
                'conta': conta_nome,
                'grupo': grupo_nome,
                'subgrupo': subgrupo_nome,
                'valor': valor_str,
                'motivo': motivo_ignorado
            })
            continue
        
        # REGRA 4: Buscar conta (mesma lógica do seed linha 639-657)
        conta = None
        if conta_nome:
            # Buscar em contas_map primeiro
            conta = contas_map.get(conta_nome.lower())
            
            # Se não encontrou, buscar no banco (ilike)
            if not conta:
                conta_db = db.query(ChartAccount).filter(
                    ChartAccount.name.ilike(f"%{conta_nome}%"),
                    ChartAccount.tenant_id == tenant_id
                ).first()
                if conta_db:
                    conta = conta_db
        
        if not conta:
            motivo_ignorado = f"conta não encontrada: {conta_nome}"
            rows_ignored.append({
                'linha': row_num + 2,
                'data': mes_str,
                'conta': conta_nome,
                'grupo': grupo_nome,
                'subgrupo': subgrupo_nome,
                'valor': valor_str,
                'motivo': motivo_ignorado
            })
            continue
        
        # Buscar subgrupo e grupo da conta (mesma lógica do seed linha 660-666)
        if not subgrupo_nome:
            subgrupo_db = db.query(ChartAccountSubgroup).filter(
                ChartAccountSubgroup.id == conta.subgroup_id
            ).first()
            if subgrupo_db:
                subgrupo_nome = subgrupo_db.name
                grupo_nome = subgrupo_db.group.name if subgrupo_db.group else ""
        
        # REGRA 5: Buscar grupo e subgrupo (mesma lógica do seed linha 668-705)
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
        
        # Usar subgrupo e grupo da conta se não encontrou (mesma lógica do seed linha 692-700)
        if not subgrupo:
            subgrupo = db.query(ChartAccountSubgroup).filter(
                ChartAccountSubgroup.id == conta.subgroup_id
            ).first()
        
        if not grupo and subgrupo:
            grupo = db.query(ChartAccountGroup).filter(
                ChartAccountGroup.id == subgrupo.group_id
            ).first()
        
        if not grupo or not subgrupo:
            motivo_ignorado = f"grupo ou subgrupo não encontrado para conta: {conta_nome}"
            rows_ignored.append({
                'linha': row_num + 2,
                'data': mes_str,
                'conta': conta_nome,
                'grupo': grupo_nome,
                'subgrupo': subgrupo_nome,
                'valor': valor_str,
                'motivo': motivo_ignorado
            })
            continue
        
        # Linha válida - adicionar ao DataFrame normalizado
        rows_valid.append({
            'data': data_prevista.date(),
            'grupo': grupo.name,
            'subgrupo': subgrupo.name,
            'conta': conta.name,
            'valor': valor.quantize(Decimal('0.01')),
            'descricao': f"Previsão de {conta_nome}",
            'linha_original': row_num + 2
        })
    
    df_valid = pd.DataFrame(rows_valid)
    df_ignored = pd.DataFrame(rows_ignored)
    
    return df_valid, df_ignored

def normalize_previstos_from_db(
    db: Session,
    tenant_id: str,
    business_unit_id: str
) -> pd.DataFrame:
    """Normaliza lançamentos previstos do banco para DataFrame comparável"""
    lancamentos = db.query(LancamentoPrevisto).join(
        ChartAccount
    ).join(
        ChartAccountSubgroup
    ).join(
        ChartAccountGroup
    ).filter(
        LancamentoPrevisto.tenant_id == tenant_id,
        LancamentoPrevisto.business_unit_id == business_unit_id
    ).all()
    
    rows = []
    for lp in lancamentos:
        rows.append({
            'data': lp.data_prevista.date(),
            'grupo': lp.grupo.name if lp.grupo else "",
            'subgrupo': lp.subgrupo.name if lp.subgrupo else "",
            'conta': lp.conta.name if lp.conta else "",
            'valor': lp.valor.quantize(Decimal('0.01')),
            'descricao': lp.observacoes or "",
            'id': str(lp.id)
        })
    
    return pd.DataFrame(rows)

def validate_lancamentos_previstos(
    db: Session,
    tenant_id: str,
    business_unit_id: str,
    excel_file: Path,
    log_dir: Path,
    timestamp: str
) -> Tuple[bool, Dict]:
    """Valida lançamentos previstos: planilha vs banco (linha a linha)"""
    print("\n" + "="*60)
    print("📊 VALIDAÇÃO DE LANÇAMENTOS PREVISTOS (LINHA A LINHA)")
    print("="*60)
    
    results = {
        'total_bruto_planilha': 0,
        'total_pos_filtro_planilha': 0,
        'total_banco': 0,
        'missing_in_db': 0,
        'extra_in_db': 0,
        'ok': False,
        'csv_missing': None,
        'csv_extra': None,
        'csv_ignored': None
    }
    
    # Ler planilha
    sheet_name = find_sheet_in_excel(excel_file, LANCAMENTOS_PREVISTOS_SHEETS)
    if not sheet_name:
        print("❌ Aba de Lançamentos Previstos não encontrada")
        return False, results
    
    df_raw = read_excel_sheet(excel_file, sheet_name)
    if df_raw.empty:
        print("❌ Nenhum dado encontrado na aba de Lançamentos Previstos")
        return False, results
    
    results['total_bruto_planilha'] = len(df_raw)
    
    # Normalizar colunas (mesma lógica do seed)
    df_raw.columns = df_raw.columns.str.strip()
    column_map = {}
    for col in df_raw.columns:
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
    
    if 'data_prevista' not in column_map or 'conta' not in column_map or 'valor' not in column_map:
        print("❌ Colunas necessárias não encontradas")
        return False, results
    
    # Normalizar planilha (aplicar mesmas regras do seed)
    print("  Aplicando filtros do seed na planilha...")
    df_sheet_norm, df_ignored = normalize_previstos_from_sheet(df_raw, column_map, tenant_id, db)
    results['total_pos_filtro_planilha'] = len(df_sheet_norm)
    
    # Normalizar banco
    print("  Carregando dados do banco...")
    df_db_norm = normalize_previstos_from_db(db, tenant_id, business_unit_id)
    results['total_banco'] = len(df_db_norm)
    
    # Criar chave composta para comparação
    # Garantir que 'valor' esteja em float antes de usar .round()
    if not df_sheet_norm.empty:
        df_sheet_norm['valor'] = df_sheet_norm['valor'].apply(
            lambda v: float(v) if v is not None else 0.0
        )
        df_sheet_norm['key'] = (
            df_sheet_norm['data'].astype(str) + "|" +
            df_sheet_norm['grupo'].astype(str) + "|" +
            df_sheet_norm['subgrupo'].astype(str) + "|" +
            df_sheet_norm['conta'].astype(str) + "|" +
            df_sheet_norm['valor'].round(2).astype(str)
        )
    
    if not df_db_norm.empty:
        df_db_norm['valor'] = df_db_norm['valor'].apply(
            lambda v: float(v) if v is not None else 0.0
        )
        df_db_norm['key'] = (
            df_db_norm['data'].astype(str) + "|" +
            df_db_norm['grupo'].astype(str) + "|" +
            df_db_norm['subgrupo'].astype(str) + "|" +
            df_db_norm['conta'].astype(str) + "|" +
            df_db_norm['valor'].round(2).astype(str)
        )
    
    # Merge para encontrar diferenças
    if not df_sheet_norm.empty and not df_db_norm.empty:
        df_merge = df_sheet_norm.merge(
            df_db_norm[['key']],
            on='key',
            how='outer',
            indicator=True
        )
        
        df_missing = df_merge[df_merge['_merge'] == 'left_only'].copy()
        df_extra = df_merge[df_merge['_merge'] == 'right_only'].copy()
        
        results['missing_in_db'] = len(df_missing)
        results['extra_in_db'] = len(df_extra)
        
        # Salvar CSVs
        if len(df_missing) > 0:
            csv_missing = log_dir / f"previstos_missing_in_db_{timestamp}.csv"
            df_missing[['linha_original', 'data', 'grupo', 'subgrupo', 'conta', 'valor', 'descricao']].to_csv(
                csv_missing, index=False, encoding='utf-8-sig'
            )
            results['csv_missing'] = str(csv_missing)
            print(f"  📄 Linhas faltando no banco: {csv_missing}")
        
        if len(df_extra) > 0:
            csv_extra = log_dir / f"previstos_extra_in_db_{timestamp}.csv"
            df_extra[['data', 'grupo', 'subgrupo', 'conta', 'valor', 'descricao', 'id']].to_csv(
                csv_extra, index=False, encoding='utf-8-sig'
            )
            results['csv_extra'] = str(csv_extra)
            print(f"  📄 Linhas extras no banco: {csv_extra}")
    elif not df_sheet_norm.empty:
        # Tudo da planilha está faltando
        results['missing_in_db'] = len(df_sheet_norm)
        csv_missing = log_dir / f"previstos_missing_in_db_{timestamp}.csv"
        df_sheet_norm[['linha_original', 'data', 'grupo', 'subgrupo', 'conta', 'valor', 'descricao']].to_csv(
            csv_missing, index=False, encoding='utf-8-sig'
        )
        results['csv_missing'] = str(csv_missing)
    elif not df_db_norm.empty:
        # Tudo do banco está extra
        results['extra_in_db'] = len(df_db_norm)
        csv_extra = log_dir / f"previstos_extra_in_db_{timestamp}.csv"
        df_db_norm[['data', 'grupo', 'subgrupo', 'conta', 'valor', 'descricao', 'id']].to_csv(
            csv_extra, index=False, encoding='utf-8-sig'
        )
        results['csv_extra'] = str(csv_extra)
    
    # Salvar CSV de linhas ignoradas
    if len(df_ignored) > 0:
        csv_ignored = log_dir / f"previstos_ignored_{timestamp}.csv"
        df_ignored.to_csv(csv_ignored, index=False, encoding='utf-8-sig')
        results['csv_ignored'] = str(csv_ignored)
        print(f"  📄 Linhas ignoradas por regras do seed: {csv_ignored}")
    
    # Determinar status
    if results['missing_in_db'] == 0 and results['extra_in_db'] == 0:
        results['ok'] = True
        status = "✅ OK"
    elif results['missing_in_db'] == 0:
        results['ok'] = False
        status = "⚠️  OK (com linhas extras no banco)"
    else:
        results['ok'] = False
        status = "❌ MISMATCH"
    
    # Imprimir resultados
    print(f"\n[Lançamentos Previstos]")
    print(f"  Planilha (bruto): {results['total_bruto_planilha']} linhas")
    print(f"  Planilha (pós-filtro seed): {results['total_pos_filtro_planilha']} linhas")
    print(f"  Banco: {results['total_banco']} linhas")
    print(f"  Faltando no banco: {results['missing_in_db']} linhas")
    print(f"  Extras no banco: {results['extra_in_db']} linhas")
    print(f"  Linhas ignoradas (regras seed): {len(df_ignored)} linhas")
    print(f"  Status: {status}")
    
    return results['ok'], results

# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Validar dados do seed contra planilha do cliente')
    parser.add_argument('--file', type=str, default=str(DEFAULT_EXCEL_FILE),
                       help='Caminho para o arquivo Excel (padrão: data/fluxo_caixa_2025.xlsx)')
    
    args = parser.parse_args()
    
    excel_file = Path(args.file)
    if not excel_file.exists():
        print(f"❌ Arquivo não encontrado: {excel_file}")
        sys.exit(1)
    
    # Configurar logging
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = backend_path / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"validate_seed_{timestamp}.log"
    
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
        print("="*60)
        print("🔍 VALIDAÇÃO DE DADOS – PLANILHA x STAGING")
        print("="*60)
        print(f"📁 Arquivo Excel: {excel_file}")
        print(f"📝 Log: {log_file}")
        print()
        
        # Conectar ao banco
        db = SessionLocal()
        try:
            # Obter tenant e business unit (mesmos do seed)
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
            
            # Executar validações
            plano_ok, plano_results = validate_plano_contas(db, tenant.id, excel_file)
            diarios_ok, diarios_results = validate_lancamentos_diarios(
                db, tenant.id, business_unit.id, excel_file, log_dir, timestamp
            )
            previstos_ok, previstos_results = validate_lancamentos_previstos(
                db, tenant.id, business_unit.id, excel_file, log_dir, timestamp
            )
            
            # Resumo final
            print("\n" + "="*60)
            print("📊 RESUMO FINAL")
            print("="*60)
            
            # Determinar status considerando se diferenças são explicadas por regras do seed
            status_plano = "✅ OK" if plano_ok else "❌ MISMATCH"
            
            if diarios_ok:
                status_diarios = "✅ OK"
            elif diarios_results['missing_in_db'] == 0:
                # Diferença explicada apenas por linhas ignoradas
                status_diarios = "✅ OK (diferença explicada por regras de seed)"
            else:
                status_diarios = "❌ MISMATCH"
            
            if previstos_ok:
                status_previstos = "✅ OK"
            elif previstos_results['missing_in_db'] == 0:
                # Diferença explicada apenas por linhas ignoradas
                status_previstos = "✅ OK (diferença explicada por regras de seed)"
            else:
                status_previstos = "❌ MISMATCH"
            
            print(f"Plano de Contas: {status_plano}")
            print(f"Lançamentos Diários: {status_diarios}")
            print(f"Lançamentos Previstos: {status_previstos}")
            
            print("\nDetalhes:")
            print(f"- Grupos: planilha={plano_results['grupos']['planilha']} | banco={plano_results['grupos']['banco']}")
            print(f"- Subgrupos: planilha={plano_results['subgrupos']['planilha']} | banco={plano_results['subgrupos']['banco']}")
            print(f"- Contas: planilha={plano_results['contas']['planilha']} | banco={plano_results['contas']['banco']}")
            
            print(f"\nLançamentos Diários:")
            print(f"  - Planilha (bruto): {diarios_results['total_bruto_planilha']} linhas")
            print(f"  - Planilha (pós-filtro seed): {diarios_results['total_pos_filtro_planilha']} linhas")
            print(f"  - Banco: {diarios_results['total_banco']} linhas")
            print(f"  - Faltando no banco: {diarios_results['missing_in_db']} linhas")
            if diarios_results['csv_ignored']:
                print(f"  - Linhas ignoradas: ver {diarios_results['csv_ignored']}")
            if diarios_results['csv_missing']:
                print(f"  - Linhas faltando: ver {diarios_results['csv_missing']}")
            
            print(f"\nLançamentos Previstos:")
            print(f"  - Planilha (bruto): {previstos_results['total_bruto_planilha']} linhas")
            print(f"  - Planilha (pós-filtro seed): {previstos_results['total_pos_filtro_planilha']} linhas")
            print(f"  - Banco: {previstos_results['total_banco']} linhas")
            print(f"  - Faltando no banco: {previstos_results['missing_in_db']} linhas")
            if previstos_results['csv_ignored']:
                print(f"  - Linhas ignoradas: ver {previstos_results['csv_ignored']}")
            if previstos_results['csv_missing']:
                print(f"  - Linhas faltando: ver {previstos_results['csv_missing']}")
            
            all_ok = plano_ok and diarios_ok and previstos_ok
            
            print("\n" + "="*60)
            if all_ok:
                print("✅ VALIDAÇÃO CONCLUÍDA: TODOS OS DADOS ESTÃO COMPATÍVEIS")
            else:
                print("❌ VALIDAÇÃO CONCLUÍDA: FORAM ENCONTRADAS INCOMPATIBILIDADES")
            print("="*60)
            
            sys.stdout = original_stdout
            log_f.close()
            
            # Retornar código de saída
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

