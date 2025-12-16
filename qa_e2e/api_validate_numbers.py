#!/usr/bin/env python3
"""
Validação numérica: Excel vs API
Compara totais anuais e mensais entre planilha e API
"""

import sys
import os
import argparse
import json
from pathlib import Path
from decimal import Decimal
from typing import Dict, Tuple
from datetime import datetime

try:
    import pandas as pd
    import requests
except ImportError as e:
    print(f"❌ Erro: dependência não instalada: {e}")
    print("Execute: pip install pandas openpyxl requests")
    sys.exit(1)

# Adicionar backend ao path para reutilizar funções
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    from scripts.seed_utils import parse_currency, parse_date, determine_transaction_type
except ImportError:
    # Fallback se não conseguir importar
    def parse_currency(val: str) -> Decimal:
        if not val or val == "" or pd.isna(val):
            return Decimal(0)
        val_str = str(val).replace("R$", "").replace(".", "").replace(",", ".").strip()
        try:
            return Decimal(val_str)
        except:
            return Decimal(0)
    
    def parse_date(date_str: str):
        if not date_str or pd.isna(date_str):
            return None
        try:
            if isinstance(date_str, datetime):
                return date_str.date()
            return pd.to_datetime(date_str).date()
        except:
            return None
    
    def determine_transaction_type(grupo: str) -> str:
        grupo_upper = str(grupo).upper()
        if "RECEITA" in grupo_upper:
            return "RECEITA"
        elif "DESPESA" in grupo_upper:
            return "DESPESA"
        elif "CUSTO" in grupo_upper:
            return "CUSTO"
        return "DESPESA"

OUT_DIR = Path(__file__).parent / "out"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def login_api(backend_url: str, email: str, password: str) -> str:
    """Faz login e retorna token"""
    response = requests.post(
        f"{backend_url}/api/v1/auth/login",
        json={"username": email, "password": password},
        headers={"Content-Type": "application/json"}
    )
    if response.status_code != 200:
        print(f"❌ Erro no login: {response.status_code}")
        print(response.text)
        sys.exit(1)
    data = response.json()
    return data.get("access_token")

