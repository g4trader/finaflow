#!/bin/bash
# Script para re-seed do ano 2025 após correção de CUSTO

set -e

BACKEND_PATH="$(cd "$(dirname "$0")/.." && pwd)"
EXCEL_FILE="$BACKEND_PATH/data/fluxo_caixa_2025.xlsx"

echo "="*60
echo "🔄 RE-SEED 2025 - Correção de CUSTO"
echo "="*60
echo ""

# Verificar arquivo
if [ ! -f "$EXCEL_FILE" ]; then
    echo "❌ Arquivo Excel não encontrado: $EXCEL_FILE"
    exit 1
fi

echo "📁 Arquivo: $EXCEL_FILE"
echo ""

# Limpar arquivo de log anterior se existir
LOG_FILE="$BACKEND_PATH/artifacts/seed_classification_2025.jsonl"
if [ -f "$LOG_FILE" ]; then
    echo "🗑️  Limpando log anterior..."
    rm "$LOG_FILE"
fi

# Executar seed com COST_DEBUG=1
echo "🌱 Executando seed com COST_DEBUG=1..."
echo ""

cd "$BACKEND_PATH"
COST_DEBUG=1 python3 -m scripts.seed_from_client_sheet \
    --file "$EXCEL_FILE" \
    --reset-data

echo ""
echo "✅ Seed concluído!"
echo "📄 Log de classificação: $LOG_FILE"
echo ""

