#!/bin/bash

# Script para criar ambiente STAGING completo
# Projeto: trivihair
# Região: us-central1

set -e

PROJECT_ID="trivihair"
REGION="us-central1"
DB_INSTANCE="finaflow-db-staging"
DB_NAME="finaflow_db"
DB_USER="finaflow_user"
DB_PASSWORD="finaflow_password_staging_2024"
SERVICE_NAME="finaflow-backend-staging"

echo "🚀 Criando ambiente STAGING para FinaFlow..."
echo "Projeto: $PROJECT_ID"
echo "Região: $REGION"
echo ""

# Configurar projeto
gcloud config set project $PROJECT_ID

# 1. Criar instância Cloud SQL (PostgreSQL)
echo "📦 Criando instância Cloud SQL: $DB_INSTANCE"
gcloud sql instances create $DB_INSTANCE \
  --database-version=POSTGRES_14 \
  --tier=db-f1-micro \
  --region=$REGION \
  --project=$PROJECT_ID \
  --storage-type=SSD \
  --storage-size=20GB \
  --storage-auto-increase \
  --backup-start-time=03:00 \
  --enable-bin-log \
  --maintenance-window-day=SUN \
  --maintenance-window-hour=04 \
  --maintenance-release-channel=production \
  --deletion-protection=false || echo "⚠️  Instância pode já existir"

# 2. Criar banco de dados
echo "📊 Criando banco de dados: $DB_NAME"
gcloud sql databases create $DB_NAME \
  --instance=$DB_INSTANCE \
  --project=$PROJECT_ID || echo "⚠️  Banco pode já existir"

# 3. Criar usuário (se não existir)
echo "👤 Configurando usuário do banco"
gcloud sql users create $DB_USER \
  --instance=$DB_INSTANCE \
  --password=$DB_PASSWORD \
  --project=$PROJECT_ID || echo "⚠️  Usuário pode já existir"

# 4. Atualizar senha do usuário (garantir que está correta)
echo "🔐 Atualizando senha do usuário"
gcloud sql users set-password $DB_USER \
  --instance=$DB_INSTANCE \
  --password=$DB_PASSWORD \
  --project=$PROJECT_ID

# 5. Deploy do backend no Cloud Run
echo "🚀 Fazendo deploy do backend staging..."
cd backend
gcloud builds submit --config=cloudbuild-staging.yaml --project=$PROJECT_ID . || {
  echo "❌ Erro no deploy. Tentando deploy manual..."
  
  # Deploy manual alternativo
  docker build -t gcr.io/$PROJECT_ID/finaflow-backend-staging .
  docker push gcr.io/$PROJECT_ID/finaflow-backend-staging
  
  gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/finaflow-backend-staging \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --add-cloudsql-instances $PROJECT_ID:$REGION:$DB_INSTANCE \
    --set-env-vars DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@/$DB_NAME?host=/cloudsql/$PROJECT_ID:$REGION:$DB_INSTANCE,SECRET_KEY=finaflow-secret-key-2024-staging,JWT_SECRET=finaflow-secret-key-2024-staging,CORS_ORIGINS=https://finaflow-staging.vercel.app,https://finaflow.vercel.app,ALLOWED_HOSTS=finaflow-staging.vercel.app,finaflow.vercel.app,PROJECT_ID=$PROJECT_ID,DATASET=finaflow_staging,ENVIRONMENT=staging \
    --port 8080 \
    --memory 2Gi \
    --cpu 2 \
    --timeout 600 \
    --concurrency 80 \
    --min-instances 1 \
    --max-instances 10 \
    --cpu-boost \
    --project $PROJECT_ID
}

cd ..

# 6. Obter URL do backend staging
BACKEND_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --format 'value(status.url)')

echo ""
echo "✅ Ambiente STAGING criado com sucesso!"
echo ""
echo "📋 Informações:"
echo "  Backend URL: $BACKEND_URL"
echo "  Database: $DB_INSTANCE"
echo "  Region: $REGION"
echo ""
echo "🔗 Próximos passos:"
echo "  1. Configurar frontend staging na Vercel"
echo "  2. Configurar NEXT_PUBLIC_API_URL=$BACKEND_URL"
echo "  3. Atualizar CORS no backend se necessário"
echo ""

