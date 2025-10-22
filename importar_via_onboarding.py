#!/usr/bin/env python3
"""
📊 IMPORTAÇÃO VIA ONBOARDING (FUNCIONAL)
Usar o endpoint de onboarding que já funciona para importar os dados
"""

import requests
import json
import time

# Configurações
BACKEND_URL = "https://finaflow-backend-642830139828.us-central1.run.app"
GOOGLE_SHEET_ID = "1rWMdDhwiNoC7iMycmQGWWDIacrePr1gB7c_mbt1patQ"
CREDENTIALS = {"username": "superadmin", "password": "Admin@123"}

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

def importar_via_onboarding(headers):
    """Importar dados via endpoint de onboarding"""
    print("\n🚀 IMPORTANDO VIA ONBOARDING...")
    print("-" * 40)
    
    try:
        # Usar o endpoint de onboarding que já funciona
        payload = {
            "spreadsheet_id": GOOGLE_SHEET_ID,
            "company_name": "LLM Lavanderia - Reimportação",
            "admin_email": "lucianoterresrosa@gmail.com",
            "admin_name": "Luciano Terres"
        }
        
        response = requests.post(f"{BACKEND_URL}/api/v1/admin/onboard-new-company", 
                               headers=headers, json=payload, timeout=300)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Dados importados via onboarding: {result.get('message', 'Sucesso')}")
            return True
        else:
            print(f"   ❌ Erro ao importar via onboarding: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro na importação via onboarding: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 IMPORTAÇÃO VIA ONBOARDING (FUNCIONAL)")
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
    
    # Importar via onboarding
    print("\n🚀 Iniciando importação via onboarding...")
    
    sucessos = 0
    
    # Importar via onboarding
    if importar_via_onboarding(headers):
        sucessos += 1
    
    # Verificar estado final
    print("\n📋 ESTADO FINAL DOS DADOS:")
    print("-" * 40)
    verificar_estado_atual(headers)
    
    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DA IMPORTAÇÃO:")
    print(f"   ✅ Sucessos: {sucessos}/1")
    print(f"   ❌ Falhas: {1 - sucessos}/1")
    
    if sucessos == 1:
        print("\n🎉 IMPORTAÇÃO COMPLETA COM SUCESSO!")
        print("🌐 Acesse: https://finaflow.vercel.app/transactions")
    else:
        print("\n⚠️  IMPORTAÇÃO FALHOU - Verifique os erros acima")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
