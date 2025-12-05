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
curl -o cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64
chmod +x cloud_sql_proxy
./cloud_sql_proxy -instances=trivihair:us-central1:finaflow-db-staging=tcp:5432 &
PROXY_PID=$!
sleep 5
echo "✅ Cloud SQL Proxy iniciado (PID: $PROXY_PID)"

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
echo "------------------------------------------------------------"
echo "📈 Primeira execução:"
STATS1=$(grep -A 6 "ESTATÍSTICAS DO SEED" logs/staging_seed_${TIMESTAMP1}.log | tail -6 || echo "")
if [ -n "$STATS1" ]; then
    echo "$STATS1"
else
    echo "  (Estatísticas não encontradas no log - verificar logs/staging_seed_${TIMESTAMP1}.log)"
fi

echo ""
echo "📈 Segunda execução (idempotência):"
STATS2=$(grep -A 6 "ESTATÍSTICAS DO SEED" logs/staging_seed_idempotency_${TIMESTAMP2}.log | tail -6 || echo "")
if [ -n "$STATS2" ]; then
    echo "$STATS2"
else
    echo "  (Estatísticas não encontradas no log - verificar logs/staging_seed_idempotency_${TIMESTAMP2}.log)"
fi
echo "------------------------------------------------------------"

# Extrair valores numéricos para resumo
echo ""
echo "📊 Resumo Final:"
echo "------------------------------------------------------------"
if [ -n "$STATS1" ]; then
    echo "Primeira execução:"
    echo "$STATS1" | grep -E "Grupos:|Subgrupos:|Contas:|Lançamentos Diários:|Lançamentos Previstos:" || true
fi
if [ -n "$STATS2" ]; then
    echo ""
    echo "Segunda execução (idempotência):"
    echo "$STATS2" | grep -E "Grupos:|Subgrupos:|Contas:|Lançamentos Diários:|Lançamentos Previstos:" || true
fi
echo "------------------------------------------------------------"

# 8. Parar proxy
echo ""
echo "🛑 8. Parando Cloud SQL Proxy..."
kill $PROXY_PID 2>/dev/null || true
wait $PROXY_PID 2>/dev/null || true
echo "✅ Cloud SQL Proxy parado"

# 9. Resumo
echo ""
echo "============================================================"
echo "✅ SEED EXECUTADO COM SUCESSO!"
echo "============================================================"
echo "📄 Logs salvos em:"
echo "   - backend/logs/staging_seed_${TIMESTAMP1}.log"
echo "   - backend/logs/staging_seed_idempotency_${TIMESTAMP2}.log"
echo ""
echo "📊 Para ver estatísticas detalhadas, consulte os logs acima."
echo "============================================================"

