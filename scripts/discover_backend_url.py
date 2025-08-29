#!/usr/bin/env python3
"""
Script para descobrir a URL do backend através do frontend
"""

import requests
import json
import re

def discover_backend_url():
    """Tenta descobrir a URL do backend através do frontend"""
    print("🔍 Descobrindo URL do backend...")
    
    frontend_url = "https://finaflow.vercel.app"
    
    try:
        # Tentar acessar o frontend
        print(f"   Acessando: {frontend_url}")
        response = requests.get(frontend_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Frontend acessível")
            
            # Procurar por URLs de API no código fonte
            content = response.text
            
            # Padrões comuns para URLs de API
            patterns = [
                r'https://[^"\']*\.a\.run\.app',  # Google Cloud Run
                r'https://[^"\']*\.vercel\.app',  # Vercel
                r'https://api\.[^"\']*',          # Subdomínio api
                r'https://[^"\']*\.com/api',      # Domínio com /api
            ]
            
            found_urls = []
            for pattern in patterns:
                matches = re.findall(pattern, content)
                found_urls.extend(matches)
            
            if found_urls:
                print("✅ URLs encontradas no frontend:")
                for url in set(found_urls):
                    print(f"   - {url}")
                return found_urls
            else:
                print("❌ Nenhuma URL de API encontrada no código fonte")
                return []
                
        else:
            print(f"❌ Frontend não acessível: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Erro ao acessar frontend: {e}")
        return []

def test_backend_urls(urls):
    """Testa as URLs encontradas"""
    print("\n🔧 Testando URLs do backend...")
    
    working_urls = []
    for url in urls:
        try:
            print(f"   Testando: {url}")
            
            # Tentar acessar a documentação da API
            response = requests.get(f"{url}/docs", timeout=5)
            if response.status_code == 200:
                print(f"✅ Backend funcionando em: {url}")
                working_urls.append(url)
            else:
                print(f"   ❌ Status: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Erro: {str(e)[:50]}...")
            continue
    
    return working_urls

def main():
    print("🚀 Script de Descoberta do Backend - finaFlow")
    print("=" * 50)
    
    # Descobrir URLs
    urls = discover_backend_url()
    
    if not urls:
        print("\n❌ Não foi possível descobrir URLs do backend")
        print("\n📋 URLs comuns para testar:")
        print("   - https://finaflow-backend-xxxxx-uc.a.run.app")
        print("   - https://api.finaflow.com")
        print("   - https://finaflow-api.vercel.app")
        return
    
    # Testar URLs
    working_urls = test_backend_urls(urls)
    
    if working_urls:
        print(f"\n🎉 Backend encontrado em: {working_urls[0]}")
        print("\n📋 Use esta URL no script de criação do super admin")
    else:
        print("\n❌ Nenhuma URL do backend está funcionando")

if __name__ == "__main__":
    main()
