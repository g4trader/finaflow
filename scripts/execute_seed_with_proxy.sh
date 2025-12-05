#!/bin/bash
# Script para executar seed STAGING usando Cloud SQL Proxy
# Execute este script no Cloud Shell
# Uso: curl -s https://raw.githubusercontent.com/g4trader/finaflow/staging/scripts/execute_seed_with_proxy.sh | bash

set -e

echo "============================================================"
echo "🌱 EXECUTAR SEED STAGING - CLOUD SQL PROXY"
echo "============================================================"

# 0. Configurar projeto gcloud
echo ""
echo "⚙️  0. Configurando projeto gcloud..."
gcloud config set project trivihair >/dev/null 2>&1 || echo "⚠️  Aviso: não foi possível configurar projeto (continuando...)"
echo "✅ Projeto configurado"

# 1. Iniciar Cloud SQL Proxy
echo ""
echo "🔌 1. Iniciando Cloud SQL Proxy..."
# Parar qualquer instância anterior do proxy
pkill cloud_sql_proxy 2>/dev/null || true
sleep 2
# Remover arquivo antigo se existir
rm -f cloud_sql_proxy
# Baixar Cloud SQL Proxy
curl -o cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64
chmod +x cloud_sql_proxy
# Iniciar proxy em background
./cloud_sql_proxy -instances=trivihair:us-central1:finaflow-db-staging=tcp:5432 > /dev/null 2>&1 &
PROXY_PID=$!
sleep 5
# Verificar se o proxy está rodando
if ps -p $PROXY_PID > /dev/null 2>&1; then
    echo "✅ Cloud SQL Proxy iniciado (PID: $PROXY_PID)"
else
    echo "❌ Falha ao iniciar Cloud SQL Proxy"
    exit 1
fi

# 2. Clonar repositório
echo ""
echo "📁 2. Clonando repositório..."
cd ~
rm -rf finaflow
git clone https://github.com/g4trader/finaflow.git
cd finaflow
git checkout staging
cd backend
echo "✅ Repositório clonado"

# 3. Instalar dependências
echo ""
echo "📦 3. Instalando dependências..."
pip3 install -q -r requirements.txt
pip3 install -q pandas openpyxl
echo "✅ Dependências instaladas"

# 4. Configurar DATABASE_URL
echo ""
echo "🔧 4. Configurando DATABASE_URL..."
export DATABASE_URL="postgresql://finaflow_user:Finaflow123!@127.0.0.1:5432/finaflow"
echo "✅ DATABASE_URL: $DATABASE_URL"

# 5. Executar seed (primeira vez)
echo ""
echo "🚀 5. Executando seed (primeira vez)..."
mkdir -p logs
TIMESTAMP1=$(date +%Y%m%d_%H%M%S)
python3 -m scripts.seed_from_client_sheet --file data/fluxo_caixa_2025.xlsx 2>&1 | tee logs/staging_seed_${TIMESTAMP1}.log
SEED_EXIT_CODE=$?

if [ $SEED_EXIT_CODE -ne 0 ]; then
    echo "❌ Seed falhou com código $SEED_EXIT_CODE"
    kill $PROXY_PID 2>/dev/null || true
    exit 1
fi

# 6. Executar seed (segunda vez - idempotência)
echo ""
echo "🔁 6. Executando seed (segunda vez - idempotência)..."
TIMESTAMP2=$(date +%Y%m%d_%H%M%S)
python3 -m scripts.seed_from_client_sheet --file data/fluxo_caixa_2025.xlsx 2>&1 | tee logs/staging_seed_idempotency_${TIMESTAMP2}.log
SEED_EXIT_CODE=$?

if [ $SEED_EXIT_CODE -ne 0 ]; then
    echo "❌ Seed (idempotência) falhou com código $SEED_EXIT_CODE"
    kill $PROXY_PID 2>/dev/null || true
    exit 1
fi

# 7. Extrair e exibir estatísticas dos logs
echo ""
echo "📊 7. Estatísticas do Seed:"
echo "============================================================"

