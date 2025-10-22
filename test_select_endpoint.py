#!/usr/bin/env python3
import requests
import time

# Aguardar deploy
print("⏳ Aguardando 30 segundos para o deploy finalizar...")
time.sleep(30)

# Testar endpoints
BACKEND_URL = "https://finaflow-backend-6arhlm3mha-uc.a.run.app"

print("\n🔍 Testando endpoints após deploy...\n")

# 1. Testar endpoint de auth test
print("1️⃣ Testando /api/v1/auth/test...")
test_response = requests.get(f"{BACKEND_URL}/api/v1/auth/test")
print(f"   Status: {test_response.status_code}")
if test_response.status_code == 200:
    print(f"   ✅ Funcionando: {test_response.json()}")
else:
    print(f"   ❌ Erro: {test_response.text}")

# 2. Testar login
print("\n2️⃣ Testando login...")
login_response = requests.post(
    f"{BACKEND_URL}/api/v1/auth/login",
    data={"username": "admin", "password": "admin123"},
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)

if login_response.status_code == 200:
    print("   ✅ Login funcionando")
    
    token_data = login_response.json()
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Obter business units
    print("\n3️⃣ Obtendo business units...")
    bus_response = requests.get(f"{BACKEND_URL}/api/v1/auth/user-business-units", headers=headers)
    
    if bus_response.status_code == 200:
        bus_data = bus_response.json()
        print(f"   ✅ Business units encontradas: {len(bus_data)}")
        
        if len(bus_data) > 0:
            business_unit_id = bus_data[0]['id']
            print(f"   📋 BU: {bus_data[0]['tenant_name']} > {bus_data[0]['name']}")
            print(f"   🆔 ID: {business_unit_id}")
            
            # 4. Testar seleção de business unit
            print("\n4️⃣ Testando seleção de business unit...")
            selection_data = {"business_unit_id": business_unit_id}
            select_response = requests.post(
                f"{BACKEND_URL}/api/v1/auth/select-business-unit",
                json=selection_data,
                headers=headers
            )
            
            print(f"   Status: {select_response.status_code}")
            
            if select_response.status_code == 200:
                response_data = select_response.json()
                print("   ✅✅✅ SELEÇÃO FUNCIONANDO!")
                print(f"   👤 Empresa: {response_data['user']['tenant_name']}")
                print(f"   🏢 Unidade: {response_data['user']['business_unit_name']}")
                print(f"   🔑 Token: {response_data['access_token'][:50]}...")
                print("\n🎉🎉🎉 PROBLEMA RESOLVIDO! 🎉🎉🎉")
                print("✅ O usuário pode agora selecionar empresa e acessar o dashboard!")
            else:
                print(f"   ❌ Erro na seleção: {select_response.status_code}")
                print(f"   Resposta: {select_response.text}")
                print("\n⚠️ O problema ainda persiste.")
                print("   Possíveis causas:")
                print("   - Arquivo hybrid_app.py não foi atualizado no deploy")
                print("   - Cloud Build ainda usando arquivo antigo")
                print("   - Necessário verificar logs do Cloud Run")
        else:
            print("   ❌ Nenhuma business unit encontrada")
    else:
        print(f"   ❌ Erro ao buscar business units: {bus_response.status_code}")
else:
    print(f"   ❌ Erro no login: {login_response.status_code}")

print(f"\n🔗 Teste manual: {BACKEND_URL}/api/v1/auth/test")
print(f"🔗 Frontend: https://finaflow.vercel.app/login")



