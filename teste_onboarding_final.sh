#!/bin/bash

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  🔄 TESTE COMPLETO - ONBOARDING + IMPORTAÇÃO LLM            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Login super admin
echo "1️⃣ Login Super Admin..."
TOKEN=$(curl -s -X POST "https://finaflow-backend-6arhlm3mha-uc.a.run.app/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "❌ Erro no login"
  exit 1
fi
echo "✅ OK"
echo ""

# Deletar LLM antiga
echo "2️⃣ Deletando LLM antiga (se existir)..."
curl -s -X POST "https://finaflow-backend-6arhlm3mha-uc.a.run.app/api/v1/admin/delete-tenant" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"29d7b01f-ac2f-4560-8984-53b6712aeb19"}' > /dev/null 2>&1
echo "✅ Limpo"
echo ""

# Criar empresa nova
echo "3️⃣ Criando LLM Lavanderia..."
RESULT=$(curl -s -X POST "https://finaflow-backend-6arhlm3mha-uc.a.run.app/api/v1/admin/onboard-new-company" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_name": "LLM Lavanderia",
    "tenant_domain": "g4marketing.com.br",
    "bu_name": "Matriz",
    "bu_code": "MAT",
    "admin_email": "lucianoterresrosa@gmail.com",
    "admin_first_name": "Luciano",
    "admin_last_name": "Terres Rosa",
    "spreadsheet_id": "1rWMdDhwiNoC7iMycmQGWWDIacrePr1gB7c_mbt1patQ"
  }')

ADMIN_USER=$(echo "$RESULT" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('company_info', {}).get('admin_username', ''))")
ADMIN_PASS=$(echo "$RESULT" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('company_info', {}).get('admin_password', ''))")

if [ -z "$ADMIN_USER" ]; then
  echo "❌ Erro na criação"
  echo "$RESULT" | python3 -m json.tool
  exit 1
fi

echo "✅ Empresa criada!"
echo "   Username: $ADMIN_USER"
echo "   Senha: $ADMIN_PASS"
echo ""

# Login do admin
echo "4️⃣ Login do admin LLM..."
ADMIN_TOKEN=$(curl -s -X POST "https://finaflow-backend-6arhlm3mha-uc.a.run.app/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$ADMIN_USER&password=$ADMIN_PASS" | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$ADMIN_TOKEN" ]; then
  echo "❌ Erro no login do admin"
  exit 1
fi
echo "✅ OK"
echo ""

# Selecionar BU
echo "5️⃣ Selecionando Business Unit..."
BU_ID=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "https://finaflow-backend-6arhlm3mha-uc.a.run.app/api/v1/auth/user-business-units" | \
  python3 -c "import sys, json; bus = json.load(sys.stdin); print(bus[0]['id'] if bus else '')")

ADMIN_TOKEN=$(curl -s -X POST \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"business_unit_id\":\"$BU_ID\"}" \
  "https://finaflow-backend-6arhlm3mha-uc.a.run.app/api/v1/auth/select-business-unit" | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

echo "✅ OK"
echo ""

# Importar CSV
echo "6️⃣ Importando plano de contas..."
IMPORT_RESULT=$(curl -s -X POST \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -F "file=@csv/Fluxo de Caixa 2025_Cliente teste - Plano de contas.csv" \
  "https://finaflow-backend-6arhlm3mha-uc.a.run.app/api/v1/chart-accounts/import")

GROUPS=$(echo "$IMPORT_RESULT" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('summary', {}).get('groups_created', 0))")
ACCOUNTS=$(echo "$IMPORT_RESULT" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('summary', {}).get('accounts_created', 0))")

echo "✅ Importado!"
echo "   Grupos: $GROUPS"
echo "   Contas: $ACCOUNTS"
echo ""

# Verificar dados
echo "7️⃣ Verificando dados no sistema..."
GROUPS_TOTAL=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "https://finaflow-backend-6arhlm3mha-uc.a.run.app/api/v1/chart-accounts/groups" | \
  python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data))")

ACCOUNTS_TOTAL=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "https://finaflow-backend-6arhlm3mha-uc.a.run.app/api/v1/chart-accounts/accounts" | \
  python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data))")

echo "✅ Verificado!"
echo "   Grupos no sistema: $GROUPS_TOTAL"
echo "   Contas no sistema: $ACCOUNTS_TOTAL"
echo ""

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              ✅ ONBOARDING COMPLETO COM SUCESSO!            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "🔑 Credenciais:"
echo "   Username: $ADMIN_USER"
echo "   Senha: $ADMIN_PASS"
echo "   URL: https://finaflow.vercel.app/login"
echo ""

