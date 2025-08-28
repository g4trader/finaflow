#!/usr/bin/env python3
"""
Script para criar o usuário super admin no sistema finaFlow
"""

import requests
import json
import sys
from uuid import uuid4

# Configurações
BASE_URL = "http://localhost:8000"  # Altere para a URL do seu backend
SUPER_ADMIN_USERNAME = "admin"
SUPER_ADMIN_EMAIL = "admin@finaflow.com"
SUPER_ADMIN_PASSWORD = "admin123"

def create_super_admin():
    """Cria o usuário super admin diretamente no banco de dados"""
    print("🔧 Criando usuário Super Admin...")
    
    # Dados do usuário super admin
    user_data = {
        "id": str(uuid4()),
        "username": SUPER_ADMIN_USERNAME,
        "email": SUPER_ADMIN_EMAIL,
        "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iQeO",  # admin123
        "role": "super_admin",
        "tenant_id": None
    }
    
    try:
        # Tentar fazer login primeiro para verificar se o usuário já existe
        login_data = {
            "username": SUPER_ADMIN_USERNAME,
            "password": SUPER_ADMIN_PASSWORD
        }
        
        response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
        
        if response.status_code == 200:
            print("✅ Usuário super admin já existe!")
            print(f"   Username: {SUPER_ADMIN_USERNAME}")
            print(f"   Email: {SUPER_ADMIN_EMAIL}")
            print(f"   Senha: {SUPER_ADMIN_PASSWORD}")
            return True
        else:
            print("❌ Usuário não encontrado. Criando...")
            
            # Como não há endpoint público para criar super admin, vamos usar uma abordagem alternativa
            # Você precisará criar o usuário manualmente no banco de dados ou usar um endpoint de setup
            
            print("⚠️  Para criar o super admin, você tem algumas opções:")
            print("   1. Execute o script de setup do banco de dados")
            print("   2. Crie o usuário diretamente no BigQuery")
            print("   3. Use o endpoint de signup (se disponível)")
            
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Erro: Não foi possível conectar ao backend em {BASE_URL}")
        print("   Certifique-se de que o servidor está rodando")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def test_login():
    """Testa o login com as credenciais do super admin"""
    print("\n🔐 Testando login...")
    
    login_data = {
        "username": SUPER_ADMIN_USERNAME,
        "password": SUPER_ADMIN_PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("✅ Login realizado com sucesso!")
            print(f"   Token: {token[:50]}...")
            return token
        else:
            print(f"❌ Falha no login: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao testar login: {e}")
        return None

def main():
    print("🚀 Script de Criação do Super Admin - finaFlow")
    print("=" * 50)
    
    # Testar se o backend está rodando
    try:
        response = requests.get(f"{BASE_URL}/docs")
        print("✅ Backend está rodando")
    except:
        print("❌ Backend não está rodando")
        print(f"   Certifique-se de que o servidor está rodando em {BASE_URL}")
        return
    
    # Criar super admin
    if create_super_admin():
        # Testar login
        token = test_login()
        if token:
            print("\n🎉 Super Admin configurado com sucesso!")
            print("\n📋 Credenciais para acesso:")
            print(f"   Username: {SUPER_ADMIN_USERNAME}")
            print(f"   Email: {SUPER_ADMIN_EMAIL}")
            print(f"   Senha: {SUPER_ADMIN_PASSWORD}")
            print("\n🌐 Acesse: https://finaflow.vercel.app/login")
            print("   Use o username (não email) para fazer login")
        else:
            print("\n❌ Falha ao fazer login com o super admin")
    else:
        print("\n❌ Não foi possível criar o super admin automaticamente")
        print("\n📋 Para criar manualmente, use estas credenciais:")
        print(f"   Username: {SUPER_ADMIN_USERNAME}")
        print(f"   Email: {SUPER_ADMIN_EMAIL}")
        print(f"   Senha: {SUPER_ADMIN_PASSWORD}")
        print(f"   Role: super_admin")

if __name__ == "__main__":
    main()
