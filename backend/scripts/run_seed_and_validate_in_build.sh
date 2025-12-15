#!/usr/bin/env bash
set -euo pipefail

# Script para executar seed + validação dentro do Cloud Build
# Usa Cloud SQL Proxy para conectar ao banco

CLOUDSQL_INSTANCE="trivihair:us-central1:finaflow-db-staging"
PROXY_PORT=5432
EXCEL_FILE="${1:-data/fluxo_caixa_2025.xlsx}"
YEAR="${2:-2025}"
BACKEND_URL="${3:-https://finaflow-backend-staging-642830139828.us-central1.run.app}"

echo "================================================================"
echo "FinaFlow - Seed + Validação (Cloud Build)"
echo "================================================================"
echo "Arquivo: $EXCEL_FILE"
echo "Ano: $YEAR"
echo "Backend URL: $BACKEND_URL"
echo "================================================================"

# Baixar Cloud SQL Proxy se não existir
if [ ! -f "/tmp/cloud_sql_proxy" ]; then
  echo "📥 Baixando Cloud SQL Proxy..."
  curl -o /tmp/cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64
  chmod +x /tmp/cloud_sql_proxy
fi

# Iniciar Cloud SQL Proxy em background
echo "🔌 Iniciando Cloud SQL Proxy..."
/tmp/cloud_sql_proxy -instances="$CLOUDSQL_INSTANCE=tcp:$PROXY_PORT" > /tmp/proxy.log 2>&1 &
PROXY_PID=$!

# Aguardar proxy estar pronto
echo "⏳ Aguardando proxy estar pronto..."
sleep 5

# Verificar se proxy está rodando
if ! kill -0 $PROXY_PID 2>/dev/null; then
  echo "❌ Erro: Cloud SQL Proxy não iniciou"
  cat /tmp/proxy.log
  exit 1
fi

# Configurar DATABASE_URL
export DATABASE_URL="postgresql://finaflow_user:Finaflow123!@127.0.0.1:$PROXY_PORT/finaflow"
export PYTHONPATH=/app

# Função para limpar proxy ao sair
cleanup() {
  echo "🧹 Parando Cloud SQL Proxy..."
  kill $PROXY_PID 2>/dev/null || true
  wait $PROXY_PID 2>/dev/null || true
}
trap cleanup EXIT

# 1. Seed
echo ""
echo "[1/2] Executando seed..."
python3 -m scripts.seed_from_client_sheet --file "$EXCEL_FILE"
SEED_EXIT=$?

if [ $SEED_EXIT -ne 0 ]; then
  echo "❌ Seed falhou. Abortando validação."
  exit 1
fi

echo "✅ Seed concluído com sucesso."

# 2. Validação
echo ""
echo "[2/2] Executando validação..."
export BACKEND_URL="$BACKEND_URL"
python3 -m scripts.validate_dashboard_against_client_sheet \
  --file "$EXCEL_FILE" \
  --year "$YEAR" \
  --backend-url "$BACKEND_URL"
VAL_EXIT=$?

if [ $VAL_EXIT -ne 0 ]; then
  echo "❌ Validação encontrou mismatches ou erros."
  exit 2
fi

echo ""
echo "✅ Seed + validação concluídos sem mismatches."
echo "✅ Versão 2.0 consistente entre planilha, banco e API."
exit 0

