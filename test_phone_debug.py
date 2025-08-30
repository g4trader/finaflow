#!/usr/bin/env python3
"""
Teste simples para verificar o problema do telefone
"""

import requests
import json

def test_phone_debug():
    """Testa o problema do telefone"""
    
    print("🧪 Testando problema do telefone...")
    
    # 1. Verificar usuários existentes
    print("1. Verificando usuários existentes...")
    response = requests.get("https://finaflow-backend-609095880025.us-central1.run.app/api/v1/users")
    users = response.json()
    
    for user in users:
        print(f"   - {user['name']}: {user['phone']}")
    
    # 2. Criar um usuário de teste via API direta
    print("\n2. Criando usuário de teste via API...")
    
    test_user_data = {
        "name": "Teste API Direta",
        "email": "teste.api@exemplo.com",
        "phone": "11987654321",  # Número sem máscara
        "role": "user",
        "status": "active"
    }
    
    print(f"   Dados enviados: {test_user_data}")
    
    response = requests.post(
        "https://finaflow-backend-609095880025.us-central1.run.app/api/v1/users",
        json=test_user_data
    )
    
    if response.status_code == 201:
        created_user = response.json()
        print(f"   ✅ Usuário criado: {created_user['name']}")
        print(f"   Telefone salvo: {created_user['phone']}")
        
        if created_user['phone'] == '11987654321':
            print("   ✅ Telefone salvo corretamente (sem máscara)")
        else:
            print(f"   ❌ Telefone salvo incorretamente: {created_user['phone']}")
    else:
        print(f"   ❌ Erro ao criar usuário: {response.status_code}")
        print(f"   Resposta: {response.text}")
    
    # 3. Verificar usuários novamente
    print("\n3. Verificando usuários após criação...")
    response = requests.get("https://finaflow-backend-609095880025.us-central1.run.app/api/v1/users")
    users = response.json()
    
    for user in users:
        print(f"   - {user['name']}: {user['phone']}")
    
    print("\n🎉 Teste concluído!")

if __name__ == "__main__":
    test_phone_debug()
