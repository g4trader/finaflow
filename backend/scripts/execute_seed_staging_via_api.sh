#!/bin/bash
# Script para executar seed no STAGING via API endpoint
# Usa o endpoint /api/v1/admin/seed-staging

set -e

BACKEND_URL="${BACKEND_URL:-https://finaflow-backend-staging-642830139828.us-central1.run.app}"
QA_EMAIL="${QA_EMAIL:-qa@finaflow.test}"
QA_PASSWORD="${QA_PASSWORD:-Finaflow123!}"

echo "============================================================"
echo "🔄 RE-SEED 2025 - Correção de CUSTO (STAGING via API)"
echo "============================================================"
echo ""
echo "📡 Backend URL: $BACKEND_URL"
echo "👤 Email: $QA_EMAIL"
echo ""

# 1. Fazer login e obter token
echo "🔐 Fazendo login..."
LOGIN_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$QA_EMAIL\", \"password\": \"$QA_PASSWORD\"}")

TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token // .token // empty')

if [ -z "$TOKEN" ] || [ "$TOKEN" == "null" ]; then
    echo "❌ Erro ao fazer login"
    echo "Resposta: $LOGIN_RESPONSE"
    exit 1
fi

echo "✅ Login realizado com sucesso"
echo ""

# 2. Verificar se usuário é super_admin
echo "🔍 Verificando permissões..."
USER_INFO=$(curl -s -X GET "$BACKEND_URL/api/v1/auth/me" \
    -H "Authorization: Bearer $TOKEN")

USER_ROLE=$(echo "$USER_INFO" | jq -r '.role // .role.value // empty')

if [ "$USER_ROLE" != "super_admin" ]; then
    echo "❌ Usuário não é super_admin (role: $USER_ROLE)"
    echo "   O endpoint /api/v1/admin/seed-staging requer super_admin"
    exit 1
fi

echo "✅ Permissões OK (role: $USER_ROLE)"
echo ""

# 3. Executar seed com COST_DEBUG=1 e reset-data
echo "🌱 Executando seed com COST_DEBUG=1 e --reset-data..."
echo "⚠️  ATENÇÃO: Isso vai apagar todos os lançamentos diários e previstos do tenant!"
echo ""

# Fazer requisição para o endpoint de seed
SEED_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/admin/seed-staging" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"reset_data": true, "cost_debug": true}' \
    -w "\n%{http_code}")

HTTP_CODE=$(echo "$SEED_RESPONSE" | tail -n1)
BODY=$(echo "$SEED_RESPONSE" | sed '$d')

echo "📊 Status HTTP: $HTTP_CODE"
echo ""

if [ "$HTTP_CODE" != "200" ]; then
    echo "❌ Seed falhou"
    echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
    exit 1
fi

SUCCESS=$(echo "$BODY" | jq -r '.success // false')

if [ "$SUCCESS" == "true" ]; then
    echo "✅ Seed concluído com sucesso!"
    echo ""
    echo "📄 Output (últimas linhas):"
    echo "$BODY" | jq -r '.output // ""' | tail -20
    echo ""
else
    echo "❌ Seed falhou"
    echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
    exit 1
fi

echo "🔍 Próximo passo: Executar auditoria para validar equalização"
echo "   make audit"
echo ""

