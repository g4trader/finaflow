#!/usr/bin/env python3
"""
Script de Debug - Identifica divergência de CUSTO entre Excel e Banco

Gera CSV e JSON com comparação detalhada por grupo/subgrupo.
"""

import sys
import os
import json
import csv
from pathlib import Path
from decimal import Decimal
from typing import Dict, List
from collections import defaultdict
from datetime import datetime

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

try:
    import pandas as pd
except ImportError:
    print("❌ Erro: pandas não está instalado")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("❌ Erro: requests não está instalado")
    sys.exit(1)

ARTIFACTS_DIR = backend_path / "artifacts"
YEAR = 2025

def load_baseline() -> Dict:
    """Carrega baseline do Excel"""
    baseline_path = ARTIFACTS_DIR / f"baseline_excel_{YEAR}.json"
    if not baseline_path.exists():
        print(f"❌ Baseline não encontrado: {baseline_path}")
        sys.exit(1)
    
    with open(baseline_path, "r", encoding="utf-8") as f:
        return json.load(f)

def find_sheet_in_excel(excel_file, sheet_names: List[str]) -> str:
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

def parse_date(date_value):
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
        "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y",
        "%d-%m-%Y %H:%M:%S", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value_str, fmt)
        except:
            continue
    return None

def determine_transaction_type(grupo_nome: str, subgrupo_nome: str = None) -> str:
    """Determina o tipo de transação baseado no grupo e subgrupo"""
    grupo_lower = grupo_nome.lower()
    subgrupo_lower = (subgrupo_nome or "").lower()
    if any(kw in grupo_lower for kw in ["receita", "venda", "renda", "faturamento", "vendas"]):
        return "RECEITA"
    if any(kw in grupo_lower for kw in ["custo", "custos"]) or any(
        kw in subgrupo_lower for kw in ["custo", "custos", "mercadoria", "produto"]
    ):
        return "CUSTO"
    return "DESPESA"

LANCAMENTOS_DIARIOS_SHEETS = ["Lançamento Diário", "Lançamento Diario", "Lancamento Diario", "Lançamentos Diários"]

def calculate_excel_cost_by_group_subgroup(excel_file: Path) -> Dict[tuple, Decimal]:
    """
    Calcula custo do Excel agrupado por (grupo, subgrupo)
    Retorna: {(grupo, subgrupo): Decimal}
    """
    
    cost_by_group = defaultdict(lambda: Decimal(0))
    
    # Encontrar aba
    sheet_name = find_sheet_in_excel(excel_file, LANCAMENTOS_DIARIOS_SHEETS)
    if not sheet_name:
        print("⚠️  Aba de Lançamentos Diários não encontrada")
        return cost_by_group
    
    # Ler dados
    df = read_excel_sheet(excel_file, sheet_name)
    if df.empty:
        return cost_by_group
    
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
        print(f"⚠️  Colunas necessárias não encontradas")
        return cost_by_group
    
    # Processar linhas
    for _, row in df.iterrows():
        try:
            data_str = str(row[column_map['data_movimentacao']]) if pd.notna(row[column_map['data_movimentacao']]) else ""
            valor_str = str(row[column_map['valor']]) if pd.notna(row[column_map['valor']]) else ""
            grupo_str = str(row[column_map.get('grupo', '')]) if column_map.get('grupo') and pd.notna(row[column_map.get('grupo', '')]) else ""
            subgrupo_str = str(row[column_map.get('subgrupo', '')]) if column_map.get('subgrupo') and pd.notna(row[column_map.get('subgrupo', '')]) else ""
            
            data = parse_date(data_str)
            if not data or data.year != YEAR:
                continue
            
            valor = parse_currency(valor_str)
            if valor == 0:
                continue
            
            tipo = determine_transaction_type(grupo_str, subgrupo_str)
            
            if tipo == "CUSTO":
                key = (grupo_str.strip(), subgrupo_str.strip())
                cost_by_group[key] += valor
        except Exception:
            continue
    
    return dict(cost_by_group)

