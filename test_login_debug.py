"""
Debug detalhado do problema de login
"""

import requests
import time
import json

def test_login_flow():
    """Testar todo o fluxo de login"""
    
    print("🔍 DEBUG DETALHADO DO LOGIN")
    print("=" * 50)
    
    # 1. Testar se o frontend está carregando a página de login
    print("1. 🌐 Testando carregamento da página de login...")
    try:
        response = requests.get("http://localhost:3000/login", timeout=10)
        if response.status_code == 200:
            content = response.text
            
            # Verificar se não é apenas loading
            if "Carregando..." in content and "animate-spin" in content:
                print("   ❌ Página ainda mostrando apenas 'Carregando...'")
                return False
            elif "username" in content.lower() or "email" in content.lower():
                print("   ✅ Página de login carregada corretamente")
            else:
                print("   ⚠️  Página carregou mas conteúdo inesperado")
                print(f"   📄 Primeiros 500 chars: {content[:500]}")
                
        else:
            print(f"   ❌ Erro HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro ao acessar página: {e}")
        return False
    
    # 2. Testar se o backend está respondendo
    print("\n2. 🔧 Testando backend...")
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Backend respondendo")
        else:
            print(f"   ❌ Backend com problema: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Backend inacessível: {e}")
        return False
    
    # 3. Testar login via API
    print("\n3. 🔐 Testando login via API...")
    try:
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        response = requests.post(
            'http://127.0.0.1:8000/api/v1/auth/login',
            data=login_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            print("   ✅ Login via API funcionando")
            print(f"   🎫 Token recebido: {token[:20] if token else 'N/A'}...")
            
            # 4. Testar se o token é válido
            print("\n4. 🎫 Testando validade do token...")
            headers = {'Authorization': f'Bearer {token}'}
            test_response = requests.get(
                'http://127.0.0.1:8000/api/v1/auth/me',
                headers=headers,
                timeout=10
            )
            
            if test_response.status_code == 200:
                user_data = test_response.json()
                print("   ✅ Token válido")
                print(f"   👤 Usuário: {user_data.get('username', 'N/A')}")
                return True
            else:
                print(f"   ❌ Token inválido: {test_response.status_code}")
                return False
                
        else:
            print(f"   ❌ Login API falhou: {response.status_code}")
            print(f"   📄 Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro no login API: {e}")
        return False

def test_frontend_config():
    """Testar configuração do frontend"""
    
    print("\n5. ⚙️  Testando configuração do frontend...")
    
    # Verificar se há arquivo .env
    import os
    env_file = "/Users/lucianoterres/Documents/GitHub/finaflow/frontend/.env.local"
    if os.path.exists(env_file):
        print("   ✅ Arquivo .env.local encontrado")
        with open(env_file, 'r') as f:
            content = f.read()
            if "BACKEND_URL" in content:
                print("   ✅ BACKEND_URL configurado")
            else:
                print("   ⚠️  BACKEND_URL não encontrado no .env.local")
    else:
        print("   ❌ Arquivo .env.local não encontrado")
    
    # Verificar se o frontend está usando a URL correta do backend
    try:
        # Testar se o frontend consegue acessar o backend
        response = requests.get("http://localhost:3000/api/health", timeout=5)
        print(f"   📊 Frontend proxy status: {response.status_code}")
    except:
        print("   ⚠️  Frontend não tem proxy configurado (normal)")

def check_browser_console_errors():
    """Simular verificação de erros do console"""
    
    print("\n6. 🔍 Possíveis problemas no frontend:")
    print("   • Verificar se há erros no console do browser (F12)")
    print("   • Verificar se o AuthContext está carregando corretamente")
    print("   • Verificar se há problemas de CORS")
    print("   • Verificar se o localStorage está sendo usado")
    print("   • Verificar se o JWT está sendo decodificado corretamente")

if __name__ == "__main__":
    success = test_login_flow()
    test_frontend_config()
    check_browser_console_errors()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 BACKEND FUNCIONANDO PERFEITAMENTE")
        print("❌ PROBLEMA ESTÁ NO FRONTEND")
        print("\n💡 PRÓXIMOS PASSOS:")
        print("1. Abrir http://localhost:3000/login no browser")
        print("2. Pressionar F12 para abrir DevTools")
        print("3. Ir na aba Console para ver erros")
        print("4. Tentar fazer login e ver onde falha")
        print("5. Verificar se há erros de JavaScript")
    else:
        print("❌ PROBLEMA NO BACKEND OU CONEXÃO")
        print("🔧 Verificar se o backend está rodando corretamente")







