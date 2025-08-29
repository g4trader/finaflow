#!/usr/bin/env python3
"""
Script para testar a verificação de senha e debug completo
"""

import requests
import json
import bcrypt

# Configurações
BACKEND_URL = "https://finaflow-backend-609095880025.us-central1.run.app"
FRONTEND_URL = "https://finaflow.vercel.app"

def test_password_hash():
    """Testa se o hash da senha está correto"""
    print("🔍 Testando hash da senha...")
    
    # Hash conhecido para 'admin123'
    known_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iQeO"
    password = "admin123"
    
    try:
        # Testar se o hash está correto
        is_valid = bcrypt.checkpw(password.encode(), known_hash.encode())
        print(f"   Hash válido para 'admin123': {is_valid}")
        
        if is_valid:
            print("   ✅ Hash da senha está correto")
        else:
            print("   ❌ Hash da senha está incorreto")
            
        # Gerar um novo hash para comparação
        new_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        print(f"   Novo hash gerado: {new_hash}")
        
        return is_valid
        
    except Exception as e:
        print(f"   ❌ Erro ao testar hash: {e}")
        return False

def test_backend_health():
    """Testa a saúde do backend"""
    print("\n🔍 Testando saúde do backend...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/healthz", timeout=5)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"   Saúde: {health_data}")
            return True
        else:
            print(f"   ❌ Backend não está saudável: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro ao verificar saúde: {e}")
        return False

def test_database_connection():
    """Testa a conexão com o banco de dados"""
    print("\n🔍 Testando conexão com banco...")
    
    try:
        # Tentar acessar a documentação da API
        response = requests.get(f"{BACKEND_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("   ✅ Backend está respondendo")
            
            # Tentar fazer uma requisição que acessa o banco
            # Vamos tentar o endpoint de login com dados inválidos para ver se chega no banco
            data = {
                'username': 'usuario_inexistente',
                'password': 'senha_qualquer'
            }
            
            headers = {
                'Origin': FRONTEND_URL,
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            
            response = requests.post(f"{BACKEND_URL}/auth/login", data=data, headers=headers, timeout=10)
            
            if response.status_code == 400:
                error_data = response.json()
                if "Invalid credentials" in error_data.get("detail", ""):
                    print("   ✅ Backend está acessando o banco (usuário não encontrado)")
                    return True
                else:
                    print(f"   ⚠️  Erro inesperado: {error_data}")
                    return False
            else:
                print(f"   ⚠️  Resposta inesperada: {response.status_code}")
                return False
                
        else:
            print(f"   ❌ Backend não está respondendo: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro ao testar banco: {e}")
        return False

def test_exact_credentials():
    """Testa as credenciais exatas"""
    print("\n🔍 Testando credenciais exatas...")
    
    # Testar com diferentes variações
    test_cases = [
        {"username": "admin", "password": "admin123"},
        {"username": " admin", "password": "admin123"},  # com espaço
        {"username": "admin ", "password": "admin123"},  # com espaço
        {"username": "Admin", "password": "admin123"},   # maiúscula
        {"username": "ADMIN", "password": "admin123"},   # maiúsculas
    ]
    
    headers = {
        'Origin': FRONTEND_URL,
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    for i, credentials in enumerate(test_cases, 1):
        print(f"   Teste {i}: username='{credentials['username']}'")
        
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
            else:
                print(f"      ❌ Erro: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"      ❌ Erro: {e}")
    
    return None

def main():
    print("🚀 Debug Completo - finaFlow")
    print("=" * 50)
    
    # Testar hash da senha
    hash_valid = test_password_hash()
    
    # Testar saúde do backend
    backend_healthy = test_backend_health()
    
    # Testar conexão com banco
    db_working = test_database_connection()
    
    # Testar credenciais
    working_credentials = test_exact_credentials()
    
    print("\n📊 Resumo:")
    print(f"   Hash válido: {hash_valid}")
    print(f"   Backend saudável: {backend_healthy}")
    print(f"   Banco funcionando: {db_working}")
    print(f"   Credenciais funcionais: {working_credentials is not None}")
    
    if working_credentials:
        print(f"\n🎉 Credenciais funcionais encontradas: {working_credentials}")
        print("\n📋 Use estas credenciais no frontend:")
        print(f"   Username: {working_credentials['username']}")
        print(f"   Senha: {working_credentials['password']}")
    else:
        print("\n❌ Nenhuma credencial funcionou")
        print("\n📋 Próximos passos:")
        print("   1. Verifique se o usuário existe no BigQuery")
        print("   2. Verifique se o hash está correto")
        print("   3. Verifique se não há espaços extras no username")
        print("   4. Recrie o usuário no BigQuery")

if __name__ == "__main__":
    main()
