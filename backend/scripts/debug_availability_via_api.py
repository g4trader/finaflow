#!/usr/bin/env python3
"""
Script para debugar saldo negativo via API
"""

import requests
import json
import os
from decimal import Decimal

BACKEND_URL = os.getenv("BACKEND_URL", "https://finaflow-backend-staging-642830139828.us-central1.run.app")
QA_USERNAME = os.getenv("QA_USERNAME", "qa")
QA_PASSWORD = os.getenv("QA_PASSWORD", "QaFinaflow123!")

def login():
    """Fazer login e obter token"""
    response = requests.post(
        f"{BACKEND_URL}/api/v1/auth/login",
        json={"username": QA_USERNAME, "password": QA_PASSWORD}
    )
    if response.status_code != 200:
        raise Exception(f"Erro no login: {response.text}")
    return response.json()["access_token"]

def get_availability(token):
    """Buscar disponibilidades"""
    response = requests.get(
        f"{BACKEND_URL}/api/v1/dashboard/operational/availability",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code != 200:
        raise Exception(f"Erro ao buscar disponibilidades: {response.text}")
    return response.json()

def main():
    print("="*80)
    print("🔍 DEBUG: Saldo Negativo de Disponibilidades (via API)")
    print("="*80)
    print(f"🌐 Backend: {BACKEND_URL}")
    print()
    
    try:
        # Login
        print("🔐 Fazendo login...")
        token = login()
        print("✅ Login realizado")
        print()
        
        # Buscar disponibilidades
        print("📊 Buscando disponibilidades...")
        data = get_availability(token)
        print("✅ Dados obtidos")
        print()
        
        print("="*80)
        print("📊 RESULTADO ATUAL")
        print("="*80)
        print(f"🏦 Bancos:        R$ {data['banks']:,.2f}")
        print(f"💵 Caixa:         R$ {data['cash']:,.2f}")
        print(f"📈 Investimentos: R$ {data['investments']:,.2f}")
        print(f"🟦 Total:          R$ {data['total']:,.2f}")
        print()
        
        if data['total'] < 0:
            print("⚠️  SALDO NEGATIVO DETECTADO!")
            print()
            print("🔍 Possíveis causas:")
            print("  1. Lógica de cálculo pode estar invertida")
            print("  2. Contas classificadas incorretamente")
            print("  3. Mais despesas/custos do que receitas nas contas de disponibilidade")
            print("  4. Problema na classificação de tipos de transação")
            print()
            print("💡 PRÓXIMOS PASSOS:")
            print("  - Verificar se RECEITA aumenta saldo e DESPESA/CUSTO diminui")
            print("  - Verificar quais contas estão sendo classificadas como BANK/CASH/INVESTMENT")
            print("  - Verificar se há contas que não deveriam estar sendo incluídas")
        else:
            print("✅ Saldo positivo ou zero")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

