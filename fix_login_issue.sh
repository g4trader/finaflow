#!/bin/bash

# 🔧 Script de Correção Automatizada - Problema de Login
# Data: 18/10/2025
# Problema: HTTP 500 / Timeout no login
# Solução: Configurar Cloud SQL Proxy no Cloud Run

set -e  # Parar em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
PROJECT_ID="trivihair"
REGION="us-central1"
SERVICE_NAME="finaflow-backend"
SQL_INSTANCE="finaflow-db"
SQL_CONNECTION="${PROJECT_ID}:${REGION}:${SQL_INSTANCE}"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   🔧 FinaFlow - Correção de Login (500/Timeout)    ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Verificar se está no diretório correto
if [ ! -f "backend/cloudbuild.yaml" ]; then
    echo -e "${RED}❌ Erro: Execute este script a partir do diretório raiz do projeto${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 Configurações:${NC}"
echo -e "   Projeto GCP: ${GREEN}${PROJECT_ID}${NC}"
echo -e "   Região: ${GREEN}${REGION}${NC}"
echo -e "   Cloud Run: ${GREEN}${SERVICE_NAME}${NC}"
echo -e "   Cloud SQL: ${GREEN}${SQL_CONNECTION}${NC}"
echo ""

# Perguntar se deseja continuar
read -p "Deseja continuar com as correções? (s/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo -e "${YELLOW}❌ Operação cancelada pelo usuário${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   ETAPA 1: Verificar Permissões IAM               ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Obter Service Account do Cloud Run
echo -e "${YELLOW}🔍 Obtendo Service Account do Cloud Run...${NC}"
SERVICE_ACCOUNT=$(gcloud run services describe ${SERVICE_NAME} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --format="value(spec.template.spec.serviceAccountName)" 2>/dev/null || echo "")

if [ -z "$SERVICE_ACCOUNT" ]; then
    SERVICE_ACCOUNT="${PROJECT_ID}@appspot.gserviceaccount.com"
    echo -e "${YELLOW}⚠️  Usando Service Account default: ${SERVICE_ACCOUNT}${NC}"
else
    echo -e "${GREEN}✅ Service Account encontrado: ${SERVICE_ACCOUNT}${NC}"
fi

# Conceder permissões Cloud SQL Client
echo -e "${YELLOW}🔑 Concedendo permissão Cloud SQL Client...${NC}"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/cloudsql.client" \
  --project=${PROJECT_ID} \
  --quiet 2>/dev/null || echo -e "${YELLOW}⚠️  Permissão já existe ou erro ao conceder${NC}"

echo -e "${GREEN}✅ Permissões verificadas${NC}"
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   ETAPA 2: Verificar Cloud SQL                     ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${YELLOW}🔍 Verificando status do Cloud SQL...${NC}"
SQL_STATE=$(gcloud sql instances describe ${SQL_INSTANCE} \
  --project=${PROJECT_ID} \
  --format="value(state)" 2>/dev/null || echo "UNKNOWN")

if [ "$SQL_STATE" == "RUNNABLE" ]; then
    echo -e "${GREEN}✅ Cloud SQL está rodando${NC}"
else
    echo -e "${RED}❌ Cloud SQL não está disponível (Estado: ${SQL_STATE})${NC}"
    echo -e "${YELLOW}⚠️  Continuando mesmo assim...${NC}"
fi

SQL_IP=$(gcloud sql instances describe ${SQL_INSTANCE} \
  --project=${PROJECT_ID} \
  --format="value(ipAddresses[0].ipAddress)" 2>/dev/null || echo "N/A")
echo -e "   IP Público: ${GREEN}${SQL_IP}${NC}"
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   ETAPA 3: Build e Deploy do Backend               ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${YELLOW}🏗️  Iniciando build via Cloud Build...${NC}"
echo -e "${YELLOW}⏳ Isso pode demorar 5-10 minutos...${NC}"
echo ""

# Executar build
gcloud builds submit \
  --config=backend/cloudbuild.yaml \
  --project=${PROJECT_ID} \
  . || {
    echo -e "${RED}❌ Erro no build. Verifique os logs acima.${NC}"
    exit 1
  }

echo -e "${GREEN}✅ Build concluído com sucesso!${NC}"
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   ETAPA 4: Verificar Deploy                        ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${YELLOW}⏳ Aguardando deploy finalizar...${NC}"
sleep 10

# Listar últimas revisões
echo -e "${YELLOW}📋 Últimas revisões:${NC}"
gcloud run revisions list \
  --service=${SERVICE_NAME} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --limit=3 \
  --format="table(metadata.name,status.conditions[0].status,metadata.creationTimestamp)" || true

echo ""

# Obter URL do serviço
BACKEND_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --format="value(status.url)" 2>/dev/null || echo "")

