# Migração para o Projeto Trivihair

## ✅ Alterações Realizadas

Este documento descreve todas as alterações realizadas para migrar o sistema FINAFlow do projeto `automatizar-452311` para o projeto `trivihair`.

### 1. Credenciais do Google Cloud

**Arquivo atualizado**: `google_credentials.json`

- ✅ Atualizado com as credenciais da service account `dashboardluciano@trivihair.iam.gserviceaccount.com`
- ✅ Project ID: `trivihair`

**⚠️ IMPORTANTE**: Este arquivo contém informações sensíveis e não deve ser commitado no Git.

### 2. Configurações de Deploy

#### Cloud Run Service Configuration

**Arquivos atualizados**:
- ✅ `service.yaml` (raiz)
- ✅ `backend/service.yaml`

**Mudanças**:
```yaml
# Antes
image: gcr.io/automatizar-452311/finaflow-backend

# Depois
image: gcr.io/trivihair/finaflow-backend
```

#### Cloud Build

**Arquivo**: `backend/cloudbuild.yaml`

O arquivo já usa a variável `$PROJECT_ID`, então funciona automaticamente com o novo projeto quando executado com:
```bash
gcloud config set project trivihair
gcloud builds submit --config=backend/cloudbuild.yaml
```

### 3. Docker Compose

**Arquivo atualizado**: `docker-compose.yml`

```yaml
# Antes
- PROJECT_ID=automatizar-452311

# Depois
- PROJECT_ID=trivihair
```

### 4. Arquivos de API

**Arquivos atualizados**:
- ✅ `backend/app/api/debug.py`
- ✅ `app/api/debug.py`

**Mudanças**: Todas as referências a `automatizar-452311.finaflow.*` foram alteradas para `trivihair.finaflow.*`

Queries atualizadas:
- `trivihair.finaflow.Accounts`
- `trivihair.finaflow.Transactions`
- `trivihair.finaflow.Users`

### 5. Scripts de Configuração

**Arquivos atualizados**:
- ✅ `scripts/final_query.sql`
- ✅ `scripts/debug_database_query.py`
- ✅ `scripts/create_super_admin_bigquery.py`
- ✅ `scripts/create_consistent_hash.py`
- ✅ `scripts/check_bigquery_user.py`

Todos os scripts SQL agora referenciam:
```sql
`trivihair.finaflow.Users`
`trivihair.finaflow.Accounts`
`trivihair.finaflow.Transactions`
```

### 6. Documentação

**Novos arquivos criados**:
- ✅ `docs/GUIA_DEPLOY_TRIVIHAIR.md` - Guia completo de deploy
- ✅ `MIGRACAO_TRIVIHAIR.md` - Este arquivo
- ✅ `deploy_trivihair.sh` - Script automatizado de deploy

## 🚀 Como Fazer o Deploy

### Método 1: Script Automatizado (Recomendado)

```bash
# Dar permissão de execução
chmod +x deploy_trivihair.sh

# Executar
./deploy_trivihair.sh
```

### Método 2: Cloud Build

```bash
# Configurar projeto
gcloud config set project trivihair

# Fazer deploy
gcloud builds submit --config=backend/cloudbuild.yaml
```

### Método 3: Manual

```bash
# 1. Configurar projeto
gcloud config set project trivihair
gcloud auth configure-docker

# 2. Construir imagem
cd backend
docker build -t gcr.io/trivihair/finaflow-backend .

# 3. Push
docker push gcr.io/trivihair/finaflow-backend

# 4. Deploy
gcloud run deploy finaflow-backend \
  --image gcr.io/trivihair/finaflow-backend \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated
```

## 📊 Checklist de Migração

### Antes do Deploy

- [x] Credenciais do GCP atualizadas
- [x] Arquivos de configuração atualizados
- [x] Scripts SQL atualizados
- [x] Documentação criada
- [ ] Projeto trivihair configurado no GCP Console
- [ ] APIs necessárias habilitadas (Cloud Run, Cloud Build, etc.)
- [ ] Service Account com permissões corretas

### Durante o Deploy

- [ ] Build da imagem Docker bem-sucedido
- [ ] Push para GCR concluído
- [ ] Deploy no Cloud Run bem-sucedido
- [ ] Variáveis de ambiente configuradas
- [ ] URL do backend obtida

### Após o Deploy

- [ ] Backend respondendo (testar `/docs`)
- [ ] Banco de dados configurado (PostgreSQL ou BigQuery)
- [ ] Usuário super admin criado
- [ ] Login funcionando
- [ ] Frontend atualizado com nova URL do backend (Vercel)
- [ ] CORS configurado corretamente
- [ ] Testes E2E executados

## 🔧 Configurações Necessárias

### APIs do GCP a Habilitar

```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable sql-component.googleapis.com
```

### Permissões da Service Account

A service account `dashboardluciano@trivihair.iam.gserviceaccount.com` precisa dos seguintes roles:

