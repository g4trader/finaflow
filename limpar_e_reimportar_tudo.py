#!/usr/bin/env python3
"""
🧹 LIMPEZA TOTAL E REIMPORTAÇÃO COMPLETA
Limpar todos os dados e reimportar da planilha corretamente
"""

import requests
import time

BACKEND_URL = "https://finaflow-backend-642830139828.us-central1.run.app"
GOOGLE_SHEET_ID = "1rWMdDhwiNoC7iMycmQGWWDIacrePr1gB7c_mbt1patQ"
CREDENTIALS = {"username": "lucianoterresrosa", "password": "xs95LIa9ZduX"}

print("🎯 LIMPEZA TOTAL E REIMPORTAÇÃO")
print("=" * 80)

# Login
response = requests.post(f"{BACKEND_URL}/api/v1/auth/login", data=CREDENTIALS, timeout=10)
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✅ Login realizado\n")

# 0. Limpar Plano de Contas
print("0️⃣ LIMPANDO PLANO DE CONTAS...")
response = requests.post(f"{BACKEND_URL}/api/v1/admin/limpar-plano-contas", headers=headers, timeout=10)
result = response.json()
print(f"   {result['message']}\n")

# 1. Limpar Lançamentos
print("1️⃣ LIMPANDO LANÇAMENTOS...")
response = requests.post(f"{BACKEND_URL}/api/v1/admin/limpar-via-sql", headers=headers, timeout=10)
result = response.json()
print(f"   {result['message']}\n")

# 2. Limpar Previsões
print("2️⃣ LIMPANDO PREVISÕES...")
try:
    # Buscar todas
    response = requests.get(f"{BACKEND_URL}/api/v1/lancamentos-previstos", headers=headers, timeout=10)
    if response.status_code == 200:
        previsoes = response.json().get("previsoes", [])
        print(f"   Encontradas {len(previsoes)} previsões para remover")
        for prev in previsoes:
            requests.delete(f"{BACKEND_URL}/api/v1/lancamentos-previstos/{prev['id']}", headers=headers, timeout=10)
        print(f"   ✅ {len(previsoes)} previsões removidas")
    else:
        print(f"   ✅ Nenhuma previsão para remover")
except Exception as e:
    print(f"   ⚠️ Erro ao limpar previsões: {str(e)}")

print()

# 3. Verificar limpeza
print("3️⃣ VERIFICANDO LIMPEZA...")
response = requests.get(f"{BACKEND_URL}/api/v1/lancamentos-diarios", headers=headers, timeout=10)
lanc_count = len(response.json()["lancamentos"])
response = requests.get(f"{BACKEND_URL}/api/v1/lancamentos-previstos", headers=headers, timeout=10)
prev_count = len(response.json().get("previsoes", []))
print(f"   Lançamentos: {lanc_count}")
print(f"   Previsões: {prev_count}")

if lanc_count == 0 and prev_count == 0:
    print(f"   ✅ Sistema completamente limpo!\n")
else:
    print(f"   ⚠️ Ainda há dados no sistema\n")

# 4. Importar Plano de Contas
print("4️⃣ IMPORTANDO PLANO DE CONTAS DA PLANILHA...")
print("   ⏳ Aguarde...")
response = requests.post(
    f"{BACKEND_URL}/api/v1/admin/importar-plano-contas-planilha",
    json=import_data,
    headers=headers,
    timeout=60
)

if response.status_code == 200:
    result = response.json()
    if result.get("success"):
        print(f"   ✅ {result['message']}\n")
    else:
        print(f"   ❌ Erro: {result.get('message')[:200]}\n")
else:
    print(f"   ❌ HTTP {response.status_code}\n")

time.sleep(2)

# 5. Importar Lançamentos
print("5️⃣ IMPORTANDO LANÇAMENTOS DA PLANILHA...")
print("   ⏳ Aguarde 1-2 minutos...")
import_data = {"spreadsheet_id": GOOGLE_SHEET_ID}
response = requests.post(
    f"{BACKEND_URL}/api/v1/admin/importar-lancamentos-planilha",
    json=import_data,
    headers=headers,
    timeout=300
)

if response.status_code == 200:
    result = response.json()
    if result.get("success"):
        print(f"   ✅ {result['message']}\n")
    else:
        print(f"   ❌ Erro: {result.get('message')[:200]}\n")
else:
    print(f"   ❌ HTTP {response.status_code}\n")

# 6. Importar Previsões
print("6️⃣ IMPORTANDO PREVISÕES DA PLANILHA...")
print("   ⏳ Aguarde 1-2 minutos...")
response = requests.post(
    f"{BACKEND_URL}/api/v1/admin/importar-previsoes-planilha",
    json=import_data,
    headers=headers,
    timeout=300
)

if response.status_code == 200:
    result = response.json()
    if result.get("success"):
        print(f"   ✅ {result['message']}\n")
    else:
        print(f"   ❌ Erro: {result.get('message')[:200]}\n")
else:
    print(f"   ❌ HTTP {response.status_code}\n")

# 7. Verificação final
print("7️⃣ VERIFICAÇÃO FINAL...")
response = requests.get(f"{BACKEND_URL}/api/v1/lancamentos-diarios", headers=headers, timeout=10)
lanc = response.json()["lancamentos"]
response = requests.get(f"{BACKEND_URL}/api/v1/lancamentos-previstos", headers=headers, timeout=10)
prev = response.json().get("previsoes", [])
response = requests.get(f"{BACKEND_URL}/api/v1/lancamentos-diarios/plano-contas", headers=headers, timeout=10)
plano = response.json()

print(f"   Lançamentos: {len(lanc)}")
print(f"   Previsões: {len(prev)}")
print(f"   Grupos: {len(plano['grupos'])}")
print(f"   Subgrupos: {len(plano['subgrupos'])}")
print(f"   Contas: {len(plano['contas'])}")

# Tipos
if lanc:
    tipos = {}
    for l in lanc:
        tipos[l["transaction_type"]] = tipos.get(l["transaction_type"], 0) + 1
    print(f"\n   Tipos de lançamentos:")
    for tipo, count in sorted(tipos.items()):
        print(f"      {tipo}: {count}")

print("\n" + "=" * 80)
print("🎉 PROCESSO CONCLUÍDO!")
print("=" * 80)

EOF
