#!/usr/bin/env python3
"""
📊 IMPORTAÇÃO AUTOMÁTICA DE DADOS DA PLANILHA
Importar plano de contas, lançamentos diários e previsões
"""

import requests
import json
import time

# Configurações
BACKEND_URL = "https://finaflow-backend-642830139828.us-central1.run.app"
GOOGLE_SHEET_ID = "1rWMdDhwiNoC7iMycmQGWWDIacrePr1gB7c_mbt1patQ"
CREDENTIALS = {"username": "lucianoterresrosa", "password": "xs95LIa9ZduX"}

def fazer_login():
    """Fazer login e obter token"""
    print("🔐 Fazendo login...")
    response = requests.post(f"{BACKEND_URL}/api/v1/auth/login", data=CREDENTIALS, timeout=30)
    if response.status_code != 200:
        print(f"❌ Erro no login: {response.status_code} - {response.text}")
        return None
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login realizado com sucesso")
    return headers

def verificar_estado_atual(headers):
    """Verificar estado atual dos dados"""
    print("\n📋 ESTADO ATUAL DOS DADOS:")
    print("-" * 40)
    
    try:
        # Verificar lançamentos
        response = requests.get(f"{BACKEND_URL}/api/v1/lancamentos-diarios?limit=1", headers=headers, timeout=30)
        if response.status_code == 200:
            total_lancamentos = response.json().get("total", 0)
            print(f"   📊 Lançamentos diários: {total_lancamentos}")
        else:
            print(f"   ❌ Erro ao verificar lançamentos: {response.status_code}")
        
        # Verificar previsões
        response = requests.get(f"{BACKEND_URL}/api/v1/lancamentos-previstos?limit=1", headers=headers, timeout=30)
        if response.status_code == 200:
            total_previsoes = response.json().get("total", 0)
            print(f"   📈 Previsões: {total_previsoes}")
        else:
            print(f"   ❌ Erro ao verificar previsões: {response.status_code}")
        
        # Verificar plano de contas
        response = requests.get(f"{BACKEND_URL}/api/v1/lancamentos-diarios/plano-contas", headers=headers, timeout=30)
        if response.status_code == 200:
            plano = response.json()
            grupos = len(plano.get("grupos", []))
            subgrupos = len(plano.get("subgrupos", []))
            contas = len(plano.get("contas", []))
            print(f"   📋 Plano de contas: {grupos} grupos, {subgrupos} subgrupos, {contas} contas")
        else:
            print(f"   ❌ Erro ao verificar plano de contas: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erro ao verificar estado: {e}")

def importar_plano_contas(headers):
    """Importar plano de contas"""
    print("\n📋 IMPORTANDO PLANO DE CONTAS...")
    print("-" * 40)
    
    try:
        payload = {"spreadsheet_id": GOOGLE_SHEET_ID}
        response = requests.post(f"{BACKEND_URL}/api/v1/admin/importar-plano-contas-planilha", 
                               headers=headers, json=payload, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Plano de contas importado: {result.get('message', 'Sucesso')}")
            return True
        else:
            print(f"   ❌ Erro ao importar plano de contas: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro na importação do plano de contas: {e}")
        return False

def importar_lancamentos(headers):
    """Importar lançamentos diários"""
    print("\n📊 IMPORTANDO LANÇAMENTOS DIÁRIOS...")
    print("-" * 40)
    
    try:
        payload = {"spreadsheet_id": GOOGLE_SHEET_ID}
        response = requests.post(f"{BACKEND_URL}/api/v1/admin/importar-lancamentos-planilha", 
                               headers=headers, json=payload, timeout=300)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Lançamentos importados: {result.get('message', 'Sucesso')}")
            return True
        else:
            print(f"   ❌ Erro ao importar lançamentos: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro na importação dos lançamentos: {e}")
        return False

def importar_previsoes(headers):
    """Importar previsões"""
    print("\n📈 IMPORTANDO PREVISÕES...")
    print("-" * 40)
    
    try:
        payload = {"spreadsheet_id": GOOGLE_SHEET_ID}
        response = requests.post(f"{BACKEND_URL}/api/v1/admin/importar-previsoes-planilha", 
                               headers=headers, json=payload, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Previsões importadas: {result.get('message', 'Sucesso')}")
            return True
        else:
            print(f"   ❌ Erro ao importar previsões: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro na importação das previsões: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 IMPORTAÇÃO AUTOMÁTICA DE DADOS DA PLANILHA")
    print("=" * 60)
    print(f"📊 Planilha: {GOOGLE_SHEET_ID}")
    print(f"👤 Usuário: {CREDENTIALS['username']}")
    print("=" * 60)
    
    # Fazer login
    headers = fazer_login()
    if not headers:
        return
    
    # Verificar estado atual
    verificar_estado_atual(headers)
    
    # Importar dados automaticamente
    print("\n🚀 Iniciando importação automática...")
    
    sucessos = 0
    
    # 1. Plano de contas
    if importar_plano_contas(headers):
        sucessos += 1
        time.sleep(2)  # Aguardar um pouco entre as importações
    
    # 2. Lançamentos diários
    if importar_lancamentos(headers):
        sucessos += 1
        time.sleep(2)
    
    # 3. Previsões
    if importar_previsoes(headers):
        sucessos += 1
    
    # Verificar estado final
    print("\n📋 ESTADO FINAL DOS DADOS:")
    print("-" * 40)
    verificar_estado_atual(headers)
    
    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DA IMPORTAÇÃO:")
    print(f"   ✅ Sucessos: {sucessos}/3")
    print(f"   ❌ Falhas: {3 - sucessos}/3")
    
    if sucessos == 3:
        print("\n🎉 IMPORTAÇÃO COMPLETA COM SUCESSO!")
        print("🌐 Acesse: https://finaflow.vercel.app/transactions")
    else:
        print("\n⚠️  IMPORTAÇÃO PARCIAL - Verifique os erros acima")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
