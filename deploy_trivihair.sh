#!/bin/bash

# Script de Deploy Automatizado - Projeto Trivihair
# FINAFlow System

set -e  # Parar em caso de erro

echo "🚀 Deploy FINAFlow - Projeto Trivihair"
echo "======================================"

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Variáveis
PROJECT_ID="trivihair"
REGION="us-central1"
SERVICE_NAME="finaflow-backend"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Função para verificar se o comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Verificar pré-requisitos
echo -e "\n${YELLOW}📋 Verificando pré-requisitos...${NC}"

if ! command_exists gcloud; then
    echo -e "${RED}❌ gcloud CLI não encontrado. Por favor, instale: https://cloud.google.com/sdk/docs/install${NC}"
    exit 1
fi

if ! command_exists docker; then
    echo -e "${RED}❌ Docker não encontrado. Por favor, instale: https://docs.docker.com/get-docker/${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Pré-requisitos OK${NC}"

# Configurar projeto GCP
echo -e "\n${YELLOW}🔧 Configurando projeto GCP...${NC}"
gcloud config set project ${PROJECT_ID}
gcloud auth configure-docker

echo -e "${GREEN}✅ Projeto configurado: ${PROJECT_ID}${NC}"

# Navegar para o diretório do backend
echo -e "\n${YELLOW}📂 Navegando para o diretório do backend...${NC}"
cd "$(dirname "$0")/backend"

# Construir imagem Docker
echo -e "\n${YELLOW}🐳 Construindo imagem Docker...${NC}"
docker build -t ${IMAGE_NAME} .

echo -e "${GREEN}✅ Imagem construída: ${IMAGE_NAME}${NC}"

# Push para GCR
echo -e "\n${YELLOW}📤 Fazendo push para Container Registry...${NC}"
docker push ${IMAGE_NAME}

echo -e "${GREEN}✅ Push concluído${NC}"

# Deploy no Cloud Run
echo -e "\n${YELLOW}☁️  Fazendo deploy no Cloud Run...${NC}"

# Perguntar se deve usar Cloud Build ou deploy direto
read -p "Usar Cloud Build para deploy automatizado? (s/n): " use_cloud_build

if [[ $use_cloud_build == "s" || $use_cloud_build == "S" ]]; then
    echo -e "\n${YELLOW}🏗️  Iniciando Cloud Build...${NC}"
    cd ..
    gcloud builds submit --config=backend/cloudbuild.yaml
else
    echo -e "\n${YELLOW}🚀 Deploy direto no Cloud Run...${NC}"
    
    # Verificar se deve atualizar variáveis de ambiente
    read -p "Atualizar DATABASE_URL? (s/n): " update_db_url
    
    if [[ $update_db_url == "s" || $update_db_url == "S" ]]; then
        read -p "Digite a DATABASE_URL: " db_url
        ENV_VARS="DATABASE_URL=${db_url}"
    else
        ENV_VARS="DATABASE_URL=postgresql://finaflow_user:finaflow_password@34.70.102.98:5432/finaflow_db"
    fi
    
    gcloud run deploy ${SERVICE_NAME} \
        --image ${IMAGE_NAME} \
        --region ${REGION} \
        --platform managed \
        --allow-unauthenticated \
        --set-env-vars "${ENV_VARS}" \
        --set-env-vars "SECRET_KEY=finaflow-secret-key-2024" \
        --set-env-vars "ALLOWED_HOSTS=localhost,127.0.0.1,finaflow.vercel.app" \
        --set-env-vars "CORS_ORIGINS=https://finaflow.vercel.app,http://localhost:3000" \
        --set-env-vars "PROJECT_ID=trivihair" \
        --set-env-vars "DATASET=finaflow" \
        --port 8080 \
        --memory 1Gi \
        --cpu 1 \
        --timeout 300 \
        --concurrency 80
fi

# Obter URL do serviço
echo -e "\n${YELLOW}🔍 Obtendo URL do serviço...${NC}"
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format="value(status.url)")

echo -e "\n${GREEN}✅ Deploy concluído com sucesso!${NC}"
echo -e "\n${GREEN}📊 Informações do Deploy:${NC}"
echo -e "   Projeto: ${PROJECT_ID}"
echo -e "   Região: ${REGION}"
echo -e "   Serviço: ${SERVICE_NAME}"
echo -e "   URL: ${SERVICE_URL}"

# Testar o endpoint
echo -e "\n${YELLOW}🧪 Testando endpoint...${NC}"
if curl -s "${SERVICE_URL}/docs" > /dev/null; then
    echo -e "${GREEN}✅ Backend está respondendo!${NC}"
    echo -e "\n${GREEN}🌐 Acesse a documentação: ${SERVICE_URL}/docs${NC}"
else
    echo -e "${RED}⚠️  Backend não está respondendo. Verifique os logs.${NC}"
fi

# Mostrar próximos passos
echo -e "\n${YELLOW}📋 Próximos Passos:${NC}"
echo -e "   1. Configure a URL do backend no Vercel:"
echo -e "      NEXT_PUBLIC_API_URL=${SERVICE_URL}"
echo -e "\n   2. Crie o usuário super admin (se necessário):"
echo -e "      cd scripts && python3 create_super_admin_bigquery.py"
echo -e "\n   3. Teste o login:"
echo -e "      https://finaflow.vercel.app/login"
echo -e "      Username: admin"
echo -e "      Senha: admin123"
echo -e "\n   4. Verifique os logs:"
echo -e "      gcloud run logs tail ${SERVICE_NAME} --region ${REGION}"

echo -e "\n${GREEN}🎉 Deploy finalizado!${NC}"


