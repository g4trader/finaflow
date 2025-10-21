#!/usr/bin/env python3
"""
Script para verificar se os lançamentos foram importados corretamente
"""

import requests
import json

# Configurações
BACKEND_URL = "https://finaflow-backend-642830139828.us-central1.run.app"

# Credenciais do usuário LLM Lavanderia
CREDENTIALS = {
    "username": "lucianoterresrosa",
    "password": "xs95LIa9ZduX"
}

def login():
    """Fazer login no sistema"""
    print("🔐 Fazendo login...")
    
    login_data = {
        "username": CREDENTIALS["username"],
        "password": CREDENTIALS["password"]
    }
    
    response = requests.post(
        f"{BACKEND_URL}/api/v1/auth/login", 
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        data = response.json()
        token = data["access_token"]
        print("✅ Login realizado com sucesso")
        return token
    else:
        print(f"❌ Erro no login: {response.status_code} - {response.text}")
        return None

def verificar_lancamentos(token):
    """Verificar lançamentos no sistema"""
    print("🔍 Verificando lançamentos...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Tentar diferentes endpoints
    endpoints = [
        "/api/v1/lancamentos-diarios?limit=10",
        "/api/v1/lancamentos-diarios",
        "/api/v1/financial/transactions?limit=10"
    ]
    
    for endpoint in endpoints:
        print(f"\n📡 Testando endpoint: {endpoint}")
        response = requests.get(f"{BACKEND_URL}{endpoint}", headers=headers)
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Resposta: {json.dumps(data, indent=2)[:500]}...")
        else:
            print(f"Erro: {response.text}")

def verificar_dashboard(token):
    """Verificar dados do dashboard"""
    print("\n📊 Verificando dados do dashboard...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Testar endpoint de cash flow
    response = requests.get(f"{BACKEND_URL}/api/v1/financial/cash-flow", headers=headers)
    
    print(f"Status Cash Flow: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Cash Flow Response: {json.dumps(data, indent=2)[:500]}...")
    else:
        print(f"Erro Cash Flow: {response.text}")

def main():
    """Função principal"""
    print("🔍 Verificando importação dos lançamentos")
    print("=" * 50)
    
    # Login
    token = login()
    if not token:
        return
    
    # Verificar lançamentos
    verificar_lancamentos(token)
    
    # Verificar dashboard
    verificar_dashboard(token)
    
    print("\n" + "=" * 50)
    print("✅ Verificação concluída")

if __name__ == "__main__":
    main()
