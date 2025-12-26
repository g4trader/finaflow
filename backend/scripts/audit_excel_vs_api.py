#!/usr/bin/env python3
"""
Script de Auditoria - Compara baseline Excel vs API

Valida que os totais da API batem com o baseline do Excel.

USO:
    python -m scripts.audit_excel_vs_api --year 2025 --backend-url <url>
"""

import sys
import os
import argparse
import json
from pathlib import Path
from decimal import Decimal
from typing import Dict, List
from datetime import datetime

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

try:
    import requests
except ImportError:
    print("❌ Erro: requests não está instalado. Execute: pip install requests")
    sys.exit(1)

ARTIFACTS_DIR = backend_path / "artifacts"
TOLERANCE = Decimal("0.01")  # R$ 0,01

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
    token = data.get("access_token")
    if not token:
        print("❌ Token não retornado")
        sys.exit(1)
    return token

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

def fetch_monthly_daily_summary(backend_url: str, token: str, year: int, month: int) -> Dict:
    """Busca resumo diário de um mês"""
    response = requests.get(
        f"{backend_url}/api/v1/financial/monthly-daily-summary?year={year}&month={month}",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code != 200:
        print(f"⚠️  Erro ao buscar monthly-daily-summary para mês {month}: {response.status_code}")
        return {}
    return response.json()

def fetch_operational_endpoints(backend_url: str, token: str) -> Dict:
    """Busca todos os endpoints do dashboard operacional"""
    endpoints = {
        "availability": "/api/v1/dashboard/operational/availability",
        "alerts": "/api/v1/dashboard/operational/alerts",
        "forecast_vs_realized": "/api/v1/dashboard/operational/forecast-vs-realized?months=6",
        "payables_summary": "/api/v1/dashboard/operational/payables-summary",
        "receivables_summary": "/api/v1/dashboard/operational/receivables-summary"
    }
    
    results = {}
    for key, endpoint in endpoints.items():
        try:
            response = requests.get(
                f"{backend_url}{endpoint}",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                results[key] = response.json()
            else:
                results[key] = {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            results[key] = {"error": str(e)}
    
    return results

def compare_values(excel_val: Decimal, api_val: Decimal, tolerance: Decimal) -> tuple[bool, Decimal]:
    """Compara valores com tolerância"""
    diff = abs(excel_val - api_val)
    return diff <= tolerance, diff

def main():
    parser = argparse.ArgumentParser(description="Auditoria Excel vs API")
    parser.add_argument("--year", type=int, default=2025, help="Ano a validar")
    parser.add_argument("--backend-url", default=os.getenv("BACKEND_URL", "https://finaflow-backend-staging-642830139828.us-central1.run.app"))
    parser.add_argument("--email", default=os.getenv("QA_EMAIL", "qa@finaflow.test"))
    parser.add_argument("--password", default=os.getenv("QA_PASSWORD", "QaFinaflow123!"))
    parser.add_argument("--baseline-file", type=str, default=None)
    
    args = parser.parse_args()
    
    # Carregar baseline
    if args.baseline_file:
        baseline_path = Path(args.baseline_file)
    else:
        baseline_path = ARTIFACTS_DIR / f"baseline_excel_{args.year}.json"
    
    if not baseline_path.exists():
        print(f"❌ Baseline não encontrado: {baseline_path}")
        print("   Execute primeiro: python -m scripts.generate_baseline_excel --year {args.year}")
        sys.exit(1)
    
    with open(baseline_path, "r", encoding="utf-8") as f:
        baseline = json.load(f)
    
    print("="*60)
    print("🔍 AUDITORIA EXCEL vs API")
    print("="*60)
    print(f"📅 Ano: {args.year}")
    print(f"📁 Baseline: {baseline_path}")
    print(f"🌐 Backend: {args.backend_url}")
    print()
    
    # Login
    print("🔐 Fazendo login...")
    token = login_api(args.backend_url, args.email, args.password)
    print("✅ Login realizado")
    print()
    
    # Buscar dados da API
    print("📡 Buscando dados da API...")
    api_annual = fetch_annual_summary(args.backend_url, token, args.year)
    print("✅ Annual summary obtido")
    
    # Buscar dados operacionais
    print("📊 Buscando endpoints operacionais...")
    api_operational = fetch_operational_endpoints(args.backend_url, token)
    print("✅ Endpoints operacionais obtidos")
    print()
    
    # Comparar totais anuais
    print("="*60)
    print("📊 COMPARAÇÃO DE TOTAIS ANUAIS")
    print("="*60)
    
    baseline_totals = baseline["annual_totals"]
    api_totals = api_annual.get("totals", {})
    
    mismatches = []
    
    field_map = {
        "receita": "revenue",
        "despesa": "expense",
        "custo": "cost",
        "saldo": "balance"
    }
    
    for excel_field, api_field in field_map.items():
        excel_val = Decimal(str(baseline_totals.get(excel_field, 0)))
        api_val = Decimal(str(api_totals.get(api_field, 0)))
        
        ok, diff = compare_values(excel_val, api_val, TOLERANCE)
        status = "✅" if ok else "❌"
        
        print(f"{status} {excel_field.upper():12s}: Excel={excel_val:>15,.2f} | API={api_val:>15,.2f} | Diff={diff:>10,.2f}")
        
        if not ok:
            mismatches.append({
                "type": "annual",
                "field": excel_field,
                "excel": float(excel_val),
                "api": float(api_val),
                "diff": float(diff)
            })
    
    print()
    
    # Comparar mensais
    print("="*60)
    print("📅 COMPARAÇÃO MENSAL")
    print("="*60)
    
    baseline_monthly = {item["month"]: item for item in baseline["monthly_totals"]}
    api_monthly = api_annual.get("monthly", [])
    
    monthly_mismatches = []
    
    for month_idx, month_data in enumerate(api_monthly, 1):
        baseline_month = baseline_monthly.get(month_idx, {})
        
        for excel_field, api_field in field_map.items():
            excel_val = Decimal(str(baseline_month.get(excel_field, 0)))
            api_val = Decimal(str(month_data.get(api_field, 0)))
            
            ok, diff = compare_values(excel_val, api_val, TOLERANCE)
            
            if not ok:
                status = "❌"
                monthly_mismatches.append({
                    "type": "monthly",
                    "month": month_idx,
                    "field": excel_field,
                    "excel": float(excel_val),
                    "api": float(api_val),
                    "diff": float(diff)
                })
            else:
                status = "✅"
            
            # Mostrar sempre os 3 primeiros meses ou se houver mismatch
            if not ok or month_idx <= 3:
                print(f"{status} Mês {month_idx:02d} {excel_field:12s}: Excel={excel_val:>15,.2f} | API={api_val:>15,.2f} | Diff={diff:>10,.2f}")
    
    print()
    
    # Validar monthly-daily-summary (soma dos dias deve bater com mensal)
    print("="*60)
    print("🔍 VALIDAÇÃO MONTHLY-DAILY-SUMMARY (soma dos dias)")
    print("="*60)
    
    daily_mismatches = []
    for month in range(1, 4):  # Validar apenas 3 primeiros meses
        daily_summary = fetch_monthly_daily_summary(args.backend_url, token, args.year, month)
        
        if not daily_summary:
            continue
        
        month_totals = daily_summary.get("month_totals", {})
        baseline_month = baseline_monthly.get(month, {})
        
        for excel_field, api_field in field_map.items():
            excel_val = Decimal(str(baseline_month.get(excel_field, 0)))
            api_val = Decimal(str(month_totals.get(api_field, 0)))
            
            ok, diff = compare_values(excel_val, api_val, TOLERANCE)
            
            if not ok:
                daily_mismatches.append({
                    "type": "daily_summary",
                    "month": month,
                    "field": excel_field,
                    "excel": float(excel_val),
                    "api": float(api_val),
                    "diff": float(diff)
                })
                print(f"❌ Mês {month:02d} {excel_field:12s}: Excel={excel_val:>15,.2f} | API (soma dias)={api_val:>15,.2f} | Diff={diff:>10,.2f}")
            else:
                print(f"✅ Mês {month:02d} {excel_field:12s}: OK")
    
    print()
    
    # Salvar relatório
    report = {
        "metadata": {
            "year": args.year,
            "backend_url": args.backend_url,
            "baseline_file": str(baseline_path),
            "baseline_hash": baseline.get("metadata", {}).get("excel_hash"),
            "audited_at": datetime.utcnow().isoformat(),
            "tolerance": float(TOLERANCE)
        },
        "annual_totals": {
            "baseline": baseline_totals,
            "api": {field_map[k]: v for k, v in baseline_totals.items() if k in field_map},
            "api_actual": api_totals
        },
        "mismatches": {
            "annual": mismatches,
            "monthly": monthly_mismatches,
            "daily_summary": daily_mismatches
        },
        "operational_endpoints": api_operational,
        "status": "PASS" if len(mismatches) == 0 and len(monthly_mismatches) == 0 and len(daily_mismatches) == 0 else "FAIL"
    }
    
    report_path = ARTIFACTS_DIR / f"audit_report_{args.year}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("="*60)
    print("📋 RESUMO")
    print("="*60)
    print(f"Mismatches anuais: {len(mismatches)}")
    print(f"Mismatches mensais: {len(monthly_mismatches)}")
    print(f"Mismatches daily-summary: {len(daily_mismatches)}")
    print()
    print(f"📄 Relatório salvo: {report_path}")
    print()
    
    if len(mismatches) == 0 and len(monthly_mismatches) == 0 and len(daily_mismatches) == 0:
        print("✅ AUDITORIA: PASS - Todos os valores batem!")
        return 0
    else:
        print("❌ AUDITORIA: FAIL - Encontrados mismatches")
        return 2

if __name__ == "__main__":
    sys.exit(main())

