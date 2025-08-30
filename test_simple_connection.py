#!/usr/bin/env python3
"""
Teste simples para verificar conexão entre frontend e backend
"""

import requests
import json

def test_backend_connection():
    """Testa se o backend está respondendo corretamente"""
    
    print("🧪 Testando conexão com o backend...")
    
    # URL do backend
    backend_url = "https://finaflow-backend-609095880025.us-central1.run.app"
    
    try:
        # Teste 1: Health check
        print("1. Testando health check...")
        response = requests.get(f"{backend_url}/")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Health check OK")
        else:
            print("❌ Health check falhou")
        
        # Teste 2: Endpoint de usuários
        print("2. Testando endpoint de usuários...")
        response = requests.get(f"{backend_url}/api/v1/users")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Endpoint de usuários OK")
            data = response.json()
            print(f"   Usuários encontrados: {len(data)}")
        else:
            print("❌ Endpoint de usuários falhou")
        
        # Teste 3: Criar um usuário de teste
        print("3. Testando criação de usuário...")
        user_data = {
            "name": "Teste Usabilidade",
            "email": "teste.usabilidade@exemplo.com",
            "phone": "11999999999",
            "role": "user",
            "status": "active"
        }
        
        response = requests.post(f"{backend_url}/api/v1/users", json=user_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 201:
            print("✅ Criação de usuário OK")
            created_user = response.json()
            print(f"   Usuário criado: {created_user['name']} ({created_user['email']})")
            
            # Teste 4: Verificar se o usuário aparece na lista
            print("4. Verificando se usuário aparece na lista...")
            response = requests.get(f"{backend_url}/api/v1/users")
            if response.status_code == 200:
                users = response.json()
                test_user = next((u for u in users if u['email'] == user_data['email']), None)
                if test_user:
                    print("✅ Usuário encontrado na lista")
                else:
                    print("❌ Usuário não encontrado na lista")
            
        else:
            print("❌ Criação de usuário falhou")
            print(f"   Erro: {response.text}")
        
        print("\n🎉 Testes de conexão concluídos!")
        
    except Exception as e:
        print(f"❌ Erro durante os testes: {e}")

if __name__ == "__main__":
    test_backend_connection()
