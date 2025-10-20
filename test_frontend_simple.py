"""
Teste simples do frontend sem Selenium
"""

import requests
import time

def test_frontend_pages():
    """Testar se as páginas do frontend estão carregando"""
    
    print("🧪 TESTE SIMPLES DO FRONTEND")
    print("=" * 40)
    
    base_url = "http://localhost:3000"
    
    # Páginas para testar
    pages = [
        "/",
        "/login", 
        "/signup",
        "/dashboard"
    ]
    
    for page in pages:
        try:
            print(f"🔍 Testando: {page}")
            response = requests.get(f"{base_url}{page}", timeout=10)
            
            if response.status_code == 200:
                content = response.text
                
                # Verificar se é apenas a tela de loading
                if "Carregando..." in content and "animate-spin" in content:
                    print(f"  ❌ {page}: Apenas tela de loading (não carregou)")
                elif "FinaFlow" in content or "login" in content.lower():
                    print(f"  ✅ {page}: Conteúdo carregado")
                else:
                    print(f"  ⚠️  {page}: Carregou mas conteúdo inesperado")
                    
                # Verificar tamanho da resposta
                print(f"  📊 Tamanho: {len(content)} bytes")
                
            else:
                print(f"  ❌ {page}: Status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ {page}: Erro de conexão - {e}")
        
        time.sleep(1)
    
    print("\n" + "=" * 40)

def test_backend_endpoints():
    """Testar endpoints do backend"""
    
    print("🔧 TESTE DO BACKEND")
    print("=" * 40)
    
    base_url = "http://127.0.0.1:8000"
    
    endpoints = [
        "/",
        "/health",
        "/docs",
        "/api/v1/import/google-sheets/sample"
    ]
    
    for endpoint in endpoints:
        try:
            print(f"🔍 Testando: {endpoint}")
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                print(f"  ✅ {endpoint}: OK")
            else:
                print(f"  ❌ {endpoint}: Status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ {endpoint}: Erro - {e}")

if __name__ == "__main__":
    test_backend_endpoints()
    print()
    test_frontend_pages()







