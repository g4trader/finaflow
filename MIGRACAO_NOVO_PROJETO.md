# Migração para Novo Projeto GCP

## 📋 Informações do Novo Projeto

- **Project ID**: `project-c6f9c72d-aca4-476d-82f`
- **Nome**: FinaFlow
- **Região**: `us-central1`

## ✅ Configurações Atualizadas

Os seguintes arquivos foram atualizados:

1. `backend/deploy_staging.sh` - Project ID atualizado
2. `backend/env_vars_staging.yaml` - Project ID e DATABASE_URL atualizados

## 🔧 Próximos Passos

### 1. Habilitar APIs Necessárias

As seguintes APIs precisam ser habilitadas no novo projeto:

- **Cloud Run Admin API**: https://console.developers.google.com/apis/api/run.googleapis.com/overview?project=project-c6f9c72d-aca4-476d-82f
- **Cloud SQL Admin API**: https://console.developers.google.com/apis/api/sqladmin.googleapis.com/overview?project=project-c6f9c72d-aca4-476d-82f
- **Cloud Build API** (se usar Cloud Build)
- **Artifact Registry API** (se usar Artifact Registry)

### 2. Criar/Configurar Cloud SQL

Se ainda não existe, criar instância do Cloud SQL:

```bash
gcloud sql instances create finaflow-db-staging \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --project=project-c6f9c72d-aca4-476d-82f
```

### 3. Criar Banco de Dados e Usuário

```bash
# Criar banco
gcloud sql databases create finaflow \
  --instance=finaflow-db-staging \
  --project=project-c6f9c72d-aca4-476d-82f

# Criar usuário (se necessário)
gcloud sql users create finaflow_user \
  --instance=finaflow-db-staging \
  --password=Finaflow123! \
  --project=project-c6f9c72d-aca4-476d-82f
```

### 4. Fazer Deploy

Após habilitar as APIs e configurar o banco:

```bash
cd backend
./deploy_staging.sh
```

### 5. Atualizar URLs nos Scripts

Os scripts Python que usam `BACKEND_URL` precisarão ser atualizados após o deploy para usar a nova URL do Cloud Run.

## 📝 Notas

- O `DATABASE_URL` no `env_vars_staging.yaml` foi atualizado para usar o novo project ID
- Certifique-se de que o Cloud SQL instance name está correto
- Verifique as permissões de IAM para garantir que o Cloud Run service account tenha acesso ao Cloud SQL

