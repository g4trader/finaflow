#!/usr/bin/env python3
"""
🔄 REIMPORTAÇÃO COMPLETA - PLANO DE CONTAS CORRETO
Limpar tudo do tenant e reimportar na ordem correta
"""

import requests
import time

BACKEND_URL = "https://finaflow-backend-642830139828.us-central1.run.app"
GOOGLE_SHEET_ID = "1rWMdDhwiNoC7iMycmQGWWDIacrePr1gB7c_mbt1patQ"
CREDENTIALS = {"username": "lucianoterresrosa", "password": "xs95LIa9ZduX"}

print("🔄 REIMPORTAÇÃO COMPLETA E LIMPA")
print("=" * 80)

# Login
print("1️⃣ FAZENDO LOGIN...")
response = requests.post(f"{BACKEND_URL}/api/v1/auth/login", data=CREDENTIALS, timeout=10)
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("   ✅ Login realizado\n")

# Limpar TUDO
print("2️⃣ LIMPANDO TODOS OS DADOS DO TENANT...")
print("   (business_unit_chart_accounts, lancamentos, previsões, contas, subgrupos, grupos)")
response = requests.post(f"{BACKEND_URL}/api/v1/admin/limpar-tudo-tenant", headers=headers, timeout=30)
result = response.json()
if result.get("success"):
    print(f"   ✅ {result['message']}\n")
else:
    print(f"   ❌ Erro: {result.get('message')}\n")
    print("   ⚠️ Continuando mesmo assim...\n")

time.sleep(2)

# Verificar limpeza
print("3️⃣ VERIFICANDO LIMPEZA...")
response = requests.get(f"{BACKEND_URL}/api/v1/lancamentos-diarios/plano-contas", headers=headers, timeout=10)
plano = response.json()
response_lanc = requests.get(f"{BACKEND_URL}/api/v1/lancamentos-diarios", headers=headers, timeout=10)
lancamentos = response_lanc.json()["lancamentos"]
response_prev = requests.get(f"{BACKEND_URL}/api/v1/lancamentos-previstos", headers=headers, timeout=10)
previsoes = response_prev.json().get("previsoes", [])

print(f"   Grupos: {len(plano['grupos'])}")
print(f"   Subgrupos: {len(plano['subgrupos'])}")
print(f"   Contas: {len(plano['contas'])}")
print(f"   Lançamentos: {len(lancamentos)}")
print(f"   Previsões: {len(previsoes)}")

if len(plano['contas']) == 0 and len(lancamentos) == 0 and len(previsoes) == 0:
    print(f"   ✅ Tenant completamente limpo!\n")
else:
    print(f"   ⚠️ Ainda há dados. Continuando...\n")

time.sleep(2)

# Importar Plano de Contas
print("4️⃣ IMPORTANDO PLANO DE CONTAS DA PLANILHA...")
print("   ⏳ Aguarde...")
import_data = {"spreadsheet_id": GOOGLE_SHEET_ID}
response = requests.post(
    f"{BACKEND_URL}/api/v1/admin/importar-plano-contas-planilha",
    json=import_data,
    headers=headers,
    timeout=120
)

if response.status_code == 200:
    result = response.json()
    if result.get("success"):
        print(f"   ✅ {result['message']}")
        details = result.get('details', {})
        print(f"      Grupos: {details.get('grupos_criados', 0)}")
        print(f"      Subgrupos: {details.get('subgrupos_criados', 0)}")
        print(f"      Contas: {details.get('contas_criadas', 0)}\n")
    else:
        print(f"   ❌ Erro: {result.get('message')}\n")
        exit(1)
else:
    print(f"   ❌ HTTP {response.status_code}: {response.text[:200]}\n")
    exit(1)

time.sleep(2)

# Verificar plano de contas
print("5️⃣ VERIFICANDO PLANO DE CONTAS...")
response = requests.get(f"{BACKEND_URL}/api/v1/lancamentos-diarios/plano-contas", headers=headers, timeout=10)
plano = response.json()
print(f"   Grupos: {len(plano['grupos'])}")
print(f"   Subgrupos: {len(plano['subgrupos'])}")
print(f"   Contas: {len(plano['contas'])}")

if len(plano['contas']) == 96:
    print(f"   ✅ Plano de contas CORRETO (96 contas)!\n")
else:
    print(f"   ⚠️ Esperado 96 contas, encontrado {len(plano['contas'])}\n")

time.sleep(2)

# Importar Lançamentos
print("6️⃣ IMPORTANDO LANÇAMENTOS DA PLANILHA...")
print("   ⏳ Aguarde 1-2 minutos...")
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

time.sleep(2)

# Importar Previsões
print("7️⃣ IMPORTANDO PREVISÕES DA PLANILHA...")
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

# Verificação final
print("8️⃣ VERIFICAÇÃO FINAL...")
print("=" * 80)

response = requests.get(f"{BACKEND_URL}/api/v1/lancamentos-diarios/plano-contas", headers=headers, timeout=10)
plano = response.json()
response = requests.get(f"{BACKEND_URL}/api/v1/lancamentos-diarios", headers=headers, timeout=10)
lancamentos = response.json()["lancamentos"]
response = requests.get(f"{BACKEND_URL}/api/v1/lancamentos-previstos", headers=headers, timeout=10)
previsoes = response.json().get("previsoes", [])

print(f"📊 RESUMO FINAL:")
print(f"   Grupos: {len(plano['grupos'])}")
print(f"   Subgrupos: {len(plano['subgrupos'])}")
print(f"   Contas: {len(plano['contas'])} {'✅ CORRETO' if len(plano['contas']) == 96 else '❌ INCORRETO (esperado 96)'}")
print(f"   Lançamentos: {len(lancamentos)}")
print(f"   Previsões: {len(previsoes)}")

if lancamentos:
    tipos = {}
    for l in lancamentos:
        tipos[l["transaction_type"]] = tipos.get(l["transaction_type"], 0) + 1
    print(f"\n   Tipos de lançamentos:")
    for tipo, count in sorted(tipos.items()):
        print(f"      {tipo}: {count}")

print("\n" + "=" * 80)
if len(plano['contas']) == 96:
    print("🎉 REIMPORTAÇÃO COMPLETA E BEM-SUCEDIDA!")
    print("✅ Sistema com plano de contas CORRETO da planilha!")
else:
    print("⚠️ ATENÇÃO: Plano de contas ainda incorreto")
    print(f"   Esperado: 96 contas")
    print(f"   Encontrado: {len(plano['contas'])} contas")
print("=" * 80)

