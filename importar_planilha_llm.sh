#!/bin/bash

echo "📊 IMPORTAÇÃO COMPLETA - LLM LAVANDERIA"
echo "========================================"
echo ""

# 1. Login
echo "🔐 Login..."
TOKEN=$(curl -s -X POST "https://finaflow-backend-6arhlm3mha-uc.a.run.app/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=lucianoterresrosa&password=a3KKQGv4n6yF" | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "❌ Erro no login"
  exit 1
fi

echo "✅ Login OK"
echo ""

# 2. Selecionar BU
echo "🎯 Selecionando BU..."
BU_ID=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "https://finaflow-backend-6arhlm3mha-uc.a.run.app/api/v1/auth/user-business-units" | \
  python3 -c "import sys, json; bus = json.load(sys.stdin); print(bus[0]['id'] if bus else '')")

if [ -z "$BU_ID" ]; then
  echo "❌ BU não encontrada"
  exit 1
fi

echo "✅ BU ID: ${BU_ID:0:8}..."

TOKEN=$(curl -s -X POST "https://finaflow-backend-6arhlm3mha-uc.a.run.app/api/v1/auth/select-business-unit" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"business_unit_id\":\"$BU_ID\"}" | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

echo "✅ Token com BU atualizado"
echo ""

# 3. Importar plano de contas
echo "📊 Importando plano de contas..."

curl -X POST "https://finaflow-backend-6arhlm3mha-uc.a.run.app/api/v1/chart-accounts/import" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@csv/Fluxo de Caixa 2025_Cliente teste - Plano de contas.csv" \
  -s | python3 -c "import sys, json; data = json.load(sys.stdin); print(f\"Resultado: {data.get('message', data)}\")"

echo ""

# 4. Verificar importação
echo "🔍 Verificando dados..."

GROUPS=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "https://finaflow-backend-6arhlm3mha-uc.a.run.app/api/v1/chart-accounts/groups" | \
  python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data))")

ACCOUNTS=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "https://finaflow-backend-6arhlm3mha-uc.a.run.app/api/v1/chart-accounts/accounts" | \
  python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data))")

echo "  Grupos: $GROUPS"
echo "  Contas: $ACCOUNTS"
echo ""

if [ "$GROUPS" -gt "0" ] && [ "$ACCOUNTS" -gt "0" ]; then
  echo "✅ IMPORTAÇÃO BEM-SUCEDIDA!"
else
  echo "⚠️  Nenhum dado importado - verificar motivo"
fi

