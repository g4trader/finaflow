#!/bin/bash

# Script de Deploy Manual para STAGING
# Execute este script com suas credenciais do GCP

set -e

echo "🚀 Deploy Manual - FinaFlow Backend STAGING"
echo "==========================================="

# Variáveis
PROJECT_ID="project-c6f9c72d-aca4-476d-82f"
REGION="us-central1"
SERVICE_NAME="finaflow-backend-staging"

# Verificar se gcloud está instalado
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI não encontrado. Instale: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Configurar projeto
echo "📋 Configurando projeto GCP..."
gcloud config set project ${PROJECT_ID}

# Verificar autenticação
echo "🔐 Verificando autenticação..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Nenhuma conta autenticada. Execute: gcloud auth login"
    exit 1
fi

echo "✅ Autenticado como: $(gcloud auth list --filter=status:ACTIVE --format='value(account)')"

# Navegar para o diretório do backend
cd "$(dirname "$0")"

# Verificar se o arquivo de env vars existe
if [ ! -f "env_vars_staging.yaml" ]; then
    echo "❌ Arquivo env_vars_staging.yaml não encontrado"
    exit 1
fi

# Fazer deploy
echo ""
echo "☁️  Fazendo deploy no Cloud Run..."
echo "   Serviço: ${SERVICE_NAME}"
echo "   Região: ${REGION}"
echo "   Projeto: ${PROJECT_ID}"
echo ""

gcloud run deploy ${SERVICE_NAME} \
  --source . \
  --region ${REGION} \
  --platform managed \
  --allow-unauthenticated \
  --add-cloudsql-instances ${PROJECT_ID}:${REGION}:finaflow-db-staging \
  --env-vars-file env_vars_staging.yaml \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 600 \
  --concurrency 80 \
  --min-instances 1 \
  --max-instances 10 \
  --cpu-boost

echo ""
echo "✅ Deploy concluído com sucesso!"
echo ""
echo "📋 URL do serviço:"
gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format="value(status.url)"
echo ""
echo "🔍 Para ver os logs:"
echo "   gcloud logging tail \"resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE_NAME}\" --project=${PROJECT_ID}"
echo ""










