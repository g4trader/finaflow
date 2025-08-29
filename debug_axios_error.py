#!/usr/bin/env python3
"""
Script para diagnosticar o erro do Axios e verificar se o deploy foi aplicado
"""

import requests
import time
import json

def check_frontend_deploy():
    """Verifica se o deploy do frontend foi aplicado"""
    print("🔍 Verificando se o deploy do frontend foi aplicado...")
    
    try:
        # Verificar se o frontend está usando HTTPS
        response = requests.get("https://finaflow.vercel.app", timeout=10)
        
        if response.status_code == 200:
            print("✅ Frontend acessível")
            
            # Procurar por URLs HTTP no código fonte
            content = response.text
            
            # Verificar se ainda há URLs HTTP
            http_urls = []
            if 'http://finaflow-backend' in content:
                http_urls.append('http://finaflow-backend')
            
            if http_urls:
                print(f"❌ AINDA ENCONTRADAS URLs HTTP: {http_urls}")
                return False
            else:
                print("✅ Nenhuma URL HTTP encontrada no código fonte")
                return True
        else:
            print(f"❌ Frontend não acessível: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao verificar frontend: {e}")
        return False

def test_backend_endpoints():
    """Testa os endpoints do backend"""
    print("\n🔍 Testando endpoints do backend...")
    
    base_url = "https://finaflow-backend-609095880025.us-central1.run.app"
    endpoints = [
        "/healthz",
        "/debug/config",
        "/debug/routes-info"
    ]
    
    for endpoint in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            response = requests.get(url, timeout=10)
            print(f"✅ {endpoint}: {response.status_code}")
            if response.status_code == 200:
                print(f"   Resposta: {response.text[:100]}...")
        except Exception as e:
            print(f"❌ {endpoint}: {e}")

def test_transactions_endpoint():
    """Testa especificamente o endpoint de transações"""
    print("\n🔍 Testando endpoint de transações...")
    
    base_url = "https://finaflow-backend-609095880025.us-central1.run.app"
    
    # Teste sem autenticação (deve retornar 401)
    try:
        response = requests.get(f"{base_url}/transactions", timeout=10)
        print(f"✅ /transactions (sem auth): {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Endpoint protegido corretamente")
        else:
            print(f"   ⚠️ Resposta inesperada: {response.text[:100]}...")
    except Exception as e:
        print(f"❌ /transactions (sem auth): {e}")

def check_environment_variables():
    """Verifica se as variáveis de ambiente estão corretas"""
    print("\n🔍 Verificando variáveis de ambiente...")
    
    try:
        # Tentar acessar uma página que pode revelar a configuração
        response = requests.get("https://finaflow.vercel.app/_next/static/chunks/pages/transactions-*.js", timeout=10)
        
        if response.status_code == 200:
            content = response.text
            
            # Procurar por configurações de API
            if 'NEXT_PUBLIC_API_URL' in content:
                print("✅ Variável NEXT_PUBLIC_API_URL encontrada no código")
            else:
                print("⚠️ Variável NEXT_PUBLIC_API_URL não encontrada no código")
                
            # Procurar por URLs HTTP
            if 'http://' in content:
                print("❌ URLs HTTP ainda presentes no código compilado")
            else:
                print("✅ Nenhuma URL HTTP encontrada no código compilado")
        else:
            print(f"⚠️ Não foi possível acessar o código compilado: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro ao verificar código compilado: {e}")

def main():
    """Função principal"""
    print("🎯 DIAGNÓSTICO COMPLETO DO ERRO AXIOS")
    print("=" * 50)
    
    # 1. Verificar se o deploy foi aplicado
    deploy_ok = check_frontend_deploy()
    
    # 2. Testar backend
    test_backend_endpoints()
    
    # 3. Testar endpoint específico
    test_transactions_endpoint()
    
    # 4. Verificar variáveis de ambiente
    check_environment_variables()
    
    print("\n" + "=" * 50)
    print("📋 RESUMO:")
    
    if deploy_ok:
        print("✅ Deploy do frontend foi aplicado")
        print("🔧 Próximo passo: Testar no navegador")
    else:
        print("❌ Deploy do frontend ainda não foi aplicado")
        print("⏳ Aguarde mais alguns minutos e teste novamente")
    
    print("\n💡 SOLUÇÕES POSSÍVEIS:")
    print("1. Aguardar o deploy do Vercel (2-3 minutos)")
    print("2. Limpar cache do navegador (Ctrl+F5)")
    print("3. Testar em aba anônima")
    print("4. Verificar se o token de autenticação está válido")

if __name__ == "__main__":
    main()
