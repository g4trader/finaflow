#!/bin/bash

# Script orquestrador - Executa todos os testes E2E
# Gera REPORT.md ao final

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variáveis de ambiente com defaults
export BACKEND_URL="${BACKEND_URL:-https://finaflow-backend-staging-642830139828.us-central1.run.app}"
export FRONTEND_URL="${FRONTEND_URL:-https://finaflow-lcz5.vercel.app}"
export YEAR="${YEAR:-2025}"
export QA_EMAIL="${QA_EMAIL:-qa@finaflow.test}"
export QA_PASSWORD="${QA_PASSWORD:-QaFinaflow123!}"

OUT_DIR="qa_e2e/out"
REPORT_FILE="qa_e2e/REPORT.md"

mkdir -p "$OUT_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 FinaFlow E2E Test Suite"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Configuração:"
echo "   Backend:  $BACKEND_URL"
echo "   Frontend: $FRONTEND_URL"
echo "   Ano:      $YEAR"
echo "   Email:    $QA_EMAIL"
echo ""

# Contador de falhas
TOTAL_FAILURES=0

# Iniciar REPORT.md
cat > "$REPORT_FILE" << EOF
# 📊 Relatório de Testes E2E - FinaFlow

**Data**: $(date '+%Y-%m-%d %H:%M:%S')
**Backend**: $BACKEND_URL
**Frontend**: $FRONTEND_URL
**Ano**: $YEAR

---

## 📋 Resumo Executivo

EOF

# 1. Testes de API - Smoke e Consistência
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}1️⃣  Testes de API - Smoke e Consistência${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if ./qa_e2e/api_smoke_and_consistency.sh; then
  echo -e "${GREEN}✅ API Smoke Tests: PASS${NC}"
  echo "✅ API Smoke Tests: PASS" >> "$REPORT_FILE"
else
  echo -e "${RED}❌ API Smoke Tests: FAIL${NC}"
  echo "❌ API Smoke Tests: FAIL" >> "$REPORT_FILE"
  TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
fi

# 2. Validação Numérica
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}2️⃣  Validação Numérica (Excel vs API)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

EXCEL_FILE="backend/data/fluxo_caixa_2025.xlsx"
if [ ! -f "$EXCEL_FILE" ]; then
  echo -e "${YELLOW}⚠️  Arquivo Excel não encontrado: $EXCEL_FILE${NC}"
  echo "⚠️  Validação Numérica: SKIP (arquivo não encontrado)" >> "$REPORT_FILE"
else
  if python3 qa_e2e/api_validate_numbers.py \
    --file "$EXCEL_FILE" \
    --year "$YEAR" \
    --backend-url "$BACKEND_URL" \
    --email "$QA_EMAIL" \
    --password "$QA_PASSWORD"; then
    echo -e "${GREEN}✅ Validação Numérica: PASS${NC}"
    echo "✅ Validação Numérica: PASS" >> "$REPORT_FILE"
  else
    EXIT_CODE=$?
    echo -e "${RED}❌ Validação Numérica: FAIL (exit code: $EXIT_CODE)${NC}"
    echo "❌ Validação Numérica: FAIL" >> "$REPORT_FILE"
    TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
  fi
fi

# 3. Testes UI com Selenium
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}3️⃣  Testes UI com Selenium${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if python3 qa_e2e/ui_selenium_smoke.py; then
  echo -e "${GREEN}✅ UI Tests: PASS${NC}"
  echo "✅ UI Tests: PASS" >> "$REPORT_FILE"
else
  echo -e "${RED}❌ UI Tests: FAIL${NC}"
  echo "❌ UI Tests: FAIL" >> "$REPORT_FILE"
  TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
fi

# Gerar relatório completo
echo "" >> "$REPORT_FILE"
echo "---" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "## 📊 Detalhes dos Testes" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Adicionar resultados da validação numérica
if [ -f "$OUT_DIR/validation_numbers.json" ]; then
  echo "### Validação Numérica" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
  echo "\`\`\`json" >> "$REPORT_FILE"
  cat "$OUT_DIR/validation_numbers.json" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
  echo "\`\`\`" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
fi

# Adicionar resultados dos testes UI
if [ -f "$OUT_DIR/ui_test_results.json" ]; then
  echo "### Testes UI" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
  echo "\`\`\`json" >> "$REPORT_FILE"
  cat "$OUT_DIR/ui_test_results.json" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
  echo "\`\`\`" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
fi

# Adicionar links e artefatos
echo "## 🔗 Links" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "- **Backend**: $BACKEND_URL" >> "$REPORT_FILE"
echo "- **Frontend**: $FRONTEND_URL" >> "$REPORT_FILE"
echo "- **Dashboard**: $FRONTEND_URL/dashboard?year=$YEAR" >> "$REPORT_FILE"
echo "- **Dashboard Operacional**: $FRONTEND_URL/dashboard-operational" >> "$REPORT_FILE"
echo "- **Financial Forecasts**: $FRONTEND_URL/financial-forecasts" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Artefatos gerados
echo "## 📁 Artefatos Gerados" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
if [ -d "$OUT_DIR/screenshots" ] && [ "$(ls -A $OUT_DIR/screenshots 2>/dev/null)" ]; then
  echo "### Screenshots" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
  for img in "$OUT_DIR/screenshots"/*; do
    if [ -f "$img" ]; then
      echo "- \`$(basename "$img")\`" >> "$REPORT_FILE"
    fi
  done
  echo "" >> "$REPORT_FILE"
fi

if [ -d "$OUT_DIR" ] && [ "$(ls -A $OUT_DIR/*.json 2>/dev/null)" ]; then
  echo "### Arquivos JSON" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
  for json_file in "$OUT_DIR"/*.json; do
    if [ -f "$json_file" ]; then
      echo "- \`$(basename "$json_file")\`" >> "$REPORT_FILE"
    fi
  done
  echo "" >> "$REPORT_FILE"
fi

# Resumo final
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $TOTAL_FAILURES -eq 0 ]; then
  echo -e "${GREEN}✅ TODOS OS TESTES PASSARAM!${NC}"
  echo "" >> "$REPORT_FILE"
  echo "## ✅ Resultado Final" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
  echo "**STATUS: PASS** - Todos os testes passaram com sucesso!" >> "$REPORT_FILE"
  exit 0
else
  echo -e "${RED}❌ $TOTAL_FAILURES etapa(s) falharam${NC}"
  echo "" >> "$REPORT_FILE"
  echo "## ❌ Resultado Final" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
  echo "**STATUS: FAIL** - $TOTAL_FAILURES etapa(s) falharam" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
  echo "Verifique os arquivos em \`qa_e2e/out/\` para mais detalhes." >> "$REPORT_FILE"
  exit 1
fi

