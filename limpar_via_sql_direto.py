#!/usr/bin/env python3
"""
🧹 LIMPEZA VIA SQL DIRETO
Usar endpoint SQL para limpar dados
"""

import requests

BACKEND_URL = "https://finaflow-backend-6arhlm3mha-uc.a.run.app"
CREDENTIALS = {"username": "lucianoterresrosa", "password": "xs95LIa9ZduX"}

print("🧹 LIMPEZA VIA SQL DIRETO")
print("=" * 60)

# Login
response = requests.post(f"{BACKEND_URL}/api/v1/auth/login", data=CREDENTIALS, timeout=10)
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✅ Login realizado")

# Buscar tenant_id e business_unit_id do token
import jwt
decoded_token = jwt.decode(token, options={"verify_signature": False})
tenant_id = decoded_token["tenant_id"]
business_unit_id = decoded_token["business_unit_id"]

print(f"📋 Tenant ID: {tenant_id}")
print(f"📋 Business Unit ID: {business_unit_id}")

# Verificar lançamentos antes
response = requests.get(f"{BACKEND_URL}/api/v1/lancamentos-diarios", headers=headers, timeout=10)
lancamentos_antes = response.json()["lancamentos"]
print(f"\n📊 Lançamentos ANTES: {len(lancamentos_antes)}")

# Mostrar IDs dos lançamentos
if lancamentos_antes:
    print("\n🗑️ Lançamentos a serem removidos:")
    for lanc in lancamentos_antes:
        print(f"   - {lanc['id']} - R$ {lanc['valor']}")

print("\n" + "=" * 60)
print("💡 SOLUÇÃO MANUAL:")
print("Por favor, acesse o banco de dados diretamente e execute:")
print(f"DELETE FROM lancamentos_diarios WHERE tenant_id = '{tenant_id}' AND business_unit_id = '{business_unit_id}';")
print("=" * 60)

EOF