- `roles/run.admin` - Para gerenciar Cloud Run
- `roles/storage.admin` - Para Container Registry
- `roles/bigquery.admin` - Para BigQuery (se usar)
- `roles/cloudsql.client` - Para Cloud SQL (se usar)

### Variáveis de Ambiente (Cloud Run)

```bash
DATABASE_URL=postgresql://finaflow_user:finaflow_password@34.70.102.98:5432/finaflow_db
SECRET_KEY=finaflow-secret-key-2024
ALLOWED_HOSTS=localhost,127.0.0.1,finaflow.vercel.app
CORS_ORIGINS=https://finaflow.vercel.app,http://localhost:3000
PROJECT_ID=trivihair
DATASET=finaflow
```

### Variáveis de Ambiente (Vercel - Frontend)

```bash
NEXT_PUBLIC_API_URL=<URL_DO_CLOUD_RUN>
```

**Nota**: Obtenha a URL do Cloud Run após o primeiro deploy.

## 🗄️ Banco de Dados

### PostgreSQL (Configuração Atual)

O sistema usa PostgreSQL no IP: `34.70.102.98`

**Connection String**:
```
postgresql://finaflow_user:finaflow_password@34.70.102.98:5432/finaflow_db
```

### BigQuery (Opcional)

Se optar por usar BigQuery, execute:

```bash
# Criar dataset
bq mk --dataset trivihair:finaflow

# Criar tabelas
bq mk --table trivihair:finaflow.Users \
  id:STRING,username:STRING,email:STRING,hashed_password:STRING,role:STRING,tenant_id:STRING,created_at:TIMESTAMP

bq mk --table trivihair:finaflow.Accounts \
  id:STRING,name:STRING,balance:FLOAT,tenant_id:STRING,created_at:TIMESTAMP

bq mk --table trivihair:finaflow.Transactions \
  id:STRING,account_id:STRING,amount:FLOAT,description:STRING,tenant_id:STRING,created_at:TIMESTAMP
```

## 👤 Usuário Super Admin

### Criar via Script

```bash
cd scripts
python3 create_super_admin_bigquery.py
```

### Criar Manualmente (BigQuery)

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

**Credenciais**:
- Username: `admin`
- Senha: `admin123`

## 🔍 Verificação e Testes

### Testar Backend

```bash
# URL do backend (obtida após deploy)
BACKEND_URL="https://finaflow-backend-<hash>.us-central1.run.app"

# Testar documentação
curl $BACKEND_URL/docs

# Testar health check (se existir)
curl $BACKEND_URL/health

# Testar login
curl -X POST "$BACKEND_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

### Ver Logs

```bash
# Logs em tempo real
gcloud run logs tail finaflow-backend --region us-central1

# Últimos 50 logs
gcloud run logs read finaflow-backend --region us-central1 --limit 50
```

### Métricas

Acesse o console:
```
https://console.cloud.google.com/run/detail/us-central1/finaflow-backend/metrics?project=trivihair
```

## ⚠️ Problemas Comuns

### 1. Erro de Permissões

**Erro**: "Permission denied" ao fazer deploy

**Solução**:
```bash
# Verificar permissões
gcloud projects get-iam-policy trivihair

# Adicionar permissões (se necessário)
gcloud projects add-iam-policy-binding trivihair \
  --member="user:seu-email@gmail.com" \
  --role="roles/run.admin"
```

### 2. Erro de Conexão com Banco

**Erro**: Timeout ou connection refused

**Solução**:
1. Verificar se o IP está correto
2. Verificar regras de firewall
3. Testar conexão local

### 3. CORS Errors

**Erro**: CORS policy no browser

**Solução**:
1. Verificar `CORS_ORIGINS` no Cloud Run
2. Incluir domínio do Vercel
3. Verificar `ALLOWED_HOSTS`

## 📞 Suporte

Para mais informações, consulte:
- [Guia de Deploy Completo](docs/GUIA_DEPLOY_TRIVIHAIR.md)
- [Documentação do Cloud Run](https://cloud.google.com/run/docs)
- [Documentação do Vercel](https://vercel.com/docs)

## 📝 Resumo das Mudanças

| Item | Antes | Depois | Status |
|------|-------|--------|--------|
| Projeto GCP | automatizar-452311 | trivihair | ✅ |
| Service Account | southmedia@... | dashboardluciano@... | ✅ |
| Container Registry | gcr.io/automatizar-452311 | gcr.io/trivihair | ✅ |
| BigQuery Tables | automatizar-452311.finaflow.* | trivihair.finaflow.* | ✅ |
| Credenciais JSON | Antigas | Novas | ✅ |
| Scripts | Antigo projeto | Novo projeto | ✅ |
| Documentação | - | Criada | ✅ |

---

**Data da Migração**: 15 de Outubro de 2025  
**Responsável**: Equipe de Desenvolvimento FINAFlow  
**Projeto**: trivihair


