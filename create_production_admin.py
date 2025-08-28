#!/usr/bin/env python3
"""
Script para criar o usuário super admin no ambiente de produção do finaFlow
"""

import requests
import json
import sys
from uuid import uuid4

# Configurações - URLs de produção
PRODUCTION_URLS = [
    "https://finaflow-backend-609095880025.us-central1.run.app",  # Google Cloud Run (URL correta)
    "https://finaflow-backend.vercel.app",  # Possível URL do backend no Vercel
    "https://api.finaflow.com",             # Possível URL customizada
    "https://finaflow-api.vercel.app",      # Outra possibilidade
]

SUPER_ADMIN_USERNAME = "admin"
SUPER_ADMIN_EMAIL = "admin@finaflow.com"
SUPER_ADMIN_PASSWORD = "admin123"

def test_backend_urls():
    """Testa diferentes URLs possíveis do backend"""
    print("🔍 Testando URLs do backend...")
    
    for url in PRODUCTION_URLS:
        try:
            print(f"   Testando: {url}")
            response = requests.get(f"{url}/docs", timeout=5)
            if response.status_code == 200:
                print(f"✅ Backend encontrado em: {url}")
                return url
        except Exception as e:
            print(f"   ❌ {url}: {str(e)[:50]}...")
            continue
    
    print("❌ Não foi possível encontrar o backend de produção")
    return None

def create_super_admin_via_api(base_url):
    """Tenta criar o super admin via API"""
    print(f"🔧 Tentando criar super admin via API em {base_url}...")
    
    # Dados do usuário super admin
    user_data = {
        "username": SUPER_ADMIN_USERNAME,
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PASSWORD,
        "role": "super_admin"
    }
    
    try:
        # Tentar criar via endpoint de signup (pode não funcionar se precisar de autenticação)
        response = requests.post(f"{base_url}/auth/signup", json=user_data, timeout=10)
        
        if response.status_code == 201:
            print("✅ Super admin criado com sucesso via API!")
            return True
        elif response.status_code == 400:
            print(f"⚠️  Erro 400: {response.text}")
            return False
        elif response.status_code == 401:
            print("❌ Endpoint requer autenticação de super admin")
            return False
        else:
            print(f"❌ Erro {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao criar via API: {e}")
        return False

def test_login(base_url):
    """Testa o login com as credenciais do super admin"""
    print(f"🔐 Testando login em {base_url}...")
    
    login_data = {
        "username": SUPER_ADMIN_USERNAME,
        "password": SUPER_ADMIN_PASSWORD
    }
    
    try:
        response = requests.post(f"{base_url}/auth/login", data=login_data, timeout=10)
        
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
    print("🚀 Script de Criação do Super Admin - Produção")
    print("=" * 50)
    
    # Testar URLs do backend
    base_url = test_backend_urls()
    
    if not base_url:
        print("\n❌ Não foi possível conectar ao backend de produção")
        print("\n📋 Opções para resolver:")
        print("   1. Verificar se o backend está deployado no Google Cloud Run")
        print("   2. Verificar a URL correta do backend")
        print("   3. Criar o usuário manualmente no banco de dados")
        print("\n🔧 Credenciais para criar manualmente:")
        print(f"   Username: {SUPER_ADMIN_USERNAME}")
        print(f"   Email: {SUPER_ADMIN_EMAIL}")
        print(f"   Senha: {SUPER_ADMIN_PASSWORD}")
        print(f"   Role: super_admin")
        return
    
    # Tentar criar super admin
    if create_super_admin_via_api(base_url):
        # Testar login
        token = test_login(base_url)
        if token:
            print("\n🎉 Super Admin configurado com sucesso!")
            print("\n📋 Credenciais para acesso:")
            print(f"   Username: {SUPER_ADMIN_USERNAME}")
            print(f"   Email: {SUPER_ADMIN_EMAIL}")
            print(f"   Senha: {SUPER_ADMIN_PASSWORD}")
            print("\n🌐 Acesse: https://finaflow.vercel.app/login")
            print("   Use o username para fazer login")
        else:
            print("\n❌ Falha ao fazer login com o super admin")
    else:
        print("\n❌ Não foi possível criar o super admin via API")
        print("\n📋 Para criar manualmente, use estas credenciais:")
        print(f"   Username: {SUPER_ADMIN_USERNAME}")
        print(f"   Email: {SUPER_ADMIN_EMAIL}")
        print(f"   Senha: {SUPER_ADMIN_PASSWORD}")
        print(f"   Role: super_admin")

if __name__ == "__main__":
    main()
