#!/usr/bin/env python3
"""Verificar se as contas de liquidação foram criadas e associadas aos lançamentos"""
import os
import sys
import requests
import json

BACKEND_URL = os.getenv("BACKEND_URL", "https://finaflow-backend-staging-642830139828.us-central1.run.app")
QA_USERNAME = os.getenv("QA_USERNAME", "qa@finaflow.test")
QA_PASSWORD = os.getenv("QA_PASSWORD", "QaFinaflow123!")

print("=" * 70)
print("🔍 VERIFICAÇÃO DE CONTAS DE LIQUIDAÇÃO")
print("=" * 70)
print(f"🌐 Backend: {BACKEND_URL}")
print()

# Login
print("🔐 Fazendo login...")
login_resp = requests.post(
    f"{BACKEND_URL}/api/v1/auth/login",
    json={"username": QA_USERNAME, "password": QA_PASSWORD}
)
if login_resp.status_code != 200:
    print(f"❌ Erro no login: {login_resp.text}")
    sys.exit(1)

token = login_resp.json()["access_token"]
print("✅ Login realizado")
print()

# Verificar endpoint de debug
headers = {"Authorization": f"Bearer {token}"}
print("📊 Buscando informações de liquidação...")
resp = requests.get(
    f"{BACKEND_URL}/api/v1/dashboard/operational/availability/debug",
    headers=headers
)

if resp.status_code != 200:
    print(f"❌ Erro ao buscar dados: {resp.text}")
    sys.exit(1)

data = resp.json()

print()
print("=" * 70)
print("📊 RESULTADO")
print("=" * 70)

# Contas de liquidação
if "liquidation_accounts" in data:
    accounts = data["liquidation_accounts"]
    print(f"\n🏦 Contas de Liquidação Criadas: {len(accounts)}")
    for acc in accounts:
        print(f"  - {acc.get('code', 'N/A'):<10} {acc.get('name', 'N/A'):<30} (tipo: {acc.get('account_type', 'N/A')})")
else:
    print("\n⚠️  Nenhuma conta de liquidação encontrada")

# Lançamentos com liquidation_account_id
if "lancamentos_with_liquidation" in data:
    print(f"\n📝 Lançamentos com liquidation_account_id: {data['lancamentos_with_liquidation']}")
else:
    print("\n⚠️  Dados de lançamentos não disponíveis")

# Disponibilidades
if "availability" in data:
    avail = data["availability"]
    print("\n💰 Disponibilidades Calculadas:")
    print(f"  Bancos:        R$ {avail.get('banks', 0):,.2f}")
    print(f"  Caixa:         R$ {avail.get('cash', 0):,.2f}")
    print(f"  Investimentos: R$ {avail.get('investments', 0):,.2f}")
    print(f"  Total:         R$ {avail.get('total', 0):,.2f}")

print()
print("=" * 70)

