#!/usr/bin/env python3
"""
Script para criar usuário via backend e testar
"""

import requests
import json

# Configurações
BACKEND_URL = "https://finaflow-backend-609095880025.us-central1.run.app"
FRONTEND_URL = "https://finaflow.vercel.app"

def create_user_via_backend():
    """Tenta criar um usuário via backend"""
    print("🔧 Tentando criar usuário via backend...")
    
    # Dados do usuário
    user_data = {
        "username": "admin2",
        "email": "admin2@finaflow.com",
        "password": "admin123",
        "role": "super_admin"
    }
    
    try:
        # Tentar criar via signup
        response = requests.post(f"{BACKEND_URL}/auth/signup", json=user_data, timeout=10)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print(f"   ✅ Usuário criado! ID: {result.get('id', '')}")
            return True
        elif response.status_code == 401:
            print("   ❌ Signup requer autenticação (esperado)")
            return False
        else:
            print(f"   ❌ Erro: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

def test_created_user():
    """Testa o login com o usuário criado"""
    print("\n🔐 Testando login com usuário criado...")
    
    credentials = {
        'username': 'admin2',
        'password': 'admin123'
    }
    
    headers = {
        'Origin': FRONTEND_URL,
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/auth/login", data=credentials, headers=headers, timeout=10)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Login funcionando! Token: {result.get('access_token', '')[:50]}...")
            return True
        elif response.status_code == 400:
            error_data = response.json()
            print(f"   ❌ Falhou: {error_data.get('detail', '')}")
            return False
        else:
            print(f"   ❌ Erro: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

def main():
    print("🚀 Criação de Usuário via Backend - finaFlow")
    print("=" * 50)
    
    # Tentar criar usuário
    user_created = create_user_via_backend()
    
    if user_created:
        # Testar login
        login_success = test_created_user()
        
        if login_success:
            print("\n🎉 Usuário criado e login funcionando!")
            print("\n📋 Credenciais funcionais:")
            print("   Username: admin2")
            print("   Senha: admin123")
            print("\n🌐 Teste no frontend: https://finaflow.vercel.app/login")
        else:
            print("\n❌ Usuário criado mas login falhou")
    else:
        print("\n❌ Não foi possível criar usuário via API")
        print("\n📋 O problema é que:")
        print("   1. O endpoint /auth/signup requer autenticação de super admin")
        print("   2. Não temos um super admin para criar outros usuários")
        print("   3. Precisamos criar o usuário diretamente no BigQuery")
        
        print("\n🔧 Solução:")
        print("   1. Execute a query no BigQuery (que já forneci)")
        print("   2. Ou me forneça um token de super admin para criar via API")

if __name__ == "__main__":
    main()
