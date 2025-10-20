#!/usr/bin/env python3
"""
Script para criar o usuário super admin diretamente no BigQuery
"""

import requests
import json
import sys
from uuid import uuid4
from datetime import datetime

# Configurações
BACKEND_URL = "https://finaflow-backend-609095880025.us-central1.run.app"
SUPER_ADMIN_USERNAME = "admin"
SUPER_ADMIN_EMAIL = "admin@finaflow.com"
SUPER_ADMIN_PASSWORD = "admin123"

def test_login():
    """Testa o login com as credenciais do super admin"""
    print("🔐 Testando login...")
    
    login_data = {
        "username": SUPER_ADMIN_USERNAME,
        "password": SUPER_ADMIN_PASSWORD
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/auth/login", data=login_data, timeout=10)
        
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

def create_user_via_direct_endpoint():
    """Tenta criar o usuário via um endpoint direto (se existir)"""
    print("🔧 Tentando criar usuário via endpoint direto...")
    
    user_data = {
        "username": SUPER_ADMIN_USERNAME,
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PASSWORD,
        "role": "super_admin"
    }
    
    try:
        # Tentar endpoint de setup/init (pode existir para primeira configuração)
        response = requests.post(f"{BACKEND_URL}/auth/setup", json=user_data, timeout=10)
        
        if response.status_code == 201:
            print("✅ Usuário criado via endpoint de setup!")
            return True
        else:
            print(f"❌ Endpoint /auth/setup não disponível: {response.status_code}")
            
        # Tentar endpoint de init
        response = requests.post(f"{BACKEND_URL}/auth/init", json=user_data, timeout=10)
        
        if response.status_code == 201:
            print("✅ Usuário criado via endpoint de init!")
            return True
        else:
            print(f"❌ Endpoint /auth/init não disponível: {response.status_code}")
            
        return False
            
    except Exception as e:
        print(f"❌ Erro ao tentar endpoints diretos: {e}")
        return False

def main():
    print("🚀 Script de Criação do Super Admin - BigQuery")
    print("=" * 50)
    
    # Testar se o backend está funcionando
    try:
        response = requests.get(f"{BACKEND_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Backend está funcionando")
        else:
            print(f"❌ Backend não está funcionando: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Erro ao conectar ao backend: {e}")
        return
    
    # Tentar criar via endpoints diretos
    if create_user_via_direct_endpoint():
        # Testar login
        token = test_login()
        if token:
            print("\n🎉 Super Admin configurado com sucesso!")
            print("\n📋 Credenciais para acesso:")
            print(f"   Username: {SUPER_ADMIN_USERNAME}")
            print(f"   Email: {SUPER_ADMIN_EMAIL}")
            print(f"   Senha: {SUPER_ADMIN_PASSWORD}")
            print("\n🌐 Acesse: https://finaflow.vercel.app/login")
            print("   Use o username para fazer login")
            return
    
    # Se não conseguiu criar via API, fornecer instruções para BigQuery
    print("\n❌ Não foi possível criar o usuário via API")
    print("\n📋 Para criar manualmente no BigQuery:")
    print("\n1. Acesse o Google Cloud Console:")
    print("   https://console.cloud.google.com")
    print("\n2. Vá para BigQuery > SQL Workspace")
    print("\n3. Execute esta query:")
    print("=" * 60)
    print("""
INSERT INTO `trivihair.finaflow.Users` 
(id, username, email, hashed_password, role, tenant_id, created_at)
VALUES 
(
  GENERATE_UUID(),
  'admin',
  'admin@finaflow.com',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iQeO',
  'super_admin',
  NULL,
  CURRENT_TIMESTAMP()
)
""")
    print("=" * 60)
    print("\n4. Depois teste o login com:")
    print(f"   Username: {SUPER_ADMIN_USERNAME}")
    print(f"   Senha: {SUPER_ADMIN_PASSWORD}")

if __name__ == "__main__":
    main()
