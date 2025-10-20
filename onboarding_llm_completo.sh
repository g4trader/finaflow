#!/bin/bash

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║     🏢 ONBOARDING COMPLETO - LLM LAVANDERIA (COM IMPORTAÇÃO)                 ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Dados do cliente
TENANT_NAME="LLM Lavanderia"
TENANT_DOMAIN="g4marketing.com.br"
ADMIN_EMAIL="lucianoterresrosa@gmail.com"
ADMIN_FIRST_NAME="Luciano"
ADMIN_LAST_NAME="Terres Rosa"
SPREADSHEET_ID="1rWMdDhwiNoC7iMycmQGWWDIacrePr1gB7c_mbt1patQ"

echo "📋 Dados do Cliente:"
echo "   Empresa: $TENANT_NAME"
echo "   Domínio: $TENANT_DOMAIN"
echo "   Admin: $ADMIN_EMAIL"
echo "   Planilha: $SPREADSHEET_ID"
echo ""

# Login super admin
echo "🔐 Login do Super Admin..."
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

# Criar empresa com importação
echo "🏢 Criando empresa e importando dados..."
echo ""

RESULT=$(curl -s -X POST "https://finaflow-backend-6arhlm3mha-uc.a.run.app/api/v1/admin/onboard-new-company" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_name": "'"$TENANT_NAME"'",
    "tenant_domain": "'"$TENANT_DOMAIN"'",
    "bu_name": "Matriz",
    "bu_code": "MAT",
    "admin_email": "'"$ADMIN_EMAIL"'",
    "admin_first_name": "'"$ADMIN_FIRST_NAME"'",
    "admin_last_name": "'"$ADMIN_LAST_NAME"'",
    "spreadsheet_id": "'"$SPREADSHEET_ID"'",
    "import_data": true
  }')

# Verificar se teve sucesso
SUCCESS=$(echo "$RESULT" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('success', False))" 2>/dev/null)

if [ "$SUCCESS" != "True" ]; then
  echo "❌ Erro no onboarding:"
  echo "$RESULT" | python3 -m json.tool
  exit 1
fi

echo "✅ Onboarding concluído!"
echo ""

# Exibir passos
echo "📊 Processo Executado:"
echo "$RESULT" | python3 -c "import sys, json; data = json.load(sys.stdin); steps = data.get('steps', []); [print(f'  {step}') for step in steps]"
echo ""

# Exibir credenciais
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                        🔑 CREDENCIAIS DE ACESSO                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

COMPANY_INFO=$(echo "$RESULT" | python3 -c "import sys, json; data = json.load(sys.stdin); print(json.dumps(data.get('company_info', {})))")

echo "$COMPANY_INFO" | python3 -c "
import sys, json
info = json.load(sys.stdin)
print(f\"Empresa: {info.get('tenant_name')}\")
print(f\"Filial: {info.get('business_unit_name')}\")
print(f\"\")
print(f\"Username: {info.get('admin_username')}\")
print(f\"Email: {info.get('admin_email')}\")
print(f\"Senha: {info.get('admin_password')}\")
print(f\"\")
print(f\"URL: {info.get('login_url')}\")
"

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║     ⚠️  SALVE E ENVIE ESTAS CREDENCIAIS PARA O CLIENTE!                      ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"

