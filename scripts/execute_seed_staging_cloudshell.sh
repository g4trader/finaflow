#!/bin/bash
# Script para executar seed STAGING no Cloud Shell
# Execute este script no Cloud Shell: https://shell.cloud.google.com/

set -e

echo "============================================================"
echo "🌱 EXECUTAR SEED STAGING - CLOUD SHELL"
echo "============================================================"

# 1. Preparar repositório
cd ~
if [ -d "finaflow" ]; then
    echo "📁 Atualizando repositório..."
    cd finaflow
    git fetch origin
    git checkout staging
    git pull origin staging
else
    echo "📁 Clonando repositório..."
    git clone https://github.com/g4trader/finaflow.git
    cd finaflow
    git checkout staging
fi

# 2. Instalar dependências
echo "📦 Instalando dependências..."
cd backend
pip3 install -q -r requirements.txt
pip3 install -q pandas openpyxl

# 3. Configurar DATABASE_URL
export DATABASE_URL="postgresql://finaflow_user:Finaflow123!@/finaflow?host=/cloudsql/trivihair:us-central1:finaflow-db-staging"
echo "✅ DATABASE_URL configurada"

# 4. Executar seed (primeira vez)
echo ""
echo "🚀 Executando seed (primeira vez)..."
mkdir -p logs
TIMESTAMP1=$(date +%Y%m%d_%H%M%S)
python3 -m scripts.seed_from_client_sheet --file data/fluxo_caixa_2025.xlsx 2>&1 | tee logs/staging_seed_${TIMESTAMP1}.log

# 5. Executar seed (segunda vez - idempotência)
echo ""
echo "🔁 Executando seed (segunda vez - idempotência)..."
TIMESTAMP2=$(date +%Y%m%d_%H%M%S)
python3 -m scripts.seed_from_client_sheet --file data/fluxo_caixa_2025.xlsx 2>&1 | tee logs/staging_seed_idempotency_${TIMESTAMP2}.log

# 6. Validar via API
echo ""
echo "🧪 Validando dados via API..."
BACKEND_URL="https://finaflow-backend-staging-642830139828.us-central1.run.app"
TOKEN=$(curl -s -X POST "$BACKEND_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"qa@finaflow.test","password":"QaFinaflow123!"}' | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")

echo "📊 Plano de Contas (primeiros 5):"
curl -s -X GET "$BACKEND_URL/api/v1/chart-accounts/hierarchy" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f'Total: {len(data)} registros'); [print(f\"  - {item.get('name', 'N/A')}\") for item in data[:5]]" 2>/dev/null || echo "  Erro ao buscar"

echo ""
echo "📊 Lançamentos Diários (primeiros 5):"
curl -s -X GET "$BACKEND_URL/api/v1/lancamentos-diarios?limit=5" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys, json; data=json.load(sys.stdin); items=data.get('items', data) if isinstance(data, dict) else data; print(f'Total: {len(items)} registros'); [print(f\"  - {item.get('observacoes', 'N/A')[:50]}\") for item in items[:5]]" 2>/dev/null || echo "  Erro ao buscar"

echo ""
echo "📊 Lançamentos Previstos (primeiros 5):"
curl -s -X GET "$BACKEND_URL/api/v1/lancamentos-previstos?limit=5" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys, json; data=json.load(sys.stdin); items=data.get('items', data) if isinstance(data, dict) else data; print(f'Total: {len(items)} registros'); [print(f\"  - {item.get('observacoes', 'N/A')[:50]}\") for item in items[:5]]" 2>/dev/null || echo "  Erro ao buscar"

# 7. Commitar logs
echo ""
echo "📦 Commitando logs..."
cd ~/finaflow
git add backend/logs/*.log 2>/dev/null || true
git commit -m "qa(seed): executar seed do STAGING a partir da planilha do cliente e registrar evidências" || echo "⚠️  Nenhuma mudança para commitar"
git push origin staging || echo "⚠️  Push falhou"

echo ""
echo "============================================================"
echo "✅ SEED EXECUTADO COM SUCESSO!"
echo "============================================================"
echo "📄 Logs salvos em:"
echo "   - backend/logs/staging_seed_${TIMESTAMP1}.log"
echo "   - backend/logs/staging_seed_idempotency_${TIMESTAMP2}.log"

