#!/usr/bin/env python3
"""
Script para verificar e corrigir a configuração do Vercel
"""

import requests
import json

def check_vercel_config():
    """Verifica a configuração atual do Vercel"""
    print("🔍 Verificando configuração do Vercel...")
    
    # Testar o frontend para ver qual URL está sendo usada
    try:
        response = requests.get("https://finaflow.vercel.app", timeout=10)
        print("✅ Frontend acessível")
        
        # Verificar se há requisições HTTP sendo feitas
        print("🔍 Verificando se há requisições HTTP...")
        
        # Simular uma requisição que o frontend faria
        test_url = "http://finaflow-backend-609095880025.us-central1.run.app/healthz"
        try:
            response = requests.get(test_url, timeout=5)
            print(f"❌ REQUISIÇÃO HTTP FUNCIONANDO: {test_url}")
            print("   Isso indica que NEXT_PUBLIC_API_URL está configurado como HTTP")
        except:
            print("✅ Requisições HTTP não estão funcionando (bom!)")
        
        # Testar HTTPS
        test_url_https = "https://finaflow-backend-609095880025.us-central1.run.app/healthz"
        try:
            response = requests.get(test_url_https, timeout=5)
            print(f"✅ REQUISIÇÃO HTTPS FUNCIONANDO: {test_url_https}")
        except Exception as e:
            print(f"❌ Requisição HTTPS falhou: {e}")
            
    except Exception as e:
        print(f"❌ Erro ao acessar frontend: {e}")

def provide_solution():
    """Fornece a solução para o problema"""
    print("\n🔧 SOLUÇÃO PARA O PROBLEMA:")
    print("=" * 50)
    print("O problema é que NEXT_PUBLIC_API_URL está configurado como HTTP em vez de HTTPS")
    print("\n📋 PASSOS PARA CORRIGIR:")
    print("1. Acesse: https://vercel.com/dashboard")
    print("2. Clique no projeto 'finaflow'")
    print("3. Vá em 'Settings' > 'Environment Variables'")
    print("4. Encontre a variável 'NEXT_PUBLIC_API_URL'")
    print("5. Altere o valor de:")
    print("   ❌ http://finaflow-backend-609095880025.us-central1.run.app")
    print("   ✅ https://finaflow-backend-609095880025.us-central1.run.app")
    print("6. Clique em 'Save'")
    print("7. Vá em 'Deployments' e faça 'Redeploy'")
    print("\n🎯 URL CORRETA:")
    print("https://finaflow-backend-609095880025.us-central1.run.app")

def main():
    print("🚀 Verificação da Configuração do Vercel - finaFlow")
    print("=" * 60)
    
    check_vercel_config()
    provide_solution()
    
    print("\n✅ Após corrigir, o sistema deve funcionar perfeitamente!")

if __name__ == "__main__":
    main()