def fetch_annual_summary(backend_url: str, token: str, year: int) -> Dict:
    """Busca resumo anual da API"""
    response = requests.get(
        f"{backend_url}/api/v1/financial/annual-summary?year={year}",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code != 200:
        print(f"❌ Erro ao buscar annual-summary: {response.status_code}")
        print(response.text)
        sys.exit(1)
    return response.json()

def aggregate_excel(file_path: Path, year: int) -> Dict[Tuple[int, int], Dict[str, Decimal]]:
    """Agrega totais mensais do Excel"""
    print(f"📊 Lendo Excel: {file_path}")
    
    # Tentar encontrar a aba de lançamentos diários
    excel_file = pd.ExcelFile(file_path)
    sheet_name = None
    for name in excel_file.sheet_names:
        if "diário" in name.lower() or "diarios" in name.lower() or "lançamento" in name.lower():
            sheet_name = name
            break
    
    if not sheet_name:
        # Usar primeira aba
        sheet_name = excel_file.sheet_names[0]
    
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    
    # Tentar identificar colunas
    col_map = {}
    for col in df.columns:
        col_lower = str(col).lower()
        if "data" in col_lower and "mov" in col_lower:
            col_map['data'] = col
        elif "valor" in col_lower:
            col_map['valor'] = col
        elif "grupo" in col_lower:
            col_map['grupo'] = col
        elif "subgrupo" in col_lower:
            col_map['subgrupo'] = col
    
    if 'data' not in col_map or 'valor' not in col_map:
        print("❌ Não foi possível identificar colunas necessárias no Excel")
        print(f"Colunas encontradas: {list(df.columns)}")
        sys.exit(1)
    
    # Agregar por mês
    monthly = {}
    for _, row in df.iterrows():
        data_str = str(row[col_map['data']]) if pd.notna(row[col_map['data']]) else ""
        valor_str = str(row[col_map['valor']]) if pd.notna(row[col_map['valor']]) else ""
        grupo_str = str(row[col_map.get('grupo', '')]) if col_map.get('grupo') and pd.notna(row[col_map['grupo']]) else ""
        
        data = parse_date(data_str)
        if not data or data.year != year:
            continue
        
        valor = parse_currency(valor_str)
        if valor == 0:
            continue
        
        tipo = determine_transaction_type(grupo_str)
        key = (year, data.month)
        
        if key not in monthly:
            monthly[key] = {
                "receita": Decimal(0),
                "despesa": Decimal(0),
                "custo": Decimal(0)
            }
        
        if tipo == "RECEITA":
            monthly[key]["receita"] += valor
        elif tipo == "DESPESA":
            monthly[key]["despesa"] += valor
        elif tipo == "CUSTO":
            monthly[key]["custo"] += valor
    
    # Calcular saldo
    for key in monthly:
        monthly[key]["saldo"] = monthly[key]["receita"] - monthly[key]["despesa"] - monthly[key]["custo"]
    
    return monthly

def compare_values(excel_val: Decimal, api_val: Decimal, tolerance: Decimal) -> Tuple[bool, Decimal]:
    """Compara valores com tolerância"""
    diff = abs(excel_val - api_val)
    return diff <= tolerance, diff

def main():
    parser = argparse.ArgumentParser(description="Validação numérica Excel vs API")
    parser.add_argument("--file", required=True, help="Caminho do arquivo Excel")
    parser.add_argument("--year", type=int, default=2025, help="Ano a validar")
    parser.add_argument("--backend-url", default=os.getenv("BACKEND_URL", "https://finaflow-backend-staging-642830139828.us-central1.run.app"))
    parser.add_argument("--token", help="Token de autenticação (ou usar QA_EMAIL/QA_PASSWORD)")
    parser.add_argument("--tolerance", type=float, default=0.01, help="Tolerância para comparação")
    parser.add_argument("--email", default=os.getenv("QA_EMAIL", "qa@finaflow.test"))
    parser.add_argument("--password", default=os.getenv("QA_PASSWORD", "QaFinaflow123!"))
    
    args = parser.parse_args()
    
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"❌ Arquivo não encontrado: {file_path}")
        sys.exit(1)
    
    tolerance = Decimal(str(args.tolerance))
    
    # Obter token
    if args.token:
        token = args.token
    else:
        print("🔐 Fazendo login...")
        token = login_api(args.backend_url, args.email, args.password)
        print("✅ Login realizado")
    
    # Buscar dados da API
    print("📡 Buscando dados da API...")
    api_data = fetch_annual_summary(args.backend_url, token, args.year)
    
    # Agregar Excel
    excel_monthly = aggregate_excel(file_path, args.year)
    
    # Comparar
    print("\n📊 Comparando valores...")
    mismatches = []
    
    # Totais anuais
    excel_totals = {
        "receita": Decimal(0),
        "despesa": Decimal(0),
        "custo": Decimal(0),
        "saldo": Decimal(0)
    }
    
    for key, values in excel_monthly.items():
        excel_totals["receita"] += values["receita"]
        excel_totals["despesa"] += values["despesa"]
        excel_totals["custo"] += values["custo"]
        excel_totals["saldo"] += values["saldo"]
    
    api_totals = api_data.get("totals", {})
    
    print("\n📈 TOTAIS ANUAIS:")
    for field in ["revenue", "expense", "cost", "balance"]:
        excel_field = {"revenue": "receita", "expense": "despesa", "cost": "custo", "balance": "saldo"}[field]
        excel_val = excel_totals[excel_field]
        api_val = Decimal(str(api_totals.get(field, 0)))
        
        ok, diff = compare_values(excel_val, api_val, tolerance)
        status = "✅" if ok else "❌"
        print(f"  {status} {field.upper()}: Excel={excel_val}, API={api_val}, Diff={diff}")
        
        if not ok:
            mismatches.append({
                "type": "annual",
                "field": field,
                "excel": float(excel_val),
                "api": float(api_val),
                "diff": float(diff)
            })
    
    # Mensais
    print("\n📅 COMPARAÇÃO MENSAL:")
    api_monthly = api_data.get("monthly", [])
    
    for month_idx, month_data in enumerate(api_monthly, 1):
        excel_key = (args.year, month_idx)
        excel_vals = excel_monthly.get(excel_key, {
            "receita": Decimal(0),
            "despesa": Decimal(0),
            "custo": Decimal(0),
            "saldo": Decimal(0)
        })
        
        for field in ["revenue", "expense", "cost", "balance"]:
            excel_field = {"revenue": "receita", "expense": "despesa", "cost": "custo", "balance": "saldo"}[field]
            excel_val = excel_vals[excel_field]
            api_val = Decimal(str(month_data.get(field, 0)))
            
            ok, diff = compare_values(excel_val, api_val, tolerance)
            if not ok:
                status = "❌"
                mismatches.append({
                    "type": "monthly",
                    "month": month_idx,
                    "field": field,
                    "excel": float(excel_val),
                    "api": float(api_val),
                    "diff": float(diff)
                })
            else:
                status = "✅"
            
            if not ok or month_idx <= 3:  # Mostrar sempre os 3 primeiros meses
                print(f"  {status} Mês {month_idx:02d} {field}: Excel={excel_val}, API={api_val}, Diff={diff}")
    
    # Salvar resultados
    results = {
        "year": args.year,
        "tolerance": float(tolerance),
        "excel_totals": {k: float(v) for k, v in excel_totals.items()},
        "api_totals": api_totals,
        "mismatches": mismatches,
        "status": "PASS" if len(mismatches) == 0 else "FAIL"
    }
    
    with open(OUT_DIR / "validation_numbers.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Resumo
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    if len(mismatches) == 0:
        print("✅ Validação numérica: PASS")
        return 0
    else:
        print(f"❌ Validação numérica: FAIL ({len(mismatches)} mismatch(es))")
        return 2

if __name__ == "__main__":
    sys.exit(main())

