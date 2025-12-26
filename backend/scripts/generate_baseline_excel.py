#!/usr/bin/env python3
"""
Script de Baseline - Gera "Mapa de Verdade" da planilha Excel

Extrai:
- Totais anuais (receita, despesa, custo, saldo)
- Totais mensais (12 meses)
- Ordem dos grupos/subgrupos/contas conforme planilha

USO:
    python -m scripts.generate_baseline_excel --file data/fluxo_caixa_2025.xlsx --year 2025
"""

import sys
import os
import argparse
import json
import csv
import hashlib
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Tuple
from collections import defaultdict

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

try:
    import pandas as pd
except ImportError:
    print("❌ Erro: pandas não está instalado. Execute: pip install pandas openpyxl")
    sys.exit(1)

# Importar funções utilitárias sem depender de modelos do banco
import re
from typing import Optional, List as ListType

# Copiar funções necessárias para evitar importar modelos
def parse_currency(value) -> Decimal:
    """Converte valor monetário (BRL) para Decimal"""
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
        return Decimal("0")

def parse_date(date_value) -> Optional[datetime]:
    """Converte valor para datetime"""
    if pd.isna(date_value) or date_value == "" or date_value is None:
        return None
    if isinstance(date_value, datetime):
        return date_value
    if isinstance(date_value, pd.Timestamp):
        return date_value.to_pydatetime()
    value_str = str(date_value).strip()
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

def determine_transaction_type(grupo_nome: str, subgrupo_nome: Optional[str] = None) -> str:
    """Determina o tipo de transação baseado no grupo e subgrupo"""
    grupo_lower = grupo_nome.lower()
    subgrupo_lower = (subgrupo_nome or "").lower()
    if any(keyword in grupo_lower for keyword in ["receita", "venda", "renda", "faturamento", "vendas"]):
        return "RECEITA"
    if any(keyword in grupo_lower for keyword in ["custo", "custos"]) or any(
        keyword in subgrupo_lower for keyword in ["custo", "custos", "mercadoria", "produto"]
    ):
        return "CUSTO"
    return "DESPESA"

def find_sheet_in_excel(excel_file, sheet_names: ListType[str]) -> Optional[str]:
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

# Constantes
LANCAMENTOS_DIARIOS_SHEETS = ["Lançamento Diário", "Lançamento Diario", "Lancamento Diario", "Lançamentos Diários"]
PLANO_CONTAS_SHEETS = ["Plano de contas|LLM", "Plano de contas", "Plano de Contas", "Plano de Contas|LLM"]

# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

DEFAULT_EXCEL_FILE = backend_path / "data" / "fluxo_caixa_2025.xlsx"
ARTIFACTS_DIR = backend_path / "artifacts"

# ============================================================================
# FUNÇÕES DE PROCESSAMENTO
# ============================================================================

