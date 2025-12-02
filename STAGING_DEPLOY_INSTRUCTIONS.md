# 🚀 INSTRUÇÕES PARA DEPLOY STAGING

**IMPORTANTE**: Execute estes comandos com permissões adequadas no projeto `trivihair`.

---

## ⚡ EXECUÇÃO RÁPIDA

### Opção 1: Script Automatizado

```bash
cd /Users/lucianoterres/Documents/GitHub/finaflow
./scripts/create-staging.sh
```

### Opção 2: Comandos Manuais (se script falhar)

Execute os comandos abaixo na ordem:

---

## 1️⃣ CRIAR BANCO DE DADOS STAGING

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
  --enable-bin-log \
  --project=trivihair

# Criar banco de dados
gcloud sql databases create finaflow_db \
  --instance=finaflow-db-staging \
  --project=trivihair

# Criar/atualizar usuário
gcloud sql users create finaflow_user \
  --instance=finaflow-db-staging \
  --password=finaflow_password_staging_2024 \
  --project=trivihair || \
gcloud sql users set-password finaflow_user \
  --instance=finaflow-db-staging \
  --password=finaflow_password_staging_2024 \
  --project=trivihair
```

**⏱️ Tempo estimado**: 5-10 minutos

---

## 2️⃣ DEPLOY BACKEND STAGING

```bash
cd /Users/lucianoterres/Documents/GitHub/finaflow/backend

# Deploy via Cloud Build
gcloud builds submit --config=cloudbuild-staging.yaml --project=trivihair .
```

**⏱️ Tempo estimado**: 10-15 minutos

---

## 3️⃣ OBTER URL DO BACKEND

```bash
gcloud run services describe finaflow-backend-staging \
  --region us-central1 \
  --project trivihair \
  --format 'value(status.url)'
```

**Salve esta URL** - será usada no frontend!

---

## 4️⃣ INICIALIZAR BANCO STAGING

```bash
# Conectar e executar migrations
export DATABASE_URL="postgresql://finaflow_user:finaflow_password_staging_2024@/finaflow_db?host=/cloudsql/trivihair:us-central1:finaflow-db-staging"

cd /Users/lucianoterres/Documents/GitHub/finaflow/backend
python create_tables.py
```

**OU** via gcloud:

```bash
gcloud sql connect finaflow-db-staging --user=finaflow_user --project=trivihair
# Depois executar SQL manualmente ou usar create_tables.py
```

---

## 5️⃣ CONFIGURAR FRONTEND STAGING NA VERCEL

### Via Dashboard Vercel:

1. Acesse: https://vercel.com/dashboard
2. Clique em "Add New Project"
3. Importe o repositório `finaflow`
4. Configure:
   - **Project Name**: `finaflow-staging`
   - **Root Directory**: `frontend`
   - **Framework Preset**: Next.js
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

### Variáveis de Ambiente:

Adicione estas variáveis no projeto Vercel:

```
NEXT_PUBLIC_API_URL=https://finaflow-backend-staging-XXXXX.us-central1.run.app
ENVIRONMENT=staging
```

**Substitua `XXXXX` pela URL real obtida no passo 3.**

### Via CLI:

```bash
cd /Users/lucianoterres/Documents/GitHub/finaflow/frontend

# Login (se necessário)
vercel login

# Criar projeto staging
vercel --prod --name finaflow-staging

# Adicionar variáveis de ambiente
vercel env add NEXT_PUBLIC_API_URL production
# Cole a URL do backend quando solicitado

vercel env add ENVIRONMENT production
# Digite: staging
```

---

## 6️⃣ VERIFICAR DEPLOY

### Backend Health Check:

```bash
# Substitua pela URL real
curl https://finaflow-backend-staging-XXXXX.us-central1.run.app/health
```

**Resposta esperada:**
```json
{
  "status": "healthy",
  "service": "finaflow-backend-staging",
  "version": "1.0.0"
}
```

### Frontend:

Acesse: `https://finaflow-staging.vercel.app`

---

## 7️⃣ HABILITAR LOGS DETALHADOS

Os logs já estão habilitados por padrão no Cloud Run. Para visualizar:

```bash
# Logs do backend
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=finaflow-backend-staging" --project=trivihair

# Logs do banco
gcloud logging tail "resource.type=cloudsql_database AND resource.labels.database_id=trivihair:us-central1:finaflow-db-staging" --project=trivihair
```

**OU** via Console:
- Backend: https://console.cloud.google.com/run/detail/us-central1/finaflow-backend-staging/logs?project=trivihair
- Banco: https://console.cloud.google.com/sql/instances/finaflow-db-staging/logs?project=trivihair

---

## 📋 CHECKLIST FINAL

Após completar todos os passos, verifique:

- [ ] Banco `finaflow-db-staging` criado e acessível
- [ ] Backend `finaflow-backend-staging` deployado e respondendo
- [ ] Health check do backend funcionando
- [ ] Frontend staging deployado na Vercel
- [ ] `NEXT_PUBLIC_API_URL` configurado corretamente
- [ ] CORS permitindo acesso do frontend staging
- [ ] Tabelas do banco inicializadas
- [ ] Logs acessíveis e funcionando
- [ ] Links de acesso coletados

---

## 🔗 LINKS PARA PM E QA

Após deploy completo, envie:

**Frontend Staging:**
```
https://finaflow-staging.vercel.app
```

**Backend Staging:**
```
https://finaflow-backend-staging-XXXXX.us-central1.run.app
```

**API Docs:**
```
https://finaflow-backend-staging-XXXXX.us-central1.run.app/docs
```

**Health Check:**
```
https://finaflow-backend-staging-XXXXX.us-central1.run.app/health
```

**Logs (Console):**
- Backend: https://console.cloud.google.com/run/detail/us-central1/finaflow-backend-staging/logs?project=trivihair
- Banco: https://console.cloud.google.com/sql/instances/finaflow-db-staging/logs?project=trivihair

---

## ⚠️ TROUBLESHOOTING

### Erro: "Permission denied"
- Verifique se está autenticado: `gcloud auth list`
- Verifique permissões no projeto: `gcloud projects get-iam-policy trivihair`

### Erro: "API not enabled"
- Habilite Cloud SQL Admin API: https://console.cloud.google.com/apis/library/sqladmin.googleapis.com?project=trivihair
- Habilite Cloud Run API: https://console.cloud.google.com/apis/library/run.googleapis.com?project=trivihair

### Erro: "Database connection failed"
- Verifique se Unix Socket está configurado: `/cloudsql/trivihair:us-central1:finaflow-db-staging`
- Verifique se Cloud SQL instance está conectada ao Cloud Run service

### Erro: "CORS error"
- Verifique se `CORS_ORIGINS` inclui a URL do frontend staging
- Verifique se `ALLOWED_HOSTS` está configurado

---

**Última atualização**: Janeiro 2025

