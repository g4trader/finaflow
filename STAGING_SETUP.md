# 🚀 SETUP AMBIENTE STAGING - FINAFLOW

**Data**: Janeiro 2025  
**Status**: ⚙️ Em Configuração

---

## 📋 OBJETIVO

Criar ambiente STAGING completo para validação do QA antes de produção.

---

## 🏗️ ARQUITETURA STAGING

```
┌─────────────────────────────────────────────────────────────┐
│              FRONTEND STAGING (Vercel)                      │
│         https://finaflow-staging.vercel.app                 │
└───────────────────────┬───────────────────────────────────────┘
                        │
                        │ HTTPS/REST API
                        │
        ┌───────────────▼───────────────────────┐
        │     BACKEND STAGING (Cloud Run)        │
        │     finaflow-backend-staging           │
        │     us-central1                        │
        └───────────────┬───────────────────────┘
                        │
                        │ Unix Socket
                        │ /cloudsql/trivihair:us-central1:finaflow-db-staging
                        │
        ┌───────────────▼───────────────────────┐
        │     BANCO STAGING (Cloud SQL)         │
        │     finaflow-db-staging                │
        │     PostgreSQL 14                      │
        └───────────────────────────────────────┘
```

---

## 🔧 COMANDOS PARA CRIAÇÃO

### 1. Criar Banco de Dados Staging

```bash
# Configurar projeto
gcloud config set project trivihair

# Criar instância Cloud SQL
gcloud sql instances create finaflow-db-staging \
  --database-version=POSTGRES_14 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --storage-type=SSD \
  --storage-size=20GB \
  --storage-auto-increase \
  --backup-start-time=03:00 \
  --enable-bin-log

# Criar banco de dados
gcloud sql databases create finaflow_db \
  --instance=finaflow-db-staging

# Criar usuário
gcloud sql users create finaflow_user \
  --instance=finaflow-db-staging \
  --password=finaflow_password_staging_2024

# Atualizar senha (garantir)
gcloud sql users set-password finaflow_user \
  --instance=finaflow-db-staging \
  --password=finaflow_password_staging_2024
```

### 2. Deploy Backend Staging

```bash
cd backend

# Opção 1: Via Cloud Build (recomendado)
gcloud builds submit --config=cloudbuild-staging.yaml --project=trivihair .

# Opção 2: Deploy manual
docker build -t gcr.io/trivihair/finaflow-backend-staging .
docker push gcr.io/trivihair/finaflow-backend-staging

gcloud run deploy finaflow-backend-staging \
  --image gcr.io/trivihair/finaflow-backend-staging \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --add-cloudsql-instances trivihair:us-central1:finaflow-db-staging \
  --set-env-vars DATABASE_URL=postgresql://finaflow_user:finaflow_password_staging_2024@/finaflow_db?host=/cloudsql/trivihair:us-central1:finaflow-db-staging,SECRET_KEY=finaflow-secret-key-2024-staging,JWT_SECRET=finaflow-secret-key-2024-staging,CORS_ORIGINS=https://finaflow-staging.vercel.app,https://finaflow.vercel.app,ALLOWED_HOSTS=finaflow-staging.vercel.app,finaflow.vercel.app,PROJECT_ID=trivihair,DATASET=finaflow_staging,ENVIRONMENT=staging \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 600 \
  --concurrency 80 \
  --min-instances 1 \
  --max-instances 10 \
  --cpu-boost
```

### 3. Obter URL do Backend

```bash
gcloud run services describe finaflow-backend-staging \
  --region us-central1 \
  --format 'value(status.url)'
```

### 4. Configurar Frontend Staging na Vercel

```bash
cd frontend

# Criar projeto staging na Vercel
vercel --prod --name finaflow-staging

# Ou via dashboard Vercel:
# 1. Acessar https://vercel.com
# 2. Importar projeto
# 3. Criar novo projeto: finaflow-staging
# 4. Configurar variáveis de ambiente:
```

**Variáveis de Ambiente Vercel (Staging):**
```
NEXT_PUBLIC_API_URL=https://finaflow-backend-staging-XXXXX.us-central1.run.app
ENVIRONMENT=staging
```

