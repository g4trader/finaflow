#!/bin/bash
# Script para re-seed do ano 2025 após correção de CUSTO no STAGING

set -e

BACKEND_PATH="$(cd "$(dirname "$0")/.." && pwd)"
EXCEL_FILE="$BACKEND_PATH/data/fluxo_caixa_2025.xlsx"

# DATABASE_URL do STAGING
export DATABASE_URL="${DATABASE_URL:-postgresql://finaflow_user:Finaflow123!@34.41.169.224:5432/finaflow}"

echo "============================================================"
echo "🔄 RE-SEED 2025 - Correção de CUSTO (STAGING)"
echo "============================================================"
echo ""

# Verificar arquivo
if [ ! -f "$EXCEL_FILE" ]; then
    echo "❌ Arquivo Excel não encontrado: $EXCEL_FILE"
    exit 1
fi

echo "📁 Arquivo: $EXCEL_FILE"
echo "🗄️  Banco: STAGING (${DATABASE_URL#*@})"
echo ""

# Limpar arquivo de log anterior se existir
LOG_FILE="$BACKEND_PATH/artifacts/seed_classification_2025.jsonl"
if [ -f "$LOG_FILE" ]; then
    echo "🗑️  Limpando log anterior..."
    rm "$LOG_FILE"
fi

# Criar diretório de artifacts se não existir
mkdir -p "$BACKEND_PATH/artifacts"

# Executar seed com COST_DEBUG=1 e --reset-data
echo "🌱 Executando seed com COST_DEBUG=1 e --reset-data..."
echo "⚠️  ATENÇÃO: Isso vai apagar todos os lançamentos diários e previstos do tenant!"
echo ""

cd "$BACKEND_PATH"

COST_DEBUG=1 python3 -m scripts.seed_from_client_sheet \
    --file "$EXCEL_FILE" \
    --reset-data

SEED_EXIT=$?

if [ $SEED_EXIT -ne 0 ]; then
    echo ""
    echo "❌ Seed falhou com código $SEED_EXIT"
    exit 1
fi

echo ""
echo "✅ Seed concluído!"
if [ -f "$LOG_FILE" ]; then
    LOG_LINES=$(wc -l < "$LOG_FILE" 2>/dev/null || echo "0")
    echo "📄 Log de classificação: $LOG_FILE ($LOG_LINES linhas)"
fi
echo ""
echo "🔍 Próximo passo: Executar auditoria para validar equalização"
echo "   make audit"
echo ""

