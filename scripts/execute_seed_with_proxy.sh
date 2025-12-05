#!/bin/bash
# Script para executar seed STAGING usando Cloud SQL Proxy
# Execute este script no Cloud Shell
# Uso: curl -s https://raw.githubusercontent.com/g4trader/finaflow/staging/scripts/execute_seed_with_proxy.sh | bash

set -e

echo "============================================================"
echo "🌱 EXECUTAR SEED STAGING - CLOUD SQL PROXY"
echo "============================================================"

# 0. Configurar projeto gcloud e autenticação
echo ""
echo "⚙️  0. Configurando projeto gcloud e autenticação..."
gcloud config set project trivihair >/dev/null 2>&1 || echo "⚠️  Aviso: não foi possível configurar projeto (continuando...)"

# No Cloud Shell, configurar Application Default Credentials
# O Cloud Shell tem credenciais automáticas, mas precisamos configurá-las para o proxy
echo "   Configurando credenciais para Cloud SQL Proxy..."
gcloud auth application-default print-access-token >/dev/null 2>&1 || {
    echo "   Configurando Application Default Credentials..."
    gcloud auth application-default login --no-launch-browser --quiet 2>&1 | head -5 || {
        echo "   Usando credenciais automáticas do Cloud Shell (metadata server)..."
        # Limpar variável para usar metadata server
        unset GOOGLE_APPLICATION_CREDENTIALS
    }
}

# Verificar conta ativa
ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | head -1)
if [ -n "$ACTIVE_ACCOUNT" ]; then
    echo "✅ Projeto configurado (conta: $ACTIVE_ACCOUNT)"
else
    echo "✅ Projeto configurado (usando credenciais automáticas do Cloud Shell)"
fi

# 1. Iniciar Cloud SQL Proxy
echo ""
echo "🔌 1. Iniciando Cloud SQL Proxy..."
# Parar qualquer instância anterior do proxy
pkill cloud_sql_proxy 2>/dev/null || true
sleep 2
# Remover arquivo antigo se existir
rm -f cloud_sql_proxy
# Baixar Cloud SQL Proxy
echo "   Baixando Cloud SQL Proxy..."
curl -o cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64
chmod +x cloud_sql_proxy
# Verificar se o download foi bem-sucedido
if [ ! -f cloud_sql_proxy ]; then
    echo "❌ Falha ao baixar Cloud SQL Proxy"
    exit 1
fi
echo "   Arquivo baixado com sucesso"

# Criar arquivo de log
LOG_FILE="/tmp/cloud_sql_proxy_$$.log"
echo "   Iniciando proxy (logs em: $LOG_FILE)..."

# No Cloud Shell, usar credenciais automáticas (sem especificar arquivo)
# O Cloud Shell já tem credenciais configuradas automaticamente
echo "   Usando credenciais automáticas do Cloud Shell..."

# Iniciar proxy em background com logs para debug
# No Cloud Shell, não precisa de -credential_file, usa as credenciais automáticas
./cloud_sql_proxy -instances=trivihair:us-central1:finaflow-db-staging=tcp:5432 > "$LOG_FILE" 2>&1 &
PROXY_PID=$!
echo "   PID do proxy: $PROXY_PID"

# Aguardar e verificar progressivamente
PROXY_STARTED=false
for i in {1..10}; do
    sleep 1
    # Verificar se o processo ainda está rodando
    if ! ps -p $PROXY_PID > /dev/null 2>&1; then
        echo "❌ Cloud SQL Proxy parou após $i segundos"
        echo ""
        echo "   === LOGS DO PROXY ==="
        if [ -f "$LOG_FILE" ]; then
            cat "$LOG_FILE"
        else
            echo "   Arquivo de log não encontrado: $LOG_FILE"
        fi
        echo "   ====================="
        echo ""
        exit 1
    fi
    # Verificar se a porta está ouvindo
    if netstat -an 2>/dev/null | grep -q ":5432.*LISTEN" || ss -an 2>/dev/null | grep -q ":5432.*LISTEN" || lsof -i :5432 >/dev/null 2>&1; then
        echo "✅ Cloud SQL Proxy iniciado e porta 5432 está ouvindo (PID: $PROXY_PID)"
        PROXY_STARTED=true
        break
    fi
done

# Se chegou aqui mas não iniciou, verificar logs
if [ "$PROXY_STARTED" = false ]; then
    echo "⚠️  Proxy iniciado mas porta 5432 ainda não está ouvindo após 10 segundos"
    echo ""
    echo "   === LOGS DO PROXY ==="
    if [ -f "$LOG_FILE" ]; then
        cat "$LOG_FILE"
    else
        echo "   Arquivo de log não encontrado: $LOG_FILE"
    fi
    echo "   ====================="
    echo ""
    echo "   Tentando continuar mesmo assim (pode funcionar)..."
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

