#!/bin/bash

# Script para executar validação de dados no Cloud Shell usando Cloud SQL Proxy
# Uso: curl -s https://raw.githubusercontent.com/g4trader/finaflow/staging/scripts/execute_validation_with_proxy.sh | bash

set -e

echo "============================================================"
echo "🔍 EXECUTAR VALIDAÇÃO DE DADOS - CLOUD SQL PROXY"
echo "============================================================"
echo ""

# 0. Configurar projeto
echo "⚙️  0. Configurando projeto gcloud..."
gcloud config set project trivihair
echo "✅ Projeto configurado"
echo ""

# 1. Iniciar Cloud SQL Proxy
echo "🔌 1. Iniciando Cloud SQL Proxy..."
if ! pgrep -x cloud_sql_proxy > /dev/null; then
    # Parar proxy anterior se existir
    pkill cloud_sql_proxy || true
    rm -f cloud_sql_proxy
    
    # Baixar proxy
    echo "  Baixando Cloud SQL Proxy..."
    curl -o cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64
    chmod +x cloud_sql_proxy
    
    # Iniciar proxy
    echo "  Iniciando proxy (logs em: /tmp/cloud_sql_proxy_$$.log)..."
    ./cloud_sql_proxy -instances=trivihair:us-central1:finaflow-db-staging=tcp:5432 > /tmp/cloud_sql_proxy_$$.log 2>&1 &
    PROXY_PID=$!
    
    # Configurar credenciais se necessário
    if ! gcloud auth application-default print-access-token > /dev/null 2>&1; then
        echo "  Configurando credenciais automáticas..."
        gcloud auth application-default login --no-launch-browser --quiet || true
    fi
    
    # Aguardar proxy iniciar
    echo "  Aguardando proxy iniciar..."
    sleep 5
    
    # Verificar se proxy está rodando
    if ! ps -p $PROXY_PID > /dev/null 2>&1; then
        echo "❌ Falha ao iniciar Cloud SQL Proxy"
        cat /tmp/cloud_sql_proxy_$$.log
        exit 1
    fi
    
    # Verificar se porta está ouvindo
    if ! netstat -an | grep :5432 | grep LISTEN > /dev/null 2>&1; then
        echo "  Aguardando mais alguns segundos..."
        sleep 5
        if ! netstat -an | grep :5432 | grep LISTEN > /dev/null 2>&1; then
            echo "❌ Falha ao iniciar Cloud SQL Proxy (porta 5432 não está ouvindo)"
            cat /tmp/cloud_sql_proxy_$$.log
            exit 1
        fi
    fi
    
    echo "✅ Cloud SQL Proxy iniciado e porta 5432 está ouvindo (PID: $PROXY_PID)"
else
    echo "✅ Cloud SQL Proxy já está rodando"
    PROXY_PID=$(pgrep -x cloud_sql_proxy | head -1)
fi
echo ""

# 2. Clonar repositório
echo "📁 2. Clonando repositório..."
cd ~
if [ -d "finaflow" ]; then
    cd finaflow
    git fetch origin
    git checkout staging
    git pull origin staging
else
    git clone https://github.com/g4trader/finaflow.git
    cd finaflow
    git checkout staging
fi
echo "✅ Repositório atualizado"
echo ""

# 3. Instalar dependências
echo "📦 3. Instalando dependências..."
cd backend
pip3 install -q -r requirements.txt
pip3 install -q pandas openpyxl
echo "✅ Dependências instaladas"
echo ""

# 4. Configurar DATABASE_URL
echo "🔧 4. Configurando DATABASE_URL..."
export DATABASE_URL="postgresql://finaflow_user:Finaflow123!@127.0.0.1:5432/finaflow"
echo "✅ DATABASE_URL: postgresql://finaflow_user:***@127.0.0.1:5432/finaflow"
echo ""

# 5. Executar validação
echo "🚀 5. Executando validação..."
echo "🔗 Conectando ao banco via TCP: 127.0.0.1:5432"
python3 -m scripts.validate_seed_against_client_sheet --file data/fluxo_caixa_2025.xlsx
VALIDATION_EXIT_CODE=$?
echo ""

# 6. Parar Cloud SQL Proxy (se iniciado por este script)
if [ ! -z "$PROXY_PID" ] && ps -p $PROXY_PID > /dev/null 2>&1; then
    echo "🛑 6. Parando Cloud SQL Proxy..."
    kill $PROXY_PID || true
    wait $PROXY_PID 2>/dev/null || true
    echo "✅ Cloud SQL Proxy parado"
    echo ""
fi

# 7. Resultado final
echo "============================================================"
if [ $VALIDATION_EXIT_CODE -eq 0 ]; then
    echo "✅ VALIDAÇÃO CONCLUÍDA COM SUCESSO!"
else
    echo "❌ VALIDAÇÃO ENCONTROU INCOMPATIBILIDADES"
fi
echo "============================================================"
echo ""
echo "📄 Logs completos salvos em:"
echo "   - ~/finaflow/backend/logs/validate_seed_*.log"
echo ""

exit $VALIDATION_EXIT_CODE

