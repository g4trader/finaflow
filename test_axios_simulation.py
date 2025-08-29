#!/usr/bin/env python3
"""
Script para simular as requisições do Axios e identificar o problema específico
"""

import requests
import json

def test_login():
    """Testa o login para obter um token válido"""
    print("🔐 Testando login...")
    
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    try:
        response = requests.post(
            'https://finaflow-backend-609095880025.us-central1.run.app/auth/login',
            data=login_data,
            headers=headers,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            print(f"✅ Login bem-sucedido! Token: {token[:20]}...")
            return token
        else:
            print(f"❌ Login falhou: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erro no login: {e}")
        return None

def test_transactions_with_token(token):
    """Testa o endpoint de transações com token"""
    print(f"\n🔍 Testando transações com token...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(
            'https://finaflow-backend-609095880025.us-central1.run.app/transactions',
            headers=headers,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Transações obtidas com sucesso!")
            print(f"   Quantidade: {len(data)} transações")
            if data:
                print(f"   Primeira transação: {data[0]}")
        elif response.status_code == 401:
            print("❌ Token inválido ou expirado")
        elif response.status_code == 403:
            print("❌ Sem permissão para acessar transações")
        else:
            print(f"❌ Erro inesperado: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Erro de conexão (Network Error)")
    except requests.exceptions.Timeout:
        print("❌ Timeout na requisição")
    except Exception as e:
        print(f"❌ Erro geral: {e}")

def test_other_endpoints_with_token(token):
    """Testa outros endpoints para comparar"""
    print(f"\n🔍 Testando outros endpoints...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    endpoints = [
        '/accounts',
        '/groups', 
        '/subgroups',
        '/users'
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(
                f'https://finaflow-backend-609095880025.us-central1.run.app{endpoint}',
                headers=headers,
                timeout=10
            )
            
            print(f"✅ {endpoint}: {response.status_code}")
            
        except Exception as e:
            print(f"❌ {endpoint}: {e}")

def test_without_https_redirect():
    """Testa se há redirecionamento HTTP para HTTPS"""
    print(f"\n🔍 Testando redirecionamento HTTP...")
    
    try:
        # Tentar HTTP primeiro
        response = requests.get(
            'http://finaflow-backend-609095880025.us-central1.run.app/transactions',
            allow_redirects=False,
            timeout=10
        )
        
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code in [301, 302, 307, 308]:
            print(f"✅ Redirecionamento detectado para: {response.headers.get('Location')}")
        else:
            print("⚠️ Sem redirecionamento HTTP->HTTPS")
            
    except Exception as e:
        print(f"❌ Erro no teste HTTP: {e}")

def main():
    """Função principal"""
    print("🎯 SIMULAÇÃO COMPLETA DO AXIOS")
    print("=" * 50)
    
    # 1. Testar login
    token = test_login()
    
    if token:
        # 2. Testar transações com token
        test_transactions_with_token(token)
        
        # 3. Testar outros endpoints
        test_other_endpoints_with_token(token)
    
    # 4. Testar redirecionamento
    test_without_https_redirect()
    
    print("\n" + "=" * 50)
    print("📋 CONCLUSÕES:")
    print("• Se o login falhar: problema de credenciais")
    print("• Se transações falhar mas outros funcionarem: problema específico do endpoint")
    print("• Se todos falharem: problema de autenticação geral")
    print("• Se houver Network Error: problema de conectividade")

if __name__ == "__main__":
    main()
