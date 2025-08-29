#!/usr/bin/env python3
"""
Script para testar a decodificação do token JWT
"""

import requests
import json

# Configurações
API_URL = "https://finaflow-backend-609095880025.us-central1.run.app"

def test_token_decode():
    """Testa a decodificação do token JWT"""
    print("🔧 Testando decodificação do token...")
    
    # 1. Fazer login para obter o token
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    try:
        response = requests.post(f"{API_URL}/auth/login", data=login_data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            token = response.json().get('access_token')
            print(f"   ✅ Token obtido: {token[:50]}...")
            
            # 2. Testar decodificação do token
            test_data = {"token": token}
            test_headers = {'Content-Type': 'application/json'}
            
            response = requests.post(
                f"{API_URL}/debug/test-token", 
                json=test_data, 
                headers=test_headers, 
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Decodificação: {result}")
                
                if result.get("success"):
                    print(f"   ✅ Token válido e UserInDB criado com sucesso!")
                    return True
                else:
                    print(f"   ❌ Erro na decodificação: {result.get('error')}")
                    return False
            else:
                print(f"   ❌ Erro no endpoint: {response.status_code} - {response.text}")
                return False
                
        else:
            print(f"   ❌ Login falhou: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

def main():
    print("🚀 Debug da Decodificação de Token - finaFlow")
    print("=" * 50)
    
    success = test_token_decode()
    
    if success:
        print("\n🎉 Token está sendo decodificado corretamente!")
    else:
        print("\n❌ Há problemas na decodificação do token")

if __name__ == "__main__":
    main()
