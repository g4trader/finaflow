#!/usr/bin/env python3
"""
Script para testar se o login está funcionando após a correção do formato de dados
"""

import requests
import time

# Configurações
BACKEND_URL = "https://finaflow-backend-609095880025.us-central1.run.app"
FRONTEND_URL = "https://finaflow.vercel.app"

def test_login_format():
    """Testa o login com o formato correto de dados"""
    print("🔐 Testando login com formato correto...")
    
    # Dados no formato application/x-www-form-urlencoded
    data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    headers = {
        'Origin': FRONTEND_URL,
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/auth/login", data=data, headers=headers, timeout=10)
        
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Login funcionando!")
            print(f"   Token: {result.get('access_token', '')[:50]}...")
            return True
        elif response.status_code == 400:
            print("⚠️  Login falhou (credenciais incorretas)")
            print(f"   Resposta: {response.text}")
            return False
        elif response.status_code == 422:
            print("❌ Erro 422: Formato de dados incorreto")
            print(f"   Resposta: {response.text}")
            return False
        else:
            print(f"❌ Erro inesperado: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar login: {e}")
        return False

def wait_for_frontend_deploy():
    """Aguarda o deploy do frontend"""
    print("⏳ Aguardando deploy do frontend...")
    print("   (O deploy do Vercel pode levar alguns minutos)")
    print("=" * 50)
    
    max_attempts = 30  # 5 minutos (10 segundos cada)
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        print(f"   Tentativa {attempt}/{max_attempts}...")
        
        if test_login_format():
            print("\n🎉 Login funcionando corretamente!")
            print("\n📋 Agora você pode:")
            print("   1. Acessar: https://finaflow.vercel.app/login")
            print("   2. Fazer login com: admin / admin123")
            print("   3. Criar o usuário super admin no BigQuery (se necessário)")
            return True
        else:
            print("   ❌ Login ainda não está funcionando")
            if attempt < max_attempts:
                print("   ⏳ Aguardando 10 segundos...")
                time.sleep(10)
    
    print("\n❌ Timeout: Login não funcionou após 5 minutos")
    print("\n📋 Verifique:")
    print("   1. Se o Vercel fez o deploy")
    print("   2. Se o usuário super admin existe no BigQuery")
    print("   3. Se as credenciais estão corretas")
    return False

def main():
    print("🚀 Teste de Login - finaFlow")
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
    
    # Aguardar deploy e testar login
    wait_for_frontend_deploy()

if __name__ == "__main__":
    main()
