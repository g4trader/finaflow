#!/usr/bin/env python3
"""
Script para aguardar o deploy do backend e testar CORS
"""

import requests
import time
import sys

# Configurações
BACKEND_URL = "https://finaflow-backend-609095880025.us-central1.run.app"
FRONTEND_URL = "https://finaflow.vercel.app"

def test_cors():
    """Testa se o CORS está funcionando"""
    try:
        headers = {
            'Origin': FRONTEND_URL,
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type',
        }
        
        response = requests.options(f"{BACKEND_URL}/auth/login", headers=headers, timeout=5)
        
        if response.status_code == 200:
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            if cors_origin and FRONTEND_URL in cors_origin:
                return True
        return False
        
    except:
        return False

def main():
    print("⏳ Aguardando deploy do backend...")
    print("   (O deploy automático pode levar alguns minutos)")
    print("=" * 50)
    
    max_attempts = 30  # 5 minutos (10 segundos cada)
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        print(f"   Tentativa {attempt}/{max_attempts}...")
        
        if test_cors():
            print("\n🎉 CORS configurado com sucesso!")
            print("\n📋 Agora você pode:")
            print("   1. Acessar: https://finaflow.vercel.app/login")
            print("   2. Fazer login com: admin / admin123")
            print("   3. Criar o usuário super admin no BigQuery (se necessário)")
            return True
        else:
            print("   ❌ CORS ainda não está funcionando")
            if attempt < max_attempts:
                print("   ⏳ Aguardando 10 segundos...")
                time.sleep(10)
    
    print("\n❌ Timeout: CORS não foi configurado após 5 minutos")
    print("\n📋 Verifique:")
    print("   1. Se o Google Cloud Build está funcionando")
    print("   2. Se há erros no deploy")
    print("   3. Se o Cloud Run foi atualizado")
    return False

if __name__ == "__main__":
    main()
