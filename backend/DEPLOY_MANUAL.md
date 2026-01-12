# 🚀 Deploy Manual - Backend STAGING

## Problema

Não há deploy automático configurado no Cloud Run. Este guia explica como fazer o deploy manual.

## Pré-requisitos

1. **gcloud CLI instalado**: https://cloud.google.com/sdk/docs/install
2. **Autenticação GCP**: Execute `gcloud auth login`
3. **Permissões necessárias**:
   - `run.services.create`
   - `run.services.update`
   - `run.services.get`
   - `cloudsql.instances.connect`
   - `storage.objects.create` (para build)

## Método 1: Script Automatizado (Recomendado)

```bash
cd backend
./deploy_staging.sh
```

O script irá:
- Verificar autenticação
- Configurar projeto GCP
- Fazer build e deploy no Cloud Run
- Mostrar URL do serviço

## Método 2: Comando Manual

```bash
cd backend

# Configurar projeto
gcloud config set project trivihair

# Fazer deploy
gcloud run deploy finaflow-backend-staging \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --add-cloudsql-instances trivihair:us-central1:finaflow-db-staging \
  --env-vars-file env_vars_staging.yaml \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 600 \
  --concurrency 80 \
  --min-instances 1 \
  --max-instances 10 \
  --cpu-boost
```

## Variáveis de Ambiente

O arquivo `env_vars_staging.yaml` contém:
- `DATABASE_URL`: Conexão com Cloud SQL
- `CORS_ORIGINS`: `https://finaflow-lcz5.vercel.app,https://finaflow.vercel.app,http://localhost:3000`
- `JWT_SECRET`: Chave secreta para JWT
- `ENVIRONMENT`: `staging`

## Verificar Deploy

Após o deploy, verifique:

1. **URL do serviço**:
   ```bash
   gcloud run services describe finaflow-backend-staging \
     --region us-central1 \
     --format="value(status.url)"
   ```

2. **Health check**:
   ```bash
   curl https://finaflow-backend-staging-642830139828.us-central1.run.app/health
   ```

3. **Logs**:
   ```bash
   gcloud logging tail \
     "resource.type=cloud_run_revision AND resource.labels.service_name=finaflow-backend-staging" \
     --project=trivihair
   ```

## Troubleshooting

### Erro: Permission Denied

Se receber erro de permissão:
1. Verifique se está autenticado: `gcloud auth list`
2. Verifique se tem as permissões necessárias no projeto
3. Entre em contato com o administrador do projeto GCP

### Erro: Build Failed

Se o build falhar:
1. Verifique os logs do Cloud Build no Console GCP
2. Verifique se o Dockerfile está correto
3. Verifique se todas as dependências estão no `requirements.txt`

### Erro: Database Connection

Se houver erro de conexão com o banco:
1. Verifique se a instância Cloud SQL está rodando
2. Verifique se o `DATABASE_URL` está correto
3. Verifique se o Cloud Run tem permissão para conectar ao Cloud SQL

## Próximos Passos

Após o deploy bem-sucedido:

1. ✅ Validar que o serviço está respondendo
2. ✅ Testar endpoints principais
3. ✅ Validar CORS está funcionando
4. ✅ Executar testes E2E se necessário