if [ -z "$BACKEND_URL" ]; then
    echo -e "${RED}❌ Erro ao obter URL do Cloud Run${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Backend URL: ${BACKEND_URL}${NC}"
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   ETAPA 5: Testar Endpoints                        ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${YELLOW}🧪 Testando Health Check...${NC}"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "${BACKEND_URL}/health" 2>/dev/null || echo "ERROR\n000")
HEALTH_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | head -n-1)

if [ "$HEALTH_CODE" == "200" ]; then
    echo -e "${GREEN}✅ Health Check: OK (200)${NC}"
    echo -e "   Resposta: ${HEALTH_BODY}"
else
    echo -e "${RED}❌ Health Check falhou (${HEALTH_CODE})${NC}"
    echo -e "   Resposta: ${HEALTH_BODY}"
fi
echo ""

echo -e "${YELLOW}🧪 Testando Login...${NC}"
LOGIN_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BACKEND_URL}/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=Admin@123" 2>/dev/null || echo "ERROR\n000")
LOGIN_CODE=$(echo "$LOGIN_RESPONSE" | tail -n1)
LOGIN_BODY=$(echo "$LOGIN_RESPONSE" | head -n-1)

if [ "$LOGIN_CODE" == "200" ]; then
    echo -e "${GREEN}✅ Login: OK (200)${NC}"
    ACCESS_TOKEN=$(echo "$LOGIN_BODY" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4 || echo "")
    if [ -n "$ACCESS_TOKEN" ]; then
        echo -e "   Token recebido: ${ACCESS_TOKEN:0:50}..."
    fi
else
    echo -e "${RED}❌ Login falhou (${LOGIN_CODE})${NC}"
    echo -e "   Resposta: ${LOGIN_BODY}"
fi
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   RESUMO DA CORREÇÃO                               ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ "$HEALTH_CODE" == "200" ] && [ "$LOGIN_CODE" == "200" ]; then
    echo -e "${GREEN}✅ SUCESSO! Sistema está funcionando corretamente.${NC}"
    echo ""
    echo -e "${GREEN}📱 Próximos Passos:${NC}"
    echo -e "   1. Acesse: ${YELLOW}https://finaflow.vercel.app/login${NC}"
    echo -e "   2. Faça login com: ${YELLOW}admin / Admin@123${NC}"
    echo -e "   3. Você deve ser redirecionado para seleção de empresa"
    echo ""
    exit 0
elif [ "$HEALTH_CODE" == "200" ]; then
    echo -e "${YELLOW}⚠️  PARCIALMENTE OK: Health check funciona, mas login falhou.${NC}"
    echo ""
    echo -e "${YELLOW}🔍 Verificações adicionais:${NC}"
    echo -e "   1. Confirmar senha do usuário admin (Admin@123 ou admin123)"
    echo -e "   2. Ver logs: ${YELLOW}gcloud logging tail \"resource.type=cloud_run_revision\" --project=${PROJECT_ID}${NC}"
    echo -e "   3. Verificar banco de dados tem usuário admin"
    echo ""
    exit 1
else
    echo -e "${RED}❌ FALHA: Sistema não está respondendo corretamente.${NC}"
    echo ""
    echo -e "${YELLOW}🔍 Próximos Passos de Debug:${NC}"
    echo -e "   1. Ver logs: ${YELLOW}gcloud logging tail \"resource.type=cloud_run_revision\" --project=${PROJECT_ID}${NC}"
    echo -e "   2. Verificar Cloud SQL Proxy configurado: ${YELLOW}gcloud run services describe ${SERVICE_NAME} --region=${REGION} --project=${PROJECT_ID}${NC}"
    echo -e "   3. Testar conexão direta ao banco de dados"
    echo ""
    exit 1
fi

