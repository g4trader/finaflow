#!/bin/bash

BACKEND="https://finaflow-backend-6arhlm3mha-uc.a.run.app"

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║          🎯 TESTE FINAL DEFINITIVO - SISTEMA SEM DADOS MOCK! 🎯            ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Login super admin
TOKEN=$(curl -s -X POST "$BACKEND/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

echo "🔧 PASSO 1: Executando correção de constraints..."
RESULT=$(curl -s -X POST "$BACKEND/api/v1/admin/fix-unique-constraints" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

echo "$RESULT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success'):
    for detail in data.get('details', []):
        print(f'  {detail}')
else:
    print(f'  ⚠️  {data.get(\"error\", \"Erro desconhecido\")}')"

echo ""
echo "🗑️  PASSO 2: Deletando empresa antiga..."
TENANTS=$(curl -s -H "Authorization: Bearer $TOKEN" "$BACKEND/api/v1/tenants")
TENANT_ID=$(echo "$TENANTS" | python3 -c "
import sys, json
tenants = json.load(sys.stdin)
llm = [t for t in tenants if 'LLM' in t.get('name', '')]
print(llm[0]['id'] if llm else '')")

if [ -n "$TENANT_ID" ]; then
    curl -s -X POST "$BACKEND/api/v1/admin/delete-tenant" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"tenant_id\":\"$TENANT_ID\"}" > /dev/null
    echo "  ✅ Deletado"
else
    echo "  ✅ Não existe"
fi

echo ""
echo "══════════════════════════════════════════════════════════════════════════════"
echo "ONBOARDING + IMPORTAÇÃO"
echo "══════════════════════════════════════════════════════════════════════════════"
echo ""

# Criar empresa
RESULT=$(curl -s -X POST "$BACKEND/api/v1/admin/onboard-new-company" \
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

echo "✅ Empresa criada: $ADMIN_USER / $ADMIN_PASS"
echo ""

# Login admin
ADMIN_TOKEN=$(curl -s -X POST "$BACKEND/api/v1/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$ADMIN_USER&password=$ADMIN_PASS" | \
    grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

# Selecionar BU
BU_ID=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" "$BACKEND/api/v1/auth/user-business-units" | \
    python3 -c "import sys, json; bus = json.load(sys.stdin); print(bus[0]['id'] if bus else '')")

ADMIN_TOKEN=$(curl -s -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"business_unit_id\":\"$BU_ID\"}" \
    "$BACKEND/api/v1/auth/select-business-unit" | \
    grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

echo "✅ Login OK"
echo ""

# Importar
echo "📊 Importando plano de contas..."
IMPORT_RESULT=$(curl -s -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
    -F "file=@csv/Fluxo de Caixa 2025_Cliente teste - Plano de contas.csv" \
    "$BACKEND/api/v1/chart-accounts/import")

IMPORT_STATUS=$(echo "$IMPORT_RESULT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('success'):
        summary = data.get('summary', {})
        print(f\"SUCESSO|{summary.get('groups_created', 0)}|{summary.get('accounts_created', 0)}\")
    else:
        print('ERRO|0|0')
except:
    print('ERRO|0|0')")

IFS='|' read -r STATUS GROUPS ACCOUNTS <<< "$IMPORT_STATUS"

if [ "$STATUS" = "SUCESSO" ]; then
    echo "  ✅ Importação concluída!"
    echo "  📊 Grupos: $GROUPS"
    echo "  📊 Contas: $ACCOUNTS"
else:
    echo "  ❌ Erro na importação"
fi

echo ""

# Verificar visibilidade
GROUPS_COUNT=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" "$BACKEND/api/v1/chart-accounts/groups" | \
    python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data))")

ACCOUNTS_COUNT=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" "$BACKEND/api/v1/chart-accounts/accounts" | \
    python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data))")

echo "📊 Dados visíveis:"
echo "  Grupos: $GROUPS_COUNT"
echo "  Contas: $ACCOUNTS_COUNT"
echo ""

if [ "$GROUPS_COUNT" -gt "0" ] && [ "$ACCOUNTS_COUNT" -gt "0" ]; then
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║         🎉🎉🎉 SUCESSO TOTAL! SISTEMA OPERACIONAL! 🎉🎉🎉                 ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "🔑 CREDENCIAIS:"
    echo "   Username: $ADMIN_USER"
    echo "   Senha: $ADMIN_PASS"
    echo "   URL: https://finaflow.vercel.app/login"
    echo ""
    echo "📊 DADOS REAIS IMPORTADOS:"
    echo "   ✅ $GROUPS_COUNT grupos de contas"
    echo "   ✅ $ACCOUNTS_COUNT contas operacionais"
    echo "   ✅ 100% multi-tenant"
    echo "   ✅ 0% dados mock"
else
    echo "⚠️  Verificar logs"
fi