# Primeira execução
echo "📈 Primeira execução:"
STATS1=$(grep -A 6 "ESTATÍSTICAS DO SEED" logs/staging_seed_${TIMESTAMP1}.log 2>/dev/null | tail -6 || echo "")
if [ -n "$STATS1" ]; then
    echo "$STATS1"
    # Extrair valores para resumo
    GRUPOS1=$(echo "$STATS1" | grep "Grupos:" | sed 's/.*Grupos: //' || echo "N/A")
    SUBGRUPOS1=$(echo "$STATS1" | grep "Subgrupos:" | sed 's/.*Subgrupos: //' || echo "N/A")
    CONTAS1=$(echo "$STATS1" | grep "Contas:" | sed 's/.*Contas: //' || echo "N/A")
    LANC_DIARIOS1=$(echo "$STATS1" | grep "Lançamentos Diários:" | sed 's/.*Lançamentos Diários: //' || echo "N/A")
    LANC_PREVISTOS1=$(echo "$STATS1" | grep "Lançamentos Previstos:" | sed 's/.*Lançamentos Previstos: //' || echo "N/A")
else
    echo "  ⚠️  Estatísticas não encontradas no log"
    echo "  📄 Verificar: logs/staging_seed_${TIMESTAMP1}.log"
fi

echo ""
echo "📈 Segunda execução (idempotência):"
STATS2=$(grep -A 6 "ESTATÍSTICAS DO SEED" logs/staging_seed_idempotency_${TIMESTAMP2}.log 2>/dev/null | tail -6 || echo "")
if [ -n "$STATS2" ]; then
    echo "$STATS2"
    # Extrair valores para resumo
    GRUPOS2=$(echo "$STATS2" | grep "Grupos:" | sed 's/.*Grupos: //' || echo "N/A")
    SUBGRUPOS2=$(echo "$STATS2" | grep "Subgrupos:" | sed 's/.*Subgrupos: //' || echo "N/A")
    CONTAS2=$(echo "$STATS2" | grep "Contas:" | sed 's/.*Contas: //' || echo "N/A")
    LANC_DIARIOS2=$(echo "$STATS2" | grep "Lançamentos Diários:" | sed 's/.*Lançamentos Diários: //' || echo "N/A")
    LANC_PREVISTOS2=$(echo "$STATS2" | grep "Lançamentos Previstos:" | sed 's/.*Lançamentos Previstos: //' || echo "N/A")
else
    echo "  ⚠️  Estatísticas não encontradas no log"
    echo "  📄 Verificar: logs/staging_seed_idempotency_${TIMESTAMP2}.log"
fi

echo "============================================================"

# Resumo final
echo ""
echo "📊 RESUMO FINAL:"
echo "------------------------------------------------------------"
echo "Primeira execução:"
echo "  - Grupos: $GRUPOS1"
echo "  - Subgrupos: $SUBGRUPOS1"
echo "  - Contas: $CONTAS1"
echo "  - Lançamentos Diários: $LANC_DIARIOS1"
echo "  - Lançamentos Previstos: $LANC_PREVISTOS1"
echo ""
echo "Segunda execução (idempotência):"
echo "  - Grupos: $GRUPOS2"
echo "  - Subgrupos: $SUBGRUPOS2"
echo "  - Contas: $CONTAS2"
echo "  - Lançamentos Diários: $LANC_DIARIOS2"
echo "  - Lançamentos Previstos: $LANC_PREVISTOS2"
echo "------------------------------------------------------------"

# 8. Parar proxy
echo ""
echo "🛑 8. Parando Cloud SQL Proxy..."
kill $PROXY_PID 2>/dev/null || pkill cloud_sql_proxy 2>/dev/null || true
wait $PROXY_PID 2>/dev/null || true
echo "✅ Cloud SQL Proxy parado"

# 9. Resumo final
echo ""
echo "============================================================"
echo "✅ SEED CONCLUÍDO COM SUCESSO!"
echo "============================================================"
echo ""
echo "📄 Logs completos salvos em:"
echo "   - ~/finaflow/backend/logs/staging_seed_${TIMESTAMP1}.log"
echo "   - ~/finaflow/backend/logs/staging_seed_idempotency_${TIMESTAMP2}.log"
echo ""
echo "📊 Próximos passos:"
echo "   1. Validar dados no frontend: https://finaflow-lcz5.vercel.app/"
echo "   2. Executar QA funcional: docs/CHECKLIST_QA_FUNCIONAL_POS_SEED.md"
echo "   3. Verificar status: docs/SEED_STAGING_STATUS.md"
echo ""
echo "============================================================"

