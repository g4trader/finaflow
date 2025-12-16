#!/bin/bash

# Script de testes de API - Smoke e Consistência
# Testa endpoints críticos e valida respostas

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variáveis de ambiente
BACKEND_URL="${BACKEND_URL:-https://finaflow-backend-staging-642830139828.us-central1.run.app}"
QA_EMAIL="${QA_EMAIL:-qa@finaflow.test}"
QA_PASSWORD="${QA_PASSWORD:-QaFinaflow123!}"
YEAR="${YEAR:-2025}"

OUT_DIR="qa_e2e/out"
mkdir -p "$OUT_DIR"

echo "🔐 Fazendo login..."
LOGIN_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$QA_EMAIL\",\"password\":\"$QA_PASSWORD\"}")

TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token // empty')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ] || [ "$TOKEN" = "" ]; then
  echo -e "${RED}❌ Falha no login${NC}"
  echo "$LOGIN_RESPONSE" > "$OUT_DIR/login_error.json"
  exit 1
fi

echo -e "${GREEN}✅ Login realizado com sucesso${NC}"

# Validar auth/me
echo "👤 Validando auth/me..."
ME_RESPONSE=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $TOKEN" "$BACKEND_URL/api/v1/auth/me")
HTTP_CODE=$(echo "$ME_RESPONSE" | tail -n1)
BODY=$(echo "$ME_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" != "200" ]; then
  echo -e "${RED}❌ auth/me falhou: HTTP $HTTP_CODE${NC}"
  echo "$BODY" > "$OUT_DIR/auth_me_error.json"
  exit 1
fi

echo -e "${GREEN}✅ auth/me OK${NC}"

# Função para testar endpoint
test_endpoint() {
  local name=$1
  local url=$2
  local token=$3
  
  echo ""
  echo "🧪 Testando: $name"
  echo "   URL: $url"
  
  RESPONSE=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $token" "$url")
  HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
  BODY=$(echo "$RESPONSE" | sed '$d')
  
  if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ]; then
    echo -e "${GREEN}   ✅ HTTP $HTTP_CODE${NC}"
    echo "$BODY" | jq . > "$OUT_DIR/${name//\//_}.json" 2>/dev/null || echo "$BODY" > "$OUT_DIR/${name//\//_}.json"
    return 0
  else
    echo -e "${RED}   ❌ HTTP $HTTP_CODE${NC}"
    echo "$BODY" > "$OUT_DIR/${name//\//_}_error.json"
    return 1
  fi
}

# Contador de falhas
FAILURES=0

# Testar endpoints
echo ""
echo "📊 Testando endpoints do dashboard..."

test_endpoint "annual-summary" "$BACKEND_URL/api/v1/financial/annual-summary?year=$YEAR" "$TOKEN" || FAILURES=$((FAILURES + 1))

test_endpoint "validation-status" "$BACKEND_URL/api/v1/system/validation-status?year=$YEAR" "$TOKEN" || FAILURES=$((FAILURES + 1))

echo ""
echo "📊 Testando endpoints do dashboard operacional..."

test_endpoint "operational-availability" "$BACKEND_URL/api/v1/dashboard/operational/availability" "$TOKEN" || FAILURES=$((FAILURES + 1))

test_endpoint "operational-alerts" "$BACKEND_URL/api/v1/dashboard/operational/alerts" "$TOKEN" || FAILURES=$((FAILURES + 1))

test_endpoint "operational-forecast-vs-realized" "$BACKEND_URL/api/v1/dashboard/operational/forecast-vs-realized?months=6" "$TOKEN" || FAILURES=$((FAILURES + 1))

test_endpoint "operational-payables-summary" "$BACKEND_URL/api/v1/dashboard/operational/payables-summary" "$TOKEN" || FAILURES=$((FAILURES + 1))

test_endpoint "operational-receivables-summary" "$BACKEND_URL/api/v1/dashboard/operational/receivables-summary" "$TOKEN" || FAILURES=$((FAILURES + 1))

echo ""
echo "📊 Testando endpoint de previsões (forecast)..."

test_endpoint "lancamentos-previstos" "$BACKEND_URL/api/v1/lancamentos-previstos" "$TOKEN" || FAILURES=$((FAILURES + 1))

# Resumo
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $FAILURES -eq 0 ]; then
  echo -e "${GREEN}✅ Todos os testes passaram!${NC}"
  exit 0
else
  echo -e "${RED}❌ $FAILURES teste(s) falharam${NC}"
  exit 1
fi

