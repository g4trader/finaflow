#!/usr/bin/env python3
"""
Script para debugar o problema de login
"""

import requests
import json

# Configurações
BACKEND_URL = "https://finaflow-backend-609095880025.us-central1.run.app"
FRONTEND_URL = "https://finaflow.vercel.app"

def test_different_credentials():
    """Testa diferentes combinações de credenciais"""
    print("🔍 Testando diferentes credenciais...")
    
    test_cases = [
        {"username": "admin", "password": "admin123"},
        {"username": "admin@finaflow.com", "password": "admin123"},
        {"username": "admin", "password": "admin"},
        {"username": "admin", "password": "123"},
    ]
    
    headers = {
        'Origin': FRONTEND_URL,
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    for i, credentials in enumerate(test_cases, 1):
        print(f"\n   Teste {i}: {credentials}")
        
        try:
            response = requests.post(f"{BACKEND_URL}/auth/login", data=credentials, headers=headers, timeout=10)
            
            print(f"      Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"      ✅ SUCESSO! Token: {result.get('access_token', '')[:50]}...")
                return credentials
            elif response.status_code == 400:
                print(f"      ❌ Falhou: {response.text}")
            else:
                print(f"      ❌ Erro: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"      ❌ Erro: {e}")
    
    return None

def check_user_in_database():
    """Verifica se o usuário existe no banco"""
    print("\n🔍 Verificando usuário no banco...")
    
    # Tentar fazer uma requisição para listar usuários (se houver endpoint)
    try:
        response = requests.get(f"{BACKEND_URL}/users", timeout=10)
        if response.status_code == 200:
            users = response.json()
            print(f"   Usuários encontrados: {len(users)}")
            for user in users:
                if user.get('username') == 'admin':
                    print(f"   ✅ Usuário admin encontrado: {user}")
                    return True
        else:
            print(f"   ❌ Não foi possível listar usuários: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro ao verificar usuários: {e}")
    
    return False

def test_password_hash():
    """Testa se a senha hash está correta"""
    print("\n🔍 Verificando hash da senha...")
    
    # Hash conhecido para 'admin123'
    known_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iQeO"
    
    print(f"   Hash conhecido para 'admin123': {known_hash}")
    print("   Verifique se este hash está no BigQuery")
    
    return known_hash

def main():
    print("🚀 Debug de Login - finaFlow")
    print("=" * 50)
    
    # Testar diferentes credenciais
    working_credentials = test_different_credentials()
    
    if working_credentials:
        print(f"\n🎉 Credenciais funcionais encontradas: {working_credentials}")
        print("\n📋 Use estas credenciais no frontend:")
        print(f"   Username: {working_credentials['username']}")
        print(f"   Senha: {working_credentials['password']}")
        return
    
    # Verificar usuário no banco
    user_exists = check_user_in_database()
    
    # Verificar hash da senha
    known_hash = test_password_hash()
    
    print("\n📋 Próximos passos:")
    print("   1. Verifique se o hash no BigQuery é exatamente:")
    print(f"      {known_hash}")
    print("   2. Verifique se o username no BigQuery é exatamente: 'admin'")
    print("   3. Verifique se não há espaços extras nos campos")
    print("   4. Tente recriar o usuário no BigQuery")

if __name__ == "__main__":
    main()
