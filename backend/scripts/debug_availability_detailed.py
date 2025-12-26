#!/usr/bin/env python3
"""
Script para debugar saldo negativo com detalhes via API
"""

import requests
import json
import os

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

def get_availability_debug(token):
    """Buscar detalhes de disponibilidades"""
    response = requests.get(
        f"{BACKEND_URL}/api/v1/dashboard/operational/availability/debug",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code != 200:
        raise Exception(f"Erro ao buscar debug: {response.text}")
    return response.json()

def main():
    print("="*80)
    print("🔍 DEBUG DETALHADO: Saldo Negativo de Disponibilidades")
    print("="*80)
    print()
    
    try:
        token = login()
        data = get_availability_debug(token)
        
        print("="*80)
        print("🏦 BANCOS")
        print("="*80)
        for item in data["banks"]:
            print(f"\n  Conta: {item['conta']} ({item['codigo']})")
            print(f"  Grupo: {item['grupo']} / {item['subgrupo']}")
            print(f"  Tipo: {item['account_type']}")
            print(f"  Saldo: R$ {item['saldo']:,.2f}")
            print(f"  Receitas: R$ {item['receitas']:,.2f}")
            print(f"  Despesas/Custos: R$ {item['despesas_custos']:,.2f}")
            print(f"  Qtd lançamentos: {item['qtd_lancamentos']}")
        
        print(f"\n  TOTAL BANCOS: R$ {data['summary']['total_banks']:,.2f}")
        print()
        
        print("="*80)
        print("💵 CAIXA")
        print("="*80)
        for item in data["cash"]:
            print(f"\n  Conta: {item['conta']} ({item['codigo']})")
            print(f"  Grupo: {item['grupo']} / {item['subgrupo']}")
            print(f"  Tipo: {item['account_type']}")
            print(f"  Saldo: R$ {item['saldo']:,.2f}")
        
        print(f"\n  TOTAL CAIXA: R$ {data['summary']['total_cash']:,.2f}")
        print()
        
        print("="*80)
        print("📈 INVESTIMENTOS")
        print("="*80)
        for item in data["investments"]:
            print(f"\n  Conta: {item['conta']} ({item['codigo']})")
            print(f"  Grupo: {item['grupo']} / {item['subgrupo']}")
            print(f"  Tipo: {item['account_type']}")
            print(f"  Saldo: R$ {item['saldo']:,.2f}")
        
        print(f"\n  TOTAL INVESTIMENTOS: R$ {data['summary']['total_investments']:,.2f}")
        print()
        
        total = data['summary']['total_banks'] + data['summary']['total_cash'] + data['summary']['total_investments']
        print("="*80)
        print("📊 RESUMO")
        print("="*80)
        print(f"Bancos:        R$ {data['summary']['total_banks']:,.2f}")
        print(f"Caixa:         R$ {data['summary']['total_cash']:,.2f}")
        print(f"Investimentos: R$ {data['summary']['total_investments']:,.2f}")
        print(f"TOTAL:         R$ {total:,.2f}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

