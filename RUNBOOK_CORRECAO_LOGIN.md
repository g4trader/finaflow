# 🔧 RUNBOOK DE CORREÇÃO - PROBLEMA DE LOGIN 500/TIMEOUT

**Data**: 18/10/2025  
**Projeto**: FinaFlow - Migração GCP  
**Problema**: Login com HTTP 500 / Timeout  
**Causa Raiz**: Cloud Run sem acesso ao Cloud SQL via Proxy

---

## 📊 DIAGNÓSTICO RESUMIDO

### ❌ Problema Identificado
O Cloud Run está tentando conectar ao Cloud SQL via **IP público** sem usar o **Cloud SQL Proxy**, resultando em timeouts de 169+ segundos.

### ✅ Solução
Configurar Cloud Run para usar **Cloud SQL Proxy via Unix Socket** (`/cloudsql/...`)

---

## 🛠️ CORREÇÕES APLICADAS

### ✅ 1. Atualizado `backend/cloudbuild.yaml`
- ✅ Adicionado `--add-cloudsql-instances=trivihair:us-central1:finaflow-db`
- ✅ Atualizado `DATABASE_URL` para usar Unix Socket
- ✅ Aumentado timeout de 300s para 600s
- ✅ Definido `--min-instances=1` (evitar cold start)
- ✅ Adicionado variável `JWT_SECRET`
- ✅ Melhorado `CORS_ORIGINS` e `ALLOWED_HOSTS`

### ✅ 2. Atualizado `backend/app/database.py`
- ✅ Suporte para Unix Socket e TCP
- ✅ Logs melhorados para debug
- ✅ Fallback para IP público correto (34.41.169.224)

---

## 🚀 PASSOS PARA APLICAR A CORREÇÃO

### **PASSO 1: Verificar Permissões do Service Account**

O Cloud Run precisa de permissões para acessar o Cloud SQL:

```bash
# Obter o Service Account do Cloud Run
export PROJECT_ID=trivihair
export REGION=us-central1
export SERVICE_NAME=finaflow-backend

# Obter o Service Account atual
SERVICE_ACCOUNT=$(gcloud run services describe $SERVICE_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --format="value(spec.template.spec.serviceAccountName)")

echo "Service Account: $SERVICE_ACCOUNT"

# Se não tiver service account específico, usar o default
if [ -z "$SERVICE_ACCOUNT" ]; then
  SERVICE_ACCOUNT="${PROJECT_ID}@appspot.gserviceaccount.com"
  echo "Usando Service Account default: $SERVICE_ACCOUNT"
fi

# Conceder permissões necessárias
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/cloudsql.client" \
  --project=$PROJECT_ID

echo "✅ Permissões concedidas!"
```

---

### **PASSO 2: Fazer Deploy do Backend Corrigido**

```bash
cd /Users/lucianoterres/Documents/GitHub/finaflow

# Fazer deploy via Cloud Build
gcloud builds submit \
  --config=backend/cloudbuild.yaml \
  --project=trivihair \
  .

# Aguardar conclusão do build (pode demorar 5-10 minutos)
```

---

### **PASSO 3: Verificar Deploy**

```bash
# Verificar se a nova revisão está ativa
gcloud run revisions list \
  --service=finaflow-backend \
  --region=us-central1 \
  --project=trivihair \
  --limit=5

# Verificar logs em tempo real
gcloud logging tail \
  "resource.type=cloud_run_revision AND resource.labels.service_name=finaflow-backend" \
  --project=trivihair
```

---

### **PASSO 4: Testar Health Check**

```bash
# Testar endpoint de health
BACKEND_URL="https://finaflow-backend-6arhlm3mha-uc.a.run.app"

echo "Testando health check..."
curl -v $BACKEND_URL/health

# Deve retornar:
# {
#   "status": "healthy",
#   "service": "finaflow-backend",
#   "version": "1.0.0"
# }
```

---

### **PASSO 5: Testar Login**

```bash
# Testar login via API
curl -X POST "${BACKEND_URL}/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=Admin@123"

# Deve retornar um token JWT
```

---

### **PASSO 6: Testar Frontend**

1. Abrir: https://finaflow.vercel.app/login
2. Digitar:
   - Username: `admin`
   - Password: `Admin@123` (ou `admin123`)
3. Clicar em "Entrar"
4. Aguardar redirecionamento para `/select-business-unit`

---

## 🔍 TROUBLESHOOTING

### Problema: Build Falha

**Solução 1: Verificar erros de sintaxe**
```bash
# Validar arquivo Python
python3 -m py_compile backend/hybrid_app.py
```

**Solução 2: Verificar espaço em disco**
```bash
df -h
# Se necessário, limpar builds antigos
gcloud builds list --project=trivihair --limit=20
```

---

### Problema: Timeout Persiste

**Solução 1: Verificar Cloud SQL está rodando**
```bash
gcloud sql instances describe finaflow-db \
  --project=trivihair \
  --format="value(state)"

# Deve retornar: RUNNABLE
```

