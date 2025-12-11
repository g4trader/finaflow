#!/bin/bash
# Script de QA Completo da Versão 2.0
# Executa todas as validações necessárias para homologação

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configurações
BACKEND_URL="${BACKEND_URL:-https://finaflow-backend-staging-642830139828.us-central1.run.app}"
QA_EMAIL="qa@finaflow.test"
QA_PASSWORD="QaFinaflow123!"
YEAR=2025

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   QA COMPLETO - VERSÃO 2.0 - DASHBOARD FINANCEIRO${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Função para fazer login e obter token
get_token() {
    echo -e "${YELLOW}🔐 Fazendo login na API...${NC}"
    TOKEN=$(curl -s -X POST "$BACKEND_URL/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"username\":\"$QA_EMAIL\",\"password\":\"$QA_PASSWORD\"}" | \
        jq -r '.access_token // empty')
    
    if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
        echo -e "${RED}❌ Falha ao fazer login${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Login realizado com sucesso${NC}"
    echo "$TOKEN"
}

# Função para testar endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local token=$3
    
    echo -e "${YELLOW}📊 Testando: $name${NC}"
    response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $token" "$url")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✅ $name: OK (HTTP $http_code)${NC}"
        echo "$body" | jq '.' > /tmp/qa_${name// /_}.json 2>/dev/null || echo "$body" > /tmp/qa_${name// /_}.json
        return 0
    else
        echo -e "${RED}❌ $name: FALHOU (HTTP $http_code)${NC}"
        echo "$body"
        return 1
    fi
}

# Iniciar QA
TOKEN=$(get_token)
echo ""

# 1. Testar endpoint /annual-summary
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   1. QA DO ENDPOINT /annual-summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

test_endpoint "annual-summary" "$BACKEND_URL/api/v1/financial/annual-summary?year=$YEAR" "$TOKEN"

if [ $? -eq 0 ]; then
    # Validar estrutura
    echo -e "${YELLOW}   Validando estrutura da resposta...${NC}"
    
    # Verificar se tem 12 meses
    month_count=$(cat /tmp/qa_annual-summary.json | jq '.monthly | length')
    if [ "$month_count" = "12" ]; then
        echo -e "${GREEN}   ✅ Retorna 12 meses${NC}"
    else
        echo -e "${RED}   ❌ Retorna $month_count meses (esperado: 12)${NC}"
    fi
    
    # Verificar totais
    revenue=$(cat /tmp/qa_annual-summary.json | jq -r '.totals.revenue')
    expense=$(cat /tmp/qa_annual-summary.json | jq -r '.totals.expense')
    cost=$(cat /tmp/qa_annual-summary.json | jq -r '.totals.cost')
    balance=$(cat /tmp/qa_annual-summary.json | jq -r '.totals.balance')
    
    echo -e "${YELLOW}   Totais anuais:${NC}"
    echo -e "   Receita: R$ $revenue"
    echo -e "   Despesa: R$ $expense"
    echo -e "   Custo: R$ $cost"
    echo -e "   Saldo: R$ $balance"
    
    # Verificar saldo acumulado
    echo -e "${YELLOW}   Verificando saldo acumulado...${NC}"
    has_accumulated=$(cat /tmp/qa_annual-summary.json | jq '.monthly[0] | has("accumulated_balance")')
    if [ "$has_accumulated" = "true" ]; then
        echo -e "${GREEN}   ✅ Saldo acumulado presente${NC}"
    else
        echo -e "${RED}   ❌ Saldo acumulado ausente${NC}"
    fi
fi

echo ""

# 2. Testar endpoint /annual-summary/debug
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   2. QA DO ENDPOINT /annual-summary/debug${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

test_endpoint "annual-summary-debug" "$BACKEND_URL/api/v1/financial/annual-summary/debug?year=$YEAR" "$TOKEN"

if [ $? -eq 0 ]; then
    # Validar estrutura
    echo -e "${YELLOW}   Validando estrutura da resposta...${NC}"
    
    has_sql=$(cat /tmp/qa_annual-summary-debug.json | jq 'has("annual_totals")')
    has_memory=$(cat /tmp/qa_annual-summary-debug.json | jq '.annual_totals | has("memory")')
    has_comparison=$(cat /tmp/qa_annual-summary-debug.json | jq 'has("monthly_comparison")')
    
    if [ "$has_sql" = "true" ] && [ "$has_memory" = "true" ] && [ "$has_comparison" = "true" ]; then
        echo -e "${GREEN}   ✅ Estrutura completa (SQL, Memory, Comparison)${NC}"
    else
        echo -e "${RED}   ❌ Estrutura incompleta${NC}"
    fi
fi

echo ""

# 3. Executar script de validação completa
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   3. VALIDAÇÃO PROFUNDA (SCRIPT DE AUDITORIA)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

if [ -f "./scripts/run_validation_with_proxy.sh" ]; then
    echo -e "${YELLOW}📊 Executando script de validação completa...${NC}"
    ./scripts/run_validation_with_proxy.sh --year $YEAR
    VALIDATION_EXIT=$?
    
    if [ $VALIDATION_EXIT -eq 0 ]; then
        echo -e "${GREEN}✅ Validação completa: OK${NC}"
    else
        echo -e "${RED}❌ Validação completa: FALHOU${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  Script de validação não encontrado. Pulando...${NC}"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   QA COMPLETO FINALIZADO${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}📋 Próximos passos:${NC}"
echo "   1. Revisar arquivos JSON em /tmp/qa_*.json"
echo "   2. Validar frontend manualmente"
echo "   3. Gerar relatório final"