def login_api(backend_url: str, email: str, password: str) -> str:
    """Faz login e retorna token"""
    response = requests.post(
        f"{backend_url}/api/v1/auth/login",
        json={"username": email, "password": password}
    )
    if response.status_code != 200:
        raise Exception(f"Login falhou: {response.status_code}")
    return response.json().get("access_token")

def calculate_db_cost_by_group_subgroup(backend_url: str, token: str) -> Dict[tuple, Decimal]:
    """
    Calcula custo do banco agrupado por (grupo, subgrupo) via API
    Retorna: {(grupo_nome, subgrupo_nome): Decimal}
    """
    # Buscar transações mensais detalhadas e agregar por grupo/subgrupo
    # Usar monthly-transactions para cada mês e filtrar por tipo CUSTO
    result = defaultdict(lambda: Decimal(0))
    
    for month in range(1, 13):
        try:
            response = requests.get(
                f"{backend_url}/api/v1/financial/monthly-transactions?year={YEAR}&month={month}&type=CUSTO&page_size=10000",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                data = response.json()
                transactions = data.get("transactions", [])
                
                for tx in transactions:
                    grupo = tx.get("grupo_nome", "").strip()
                    subgrupo = tx.get("subgrupo_nome", "").strip()
                    valor = Decimal(str(tx.get("valor", 0)))
                    
                    if grupo and subgrupo and valor > 0:
                        key = (grupo, subgrupo)
                        result[key] += valor
        except Exception as e:
            print(f"⚠️  Erro ao buscar mês {month}: {e}")
            continue
    
    return dict(result)

def get_example_transaction_ids(backend_url: str, token: str, grupo: str, subgrupo: str, limit: int = 5) -> List[str]:
    """Obtém IDs de exemplo via API"""
    # Buscar em qualquer mês que tenha dados
    for month in range(1, 13):
        try:
            response = requests.get(
                f"{backend_url}/api/v1/financial/monthly-transactions?year={YEAR}&month={month}&type=CUSTO&page_size=100",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                data = response.json()
                transactions = data.get("transactions", [])
                
                example_ids = []
                for tx in transactions:
                    if tx.get("grupo_nome", "").strip() == grupo and tx.get("subgrupo_nome", "").strip() == subgrupo:
                        tx_id = tx.get("id")
                        if tx_id:
                            example_ids.append(str(tx_id))
                        if len(example_ids) >= limit:
                            return example_ids
                
                if example_ids:
                    return example_ids
        except Exception:
            continue
    
    return []

def main():
    excel_file = backend_path / "data" / "fluxo_caixa_2025.xlsx"
    if not excel_file.exists():
        print(f"❌ Arquivo Excel não encontrado: {excel_file}")
        sys.exit(1)
    
    print("="*60)
    print("🔍 DEBUG: Divergência de CUSTO 2025")
    print("="*60)
    print()
    
    # Carregar baseline
    print("📊 Carregando baseline do Excel...")
    baseline = load_baseline()
    total_excel_cost = Decimal(str(baseline["annual_totals"]["custo"]))
    print(f"✅ Custo total Excel: R$ {total_excel_cost:,.2f}")
    print()
    
    # Calcular custo do Excel por grupo/subgrupo
    print("📊 Calculando custo do Excel por grupo/subgrupo...")
    excel_cost_by_group = calculate_excel_cost_by_group_subgroup(excel_file)
    print(f"✅ {len(excel_cost_by_group)} grupos/subgrupos encontrados no Excel")
    print()
    
    # Conectar via API
    backend_url = os.getenv("BACKEND_URL", "https://finaflow-backend-staging-642830139828.us-central1.run.app")
    email = os.getenv("QA_EMAIL", "qa@finaflow.test")
    password = os.getenv("QA_PASSWORD", "QaFinaflow123!")
    
    print("🔗 Conectando via API...")
    try:
        token = login_api(backend_url, email, password)
        print("✅ Login realizado")
        print()
    except Exception as e:
        print(f"❌ Erro ao fazer login: {e}")
        sys.exit(1)
    
    # Calcular custo do banco por grupo/subgrupo
    print("📊 Calculando custo do banco por grupo/subgrupo via API...")
    print("   (Isso pode levar alguns minutos, buscando dados de todos os meses...)")
    db_cost_by_group = calculate_db_cost_by_group_subgroup(backend_url, token)
    print(f"✅ {len(db_cost_by_group)} grupos/subgrupos encontrados no banco")
    print()
    
    # Calcular total do banco
    total_db_cost = sum(db_cost_by_group.values())
    print(f"✅ Custo total Banco: R$ {total_db_cost:,.2f}")
    print()
    
    # Comparar
    print("="*60)
    print("📊 COMPARAÇÃO POR GRUPO/SUBGRUPO")
    print("="*60)
    
    all_keys = set(excel_cost_by_group.keys()) | set(db_cost_by_group.keys())
    
    diff_rows = []
    for key in sorted(all_keys):
        grupo, subgrupo = key
        excel_cost = excel_cost_by_group.get(key, Decimal(0))
        db_cost = db_cost_by_group.get(key, Decimal(0))
        delta = excel_cost - db_cost
        
        if abs(delta) > Decimal("0.01"):  # Apenas mostrar diferenças significativas
            # Obter IDs de exemplo
            example_ids = []
            if db_cost > 0:
                example_ids = get_example_transaction_ids(backend_url, token, grupo, subgrupo, 5)
            
            diff_rows.append({
                "group": grupo,
                "subgroup": subgrupo,
                "excel_cost_total_year": float(excel_cost),
                "db_cost_total_year": float(db_cost),
                "delta": float(delta),
                "delta_pct": float((delta / excel_cost * 100) if excel_cost > 0 else 0),
                "top_example_transaction_ids": ",".join(example_ids[:5])
            })
    
    # Ordenar por delta absoluto
    diff_rows.sort(key=lambda x: abs(x["delta"]), reverse=True)
    
    # Salvar CSV
    csv_path = ARTIFACTS_DIR / f"cost_diff_by_group_subgroup_{YEAR}.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        if diff_rows:
            writer = csv.DictWriter(f, fieldnames=diff_rows[0].keys())
            writer.writeheader()
            writer.writerows(diff_rows)
    print(f"✅ CSV salvo: {csv_path}")
    print(f"   {len(diff_rows)} grupos/subgrupos com diferença > R$ 0,01")
    print()
    
    # Salvar JSON resumido
    summary = {
        "metadata": {
            "year": YEAR,
            "generated_at": datetime.utcnow().isoformat(),
            "backend_url": backend_url
        },
        "total_excel_cost": float(total_excel_cost),
        "total_db_cost": float(total_db_cost),
        "total_delta": float(total_excel_cost - total_db_cost),
        "top_20_groups_by_delta": diff_rows[:20]
    }
    
    json_path = ARTIFACTS_DIR / f"cost_diff_summary_{YEAR}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"✅ JSON salvo: {json_path}")
    print()
    
    # Mostrar top 10
    print("="*60)
    print("🔝 TOP 10 DIVERGÊNCIAS")
    print("="*60)
    for i, row in enumerate(diff_rows[:10], 1):
        print(f"{i:2d}. {row['group']} / {row['subgroup']}")
        print(f"    Excel: R$ {row['excel_cost_total_year']:>12,.2f} | Banco: R$ {row['db_cost_total_year']:>12,.2f} | Delta: R$ {row['delta']:>12,.2f} ({row['delta_pct']:>6.2f}%)")
        print()
    
    print("="*60)
    print("📊 RESUMO")
    print("="*60)
    print(f"Total Excel CUSTO: R$ {total_excel_cost:,.2f}")
    print(f"Total Banco CUSTO: R$ {total_db_cost:,.2f}")
    print(f"Diferença Total:   R$ {total_excel_cost - total_db_cost:,.2f}")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

