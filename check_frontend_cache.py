#!/usr/bin/env python3
"""
Script para verificar se o frontend está usando a URL correta
"""

import requests
import re

def check_frontend_url():
    """Verifica se o frontend está usando a URL correta"""
    print("🔍 Verificando configuração do frontend...")
    
    try:
        # Acessar o frontend
        response = requests.get("https://finaflow.vercel.app", timeout=10)
        
        if response.status_code == 200:
            print("✅ Frontend acessível")
            
            # Procurar por URLs de API no código fonte
            content = response.text
            
            # Padrões para URLs de API
            http_patterns = [
                r'http://finaflow-backend-609095880025\.us-central1\.run\.app',
                r'http://[^"\']*\.a\.run\.app',
            ]
            
            https_patterns = [
                r'https://finaflow-backend-609095880025\.us-central1\.run\.app',
                r'https://[^"\']*\.a\.run\.app',
            ]
            
            # Verificar URLs HTTP (problemáticas)
            http_urls = []
            for pattern in http_patterns:
                matches = re.findall(pattern, content)
                http_urls.extend(matches)
            
            # Verificar URLs HTTPS (corretas)
            https_urls = []
            for pattern in https_patterns:
                matches = re.findall(pattern, content)
                https_urls.extend(matches)
            
            print(f"\n📊 Resultado da análise:")
            print(f"   URLs HTTP encontradas: {len(http_urls)}")
            print(f"   URLs HTTPS encontradas: {len(https_urls)}")
            
            if http_urls:
                print(f"   ❌ PROBLEMA: URLs HTTP encontradas:")
                for url in set(http_urls):
                    print(f"      - {url}")
                print(f"   💡 SOLUÇÃO: Forçar redeploy do frontend no Vercel")
                return False
            elif https_urls:
                print(f"   ✅ URLs HTTPS encontradas:")
                for url in set(https_urls):
                    print(f"      - {url}")
                print(f"   ✅ Configuração parece correta")
                return True
            else:
                print(f"   ⚠️  Nenhuma URL de API encontrada no código fonte")
                return True
                
        else:
            print(f"❌ Frontend não acessível: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao acessar frontend: {e}")
        return False

def provide_solution():
    """Fornece a solução para o problema"""
    print("\n🔧 SOLUÇÃO PARA O PROBLEMA:")
    print("=" * 50)
    print("O frontend está usando uma versão em cache com URLs HTTP")
    print("\n📋 PASSOS PARA CORRIGIR:")
    print("1. Acesse: https://vercel.com/dashboard")
    print("2. Clique no projeto 'finaflow'")
    print("3. Vá em 'Deployments'")
    print("4. Clique em 'Redeploy' no último deployment")
    print("5. Aguarde o deploy completar")
    print("6. Teste novamente no navegador")
    print("\n🔄 Alternativa - Commit vazio:")
    print("git commit --allow-empty -m 'force redeploy'")
    print("git push origin main")

def main():
    print("🚀 Verificação do Frontend - finaFlow")
    print("=" * 50)
    
    is_correct = check_frontend_url()
    provide_solution()
    
    if not is_correct:
        print("\n❌ PROBLEMA CONFIRMADO: Frontend usando URLs HTTP")
        print("   Execute os passos acima para corrigir")
    else:
        print("\n✅ Frontend parece estar configurado corretamente")

if __name__ == "__main__":
    main()
