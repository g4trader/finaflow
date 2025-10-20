# ⚡ COMANDOS DE CORREÇÃO RÁPIDA - LOGIN 500/TIMEOUT

**Data**: 18/10/2025  
**Tempo Estimado**: 15-20 minutos  
**Status**: Pronto para executar ✅

---

## 🎯 RESUMO DO PROBLEMA

**Sintoma**: Login retorna HTTP 500 ou timeout  
**Causa**: Cloud Run tentando conectar ao Cloud SQL via IP público sem Cloud SQL Proxy  
**Solução**: Configurar Cloud SQL Proxy com Unix Socket

---

## ✅ MÉTODO 1: Script Automatizado (RECOMENDADO)

```bash
cd /Users/lucianoterres/Documents/GitHub/finaflow
chmod +x fix_login_issue.sh
./fix_login_issue.sh
```

O script irá:
1. ✅ Verificar permissões IAM
2. ✅ Verificar Cloud SQL
3. ✅ Fazer build e deploy
4. ✅ Testar health check
5. ✅ Testar login

---

## 🔧 MÉTODO 2: Comandos Manuais (Passo a Passo)

### PASSO 1: Configurar Permissões IAM (2 min)

```bash
export PROJECT_ID=trivihair
export REGION=us-central1
export SERVICE_NAME=finaflow-backend

# Obter Service Account
SERVICE_ACCOUNT=$(gcloud run services describe $SERVICE_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --format="value(spec.template.spec.serviceAccountName)")

# Se vazio, usar default
if [ -z "$SERVICE_ACCOUNT" ]; then
  SERVICE_ACCOUNT="${PROJECT_ID}@appspot.gserviceaccount.com"
fi

# Conceder permissão Cloud SQL Client
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/cloudsql.client" \
  --project=$PROJECT_ID
```

---

### PASSO 2: Fazer Deploy (10-15 min)

```bash
cd /Users/lucianoterres/Documents/GitHub/finaflow

# Executar build
gcloud builds submit \
  --config=backend/cloudbuild.yaml \
  --project=trivihair \
  .

# Aguardar conclusão...
```

---

### PASSO 3: Verificar Deploy (2 min)

```bash
# Ver últimas revisões
gcloud run revisions list \
  --service=finaflow-backend \
  --region=us-central1 \
  --project=trivihair \
  --limit=5

# Ver configuração atual
gcloud run services describe finaflow-backend \
  --region=us-central1 \
  --project=trivihair \
  --format="yaml(spec.template.spec.containers[0].env)"
```

---

### PASSO 4: Testar (2 min)

```bash
BACKEND_URL="https://finaflow-backend-6arhlm3mha-uc.a.run.app"

# Health Check
curl -v $BACKEND_URL/health

# Login
curl -X POST "${BACKEND_URL}/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=Admin@123"

# Se retornar token JWT, está funcionando! ✅
```

---

## 🚀 MÉTODO 3: Aplicação Direta Via gcloud (RÁPIDO mas menos seguro)

Se quiser aplicar as mudanças SEM fazer novo build (apenas atualizar config):

```bash
gcloud run services update finaflow-backend \
  --region=us-central1 \
  --project=trivihair \
  --add-cloudsql-instances=trivihair:us-central1:finaflow-db \
  --update-env-vars="DATABASE_URL=postgresql://finaflow_user:finaflow_password@/finaflow_db?host=/cloudsql/trivihair:us-central1:finaflow-db" \
  --update-env-vars="JWT_SECRET=finaflow-secret-key-2024" \
  --update-env-vars="SECRET_KEY=finaflow-secret-key-2024" \
  --update-env-vars="CORS_ORIGINS=https://finaflow.vercel.app,http://localhost:3000" \
  --timeout=600 \
  --min-instances=1 \
  --cpu-boost
```

**⚠️ NOTA**: Este método NÃO atualiza o código. Use apenas se o código já estiver correto.

---

## 📊 VERIFICAÇÃO DE SUCESSO

### ✅ Checklist de Validação

Execute estes comandos para confirmar que tudo está OK:

```bash
# 1. Cloud SQL Proxy está configurado?
gcloud run services describe finaflow-backend \
  --region=us-central1 \
  --project=trivihair \
  --format="value(metadata.annotations.'run.googleapis.com/cloudsql-instances')"

# Deve retornar: trivihair:us-central1:finaflow-db

# 2. DATABASE_URL está correto?
gcloud run services describe finaflow-backend \
  --region=us-central1 \
  --project=trivihair \
  --format="value(spec.template.spec.containers[0].env)" | grep DATABASE_URL

# Deve conter: /cloudsql/trivihair:us-central1:finaflow-db

# 3. Timeout aumentado?
gcloud run services describe finaflow-backend \
  --region=us-central1 \
  --project=trivihair \
  --format="value(spec.template.spec.timeoutSeconds)"

# Deve retornar: 600

# 4. Min instances = 1?
gcloud run services describe finaflow-backend \
  --region=us-central1 \
  --project=trivihair \
  --format="value(spec.template.metadata.annotations.'autoscaling.knative.dev/minScale')"

# Deve retornar: 1
```

