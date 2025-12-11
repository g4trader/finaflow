#!/bin/bash
# Script para executar validação do dashboard com Cloud SQL Proxy
# Uso: ./run_validation_with_proxy.sh [--year 2025] [--debug-month M] [--debug-type TIPO]

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configurações
PROJECT_ID="trivihair"
INSTANCE="trivihair:us-central1:finaflow-db-staging"
DB_USER="finaflow_user"
DB_PASSWORD="Finaflow123!"
DB_NAME="finaflow"
PROXY_PORT=5432
BACKEND_URL="${BACKEND_URL:-https://finaflow-backend-staging-642830139828.us-central1.run.app}"

echo -e "${GREEN}🚀 Iniciando validação do dashboard com Cloud SQL Proxy${NC}"
echo ""

# 1. Verificar se está no diretório backend
if [ ! -f "scripts/validate_dashboard_against_client_sheet.py" ]; then
    echo -e "${RED}❌ Erro: Execute este script do diretório backend${NC}"
    echo "   cd ~/finaflow/backend"
    exit 1
fi

# 2. Verificar se gcloud está configurado
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Erro: gcloud CLI não encontrado${NC}"
    exit 1
fi

# 3. Configurar projeto
echo -e "${YELLOW}📋 Configurando projeto GCP...${NC}"
gcloud config set project "$PROJECT_ID" > /dev/null 2>&1 || true

# 4. Verificar/iniciar Cloud SQL Proxy
echo -e "${YELLOW}🔗 Verificando Cloud SQL Proxy...${NC}"

PROXY_PID=$(pgrep -f "cloud_sql_proxy.*$INSTANCE" || true)

if [ -z "$PROXY_PID" ]; then
    echo -e "${YELLOW}   Proxy não encontrado. Iniciando...${NC}"
    
    # Baixar proxy se não existir
    if [ ! -f "./cloud_sql_proxy" ]; then
        echo -e "${YELLOW}   Baixando Cloud SQL Proxy...${NC}"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            curl -o cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.darwin.amd64
        else
            # Linux
            curl -o cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64
        fi
        chmod +x cloud_sql_proxy
    fi
    
    # Iniciar proxy em background
    ./cloud_sql_proxy -instances="$INSTANCE=tcp:$PROXY_PORT" > /tmp/cloud_sql_proxy.log 2>&1 &
    PROXY_PID=$!
    echo -e "${GREEN}   ✅ Proxy iniciado (PID: $PROXY_PID)${NC}"
    
    # Aguardar proxy estar pronto
    echo -e "${YELLOW}   Aguardando proxy estar pronto...${NC}"
    sleep 5
    
    # Verificar se porta está aberta
    if ! nc -z 127.0.0.1 $PROXY_PORT 2>/dev/null; then
        echo -e "${RED}   ❌ Erro: Proxy não conseguiu abrir porta $PROXY_PORT${NC}"
        echo -e "${YELLOW}   Logs do proxy:${NC}"
        tail -20 /tmp/cloud_sql_proxy.log
        exit 1
    fi
    
    echo -e "${GREEN}   ✅ Proxy pronto na porta $PROXY_PORT${NC}"
    PROXY_STARTED_BY_SCRIPT=true
else
    echo -e "${GREEN}   ✅ Proxy já está rodando (PID: $PROXY_PID)${NC}"
    PROXY_STARTED_BY_SCRIPT=false
fi

# 5. Configurar DATABASE_URL
export DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@127.0.0.1:${PROXY_PORT}/${DB_NAME}"
echo -e "${GREEN}✅ DATABASE_URL configurado${NC}"

# 6. Verificar conexão com banco
echo -e "${YELLOW}🔍 Testando conexão com banco...${NC}"
python3 << EOF
import sys
import os
sys.path.insert(0, '.')
from app.database import SessionLocal
try:
    db = SessionLocal()
    db.execute("SELECT 1")
    db.close()
    print("✅ Conexão com banco OK")
except Exception as e:
    print(f"❌ Erro ao conectar: {e}")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Falha ao conectar ao banco. Verifique:${NC}"
    echo "   1. Cloud SQL Proxy está rodando"
    echo "   2. Credenciais estão corretas"
    echo "   3. Instância Cloud SQL está acessível"
    exit 1
fi

# 7. Verificar se arquivo Excel existe
EXCEL_FILE="data/fluxo_caixa_2025.xlsx"
if [ ! -f "$EXCEL_FILE" ]; then
    echo -e "${RED}❌ Erro: Arquivo Excel não encontrado: $EXCEL_FILE${NC}"
    exit 1
fi

# 8. Executar validação
echo ""
echo -e "${GREEN}📊 Executando validação do dashboard...${NC}"
echo ""

# Passar todos os argumentos para o script Python
python3 -m scripts.validate_dashboard_against_client_sheet \
    --file "$EXCEL_FILE" \
    --backend-url "$BACKEND_URL" \
    "$@"

VALIDATION_EXIT_CODE=$?

# 9. Limpar proxy se foi iniciado por este script
if [ "$PROXY_STARTED_BY_SCRIPT" = true ]; then
    echo ""
    echo -e "${YELLOW}🧹 Parando Cloud SQL Proxy...${NC}"
    kill $PROXY_PID 2>/dev/null || true
    wait $PROXY_PID 2>/dev/null || true
    echo -e "${GREEN}✅ Proxy parado${NC}"
fi

# 10. Retornar código de saída da validação
exit $VALIDATION_EXIT_CODE

