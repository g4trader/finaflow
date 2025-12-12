#!/bin/bash
# Script para criar/atualizar Cloud Run Jobs de seed e validação
# Executa no Cloud Shell ou localmente com gcloud configurado

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configurações
PROJECT_ID="trivihair"
REGION="us-central1"
SERVICE_NAME="finaflow-backend-staging"
SEED_JOB_NAME="finaflow-seed-staging-job"
VALIDATION_JOB_NAME="finaflow-validate-dashboard-staging-job"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   Configurando Cloud Run Jobs para Seed e Validação${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# 1. Configurar projeto
echo -e "${YELLOW}📋 Configurando projeto GCP...${NC}"
gcloud config set project "$PROJECT_ID" > /dev/null 2>&1 || true

# 2. Descobrir configuração do serviço
echo -e "${YELLOW}🔍 Descobrindo configuração do serviço ${SERVICE_NAME}...${NC}"

SERVICE_JSON=$(gcloud run services describe "$SERVICE_NAME" \
    --region="$REGION" \
    --format=json 2>/dev/null)

if [ -z "$SERVICE_JSON" ]; then
    echo -e "${RED}❌ Erro: Serviço ${SERVICE_NAME} não encontrado${NC}"
    exit 1
fi

# Extrair informações
IMAGE=$(echo "$SERVICE_JSON" | jq -r '.spec.template.spec.containers[0].image')
SERVICE_ACCOUNT=$(echo "$SERVICE_JSON" | jq -r '.spec.template.spec.serviceAccountName // .spec.template.spec.serviceAccountName // ""')
BACKEND_URL=$(echo "$SERVICE_JSON" | jq -r '.status.url')

echo -e "${GREEN}✅ Configuração descoberta:${NC}"
echo "   Image: $IMAGE"
echo "   Service Account: ${SERVICE_ACCOUNT:-default}"
echo "   Backend URL: $BACKEND_URL"
echo ""

# 3. Extrair env vars do serviço
echo -e "${YELLOW}📋 Extraindo variáveis de ambiente do serviço...${NC}"

ENV_VARS=$(echo "$SERVICE_JSON" | jq -r '.spec.template.spec.containers[0].env[] | "\(.name)=\(.value // "")"' 2>/dev/null || echo "")

# Construir string de env vars para os jobs
ENV_VARS_ARGS=""
if [ -n "$ENV_VARS" ]; then
    while IFS= read -r line; do
        if [ -n "$line" ]; then
            name=$(echo "$line" | cut -d'=' -f1)
            value=$(echo "$line" | cut -d'=' -f2-)
            # Pular variáveis que não são relevantes para jobs
            if [[ ! "$name" =~ ^(PORT|HOST|ENVIRONMENT)$ ]]; then
                if [ -n "$value" ]; then
                    ENV_VARS_ARGS="$ENV_VARS_ARGS --set-env-vars=$name=$value"
                fi
            fi
        fi
    done <<< "$ENV_VARS"
fi

# BACKEND_URL será adicionado explicitamente no job de validação, não aqui

echo -e "${GREEN}✅ Variáveis de ambiente extraídas${NC}"
echo ""

# 4. Criar/atualizar job de seed
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   1. Criando/Atualizando Job de Seed${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

gcloud run jobs deploy "$SEED_JOB_NAME" \
    --region="$REGION" \
    --image="$IMAGE" \
    --service-account="$SERVICE_ACCOUNT" \
    $ENV_VARS_ARGS \
    --set-env-vars="PYTHONPATH=/app" \
    --max-retries=0 \
    --tasks=1 \
    --cpu=1 \
    --memory=1Gi \
    --command=sh \
    --args="-c","cd /app && python -m scripts.seed_from_client_sheet --file data/fluxo_caixa_2025.xlsx" \
    --quiet

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Job de seed criado/atualizado: ${SEED_JOB_NAME}${NC}"
else
    echo -e "${RED}❌ Erro ao criar job de seed${NC}"
    exit 1
fi

echo ""

# 5. Criar/atualizar job de validação
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   2. Criando/Atualizando Job de Validação${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Construir env vars para validação (remover BACKEND_URL das env vars do serviço se existir)
VALIDATION_ENV_VARS_ARGS="$ENV_VARS_ARGS"
# Remover BACKEND_URL das env vars do serviço se existir
if echo "$ENV_VARS" | grep -q "BACKEND_URL"; then
    VALIDATION_ENV_VARS_ARGS=$(echo "$VALIDATION_ENV_VARS_ARGS" | sed 's/--set-env-vars=BACKEND_URL=[^ ]*//g')
fi
# BACKEND_URL será adicionado explicitamente no comando de deploy

gcloud run jobs deploy "$VALIDATION_JOB_NAME" \
    --region="$REGION" \
    --image="$IMAGE" \
    --service-account="$SERVICE_ACCOUNT" \
    $VALIDATION_ENV_VARS_ARGS \
    --set-env-vars="PYTHONPATH=/app" \
    --set-env-vars="BACKEND_URL=$BACKEND_URL" \
    --max-retries=0 \
    --tasks=1 \
    --cpu=1 \
    --memory=1Gi \
    --command=sh \
    --args="-c","cd /app && python -m scripts.validate_dashboard_against_client_sheet --file data/fluxo_caixa_2025.xlsx --year 2025 --backend-url $BACKEND_URL" \
    --quiet

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Job de validação criado/atualizado: ${VALIDATION_JOB_NAME}${NC}"
else
    echo -e "${RED}❌ Erro ao criar job de validação${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   ✅ Jobs criados com sucesso!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}📋 Próximos passos:${NC}"
echo ""
echo "1. Executar job de seed:"
echo "   gcloud run jobs execute $SEED_JOB_NAME --region=$REGION --wait"
echo ""
echo "2. Executar job de validação:"
echo "   gcloud run jobs execute $VALIDATION_JOB_NAME --region=$REGION --wait"
echo ""
echo "3. Ver logs:"
echo "   gcloud logging read \"resource.type=cloud_run_job AND resource.labels.job_name=$VALIDATION_JOB_NAME\" --limit=50 --format=json"
echo ""

