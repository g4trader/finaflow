#!/usr/bin/env python3
"""
Teste simples com curl para verificar proteção de rotas
"""

import requests
import time

def test_route_protection():
    """Testa proteção de rotas com requests"""
    base_url = "https://finaflow.vercel.app"
    
    print("🔍 TESTE SIMPLES DE PROTEÇÃO DE ROTAS")
    print("=" * 50)
    
    # Teste 1: Dashboard sem autenticação
    print("\n1️⃣ Testando dashboard sem autenticação...")
    try:
        response = requests.get(f"{base_url}/dashboard", allow_redirects=False)
        print(f"   Status: {response.status_code}")
        print(f"   URL final: {response.url}")
        
        if response.status_code == 302:
            print("   ✅ Redirecionamento detectado!")
            print(f"   Location: {response.headers.get('Location', 'N/A')}")
        elif response.status_code == 200:
            print("   ❌ Página carregou sem redirecionamento")
        else:
            print(f"   ⚠️ Status inesperado: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Teste 2: Outras rotas protegidas
    print("\n2️⃣ Testando outras rotas protegidas...")
    protected_routes = ["/accounts", "/transactions", "/users"]
    
    for route in protected_routes:
        try:
            response = requests.get(f"{base_url}{route}", allow_redirects=False)
            print(f"   {route}: {response.status_code}")
            
            if response.status_code == 302:
                print(f"   ✅ {route} redirecionando")
            elif response.status_code == 200:
                print(f"   ❌ {route} acessível sem autenticação")
            else:
                print(f"   ⚠️ {route} status {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Erro em {route}: {e}")
    
    # Teste 3: Verificar se há JavaScript de redirecionamento
    print("\n3️⃣ Verificando JavaScript de redirecionamento...")
    try:
        response = requests.get(f"{base_url}/dashboard")
        content = response.text.lower()
        
        if "router.push" in content or "router.replace" in content:
            print("   ✅ JavaScript de redirecionamento encontrado")
        elif "login" in content:
            print("   ✅ Referência a login encontrada")
        else:
            print("   ❌ Nenhum redirecionamento JavaScript encontrado")
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Teste 4: Verificar se há loading states
    print("\n4️⃣ Verificando loading states...")
    try:
        response = requests.get(f"{base_url}/dashboard")
        content = response.text.lower()
        
        if "carregando" in content or "loading" in content:
            print("   ✅ Loading states encontrados")
        else:
            print("   ❌ Loading states não encontrados")
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")

if __name__ == "__main__":
    test_route_protection()
