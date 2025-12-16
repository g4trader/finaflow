#!/usr/bin/env python3
"""
Script de validação de consistência do drill down

Valida que:
1. Soma dos dias = total mensal (monthly-daily-summary)
2. Total mensal = valor de /annual-summary
3. Summary dos lançamentos sem filtro = total do mês
"""

import sys
import os
from pathlib import Path
from decimal import Decimal

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

try:
    import requests
except ImportError:
    print("❌ Erro: dependência não instalada: requests")
    print("Execute: pip install requests")
    sys.exit(1)

# Configurações
BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "https://finaflow-backend-staging-642830139828.us-central1.run.app"
)
YEAR = 2025

def login_api(backend_url: str) -> str:
    """Faz login e retorna token"""
    login_url = f"{backend_url}/api/v1/auth/login"
    
    # Usar credenciais padrão de staging (ajustar se necessário)
    credentials = {
        "username": "qa_user",
        "password": "qa_password_2024"
    }
    
    try:
        response = requests.post(login_url, json=credentials, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        else:
            print(f"❌ Erro ao fazer login: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return None

def validate_consistency(year: int, month: int, token: str) -> bool:
    """Valida consistência para um mês específico"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n{'='*80}")
    print(f"Validando mês {month:02d}/{year}")
    print(f"{'='*80}")
    
    # 1. Buscar annual-summary
    try:
        annual_response = requests.get(
            f"{BACKEND_URL}/api/v1/financial/annual-summary?year={year}",
            headers=headers,
            timeout=30
        )
        annual_response.raise_for_status()
        annual_data = annual_response.json()
    except Exception as e:
        print(f"❌ Erro ao buscar annual-summary: {e}")
        return False
    
    # 2. Buscar daily-summary
    try:
        daily_response = requests.get(
            f"{BACKEND_URL}/api/v1/financial/monthly-daily-summary?year={year}&month={month}",
            headers=headers,
            timeout=30
        )
        daily_response.raise_for_status()
        daily_data = daily_response.json()
    except Exception as e:
        print(f"❌ Erro ao buscar daily-summary: {e}")
        return False
    
    # 3. Buscar transactions (sem filtro)
    try:
        transactions_response = requests.get(
            f"{BACKEND_URL}/api/v1/financial/monthly-transactions?year={year}&month={month}&page=1&page_size=50",
            headers=headers,
            timeout=30
        )
        transactions_response.raise_for_status()
        transactions_data = transactions_response.json()
    except Exception as e:
        print(f"❌ Erro ao buscar transactions: {e}")
        return False
    
    # 4. Comparar valores
    month_index = month - 1
    annual_month = annual_data["monthly"][month_index]
    
    # Converter para Decimal para comparação precisa
    annual_revenue = Decimal(str(annual_month["revenue"]))
    annual_expense = Decimal(str(annual_month["expense"]))
    annual_cost = Decimal(str(annual_month["cost"]))
    annual_balance = Decimal(str(annual_month["balance"]))
    
    daily_revenue = Decimal(daily_data["metadata"]["month_total_revenue"])
    daily_expense = Decimal(daily_data["metadata"]["month_total_expense"])
    daily_cost = Decimal(daily_data["metadata"]["month_total_cost"])
    daily_balance = Decimal(daily_data["metadata"]["month_total_balance"])
    
    transactions_revenue = Decimal(transactions_data["summary"]["revenue"])
    transactions_expense = Decimal(transactions_data["summary"]["expense"])
    transactions_cost = Decimal(transactions_data["summary"]["cost"])
    transactions_balance = Decimal(transactions_data["summary"]["balance"])
    
    # Validar 1: Soma dos dias = total mensal
    sum_days_revenue = sum(Decimal(day["revenue"]) for day in daily_data["days"])
    sum_days_expense = sum(Decimal(day["expense"]) for day in daily_data["days"])
    sum_days_cost = sum(Decimal(day["cost"]) for day in daily_data["days"])
    sum_days_balance = sum(Decimal(day["balance"]) for day in daily_data["days"])
    
    # Validar 2: Total mensal = annual-summary
    # Validar 3: Summary transactions = total mensal
    
    all_ok = True
    
    # Validação 1: Soma dos dias = total mensal
    if sum_days_revenue != daily_revenue:
        print(f"❌ Soma dos dias (receita) != total mensal: {sum_days_revenue} != {daily_revenue}")
        all_ok = False
    else:
        print(f"✅ Soma dos dias (receita) = total mensal: {sum_days_revenue}")
    
    if sum_days_expense != daily_expense:
        print(f"❌ Soma dos dias (despesa) != total mensal: {sum_days_expense} != {daily_expense}")
        all_ok = False
    else:
        print(f"✅ Soma dos dias (despesa) = total mensal: {sum_days_expense}")
    
    if sum_days_cost != daily_cost:
        print(f"❌ Soma dos dias (custo) != total mensal: {sum_days_cost} != {daily_cost}")
        all_ok = False
    else:
        print(f"✅ Soma dos dias (custo) = total mensal: {sum_days_cost}")
    
    if sum_days_balance != daily_balance:
        print(f"❌ Soma dos dias (saldo) != total mensal: {sum_days_balance} != {daily_balance}")
        all_ok = False
    else:
        print(f"✅ Soma dos dias (saldo) = total mensal: {sum_days_balance}")
    
    # Validação 2: Total mensal = annual-summary
    if daily_revenue != annual_revenue:
        print(f"❌ Total mensal (receita) != annual-summary: {daily_revenue} != {annual_revenue}")
        all_ok = False
    else:
        print(f"✅ Total mensal (receita) = annual-summary: {daily_revenue}")
    
    if daily_expense != annual_expense:
        print(f"❌ Total mensal (despesa) != annual-summary: {daily_expense} != {annual_expense}")
        all_ok = False
    else:
        print(f"✅ Total mensal (despesa) = annual-summary: {daily_expense}")
    
    if daily_cost != annual_cost:
        print(f"❌ Total mensal (custo) != annual-summary: {daily_cost} != {annual_cost}")
        all_ok = False
    else:
        print(f"✅ Total mensal (custo) = annual-summary: {daily_cost}")
    
    if daily_balance != annual_balance:
        print(f"❌ Total mensal (saldo) != annual-summary: {daily_balance} != {annual_balance}")
        all_ok = False
    else:
        print(f"✅ Total mensal (saldo) = annual-summary: {daily_balance}")
    
    # Validação 3: Summary transactions = total mensal
    if transactions_revenue != daily_revenue:
        print(f"❌ Summary transactions (receita) != total mensal: {transactions_revenue} != {daily_revenue}")
        all_ok = False
    else:
        print(f"✅ Summary transactions (receita) = total mensal: {transactions_revenue}")
    
    if transactions_expense != daily_expense:
        print(f"❌ Summary transactions (despesa) != total mensal: {transactions_expense} != {daily_expense}")
        all_ok = False
    else:
        print(f"✅ Summary transactions (despesa) = total mensal: {transactions_expense}")
    
    if transactions_cost != daily_cost:
        print(f"❌ Summary transactions (custo) != total mensal: {transactions_cost} != {daily_cost}")
        all_ok = False
    else:
        print(f"✅ Summary transactions (custo) = total mensal: {transactions_cost}")
    
    if transactions_balance != daily_balance:
        print(f"❌ Summary transactions (saldo) != total mensal: {transactions_balance} != {daily_balance}")
        all_ok = False
    else:
        print(f"✅ Summary transactions (saldo) = total mensal: {transactions_balance}")
    
    return all_ok

def main():
    """Valida consistência para todos os meses do ano"""
    print("="*80)
    print("VALIDAÇÃO DE CONSISTÊNCIA - DRILL DOWN")
    print("="*80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Ano: {YEAR}")
    print("="*80)
    
    # Fazer login
    print("\n🔐 Fazendo login...")
    token = login_api(BACKEND_URL)
    if not token:
        print("❌ Falha ao fazer login")
        sys.exit(1)
    print("✅ Login realizado com sucesso")
    
    # Validar cada mês
    all_months_ok = True
    for month in range(1, 13):
        month_ok = validate_consistency(YEAR, month, token)
        if not month_ok:
            all_months_ok = False
    
    # Resumo final
    print("\n" + "="*80)
    print("RESUMO FINAL")
    print("="*80)
    if all_months_ok:
        print("✅ Todos os meses estão consistentes!")
        sys.exit(0)
    else:
        print("❌ Alguns meses apresentaram inconsistências")
        sys.exit(1)

if __name__ == "__main__":
    main()

