#!/usr/bin/env python3
"""Verificar status de liquidação via API"""
import os
import sys
import requests
import json

BACKEND_URL = os.getenv("BACKEND_URL", "https://finaflow-backend-staging-642830139828.us-central1.run.app")
QA_USERNAME = os.getenv("QA_USERNAME", "qa@finaflow.test")
QA_PASSWORD = os.getenv("QA_PASSWORD", "QaFinaflow123!")

print("=" * 70)
print("🔍 VERIFICAÇÃO DE STATUS DE LIQUIDAÇÃO (via API)")
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

# Verificar status
headers = {"Authorization": f"Bearer {token}"}
print("📊 Buscando status de liquidação...")
# O router é incluído com prefixo /api/v1, então o endpoint completo é:
# /api/v1/dashboard/operational/availability/liquidation-status
resp = requests.get(
    f"{BACKEND_URL}/api/v1/dashboard/operational/availability/liquidation-status",
    headers=headers
)

if resp.status_code != 200:
    print(f"❌ Erro: {resp.status_code}")
    print(resp.text)
    sys.exit(1)

data = resp.json()

print()
print("=" * 70)
print("📊 RESULTADO")
print("=" * 70)
print()

# Contas de liquidação
accounts = data.get("liquidation_accounts", [])
print(f"1️⃣ Contas de Liquidação: {len(accounts)}")
if accounts:
    for acc in accounts:
        print(f"   - {acc['code']}: {acc['name']} (tipo: {acc['account_type']})")
else:
    print("   ⚠️  Nenhuma conta de liquidação encontrada!")
print()

# Lançamentos
lancamentos = data.get("lancamentos", {})
print(f"2️⃣ Lançamentos:")
print(f"   Total: {lancamentos.get('total', 0)}")
print(f"   Com liquidation_account_id: {lancamentos.get('com_liquidation_account_id', 0)}")
print(f"   Sem liquidation_account_id: {lancamentos.get('sem_liquidation_account_id', 0)}")
print(f"   Percentual associado: {lancamentos.get('percentual_com_liquidation', 0)}%")
print()

# Distribuição
distribution = data.get("distribution", [])
if distribution:
    print(f"3️⃣ Distribuição por código:")
    for dist in distribution:
        print(f"   - {dist['code']} ({dist['account_type']}): {dist['lancamentos_count']} lançamentos")
    print()

# Saldos
saldos = data.get("saldos_calculados", {})
print(f"4️⃣ Saldos Calculados:")
print(f"   Bancos: R$ {saldos.get('banks', 0):,.2f}")
print(f"   Caixa: R$ {saldos.get('cash', 0):,.2f}")
print(f"   Investimentos: R$ {saldos.get('investments', 0):,.2f}")
print(f"   Total: R$ {saldos.get('total', 0):,.2f}")
print()

# Diagnóstico
diagnostico = data.get("diagnostico", {})
print(f"5️⃣ Diagnóstico:")
print(f"   Contas criadas: {'✅' if diagnostico.get('contas_criadas') else '❌'}")
print(f"   Lançamentos associados: {'✅' if diagnostico.get('lancamentos_associados') else '❌'}")
print(f"   Cobertura: {diagnostico.get('cobertura_associacao', 0)}%")
print(f"   Status: {diagnostico.get('status', 'unknown')}")
print()

if diagnostico.get("status") == "precisa_re_seed":
    print("=" * 70)
    print("⚠️  AÇÃO NECESSÁRIA: Executar re-seed para popular contas de liquidação")
    print("=" * 70)
    print()
    print("Comando:")
    print("  ./scripts/run_migration_and_seed.sh")
    print()

print("=" * 70)

