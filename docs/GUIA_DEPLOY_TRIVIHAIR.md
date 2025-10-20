# Guia de Deploy - Projeto Trivihair

## Visão Geral

Este documento descreve o processo completo de deploy do sistema FINAFlow no projeto GCP **trivihair**.

## Informações do Projeto

- **Projeto GCP**: trivihair
- **Service Account**: dashboardluciano@trivihair.iam.gserviceaccount.com
- **Região**: us-central1
- **Backend**: Cloud Run
- **Frontend**: Vercel
- **Banco de Dados**: PostgreSQL (Cloud SQL ou VM externa)

## Pré-requisitos

### 1. Google Cloud Platform

Certifique-se de ter:
- Acesso ao projeto `trivihair` no GCP
- gcloud CLI instalado e configurado
- Permissões para:
  - Cloud Run
  - Container Registry (GCR)
  - Cloud Build
  - BigQuery (se usar)
  - Cloud SQL (se usar)

### 2. Configuração Local

```bash
# Instalar gcloud CLI (se ainda não tiver)
# macOS
brew install google-cloud-sdk

# Configure o projeto
gcloud auth login
gcloud config set project trivihair
gcloud auth configure-docker
```

## Estrutura de Deploy

### Backend (Cloud Run)

#### 1. Construir e Fazer Deploy

```bash
# Navegar para o diretório do backend
cd /Users/lucianoterres/Documents/GitHub/finaflow/backend

# Construir a imagem Docker
docker build -t gcr.io/trivihair/finaflow-backend .

# Fazer push para o Container Registry
docker push gcr.io/trivihair/finaflow-backend

# Deploy no Cloud Run
gcloud run deploy finaflow-backend \
  --image gcr.io/trivihair/finaflow-backend \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=postgresql://finaflow_user:finaflow_password@34.70.102.98:5432/finaflow_db \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --concurrency 80
```

#### 2. Deploy Automatizado via Cloud Build

```bash
# Do diretório raiz do projeto
gcloud builds submit --config=backend/cloudbuild.yaml
```

O arquivo `backend/cloudbuild.yaml` está configurado para:
- Construir a imagem Docker
- Fazer push para GCR
- Deploy automático no Cloud Run
- Configurar variáveis de ambiente

### Frontend (Vercel)

O frontend já está configurado para deploy automático via GitHub integration no Vercel.

#### Variáveis de Ambiente (Vercel)

Configure no dashboard da Vercel:

```
NEXT_PUBLIC_API_URL=https://finaflow-backend-<PROJECT_NUMBER>.<REGION>.run.app
```

**Nota**: Substitua `<PROJECT_NUMBER>` e `<REGION>` pela URL real do Cloud Run após o primeiro deploy.

## Configuração do Banco de Dados

### PostgreSQL

O sistema está configurado para usar PostgreSQL (não SQLite).

#### Opção 1: Cloud SQL (Recomendado para Produção)

```bash
# Criar instância Cloud SQL
gcloud sql instances create finaflow-db \
  --database-version=POSTGRES_14 \
  --tier=db-f1-micro \
  --region=us-central1

# Criar banco de dados
gcloud sql databases create finaflow_db --instance=finaflow-db

# Criar usuário
gcloud sql users create finaflow_user \
  --instance=finaflow-db \
  --password=finaflow_password

# Obter IP da instância
gcloud sql instances describe finaflow-db --format="value(ipAddresses[0].ipAddress)"
```

Atualizar a variável `DATABASE_URL` no Cloud Run com a nova connection string.

#### Opção 2: Banco Externo

Se usar o banco PostgreSQL existente (34.70.102.98):
- Certifique-se de que o Cloud Run tem acesso à rede
- Configure as regras de firewall apropriadas
- A configuração atual já aponta para este IP

### BigQuery (Opcional)

Se usar BigQuery para dados analíticos:

```bash
# Criar dataset
bq mk --dataset trivihair:finaflow

# Criar tabelas necessárias
bq mk --table trivihair:finaflow.Users \
  id:STRING,username:STRING,email:STRING,hashed_password:STRING,role:STRING,tenant_id:STRING,created_at:TIMESTAMP

bq mk --table trivihair:finaflow.Accounts \
  id:STRING,name:STRING,balance:FLOAT,tenant_id:STRING,created_at:TIMESTAMP

bq mk --table trivihair:finaflow.Transactions \
  id:STRING,account_id:STRING,amount:FLOAT,description:STRING,tenant_id:STRING,created_at:TIMESTAMP
```

## Credenciais do Google Cloud

O arquivo `google_credentials.json` na raiz do projeto já está atualizado com as credenciais do projeto trivihair.

**IMPORTANTE**: 
- Este arquivo contém informações sensíveis
- Nunca faça commit dele no Git
- Está incluído no `.gitignore`