**Solução 2: Verificar conexão direta ao Cloud SQL**
```bash
# Instalar cloud_sql_proxy localmente
curl -o cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.darwin.amd64
chmod +x cloud_sql_proxy

# Conectar via proxy
./cloud_sql_proxy -instances=trivihair:us-central1:finaflow-db=tcp:5432

# Em outro terminal, testar conexão
psql "postgresql://finaflow_user:finaflow_password@localhost:5432/finaflow_db"
```

**Solução 3: Verificar VPC / Firewall**
```bash
# Verificar se não há regras de firewall bloqueando
gcloud compute firewall-rules list --project=trivihair

# Verificar se Cloud Run está na mesma região do Cloud SQL
# Ambos devem estar em us-central1
```

---

### Problema: CORS Error no Frontend

**Solução: Atualizar CORS no backend**
```bash
gcloud run services update finaflow-backend \
  --region=us-central1 \
  --project=trivihair \
  --update-env-vars "CORS_ORIGINS=https://finaflow.vercel.app,https://finaflow-south-medias-projects.vercel.app,http://localhost:3000"
```

---

### Problema: JWT Secret Mismatch

**Solução: Garantir que JWT_SECRET está configurado**
```bash
gcloud run services update finaflow-backend \
  --region=us-central1 \
  --project=trivihair \
  --update-env-vars "JWT_SECRET=finaflow-secret-key-2024,SECRET_KEY=finaflow-secret-key-2024"
```

---

## 📋 CHECKLIST DE VALIDAÇÃO FINAL

### Backend
- [ ] Deploy concluído com sucesso
- [ ] Nova revisão ativa (não a 00003-p4n)
- [ ] Cloud SQL Proxy configurado (`--add-cloudsql-instances`)
- [ ] `DATABASE_URL` usando Unix Socket
- [ ] Health check retorna 200 OK
- [ ] Logs não mostram erros de conexão DB

### Autenticação
- [ ] Endpoint `/api/v1/auth/login` retorna token
- [ ] Token JWT válido e decodificável
- [ ] Endpoint `/api/v1/auth/user-business-units` retorna BUs
- [ ] Endpoint `/api/v1/auth/select-business-unit` funciona

### Frontend
- [ ] Login page carrega
- [ ] Login bem-sucedido redireciona para `/select-business-unit`
- [ ] Seleção de BU gera novo token
- [ ] Dashboard carrega após seleção de BU

---

## 🎯 CONFIGURAÇÕES CRÍTICAS

### DATABASE_URL

**❌ ERRADO (IP Público sem Proxy)**
```
postgresql://finaflow_user:finaflow_password@34.41.169.224:5432/finaflow_db
```

**✅ CORRETO (Unix Socket via Cloud SQL Proxy)**
```
postgresql://finaflow_user:finaflow_password@/finaflow_db?host=/cloudsql/trivihair:us-central1:finaflow-db
```

### Variáveis de Ambiente Cloud Run

```bash
DATABASE_URL=postgresql://finaflow_user:finaflow_password@/finaflow_db?host=/cloudsql/trivihair:us-central1:finaflow-db
SECRET_KEY=finaflow-secret-key-2024
JWT_SECRET=finaflow-secret-key-2024
CORS_ORIGINS=https://finaflow.vercel.app,http://localhost:3000
ALLOWED_HOSTS=finaflow.vercel.app,finaflow-backend-6arhlm3mha-uc.a.run.app,localhost
PROJECT_ID=trivihair
```

### Cloud Run Args Essenciais

```yaml
--add-cloudsql-instances=trivihair:us-central1:finaflow-db
--timeout=600
--min-instances=1
--cpu-boost
```

---

## 📞 SUPORTE ADICIONAL

### Comandos Úteis

```bash
# Ver logs de erro em tempo real
gcloud logging tail \
  "resource.type=cloud_run_revision AND severity>=ERROR" \
  --project=trivihair

# Verificar métricas de latência
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/request_latencies"' \
  --project=trivihair

# Listar todas as variáveis de ambiente do Cloud Run
gcloud run services describe finaflow-backend \
  --region=us-central1 \
  --project=trivihair \
  --format="value(spec.template.spec.containers[0].env)"

# Forçar nova revisão (rollback se necessário)
gcloud run services update-traffic finaflow-backend \
  --region=us-central1 \
  --project=trivihair \
  --to-revisions=REVISION_NAME=100
```

### Contatos GCP

- **Cloud Run**: https://console.cloud.google.com/run/detail/us-central1/finaflow-backend?project=trivihair
- **Cloud SQL**: https://console.cloud.google.com/sql/instances/finaflow-db?project=trivihair
- **Logs**: https://console.cloud.google.com/logs/query?project=trivihair
- **IAM**: https://console.cloud.google.com/iam-admin/iam?project=trivihair

---

## ✨ CONCLUSÃO

Após aplicar todas as correções acima:

1. O Cloud Run estará configurado para usar Cloud SQL Proxy
2. A conexão com o banco será via Unix Socket (rápida e segura)
3. O login deve funcionar em < 2 segundos
4. O sistema estará totalmente operacional

**Tempo Estimado de Correção**: 15-20 minutos  
**Downtime Esperado**: 0 (deploy blue-green automático)

---

**Preparado por**: Sistema de Diagnóstico FinaFlow  
**Data**: 2025-10-18  
**Status**: Pronto para aplicação ✅

