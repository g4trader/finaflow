#!/usr/bin/env python3
"""
Script para verificar os lançamentos importados
"""

import requests
import json

# Configurações
BACKEND_URL = "https://finaflow-backend-642830139828.us-central1.run.app"
USERNAME = "lucianoterresrosa"
PASSWORD = "xs95LIa9ZduX"

def fazer_login():
    """Fazer login no sistema"""
    print("🔐 Fazendo login...")
    
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    response = requests.post(f"{BACKEND_URL}/api/v1/auth/login", data=login_data)
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print("✅ Login realizado com sucesso")
        return token
    else:
        print(f"❌ Erro no login: {response.status_code} - {response.text}")
        return None

def verificar_lancamentos(token):
    """Verificar lançamentos importados"""
    print("🔍 Verificando lançamentos importados...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Tentar diferentes endpoints
    endpoints = [
        "/api/v1/lancamentos-diarios?limit=1000",
        "/api/v1/lancamentos-diarios?limit=100",
        "/api/v1/lancamentos-diarios",
        "/api/v1/financial/cash-flow"
    ]
    
    for endpoint in endpoints:
        print(f"\n📊 Testando endpoint: {endpoint}")
        response = requests.get(f"{BACKEND_URL}{endpoint}", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            
            if isinstance(data, list):
                print(f"📈 Total de lançamentos: {len(data)}")
                if len(data) > 0:
                    print(f"📋 Primeiro lançamento: {data[0]}")
            elif isinstance(data, dict):
                print(f"📊 Dados recebidos: {list(data.keys())}")
                if 'lancamentos' in data:
                    print(f"📈 Total de lançamentos: {len(data['lancamentos'])}")
                if 'total' in data:
                    print(f"📈 Total geral: {data['total']}")
                if 'items' in data:
                    print(f"📈 Total de items: {len(data['items'])}")
                if 'daily_data' in data:
                    print(f"📈 Total de dias: {len(data['daily_data'])}")
            else:
                print(f"📊 Tipo de dados: {type(data)}")
        else:
            print(f"❌ Erro: {response.status_code} - {response.text}")

def verificar_dashboard(token):
    """Verificar dados do dashboard"""
    print("\n🎯 Verificando dados do dashboard...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Testar endpoint do dashboard
    response = requests.get(f"{BACKEND_URL}/api/v1/financial/cash-flow", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Dashboard carregado com sucesso")
        
        if isinstance(data, list):
            print(f"📈 Total de dias com dados: {len(data)}")
            # Mostrar alguns dias
            for i, day_data in enumerate(data[:3]):
                print(f"  📅 {day_data}")
        elif isinstance(data, dict):
            print(f"📊 Chaves disponíveis: {list(data.keys())}")
            if 'daily_data' in data:
                print(f"📈 Total de dias com dados: {len(data['daily_data'])}")
                # Mostrar alguns dias
                for i, (date, day_data) in enumerate(list(data['daily_data'].items())[:3]):
                    print(f"  📅 {date}: {day_data}")
    else:
        print(f"❌ Erro no dashboard: {response.status_code} - {response.text}")

def main():
    """Função principal"""
    print("🚀 Verificando lançamentos importados")
    print("=" * 60)
    
    # 1. Login
    token = fazer_login()
    if not token:
        print("❌ Falha no login. Abortando.")
        return
    
    # 2. Verificar lançamentos
    verificar_lancamentos(token)
    
    # 3. Verificar dashboard
    verificar_dashboard(token)
    
    print("\n🎯 Verificação concluída!")

if __name__ == "__main__":
    main()
