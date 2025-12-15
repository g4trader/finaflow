#!/usr/bin/env bash

set -euo pipefail

# ================================================================
# FinaFlow - Seed + Validação (v2.0 QA)
# ================================================================

# Defaults
FILE="data/fluxo_caixa_2025.xlsx"
YEAR="2025"

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --file)
      FILE="$2"
      shift 2
      ;;
    --year)
      YEAR="$2"
      shift 2
      ;;
    *)
      echo "Arg desconhecido: $1" >&2
      exit 1
      ;;
  esac
done

# Defaults de STAGING (somente se não estiverem setados)
: "${DATABASE_URL:=postgresql://finaflow_user:Finaflow123!@127.0.0.1:5432/finaflow}"
: "${BACKEND_URL:=https://finaflow-backend-staging-642830139828.us-central1.run.app}"

# Máscara simples do DATABASE_URL (evitar expor senha)
DB_MASK="(mascarado)"
if [[ "$DATABASE_URL" == *"@"* ]]; then
  host_part="${DATABASE_URL#*@}"
  DB_MASK="$host_part"
fi

# Cabeçalho
echo "================================================================"
echo "FinaFlow - Seed + Validação (v2.0 QA)"
echo "================================================================"
echo "Arquivo: $FILE"
echo "Ano: $YEAR"
echo "DATABASE_URL: $DB_MASK"
echo "BACKEND_URL: $BACKEND_URL"
echo "================================================================"
echo ""

# Garantir diretório de logs
mkdir -p logs

# 1. Seed
echo "[1/2] Executando seed (scripts.seed_from_client_sheet)..."
python3 -m scripts.seed_from_client_sheet \
  --file "$FILE"
SEED_EXIT=$?

if [[ $SEED_EXIT -ne 0 ]]; then
  echo ""
  echo "❌ Seed falhou (scripts.seed_from_client_sheet). Abortando validação." >&2
  exit 1
fi

echo "✅ Seed concluído com sucesso."
echo ""

# 2. Validação
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="logs/validate_dashboard_${TIMESTAMP}.log"

echo "[2/2] Executando validação (scripts.validate_dashboard_against_client_sheet)..."
echo "Log detalhado: $LOG_FILE"

python3 -m scripts.validate_dashboard_against_client_sheet \
  --file "$FILE" \
  --year "$YEAR" \
  --backend-url "$BACKEND_URL" \
  --log-file "$LOG_FILE"
VAL_EXIT=$?

if [[ $VAL_EXIT -ne 0 ]]; then
  echo ""
  echo "❌ Validação encontrou mismatches ou erros. Ver detalhes em: $LOG_FILE" >&2
  exit 2
fi

echo ""
echo "✅ Seed + validação concluídos sem mismatches."
echo "✅ Versão 2.0 consistente entre planilha, banco e API."
exit 0


{
  "cells": [],
  "metadata": {
    "language_info": {
      "name": "python"
    }
  },
  "nbformat": 4,
  "nbformat_minor": 2
}