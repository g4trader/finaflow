#!/bin/bash

echo "🗑️  DELETANDO EMPRESA LLM LAVANDERIA"
echo "====================================="
echo ""

# Login super admin
TOKEN=$(curl -s -X POST "https://finaflow-backend-6arhlm3mha-uc.a.run.app/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "❌ Erro no login"
  exit 1
fi

echo "✅ Login OK"
echo ""

# Deletar tenant LLM
TENANT_ID="18ba26ba-bad4-4ca6-9234-73267c62f54d"

echo "Deletando tenant: $TENANT_ID"

curl -s -X DELETE \
  "https://finaflow-backend-6arhlm3mha-uc.a.run.app/api/v1/tenants/$TENANT_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('message', data))"

echo ""
echo "✅ Empresa LLM deletada!"
echo ""
echo "Pronto para refazer o onboarding com importação integrada."

