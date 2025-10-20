#!/usr/bin/env python3
"""
Teste simples de autenticação
"""
import requests

def test_login():
    url = "http://127.0.0.1:8000/api/v1/auth/login"
    data = {
        "username": "admin",
        "password": "admin123"
    }
    
    print(f"🔐 Testando login em: {url}")
    print(f"📝 Dados: {data}")
    
    try:
        response = requests.post(url, data=data, timeout=10)
        print(f"📊 Status: {response.status_code}")
        print(f"📄 Headers: {dict(response.headers)}")
        print(f"📋 Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Login bem-sucedido!")
            print(f"🎫 Token: {result.get('access_token', 'N/A')[:50]}...")
            return result.get('access_token')
        else:
            print(f"❌ Login falhou")
            return None
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

if __name__ == "__main__":
    test_login()