---

## 🔍 TROUBLESHOOTING RÁPIDO

### Problema: Build Falha com "Permission Denied"

```bash
# Ativar APIs necessárias
gcloud services enable cloudbuild.googleapis.com \
  --project=trivihair

gcloud services enable run.googleapis.com \
  --project=trivihair

gcloud services enable sqladmin.googleapis.com \
  --project=trivihair
```

---

### Problema: Timeout Persiste

```bash
# Ver logs em tempo real
gcloud logging tail \
  "resource.type=cloud_run_revision AND resource.labels.service_name=finaflow-backend" \
  --project=trivihair \
  --format=json

# Procure por:
# - "Connection timed out"
# - "could not connect to server"
# - "SQLSTATE"
```

---

### Problema: "Cloud SQL instance not found"

```bash
# Verificar se a instância existe
gcloud sql instances list --project=trivihair

# Verificar se o nome está correto
gcloud sql instances describe finaflow-db --project=trivihair

# Se não existir, criar nova instância:
gcloud sql instances create finaflow-db \
  --database-version=POSTGRES_14 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --project=trivihair
```

---

### Problema: "Service Account lacks permissions"

```bash
# Listar permissões do Service Account
gcloud projects get-iam-policy trivihair \
  --flatten="bindings[].members" \
  --filter="bindings.members:*@appspot.gserviceaccount.com"

# Adicionar todas as permissões necessárias
gcloud projects add-iam-policy-binding trivihair \
  --member="serviceAccount:trivihair@appspot.gserviceaccount.com" \
  --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding trivihair \
  --member="serviceAccount:trivihair@appspot.gserviceaccount.com" \
  --role="roles/run.invoker"
```

---

## 🎯 TESTE FINAL - FRONTEND

Após aplicar as correções, testar o fluxo completo:

1. **Abrir**: https://finaflow.vercel.app/login

2. **Login**:
   - Username: `admin`
   - Password: `Admin@123` (ou tente `admin123`)

3. **Esperar**:
   - Redirecionamento para `/select-business-unit`
   - Se demorar mais de 5 segundos, há problema

4. **Selecionar BU**:
   - Escolher "Matriz"
   - Deve redirecionar para `/dashboard`

---

## 📞 COMANDOS DE MONITORAMENTO

Enquanto o sistema roda, monitore com:

```bash
# Logs de erro (terminal 1)
gcloud logging tail \
  "resource.type=cloud_run_revision AND severity>=ERROR" \
  --project=trivihair

# Logs de info (terminal 2)
gcloud logging tail \
  "resource.type=cloud_run_revision AND textPayload=~'Login|Conectando'" \
  --project=trivihair

# Métricas de latência
watch -n 5 'gcloud monitoring time-series list \
  --filter="metric.type=\"run.googleapis.com/request_latencies\"" \
  --project=trivihair | head -20'
```

---

## ✅ CRITÉRIO DE SUCESSO

O sistema está 100% funcional quando:

- ✅ Health check retorna 200 em < 1s
- ✅ Login retorna token JWT em < 3s
- ✅ Listar BUs retorna array em < 2s
- ✅ Selecionar BU retorna novo token em < 2s
- ✅ Dashboard carrega em < 3s
- ✅ Logs não mostram erros de conexão DB

---

## 🆘 ROLLBACK (Se necessário)

Se algo der muito errado, voltar para revisão anterior:

```bash
# Listar revisões
gcloud run revisions list \
  --service=finaflow-backend \
  --region=us-central1 \
  --project=trivihair

# Voltar para revisão específica
gcloud run services update-traffic finaflow-backend \
  --region=us-central1 \
  --project=trivihair \
  --to-revisions=finaflow-backend-00040-abc=100
```

---

## 📁 ARQUIVOS MODIFICADOS

Os seguintes arquivos foram atualizados para esta correção:

1. ✅ `backend/cloudbuild.yaml`
   - Adicionado `--add-cloudsql-instances`
   - Atualizado `DATABASE_URL`
   - Aumentado timeout e min-instances

2. ✅ `backend/app/database.py`
   - Suporte para Unix Socket
   - Logs melhorados

3. 📄 `RUNBOOK_CORRECAO_LOGIN.md` (criado)
4. 📄 `fix_login_issue.sh` (criado)
5. 📄 `COMANDOS_CORRECAO_RAPIDA.md` (este arquivo)

---

## 🎊 CONCLUSÃO

Escolha um dos 3 métodos acima:

- **Método 1** (Script): Mais rápido e confiável ⭐ RECOMENDADO
- **Método 2** (Manual): Mais controle, passo a passo
- **Método 3** (gcloud update): Mais rápido mas não atualiza código

**Tempo total esperado**: 15-20 minutos  
**Downtime**: 0 (deploy gradual automático)

---

**Preparado por**: Sistema de Diagnóstico FinaFlow  
**Data**: 2025-10-18  
**Versão**: 1.0

