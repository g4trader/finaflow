#!/bin/bash
# Script para configurar permissões IAM necessárias para o deploy
# Execute este script com uma conta que tenha permissões de Owner/Admin no projeto

set -e

PROJECT_ID="project-c6f9c72d-aca4-476d-82f"
PROJECT_NUMBER="556803510516"

echo "🔧 Configurando permissões IAM para o projeto ${PROJECT_ID}"
echo ""

# Permissões para Cloud Build service account
echo "1. Concedendo permissões ao Cloud Build service account..."
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"

# Permissões para Compute Engine service account
echo ""
echo "2. Concedendo permissões ao Compute Engine service account..."
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

echo ""
echo "✅ Permissões configuradas com sucesso!"
echo ""
echo "Agora você pode executar: ./deploy_staging.sh"



