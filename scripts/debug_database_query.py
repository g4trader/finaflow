#!/usr/bin/env python3
"""
Script para debugar a consulta do banco de dados
"""

import requests
import json

# Configurações
BACKEND_URL = "https://finaflow-backend-609095880025.us-central1.run.app"
FRONTEND_URL = "https://finaflow.vercel.app"

def test_database_query():
    """Testa a consulta do banco de dados"""
    print("🔍 Testando consulta do banco de dados...")
    
    # Simular exatamente o que o backend faz
    # 1. Chama query_user("admin")
    # 2. Verifica se results existe
    # 3. Cria UserInDB(**results[0])
    # 4. Verifica a senha
    
    print("   O backend executa:")
    print("   1. results = query_user('admin')")
    print("   2. if not results: raise HTTPException")
    print("   3. user = UserInDB(**results[0])")
    print("   4. verify_password(password, user.hashed_password)")
    
    # Vamos testar com diferentes variações para ver onde falha
    test_cases = [
        {"username": "admin", "password": "admin123"},
        {"username": "admin", "password": "wrong_password"},
        {"username": "nonexistent", "password": "admin123"},
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
                error_data = response.json()
                print(f"      ❌ Falhou: {error_data.get('detail', '')}")
                
                # Se for "Invalid credentials", pode ser:
                # 1. Usuário não encontrado (results vazio)
                # 2. Senha incorreta (verify_password falhou)
                if "Invalid credentials" in error_data.get('detail', ''):
                    if credentials['username'] == 'nonexistent':
                        print("      → Usuário não encontrado (esperado)")
                    elif credentials['password'] == 'wrong_password':
                        print("      → Senha incorreta (esperado)")
                    else:
                        print("      → Problema: usuário existe mas senha falha ou usuário não encontrado")
            else:
                print(f"      ❌ Erro: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"      ❌ Erro: {e}")
    
    return None

def test_user_creation():
    """Testa se conseguimos criar um usuário via API"""
    print("\n🔧 Testando criação de usuário via API...")
    
    # Dados do usuário
    user_data = {
        "username": "test_admin",
        "email": "test@finaflow.com",
        "password": "test123",
        "role": "super_admin"
    }
    
    try:
        # Primeiro, tentar fazer login com usuário que não existe
        data = {
            'username': 'test_admin',
            'password': 'test123'
        }
        
        headers = {
            'Origin': FRONTEND_URL,
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        
        response = requests.post(f"{BACKEND_URL}/auth/login", data=data, headers=headers, timeout=10)
        
        if response.status_code == 400:
            print("   ✅ Usuário test_admin não existe (esperado)")
            
            # Agora tentar criar via signup (pode não funcionar se precisar de autenticação)
            try:
                response = requests.post(f"{BACKEND_URL}/auth/signup", json=user_data, timeout=10)
                print(f"   Signup status: {response.status_code}")
                if response.status_code == 201:
                    print("   ✅ Usuário criado via API!")
                    return True
                else:
                    print(f"   ❌ Signup falhou: {response.text}")
            except Exception as e:
                print(f"   ❌ Erro no signup: {e}")
        else:
            print(f"   ⚠️  Usuário test_admin já existe: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erro ao testar criação: {e}")
    
    return False

def main():
    print("🚀 Debug de Banco de Dados - finaFlow")
    print("=" * 50)
    
    # Testar consulta do banco
    working_credentials = test_database_query()
    
    if working_credentials:
        print(f"\n🎉 Credenciais funcionais encontradas: {working_credentials}")
        return
    
    # Testar criação de usuário
    test_user_creation()
    
    print("\n📋 Análise:")
    print("   1. Se 'admin' retorna 'Invalid credentials', o problema é:")
    print("      - Usuário não existe no banco")
    print("      - Hash da senha está incorreto")
    print("      - Problema na consulta do banco")
    print("\n   2. Verifique no BigQuery:")
    print("      SELECT * FROM `automatizar-452311.finaflow.Users` WHERE username='admin';")
    print("\n   3. Se o usuário existe, verifique o hash da senha")

if __name__ == "__main__":
    main()