## Variáveis de Ambiente

### Backend

Configure estas variáveis no Cloud Run:

```bash
DATABASE_URL=postgresql://finaflow_user:finaflow_password@34.70.102.98:5432/finaflow_db
SECRET_KEY=finaflow-secret-key-2024
ALLOWED_HOSTS=localhost,127.0.0.1,finaflow.vercel.app
CORS_ORIGINS=https://finaflow.vercel.app,http://localhost:3000
PROJECT_ID=trivihair
DATASET=finaflow
```

### Frontend

Configure no Vercel:

```bash
NEXT_PUBLIC_API_URL=<URL_DO_CLOUD_RUN>
```

## Scripts de Configuração

### Criar Usuário Super Admin

Após o deploy, crie o usuário super admin:

```bash
# Se usar BigQuery
cd scripts
python3 create_super_admin_bigquery.py
```

Ou execute manualmente no BigQuery:

```sql
INSERT INTO `trivihair.finaflow.Users` 
(id, username, email, hashed_password, role, tenant_id, created_at)
VALUES 
(
  GENERATE_UUID(),
  'admin',
  'admin@finaflow.com',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iQeO',
  'super_admin',
  NULL,
  CURRENT_TIMESTAMP()
);
```

Credenciais de acesso:
- **Username**: admin
- **Senha**: admin123

## Monitoramento e Logs

### Cloud Run Logs

```bash
# Ver logs do backend
gcloud run logs read finaflow-backend --region us-central1 --limit 50

# Seguir logs em tempo real
gcloud run logs tail finaflow-backend --region us-central1
```

### Métricas

Acesse o console do Cloud Run:
```
https://console.cloud.google.com/run?project=trivihair
```

## Troubleshooting

### Problema: Deploy falha com erro de permissões

**Solução**:
```bash
# Verificar permissões da service account
gcloud projects get-iam-policy trivihair \
  --flatten="bindings[].members" \
  --filter="bindings.members:dashboardluciano@trivihair.iam.gserviceaccount.com"

# Adicionar permissões necessárias (se necessário)
gcloud projects add-iam-policy-binding trivihair \
  --member="serviceAccount:dashboardluciano@trivihair.iam.gserviceaccount.com" \
  --role="roles/run.admin"
```

### Problema: Erro de conexão com o banco de dados

**Solução**:
1. Verificar se o IP está correto
2. Verificar regras de firewall
3. Testar conexão local:
```bash
psql -h 34.70.102.98 -U finaflow_user -d finaflow_db
```

### Problema: CORS errors no frontend

**Solução**:
1. Verificar se a URL do backend está correta no Vercel
2. Verificar se CORS_ORIGINS está configurado corretamente no Cloud Run
3. Verificar se o domínio do Vercel está incluído em ALLOWED_HOSTS

## Rollback

Se necessário fazer rollback:

```bash
# Listar revisões
gcloud run revisions list --service=finaflow-backend --region=us-central1

# Fazer rollback para revisão anterior
gcloud run services update-traffic finaflow-backend \
  --region=us-central1 \
  --to-revisions=<REVISION_NAME>=100
```

## Custos Estimados

Com a configuração atual:
- **Cloud Run**: ~$10-30/mês (dependendo do tráfego)
- **Cloud SQL (db-f1-micro)**: ~$10/mês
- **Container Registry**: ~$1-5/mês
- **BigQuery**: Pay-per-query (geralmente < $5/mês para uso moderado)

## Segurança

### Recomendações

1. **Secrets Manager**: Migrar credenciais sensíveis para o Secret Manager
```bash
# Criar secret
echo -n "finaflow_password" | gcloud secrets create db-password --data-file=-

# Usar no Cloud Run
gcloud run deploy finaflow-backend \
  --update-secrets DATABASE_PASSWORD=db-password:latest
```

2. **Cloud Armor**: Considerar adicionar proteção DDoS

3. **Identity-Aware Proxy**: Para endpoints administrativos

4. **SSL/TLS**: Sempre usar HTTPS (Cloud Run fornece por padrão)

## Próximos Passos

1. ✅ Migrar credenciais para o projeto trivihair
2. ✅ Atualizar todos os arquivos de configuração
3. ⏳ Fazer primeiro deploy no Cloud Run
4. ⏳ Configurar banco de dados PostgreSQL
5. ⏳ Criar usuário super admin
6. ⏳ Testar login e funcionalidades principais
7. ⏳ Atualizar frontend no Vercel com nova URL do backend
8. ⏳ Configurar monitoramento e alertas

## Contato e Suporte

Para dúvidas ou problemas:
- Documentação GCP: https://cloud.google.com/run/docs
- Documentação Vercel: https://vercel.com/docs

---

**Última atualização**: 15 de Outubro de 2025
**Versão**: 1.0.0
**Projeto**: trivihair


