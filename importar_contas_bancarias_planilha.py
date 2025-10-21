#!/usr/bin/env python3
"""
🏦 IMPORTADOR AUTOMÁTICO - CONTAS BANCÁRIAS DA PLANILHA
Extrai saldos de contas bancárias de todas as abas de FC diário e cria as contas
"""

import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build

BACKEND_URL = "https://finaflow-backend-642830139828.us-central1.run.app"
GOOGLE_SHEET_ID = "1rWMdDhwiNoC7iMycmQGWWDIacrePr1gB7c_mbt1patQ"
CREDENTIALS = {"username": "lucianoterresrosa", "password": "xs95LIa9ZduX"}

print("🏦 IMPORTADOR DE CONTAS BANCÁRIAS DA PLANILHA")
print("=" * 100)

# Autenticar com Google Sheets
credentials = service_account.Credentials.from_service_account_file(
    'google_credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
)
service = build('sheets', 'v4', credentials=credentials)

# Login no backend
print("1️⃣ Login no sistema...")
response = requests.post(f"{BACKEND_URL}/api/v1/auth/login", data=CREDENTIALS, timeout=10)
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("   ✅ Login OK\n")

# Analisar todos os meses para encontrar as contas
print("2️⃣ Analisando todas as abas de FC diário...")
meses = [
    ("Jan2025", 1), ("Fev2025", 2), ("Mar2025", 3), ("Abr2025", 4),
    ("Mai2025", 5), ("Jun2025", 6), ("Jul2025", 7), ("Ago2025", 8),
    ("Set2025", 9), ("Out2025", 10), ("Nov2025", 11), ("Dez2025", 12)
]

# Coletar saldos de cada mês
saldos_por_mes = {}  # {mes_num: {banco: saldo}}
contas_encontradas = set()

for aba, mes_num in meses:
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=GOOGLE_SHEET_ID,
            range=f"'FC-diário-{aba}'!B174:C184"
        ).execute()
        
        values = result.get('values', [])
        saldos_por_mes[mes_num] = {}
        
        for row in values:
            if len(row) >= 2:
                descricao = row[0].strip() if row[0] else ""
                valor_str = row[1].strip() if len(row) > 1 else ""
                
                # Identificar contas bancárias
                if descricao.upper() in ["CEF", "SICOOB", "BB", "ITAU", "BRADESCO", "SANTANDER", "NUBANK", "INTER", "C6"]:
                    try:
                        valor_limpo = valor_str.replace(".", "").replace(",", ".").strip()
                        if valor_limpo and valor_limpo != "0" and valor_limpo != "0.00":
                            valor = float(valor_limpo)
                            saldos_por_mes[mes_num][descricao] = valor
                            contas_encontradas.add(descricao)
                    except:
                        pass
    except:
        pass

print(f"   ✅ Contas bancárias encontradas: {', '.join(sorted(contas_encontradas))}\n")

# Criar as contas bancárias com saldo do mês mais recente
print("3️⃣ Criando contas bancárias no sistema...")

for banco in sorted(contas_encontradas):
    # Encontrar saldo mais recente (começar do mês 10 para trás)
    saldo_inicial = 0
    for mes_num in range(10, 0, -1):
        if mes_num in saldos_por_mes and banco in saldos_por_mes[mes_num]:
            saldo_inicial = saldos_por_mes[mes_num][banco]
            mes_ref = list(filter(lambda m: m[1] == mes_num, meses))[0][0]
            print(f"   📅 {banco}: Usando saldo de {mes_ref} = R$ {saldo_inicial:,.2f}")
            break
    
    # Criar conta
    conta_data = {
        "banco": banco,
        "agencia": "",
        "numero_conta": "",
        "tipo": "corrente",
        "saldo_inicial": saldo_inicial
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
            print(f"   ✅ {banco} criado com saldo R$ {saldo_inicial:,.2f}")
        else:
            print(f"   ⚠️ {banco}: {result.get('message', 'Erro')[:50]}")
    else:
        print(f"   ❌ {banco}: HTTP {response.status_code}")

print()

# Criar caixa/dinheiro
print("4️⃣ Criando Caixa/Dinheiro...")
caixa_data = {
    "nome": "Caixa Principal",
    "descricao": "Dinheiro físico",
    "saldo_inicial": 0.00
}

response = requests.post(
    f"{BACKEND_URL}/api/v1/caixa",
    json=caixa_data,
    headers=headers,
    timeout=10
)

if response.status_code == 200:
    print(f"   ✅ Caixa criado\n")
else:
    print(f"   ⚠️ Erro ao criar caixa: {response.status_code}\n")

# Verificar saldo disponível
print("5️⃣ VERIFICANDO SALDO DISPONÍVEL TOTAL...")
response = requests.get(f"{BACKEND_URL}/api/v1/saldo-disponivel", headers=headers, timeout=10)
if response.status_code == 200:
    saldo = response.json().get("saldo_disponivel", {})
    print(f"   💳 Contas Bancárias: R$ {saldo.get('contas_bancarias', {}).get('total', 0):,.2f}")
    print(f"   💰 Caixa/Dinheiro: R$ {saldo.get('caixas', {}).get('total', 0):,.2f}")
    print(f"   📈 Investimentos: R$ {saldo.get('investimentos', {}).get('total', 0):,.2f}")
    print(f"   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"   💎 TOTAL GERAL: R$ {saldo.get('total_geral', 0):,.2f}")
else:
    print(f"   ❌ Erro: {response.status_code}")

print("\n" + "=" * 100)
print("🎉 IMPORTAÇÃO DE CONTAS CONCLUÍDA!")
print("=" * 100)

print("\n📊 EVOLUÇÃO DOS SALDOS POR MÊS:")
print("-" * 100)
for mes_num in range(1, 11):
    if mes_num in saldos_por_mes and saldos_por_mes[mes_num]:
        mes_nome = list(filter(lambda m: m[1] == mes_num, meses))[0][0]
        total_mes = sum(saldos_por_mes[mes_num].values())
        print(f"{mes_nome:15s}: R$ {total_mes:>15,.2f}")
        for banco, saldo in sorted(saldos_por_mes[mes_num].items()):
            print(f"   {banco:12s}: R$ {saldo:>15,.2f}")

print("=" * 100)

EOF