def calculate_file_hash(file_path: Path) -> str:
    """Calcula hash MD5 do arquivo Excel"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def extract_diarios_totals(excel_file: Path, year: int) -> Tuple[Dict[Tuple[int, int], Dict[str, Decimal]], Dict[str, Decimal]]:
    """
    Extrai totais mensais e anuais dos lançamentos diários.
    
    Retorna:
    - monthly_totals: {(year, month): {"receita": Decimal, "despesa": Decimal, "custo": Decimal, "saldo": Decimal}}
    - annual_totals: {"receita": Decimal, "despesa": Decimal, "custo": Decimal, "saldo": Decimal}
    """
    monthly_totals = defaultdict(lambda: {
        "receita": Decimal(0),
        "despesa": Decimal(0),
        "custo": Decimal(0),
        "saldo": Decimal(0)
    })
    
    # Encontrar aba de lançamentos diários
    sheet_name = find_sheet_in_excel(excel_file, LANCAMENTOS_DIARIOS_SHEETS)
    if not sheet_name:
        print("⚠️  Aba de Lançamentos Diários não encontrada")
        return monthly_totals, {
            "receita": Decimal(0),
            "despesa": Decimal(0),
            "custo": Decimal(0),
            "saldo": Decimal(0)
        }
    
    # Ler dados
    df = read_excel_sheet(excel_file, sheet_name)
    if df.empty:
        print("⚠️  Planilha de Lançamentos Diários vazia")
        return monthly_totals, {
            "receita": Decimal(0),
            "despesa": Decimal(0),
            "custo": Decimal(0),
            "saldo": Decimal(0)
        }
    
    # Normalizar colunas
    df.columns = df.columns.str.strip()
    column_map = {}
    for col in df.columns:
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
    
    if 'data_movimentacao' not in column_map or 'valor' not in column_map:
        print(f"⚠️  Colunas necessárias não encontradas. Colunas: {list(df.columns)}")
        return monthly_totals, {
            "receita": Decimal(0),
            "despesa": Decimal(0),
            "custo": Decimal(0),
            "saldo": Decimal(0)
        }
    
    # Processar linhas
    for _, row in df.iterrows():
        try:
            data_str = str(row[column_map['data_movimentacao']]) if pd.notna(row[column_map['data_movimentacao']]) else ""
            valor_str = str(row[column_map['valor']]) if pd.notna(row[column_map['valor']]) else ""
            grupo_str = str(row[column_map.get('grupo', '')]) if column_map.get('grupo') and pd.notna(row[column_map.get('grupo', '')]) else ""
            subgrupo_str = str(row[column_map.get('subgrupo', '')]) if column_map.get('subgrupo') and pd.notna(row[column_map.get('subgrupo', '')]) else ""
            
            # Parse
            data = parse_date(data_str)
            if not data or data.year != year:
                continue
            
            valor = parse_currency(valor_str)
            if valor == 0:
                continue
            
            # Determinar tipo
            tipo = determine_transaction_type(grupo_str, subgrupo_str)
            
            # Agregar por mês
            key = (year, data.month)
            
            if tipo == "RECEITA":
                monthly_totals[key]["receita"] += valor
            elif tipo == "DESPESA":
                monthly_totals[key]["despesa"] += valor
            elif tipo == "CUSTO":
                monthly_totals[key]["custo"] += valor
            
        except Exception as e:
            continue
    
    # Calcular saldo mensal
    for key in monthly_totals:
        monthly_totals[key]["saldo"] = (
            monthly_totals[key]["receita"] - 
            monthly_totals[key]["despesa"] - 
            monthly_totals[key]["custo"]
        )
    
    # Calcular totais anuais
    annual_totals = {
        "receita": Decimal(0),
        "despesa": Decimal(0),
        "custo": Decimal(0),
        "saldo": Decimal(0)
    }
    
    for month_data in monthly_totals.values():
        annual_totals["receita"] += month_data["receita"]
        annual_totals["despesa"] += month_data["despesa"]
        annual_totals["custo"] += month_data["custo"]
        annual_totals["saldo"] += month_data["saldo"]
    
    return dict(monthly_totals), annual_totals

def extract_order_from_plano_contas(excel_file: Path) -> List[Dict[str, str]]:
    """
    Extrai ordem dos grupos/subgrupos/contas conforme planilha.
    
    Retorna lista ordenada de dicionários com:
    - grupo
    - subgrupo
    - conta
    - ordem (linha na planilha)
    """
    order_list = []
    
    # Encontrar aba do plano de contas
    sheet_name = find_sheet_in_excel(excel_file, PLANO_CONTAS_SHEETS)
    if not sheet_name:
        print("⚠️  Aba do Plano de Contas não encontrada")
        return order_list
    
    # Ler dados
    df = read_excel_sheet(excel_file, sheet_name)
    if df.empty:
        print("⚠️  Planilha do Plano de Contas vazia")
        return order_list
    
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
        print(f"⚠️  Colunas necessárias não encontradas. Colunas: {list(df.columns)}")
        return order_list
    
    # Processar linhas mantendo ordem
    for idx, row in df.iterrows():
        try:
            conta = str(row[column_map['conta']]).strip() if pd.notna(row[column_map['conta']]) else ""
            subgrupo = str(row[column_map['subgrupo']]).strip() if pd.notna(row[column_map['subgrupo']]) else ""
            grupo = str(row[column_map['grupo']]).strip() if pd.notna(row[column_map['grupo']]) else ""
            escolha = ""
            if 'escolha' in column_map:
                escolha = str(row[column_map['escolha']]).strip() if pd.notna(row[column_map['escolha']]) else ""
            
            # Pular linhas vazias ou com escolha diferente de "Usar"
            if not conta or not subgrupo or not grupo:
                continue
            
            if escolha and escolha.lower() not in ['usar', 'use', 'sim', 'yes', '']:
                continue
            
            order_list.append({
                "ordem": idx + 2,  # +2 porque Excel começa em 1 e tem header
                "grupo": grupo,
                "subgrupo": subgrupo,
                "conta": conta
            })
        except Exception as e:
            continue
    
    return order_list

def main():
    parser = argparse.ArgumentParser(description="Gera baseline da planilha Excel")
    parser.add_argument("--file", type=str, default=str(DEFAULT_EXCEL_FILE), help="Caminho do arquivo Excel")
    parser.add_argument("--year", type=int, default=2025, help="Ano alvo")
    
    args = parser.parse_args()
    
    excel_file = Path(args.file)
    if not excel_file.is_absolute():
        excel_file = backend_path / excel_file
    
    if not excel_file.exists():
        print(f"❌ Arquivo não encontrado: {excel_file}")
        sys.exit(1)
    
    print("="*60)
    print("📊 GERANDO BASELINE DA PLANILHA EXCEL")
    print("="*60)
    print(f"📁 Arquivo: {excel_file}")
    print(f"📅 Ano: {args.year}")
    print()
    
    # Criar diretório de artefatos
    ARTIFACTS_DIR.mkdir(exist_ok=True)
    
    # Calcular hash do arquivo
    file_hash = calculate_file_hash(excel_file)
    print(f"🔐 Hash MD5: {file_hash}")
    print()
    
    # Extrair totais
    print("📊 Extraindo totais de lançamentos diários...")
    monthly_totals, annual_totals = extract_diarios_totals(excel_file, args.year)
    
    # Formatar totais mensais
    monthly_formatted = []
    for month in range(1, 13):
        key = (args.year, month)
        month_data = monthly_totals.get(key, {
            "receita": Decimal(0),
            "despesa": Decimal(0),
            "custo": Decimal(0),
            "saldo": Decimal(0)
        })
        monthly_formatted.append({
            "year": args.year,
            "month": month,
            "receita": float(month_data["receita"]),
            "despesa": float(month_data["despesa"]),
            "custo": float(month_data["custo"]),
            "saldo": float(month_data["saldo"])
        })
    
    # Extrair ordem
    print("📋 Extraindo ordem do plano de contas...")
    order_list = extract_order_from_plano_contas(excel_file)
    
    # Montar baseline JSON
    baseline = {
        "metadata": {
            "excel_file": str(excel_file),
            "excel_hash": file_hash,
            "year": args.year,
            "generated_at": datetime.utcnow().isoformat(),
            "generator": "generate_baseline_excel.py"
        },
        "annual_totals": {
            "receita": float(annual_totals["receita"]),
            "despesa": float(annual_totals["despesa"]),
            "custo": float(annual_totals["custo"]),
            "saldo": float(annual_totals["saldo"])
        },
        "monthly_totals": monthly_formatted,
        "order": order_list
    }
    
    # Salvar JSON
    json_path = ARTIFACTS_DIR / f"baseline_excel_{args.year}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(baseline, f, indent=2, ensure_ascii=False)
    print(f"✅ Baseline JSON salvo: {json_path}")
    
    # Salvar CSV de ordem
    csv_path = ARTIFACTS_DIR / f"baseline_order_{args.year}.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        if order_list:
            writer = csv.DictWriter(f, fieldnames=["ordem", "grupo", "subgrupo", "conta"])
            writer.writeheader()
            writer.writerows(order_list)
    print(f"✅ Ordem CSV salvo: {csv_path}")
    
    # Resumo
    print()
    print("="*60)
    print("📊 RESUMO")
    print("="*60)
    print(f"Totais Anuais:")
    print(f"  Receita: R$ {annual_totals['receita']:,.2f}")
    print(f"  Despesa: R$ {annual_totals['despesa']:,.2f}")
    print(f"  Custo:   R$ {annual_totals['custo']:,.2f}")
    print(f"  Saldo:   R$ {annual_totals['saldo']:,.2f}")
    print()
    print(f"Itens no plano de contas: {len(order_list)}")
    print()
    print("✅ Baseline gerado com sucesso!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

