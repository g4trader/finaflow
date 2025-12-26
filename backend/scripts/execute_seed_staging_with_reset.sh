#!/bin/bash
# Script para executar seed no STAGING com --reset-data e COST_DEBUG=1
# Usa Cloud Run Job ou atualiza o job existente

set -e

PROJECT_ID="${PROJECT_ID:-trivihair}"
REGION="${REGION:-us-central1}"
SEED_JOB_NAME="finaflow-seed-staging-job"
CLOUDSQL_INSTANCE="trivihair:us-central1:finaflow-db-staging"

echo "============================================================"
echo "🔄 RE-SEED 2025 - Correção de CUSTO (STAGING)"
echo "============================================================"
echo ""

# 1. Verificar se o job existe
echo "🔍 Verificando se o job existe..."
JOB_EXISTS=$(gcloud run jobs describe "$SEED_JOB_NAME" \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --format="value(name)" 2>/dev/null || echo "")

if [ -z "$JOB_EXISTS" ]; then
    echo "⚠️  Job não existe. Criando job..."
    
    # Obter imagem do serviço
    SERVICE_NAME="finaflow-backend-staging"
    IMAGE=$(gcloud run services describe "$SERVICE_NAME" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(spec.template.spec.containers[0].image)" 2>/dev/null || echo "")
    
    if [ -z "$IMAGE" ]; then
        echo "❌ Não foi possível obter a imagem do serviço"
        exit 1
    fi
    
    echo "📦 Imagem: $IMAGE"
    
    # Criar job
    gcloud run jobs create "$SEED_JOB_NAME" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --image="$IMAGE" \
        --set-cloudsql-instances="$CLOUDSQL_INSTANCE" \
        --set-env-vars="PYTHONPATH=/app,COST_DEBUG=1" \
        --max-retries=0 \
        --tasks=1 \
        --cpu=2 \
        --memory=2Gi \
        --task-timeout=1800 \
        --command=sh \
        --args="-c","cd /app && python -m scripts.seed_from_client_sheet --file data/fluxo_caixa_2025.xlsx --reset-data" \
        --quiet
    
    echo "✅ Job criado"
else
    echo "✅ Job existe. Atualizando com flags --reset-data e COST_DEBUG=1..."
    
    # Atualizar job com novas flags
    gcloud run jobs update "$SEED_JOB_NAME" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --update-env-vars="COST_DEBUG=1" \
        --args="-c","cd /app && python -m scripts.seed_from_client_sheet --file data/fluxo_caixa_2025.xlsx --reset-data" \
        --quiet
    
    echo "✅ Job atualizado"
fi

echo ""
echo "🌱 Executando seed com --reset-data e COST_DEBUG=1..."
echo "⚠️  ATENÇÃO: Isso vai apagar todos os lançamentos diários e previstos do tenant!"
echo ""

# Executar job
gcloud run jobs execute "$SEED_JOB_NAME" \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --wait

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ Seed concluído com sucesso!"
    echo ""
    echo "📊 Ver logs:"
    echo "   gcloud logging read \"resource.type=cloud_run_job AND resource.labels.job_name=$SEED_JOB_NAME\" --limit=50 --format=\"value(textPayload)\" --region=$REGION"
    echo ""
    echo "🔍 Próximo passo: Executar auditoria para validar equalização"
    echo "   make audit"
    echo ""
else
    echo ""
    echo "❌ Seed falhou com código $EXIT_CODE"
    echo ""
    echo "📊 Ver logs:"
    echo "   gcloud logging read \"resource.type=cloud_run_job AND resource.labels.job_name=$SEED_JOB_NAME\" --limit=100 --format=\"value(textPayload)\" --region=$REGION"
    exit 1
fi

