#!/usr/bin/env python3
"""
Importar Planilha para LLM Lavanderia
"""

import requests
import sys

BACKEND_URL = "https://finaflow-backend-6arhlm3mha-uc.a.run.app"
ADMIN_USERNAME = "lucianoterresrosa"
ADMIN_PASSWORD = "a3KKQGv4n6yF"
SPREADSHEET_ID = "1rWMdDhwiNoC7iMycmQGWWDIacrePr1gB7c_mbt1patQ"

print("=" * 80)
print("📊 IMPORTAÇÃO DE DADOS - LLM LAVANDERIA")
print("=" * 80)
print()

# Login
print("🔐 Fazendo login como admin da LLM...")
response = requests.post(
    f"{BACKEND_URL}/api/v1/auth/login",
    data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    timeout=30
)

if response.status_code != 200:
    print("❌ Erro no login")
    sys.exit(1)

token = response.json()["access_token"]
print(f"✅ Login realizado")
print()

# Selecionar BU
print("🎯 Selecionando Business Unit...")
bu_response = requests.get(
    f"{BACKEND_URL}/api/v1/auth/user-business-units",
    headers={"Authorization": f"Bearer {token}"},
    timeout=30
)

if bu_response.status_code == 200:
    bus = bu_response.json()
    if bus:
        bu_id = bus[0]['id']
        print(f"✅ BU encontrada: {bus[0]['name']}")
        
        # Selecionar BU
        select_response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/select-business-unit",
            json={"business_unit_id": bu_id},
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=30
        )
        
        if select_response.status_code == 200:
            token = select_response.json()["access_token"]
            print(f"✅ BU selecionada - Novo token obtido")

print()

# Importar planilha local (CSV)
print("📊 Importando plano de contas do CSV local...")

import os
csv_file = "csv/Fluxo de Caixa 2025_Cliente teste - Plano de contas.csv"

if not os.path.exists(csv_file):
    print(f"⚠️  Arquivo CSV não encontrado: {csv_file}")
    print("   Criar manualmente ou usar interface /google-sheets-import")
    print()
else:
    with open(csv_file, 'rb') as f:
        files = {'file': (os.path.basename(csv_file), f, 'text/csv')}
        
        import_response = requests.post(
            f"{BACKEND_URL}/api/v1/chart-accounts/import",
            files=files,
            headers={"Authorization": f"Bearer {token}"},
            timeout=60
        )
        
        if import_response.status_code == 200:
            result = import_response.json()
            print(f"✅ Plano de contas importado!")
            print(f"   Mensagem: {result.get('message')}")
        else:
            print(f"⚠️  Erro na importação: {import_response.status_code}")

# Verificar dados importados
print()
print("🔍 Verificando dados importados...")

groups_response = requests.get(
    f"{BACKEND_URL}/api/v1/chart-accounts/groups",
    headers={"Authorization": f"Bearer {token}"},
    timeout=30
)

if groups_response.status_code == 200:
    groups = groups_response.json()
    print(f"✅ Grupos: {len(groups)}")
    for g in groups:
        print(f"   - {g['name']}")

accounts_response = requests.get(
    f"{BACKEND_URL}/api/v1/chart-accounts/accounts",
    headers={"Authorization": f"Bearer {token}"},
    timeout=30
)

if accounts_response.status_code == 200:
    accounts = accounts_response.json()
    print(f"\n✅ Contas: {len(accounts)}")

print()
print("=" * 80)
print("✅ IMPORTAÇÃO CONCLUÍDA!")
print("=" * 80)
print()
print("📝 Próximos Passos:")
print(f"  1. Enviar credenciais para {ADMIN_USERNAME}@gmail.com")
print("  2. Cliente faz login e troca senha")
print("  3. Cliente pode importar transações via interface")
print("  4. Sistema pronto para uso!")

