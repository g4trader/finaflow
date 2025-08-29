#!/usr/bin/env python3
"""
Script para debugar especificamente o middleware
"""

import requests
import time

def test_middleware():
    """Testa se o middleware está funcionando"""
    base_url = "https://finaflow.vercel.app"
    
    print("🔍 DEBUGANDO MIDDLEWARE")
    print("=" * 50)
    
    # Teste 1: Verificar se o middleware está sendo carregado
    print("\n1️⃣ Verificando se middleware está carregado...")
    
    try:
        # Fazer request para uma rota protegida
        response = requests.get(f"{base_url}/dashboard", allow_redirects=False)
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 302:
            print("   ✅ Middleware está redirecionando!")
            print(f"   Location: {response.headers.get('Location', 'N/A')}")
        elif response.status_code == 200:
            print("   ❌ Middleware não está redirecionando")
        else:
            print(f"   ⚠️ Status inesperado: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Teste 2: Verificar se há cookies
    print("\n2️⃣ Verificando cookies...")
    
    try:
        session = requests.Session()
        response = session.get(f"{base_url}/login")
        print(f"   Cookies da sessão: {dict(session.cookies)}")
        
        # Tentar acessar dashboard
        response = session.get(f"{base_url}/dashboard", allow_redirects=False)
        print(f"   Status após tentativa: {response.status_code}")
        
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Teste 3: Verificar se o middleware está no build
    print("\n3️⃣ Verificando se middleware está no build...")
    
    try:
        # Verificar se há arquivos de middleware
        response = requests.get(f"{base_url}/_next/static/chunks/pages/middleware-*.js")
        print(f"   Status middleware chunks: {response.status_code}")
        
        # Verificar _next/webpack-hmr
        response = requests.get(f"{base_url}/_next/webpack-hmr")
        print(f"   Status webpack-hmr: {response.status_code}")
        
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Teste 4: Verificar se há erros no console
    print("\n4️⃣ Verificando se há erros...")
    
    try:
        response = requests.get(f"{base_url}/dashboard")
        if "error" in response.text.lower() or "exception" in response.text.lower():
            print("   ⚠️ Possíveis erros encontrados no HTML")
        else:
            print("   ✅ Sem erros aparentes no HTML")
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")

if __name__ == "__main__":
    test_middleware()
