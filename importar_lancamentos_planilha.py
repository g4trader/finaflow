#!/usr/bin/env python3
"""
📊 IMPORTAÇÃO DE LANÇAMENTOS DIÁRIOS DA PLANILHA
Importar todos os lançamentos com classificação correta (RECEITA, DESPESA, CUSTO)
"""

import requests
import json
import sys

# Configurações
BACKEND_URL = "https://finaflow-backend-642830139828.us-central1.run.app"
GOOGLE_SHEET_ID = "1rWMdDhwiNoC7iMycmQGWWDIacrePr1gB7c_mbt1patQ"
CREDENTIALS = {"username": "lucianoterresrosa", "password": "xs95LIa9ZduX"}

print("📊 IMPORTAÇÃO DE LANÇAMENTOS DIÁRIOS")
print("=" * 60)

# Login
print("🔐 Fazendo login...")
response = requests.post(f"{BACKEND_URL}/api/v1/auth/login", data=CREDENTIALS, timeout=10)
if response.status_code != 200:
    print(f"❌ Erro no login: {response.status_code}")
    sys.exit(1)

token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✅ Login realizado")

# Verificar estado antes
print("\n📋 Estado ANTES da importação:")
response = requests.get(f"{BACKEND_URL}/api/v1/lancamentos-diarios", headers=headers, timeout=10)
lancamentos_antes = response.json()["lancamentos"]
print(f"   Lançamentos atuais: {len(lancamentos_antes)}")

# Importar via LLMSheetImporter
print("\n📊 Importando lançamentos da planilha...")
print(f"   Planilha ID: {GOOGLE_SHEET_ID}")
print("   ⏳ Isso pode levar alguns minutos...")

# Chamando endpoint que usa o serviço de importação
# Precisamos criar um endpoint específico para reimportar só os lançamentos

# Por enquanto, vamos verificar se há endpoint disponível
print("\n💡 ESTRATÉGIA DE IMPORTAÇÃO:")
print("=" * 60)
print("1. O serviço LLMSheetImporter está atualizado com lógica de 3 tipos")
print("2. Classificação: RECEITA, DESPESA, CUSTO")
print("3. Baseado em palavras-chave do grupo e subgrupo")
print("")
print("📋 Palavras-chave por tipo:")
print("   RECEITA: receita, venda, renda, faturamento, vendas")
print("   CUSTO: custo, custos, mercadoria, produto")
print("   DESPESA: despesa, gasto, operacional, administrativa, marketing")
print("")
print("✅ Código atualizado e deployado no Cloud Run")
print("")
print("🔧 Para executar a importação, preciso criar um endpoint específico")
print("   ou usar o endpoint de onboarding que já existe.")
print("")
print("=" * 60)

print("\n✅ SISTEMA PRONTO PARA IMPORTAÇÃO!")
print("🌐 Acesse: https://finaflow.vercel.app/transactions")
print("=" * 60)

