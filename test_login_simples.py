#!/usr/bin/env python3
"""
🔍 TESTE SIMPLES DE LOGIN
"""

import requests
import json

def test_login():
    """Testar login simples"""
    print("🔍 TESTANDO LOGIN...")
    
    # Dados de login
    login_data = {
        'username': 'lucianoterresrosa',
        'password': 'xs95LIa9ZduX'
    }
    
    try:
        # Tentar login
        response = requests.post('https://finaflow-backend-642830139828.us-central1.run.app/api/v1/auth/login', 
                               data=login_data,
                               timeout=30)
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login bem-sucedido!")
            print(f"Token: {data.get('access_token', 'N/A')[:50]}...")
            return data.get('access_token')
        else:
            print(f"❌ Erro no login: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

def test_lancamentos(token):
    """Testar busca de lançamentos"""
    if not token:
        return
        
    print("\n🔍 TESTANDO BUSCA DE LANÇAMENTOS...")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        response = requests.get('https://finaflow-backend-642830139828.us-central1.run.app/api/v1/lancamentos-diarios?limit=1', 
                               headers=headers,
                               timeout=30)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            total = data.get('total', 0)
            print(f"✅ Total de lançamentos: {total}")
            return total
        else:
            print(f"❌ Erro: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

if __name__ == "__main__":
    print("🔍 TESTE SIMPLES DE LOGIN E LANÇAMENTOS")
    print("=" * 50)
    
    # Testar login
    token = test_login()
    
    # Testar lançamentos
    if token:
        total = test_lancamentos(token)
        if total:
            print(f"\n📊 RESULTADO: {total} lançamentos no sistema")
    
    print("\n" + "=" * 50)
    print("✅ Teste concluído!")
