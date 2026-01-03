#!/usr/bin/env python3
"""Testar endpoint de debug de disponibilidades"""

import requests
import json
import os

BACKEND_URL = os.getenv("BACKEND_URL", "https://finaflow-backend-staging-642830139828.us-central1.run.app")
QA_USERNAME = os.getenv("QA_USERNAME", "qa")
QA_PASSWORD = os.getenv("QA_PASSWORD", "QaFinaflow123!")

def login():
    response = requests.post(
        f"{BACKEND_URL}/api/v1/auth/login",
        json={"username": QA_USERNAME, "password": QA_PASSWORD}
    )
    if response.status_code != 200:
        raise Exception(f"Erro no login: {response.text}")
    return response.json()["access_token"]

def test_debug_endpoint(token):
    """Testar endpoint de debug"""
    response = requests.get(
        f"{BACKEND_URL}/api/v1/dashboard/operational/availability/debug",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 404:
        print("❌ Endpoint de debug não encontrado (404) - deploy pode não ter sido concluído")
        return None
    if response.status_code != 200:
        print(f"❌ Erro ao buscar debug: {response.status_code} - {response.text}")
        return None
    return response.json()

def main():
    print("🔍 Testando endpoint de debug...")
    try:
        token = login()
        data = test_debug_endpoint(token)
        
        if data:
            print("✅ Endpoint de debug está disponível!")
            print()
            print("📊 Resumo:")
            print(f"  Bancos: {len(data.get('banks', []))} contas")
            print(f"  Caixa: {len(data.get('cash', []))} contas")
            print(f"  Investimentos: {len(data.get('investments', []))} contas")
            print()
            summary = data.get('summary', {})
            print(f"  Total Bancos: R$ {summary.get('total_banks', 0):,.2f}")
            print(f"  Total Caixa: R$ {summary.get('total_cash', 0):,.2f}")
            print(f"  Total Investimentos: R$ {summary.get('total_investments', 0):,.2f}")
            print()
            
            if data.get('banks'):
                print("🏦 Contas classificadas como BANCO:")
                for bank in data['banks'][:5]:  # Mostrar apenas as primeiras 5
                    print(f"  - {bank['conta']} ({bank['codigo']})")
                    print(f"    Grupo: {bank['grupo']} / Subgrupo: {bank['subgrupo']}")
                    print(f"    Account Type: {bank['account_type']}")
                    print(f"    Saldo: R$ {bank['saldo']:,.2f}")
                    print(f"    Receitas: R$ {bank['receitas']:,.2f} | Despesas/Custos: R$ {bank['despesas_custos']:,.2f}")
                    print()
        else:
            print("⚠️  Endpoint de debug não está disponível ainda")
            print("   Isso pode indicar que o deploy não foi concluído ou falhou")
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()