### 5. Atualizar CORS no Backend (se necessário)

O CORS já está configurado no `cloudbuild-staging.yaml` para aceitar:
- `https://finaflow-staging.vercel.app`
- `https://finaflow.vercel.app`

---

## 📊 CONFIGURAÇÕES

### Backend Staging

| Configuração | Valor |
|-------------|-------|
| Nome | `finaflow-backend-staging` |
| Região | `us-central1` |
| Porta | `8080` |
| Memória | `2Gi` |
| CPU | `2` |
| Min Instances | `1` |
| Max Instances | `10` |
| Timeout | `600s` |
| Concorrência | `80` |

### Banco Staging

| Configuração | Valor |
|-------------|-------|
| Nome | `finaflow-db-staging` |
| Tipo | PostgreSQL 14 |
| Tier | `db-f1-micro` |
| Região | `us-central1` |
| Storage | 20GB SSD (auto-increase) |
| Backup | Diário 03:00 |
| Unix Socket | `/cloudsql/trivihair:us-central1:finaflow-db-staging` |

### Frontend Staging

| Configuração | Valor |
|-------------|-------|
| Plataforma | Vercel |
| Nome | `finaflow-staging` |
| URL | `https://finaflow-staging.vercel.app` |
| API URL | Backend staging URL |

---

## 🔍 LOGS E MONITORAMENTO

### Ver Logs do Backend

```bash
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=finaflow-backend-staging" --project=trivihair
```

### Ver Logs do Banco

```bash
gcloud logging tail "resource.type=cloudsql_database AND resource.labels.database_id=trivihair:us-central1:finaflow-db-staging" --project=trivihair
```

### Verificar Status do Backend

```bash
gcloud run services describe finaflow-backend-staging \
  --region us-central1 \
  --project trivihair
```

### Health Check

```bash
curl https://finaflow-backend-staging-XXXXX.us-central1.run.app/health
```

---

## 🗄️ INICIALIZAR BANCO STAGING

Após criar o banco, é necessário inicializar as tabelas:

```bash
# Conectar ao banco staging
gcloud sql connect finaflow-db-staging --user=finaflow_user --project=trivihair

# Ou executar script de inicialização
export DATABASE_URL="postgresql://finaflow_user:finaflow_password_staging_2024@/finaflow_db?host=/cloudsql/trivihair:us-central1:finaflow-db-staging"
cd backend
python create_tables.py
```

---

## ✅ CHECKLIST DE DEPLOY

- [ ] Banco `finaflow-db-staging` criado
- [ ] Usuário `finaflow_user` criado no banco
- [ ] Backend `finaflow-backend-staging` deployado
- [ ] Unix Socket configurado corretamente
- [ ] Variáveis de ambiente configuradas
- [ ] CORS configurado para frontend staging
- [ ] Frontend staging criado na Vercel
- [ ] `NEXT_PUBLIC_API_URL` configurado
- [ ] Tabelas do banco inicializadas
- [ ] Health check funcionando
- [ ] Logs habilitados e acessíveis
- [ ] Links enviados para PM e QA

---

## 🔗 LINKS IMPORTANTES

### GCP Console
- **Cloud Run**: https://console.cloud.google.com/run?project=trivihair
- **Cloud SQL**: https://console.cloud.google.com/sql?project=trivihair
- **Cloud Build**: https://console.cloud.google.com/cloud-build?project=trivihair
- **Logs**: https://console.cloud.google.com/logs?project=trivihair

### Vercel
- **Dashboard**: https://vercel.com/dashboard
- **Projeto Staging**: https://vercel.com/[seu-time]/finaflow-staging

---

## 📝 NOTAS

1. **Senhas**: Use senhas diferentes para staging e produção
2. **Deletion Protection**: Staging não tem deletion protection (pode ser deletado)
3. **Backups**: Backups automáticos configurados diariamente
4. **Custos**: Staging usa tier menor (db-f1-micro) para reduzir custos
5. **Logs**: Logs detalhados habilitados para debugging

---

**Última atualização**: Janeiro 2025

