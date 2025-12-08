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
# VALIDAÇÃO DE LANÇAMENTOS DIÁRIOS
# ============================================================================

def validate_lancamentos_diarios(
    db: Session,
    tenant_id: str,
    business_unit_id: str,
    excel_file: Path
) -> Tuple[bool, Dict]:
    """Valida lançamentos diários: planilha vs banco"""
    print("\n" + "="*60)
    print("📊 VALIDAÇÃO DE LANÇAMENTOS DIÁRIOS")
    print("="*60)
    
    results = {
        'total': {'planilha': 0, 'banco': 0, 'ok': False},
        'soma_total': {'planilha': Decimal('0'), 'banco': Decimal('0'), 'ok': False},
        'por_mes': {}
    }
    
    # Ler planilha
    sheet_name = find_sheet_in_excel(excel_file, LANCAMENTOS_DIARIOS_SHEETS)
    if not sheet_name:
        print("❌ Aba de Lançamentos Diários não encontrada")
        return False, results
    
    df = read_excel_sheet(excel_file, sheet_name)
    if df.empty:
        print("❌ Nenhum dado encontrado na aba de Lançamentos Diários")
        return False, results
    
    # Normalizar colunas
    df.columns = df.columns.str.strip()
    column_map = {}
    for col in df.columns:
        col_lower = col.lower()
        if 'data' in col_lower and 'movimentação' in col_lower or 'data' in col_lower and 'movimentacao' in col_lower:
            column_map['data'] = col
        if 'valor' in col_lower and 'valor' not in column_map:
            column_map['valor'] = col
        if 'grupo' in col_lower and 'subgrupo' not in col_lower:
            column_map['grupo'] = col
        if 'subgrupo' in col_lower:
            column_map['subgrupo'] = col
        if 'conta' in col_lower:
            column_map['conta'] = col
    
    if 'data' not in column_map or 'valor' not in column_map:
        print("❌ Colunas necessárias não encontradas")
        return False, results
    
    # Processar planilha (aplicar mesmas regras do seed)
    total_planilha = 0
    soma_planilha = Decimal('0')
    por_mes_planilha = defaultdict(lambda: {'qtd': 0, 'soma': Decimal('0')})
    
    for _, row in df.iterrows():
        data_str = row[column_map['data']] if pd.notna(row[column_map['data']]) else None
        valor_str = row[column_map['valor']] if pd.notna(row[column_map['valor']]) else None
        
        # Validar data
        data = parse_date(data_str)
        if not data:
            continue
        
        # Validar valor
        valor = parse_currency(valor_str)
        if valor == Decimal('0'):
            continue
        
        # Validar grupo/subgrupo/conta (se existirem)
        if 'grupo' in column_map:
            grupo = str(row[column_map['grupo']]).strip() if pd.notna(row[column_map['grupo']]) else ""
            if not grupo:
                continue
        
        total_planilha += 1
        soma_planilha += valor
        
        # Agrupar por mês
        mes_key = f"{data.year}-{data.month:02d}"
        por_mes_planilha[mes_key]['qtd'] += 1
        por_mes_planilha[mes_key]['soma'] += valor
    
    results['total']['planilha'] = total_planilha
    results['soma_total']['planilha'] = soma_planilha
    
    # Consultar banco
    lancamentos = db.query(LancamentoDiario).filter(
        LancamentoDiario.tenant_id == tenant_id,
        LancamentoDiario.business_unit_id == business_unit_id
    ).all()
    
    total_banco = len(lancamentos)
    soma_banco = sum(ld.valor for ld in lancamentos)
    por_mes_banco = defaultdict(lambda: {'qtd': 0, 'soma': Decimal('0')})
    
    for ld in lancamentos:
        mes_key = f"{ld.data_movimentacao.year}-{ld.data_movimentacao.month:02d}"
        por_mes_banco[mes_key]['qtd'] += 1
        por_mes_banco[mes_key]['soma'] += ld.valor
    
    results['total']['banco'] = total_banco
    results['soma_total']['banco'] = soma_banco
    
    # Comparar totais
    results['total']['ok'] = results['total']['planilha'] == results['total']['banco']
    
    # Comparar soma (com tolerância)
    diff_soma = abs(results['soma_total']['planilha'] - results['soma_total']['banco'])
    results['soma_total']['ok'] = diff_soma < TOLERANCE
    
    # Comparar por mês
    todos_meses = set(list(por_mes_planilha.keys()) + list(por_mes_banco.keys()))
    for mes in sorted(todos_meses):
        qtd_planilha = por_mes_planilha[mes]['qtd']
        soma_planilha_mes = por_mes_planilha[mes]['soma']
        qtd_banco = por_mes_banco[mes]['qtd']
        soma_banco_mes = por_mes_banco[mes]['soma']
        
        diff_soma_mes = abs(soma_planilha_mes - soma_banco_mes)
        ok_mes = (qtd_planilha == qtd_banco) and (diff_soma_mes < TOLERANCE)
        
        results['por_mes'][mes] = {
            'planilha': {'qtd': qtd_planilha, 'soma': soma_planilha_mes},
            'banco': {'qtd': qtd_banco, 'soma': soma_banco_mes},
            'ok': ok_mes
        }
    
    # Imprimir resultados
    status_total = "✅ OK" if results['total']['ok'] else "❌ MISMATCH"
    status_soma = "✅ OK" if results['soma_total']['ok'] else "❌ MISMATCH"
    
    print(f"[Lançamentos Diários] Total: planilha={results['total']['planilha']} | banco={results['total']['banco']} -> {status_total}")
    print(f"[Lançamentos Diários] Soma total: planilha=R$ {results['soma_total']['planilha']:,.2f} | banco=R$ {results['soma_total']['banco']:,.2f} -> {status_soma}")
    
    if not results['soma_total']['ok']:
        diff = abs(results['soma_total']['planilha'] - results['soma_total']['banco'])
        print(f"  ⚠️  Diferença: R$ {diff:,.2f}")
    
    print("\n[Lançamentos Diários] Por mês:")
    for mes in sorted(results['por_mes'].keys()):
        mes_data = results['por_mes'][mes]
        status_mes = "✅ OK" if mes_data['ok'] else "❌ MISMATCH"
        print(f"  {mes}: planilha={mes_data['planilha']['qtd']} / R$ {mes_data['planilha']['soma']:,.2f} | banco={mes_data['banco']['qtd']} / R$ {mes_data['banco']['soma']:,.2f} -> {status_mes}")
    
    all_ok = results['total']['ok'] and results['soma_total']['ok'] and all(m['ok'] for m in results['por_mes'].values())
    return all_ok, results

