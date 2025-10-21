#!/usr/bin/env python3
"""
🏦 SETUP COMPLETO - CONTAS BANCÁRIAS DA PLANILHA
1. Criar tabelas
2. Importar contas com saldos
"""

import requests
import time
from google.oauth2 import service_account
from googleapiclient.discovery import build

BACKEND_URL = "https://finaflow-backend-642830139828.us-central1.run.app"
GOOGLE_SHEET_ID = "1rWMdDhwiNoC7iMycmQGWWDIacrePr1gB7c_mbt1patQ"
CREDENTIALS = {"username": "lucianoterresrosa", "password": "xs95LIa9ZduX"}

print("🏦 SETUP COMPLETO - CONTAS BANCÁRIAS")
print("=" * 100)

# Login
print("\n1️⃣ Login...")
time.sleep(2)
response = requests.post(f"{BACKEND_URL}/api/v1/auth/login", data=CREDENTIALS, timeout=10)
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("   ✅ Login OK")

# Criar tabelas
print("\n2️⃣ Criando tabelas...")
response = requests.post(
    f"{BACKEND_URL}/api/v1/admin/criar-tabelas-financeiras-simples",
    headers=headers,
    timeout=60
)
result = response.json()
if result.get("success"):
    print(f"   ✅ {result['message']}")
else:
    print(f"   ⚠️ {result.get('message', 'Erro')[:100]}")
    print("   Continuando...")

# Autenticar Google Sheets
print("\n3️⃣ Analisando planilha...")
credentials = service_account.Credentials.from_service_account_file(
    'google_credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
)
service = build('sheets', 'v4', credentials=credentials)

# Buscar saldo mais recente (Out2025)
result = service.spreadsheets().values().get(
    spreadsheetId=GOOGLE_SHEET_ID,
    range="'FC-diário-Out2025'!B174:C184"
).execute()

values = result.get('values', [])
contas = {}

for row in values:
    if len(row) >= 2:
        descricao = row[0].strip() if row[0] else ""
        valor_str = row[1].strip() if len(row) > 1 else ""
        
        if descricao.upper() in ["CEF", "SICOOB"]:
            try:
                valor_limpo = valor_str.replace(".", "").replace(",", ".").strip()
                if valor_limpo:
                    contas[descricao] = float(valor_limpo)
            except:
                pass

print(f"   ✅ Contas encontradas: {len(contas)}")

# Criar contas
print("\n4️⃣ Criando contas bancárias...")
for banco, saldo in sorted(contas.items()):
    print(f"   📅 {banco}: R$ {saldo:,.2f}")
    
    conta_data = {
        "banco": banco,
        "agencia": "",
        "numero_conta": "",
        "tipo": "corrente",
        "saldo_inicial": saldo
    }
    
    response = requests.post(
        f"{BACKEND_URL}/api/v1/contas-bancarias",
        json=conta_data,
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print(f"      ✅ Criado")
        else:
            print(f"      ⚠️ {result.get('message', 'Erro')[:50]}")
    else:
        print(f"      ❌ HTTP {response.status_code}")

# Criar caixa
print("\n5️⃣ Criando Caixa Principal...")
caixa_data = {
    "nome": "Caixa Principal",
    "descricao": "Dinheiro físico da empresa",
    "saldo_inicial": 0.00
}

response = requests.post(
    f"{BACKEND_URL}/api/v1/caixa",
    json=caixa_data,
    headers=headers,
    timeout=10
)

if response.status_code == 200:
    print(f"   ✅ Caixa criado")
else:
    print(f"   ⚠️ Erro: {response.status_code}")

# Verificar saldo disponível
print("\n6️⃣ SALDO DISPONÍVEL TOTAL")
print("=" * 100)
time.sleep(1)
response = requests.get(f"{BACKEND_URL}/api/v1/saldo-disponivel", headers=headers, timeout=10)

if response.status_code == 200:
    saldo = response.json().get("saldo_disponivel", {})
    
    print(f"\n💳 CONTAS BANCÁRIAS: R$ {saldo.get('contas_bancarias', {}).get('total', 0):,.2f}")
    for conta in saldo.get('contas_bancarias', {}).get('detalhes', []):
        print(f"   • {conta['banco']:20s}: R$ {conta['saldo']:>15,.2f}")
    
    print(f"\n💰 CAIXA/DINHEIRO: R$ {saldo.get('caixas', {}).get('total', 0):,.2f}")
    for caixa in saldo.get('caixas', {}).get('detalhes', []):
        print(f"   • {caixa['nome']:20s}: R$ {caixa['saldo']:>15,.2f}")
    
    print(f"\n📈 INVESTIMENTOS: R$ {saldo.get('investimentos', {}).get('total', 0):,.2f}")
    
    print(f"\n{'='*100}")
    print(f"💎 TOTAL GERAL: R$ {saldo.get('total_geral', 0):,.2f}")
    print(f"{'='*100}")
else:
    print(f"   ❌ Erro: {response.status_code}")

print("\n" + "=" * 100)
print("🎉 SETUP COMPLETO!")
print("=" * 100)
print("\n✅ Agora acesse o Dashboard e veja o Saldo Disponível!")
print("🌐 https://finaflow.vercel.app/dashboard")
print("=" * 100)