# ============================================================================
# VALIDAÇÃO DE LANÇAMENTOS PREVISTOS
# ============================================================================

def validate_lancamentos_previstos(
    db: Session,
    tenant_id: str,
    business_unit_id: str,
    excel_file: Path
) -> Tuple[bool, Dict]:
    """Valida lançamentos previstos: planilha vs banco"""
    print("\n" + "="*60)
    print("📊 VALIDAÇÃO DE LANÇAMENTOS PREVISTOS")
    print("="*60)
    
    results = {
        'total': {'planilha': 0, 'banco': 0, 'ok': False},
        'soma_total': {'planilha': Decimal('0'), 'banco': Decimal('0'), 'ok': False},
        'por_mes': {}
    }
    
    # Ler planilha
    sheet_name = find_sheet_in_excel(excel_file, LANCAMENTOS_PREVISTOS_SHEETS)
    if not sheet_name:
        print("❌ Aba de Lançamentos Previstos não encontrada")
        return False, results
    
    df = read_excel_sheet(excel_file, sheet_name)
    if df.empty:
        print("❌ Nenhum dado encontrado na aba de Lançamentos Previstos")
        return False, results
    
    # Normalizar colunas
    df.columns = df.columns.str.strip()
    column_map = {}
    for col in df.columns:
        col_lower = col.lower()
        if ('mês' in col_lower or 'mes' in col_lower or 'data' in col_lower) and 'prevista' in col_lower:
            column_map['data'] = col
        elif 'mês' in col_lower or 'mes' in col_lower:
            column_map['data'] = col
        if 'valor' in col_lower and 'valor' not in column_map:
            column_map['valor'] = col
        if 'grupo' in col_lower and 'subgrupo' not in col_lower:
            column_map['grupo'] = col
        if 'subgrupo' in col_lower:
            column_map['subgrupo'] = col
        if 'conta' in col_lower:
            column_map['conta'] = col
    
    if 'data' not in column_map or 'valor' not in column_map:
        print("❌ Colunas necessárias não encontradas")
        return False, results
    
    # Processar planilha
    total_planilha = 0
    soma_planilha = Decimal('0')
    por_mes_planilha = defaultdict(lambda: {'qtd': 0, 'soma': Decimal('0')})
    
    for _, row in df.iterrows():
        data_str = row[column_map['data']] if pd.notna(row[column_map['data']]) else None
        valor_str = row[column_map['valor']] if pd.notna(row[column_map['valor']]) else None
        
        # Validar data
        data = parse_date(data_str)
        if not data:
            # Tentar interpretar como mês/ano apenas
            if isinstance(data_str, (int, float)):
                # Assumir formato YYYYMM ou similar
                continue
            continue
        
        # Validar valor
        valor = parse_currency(valor_str)
        if valor == Decimal('0'):
            continue
        
        # Validar grupo/subgrupo/conta (se existirem)
        if 'grupo' in column_map:
            grupo = str(row[column_map['grupo']]).strip() if pd.notna(row[column_map['grupo']]) else ""
            if not grupo:
                continue
        
        total_planilha += 1
        soma_planilha += valor
        
        # Agrupar por mês
        mes_key = f"{data.year}-{data.month:02d}"
        por_mes_planilha[mes_key]['qtd'] += 1
        por_mes_planilha[mes_key]['soma'] += valor
    
    results['total']['planilha'] = total_planilha
    results['soma_total']['planilha'] = soma_planilha
    
    # Consultar banco
    lancamentos = db.query(LancamentoPrevisto).filter(
        LancamentoPrevisto.tenant_id == tenant_id,
        LancamentoPrevisto.business_unit_id == business_unit_id
    ).all()
    
    total_banco = len(lancamentos)
    soma_banco = sum(lp.valor for lp in lancamentos)
    por_mes_banco = defaultdict(lambda: {'qtd': 0, 'soma': Decimal('0')})
    
    for lp in lancamentos:
        mes_key = f"{lp.data_prevista.year}-{lp.data_prevista.month:02d}"
        por_mes_banco[mes_key]['qtd'] += 1
        por_mes_banco[mes_key]['soma'] += lp.valor
    
    results['total']['banco'] = total_banco
    results['soma_total']['banco'] = soma_banco
    
    # Comparar totais
    results['total']['ok'] = results['total']['planilha'] == results['total']['banco']
    
    # Comparar soma (com tolerância)
    diff_soma = abs(results['soma_total']['planilha'] - results['soma_total']['banco'])
    results['soma_total']['ok'] = diff_soma < TOLERANCE
    
    # Comparar por mês
    todos_meses = set(list(por_mes_planilha.keys()) + list(por_mes_banco.keys()))
    for mes in sorted(todos_meses):
        qtd_planilha = por_mes_planilha[mes]['qtd']
        soma_planilha_mes = por_mes_planilha[mes]['soma']
        qtd_banco = por_mes_banco[mes]['qtd']
        soma_banco_mes = por_mes_banco[mes]['soma']
        
        diff_soma_mes = abs(soma_planilha_mes - soma_banco_mes)
        ok_mes = (qtd_planilha == qtd_banco) and (diff_soma_mes < TOLERANCE)
        
        results['por_mes'][mes] = {
            'planilha': {'qtd': qtd_planilha, 'soma': soma_planilha_mes},
            'banco': {'qtd': qtd_banco, 'soma': soma_banco_mes},
            'ok': ok_mes
        }
    
    # Imprimir resultados
    status_total = "✅ OK" if results['total']['ok'] else "❌ MISMATCH"
    status_soma = "✅ OK" if results['soma_total']['ok'] else "❌ MISMATCH"
    
    print(f"[Lançamentos Previstos] Total: planilha={results['total']['planilha']} | banco={results['total']['banco']} -> {status_total}")
    print(f"[Lançamentos Previstos] Soma total: planilha=R$ {results['soma_total']['planilha']:,.2f} | banco=R$ {results['soma_total']['banco']:,.2f} -> {status_soma}")
    
    if not results['soma_total']['ok']:
        diff = abs(results['soma_total']['planilha'] - results['soma_total']['banco'])
        print(f"  ⚠️  Diferença: R$ {diff:,.2f}")
    
    print("\n[Lançamentos Previstos] Por mês:")
    for mes in sorted(results['por_mes'].keys()):
        mes_data = results['por_mes'][mes]
        status_mes = "✅ OK" if mes_data['ok'] else "❌ MISMATCH"
        print(f"  {mes}: planilha={mes_data['planilha']['qtd']} / R$ {mes_data['planilha']['soma']:,.2f} | banco={mes_data['banco']['qtd']} / R$ {mes_data['banco']['soma']:,.2f} -> {status_mes}")
    
    all_ok = results['total']['ok'] and results['soma_total']['ok'] and all(m['ok'] for m in results['por_mes'].values())
    return all_ok, results

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
            diarios_ok, diarios_results = validate_lancamentos_diarios(db, tenant.id, business_unit.id, excel_file)
            previstos_ok, previstos_results = validate_lancamentos_previstos(db, tenant.id, business_unit.id, excel_file)
            
            # Resumo final
            print("\n" + "="*60)
            print("📊 RESUMO FINAL")
            print("="*60)
            
            status_plano = "✅ OK" if plano_ok else "❌ MISMATCH"
            status_diarios = "✅ OK" if diarios_ok else "❌ MISMATCH"
            status_previstos = "✅ OK" if previstos_ok else "❌ MISMATCH"
            
            print(f"Plano de Contas: {status_plano}")
            print(f"Lançamentos Diários: {status_diarios}")
            print(f"Lançamentos Previstos: {status_previstos}")
            
            print("\nDetalhes:")
            print(f"- Grupos: planilha={plano_results['grupos']['planilha']} | banco={plano_results['grupos']['banco']}")
            print(f"- Subgrupos: planilha={plano_results['subgrupos']['planilha']} | banco={plano_results['subgrupos']['banco']}")
            print(f"- Contas: planilha={plano_results['contas']['planilha']} | banco={plano_results['contas']['banco']}")
            print(f"- Diários total: planilha={diarios_results['total']['planilha']} | banco={diarios_results['total']['banco']}")
            print(f"- Previstos total: planilha={previstos_results['total']['planilha']} | banco={previstos_results['total']['banco']}")
            
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

