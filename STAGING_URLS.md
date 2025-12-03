# 🎯 AMBIENTE STAGING - URLs E ACESSOS

**Data de Criação**: Janeiro 2025  
**Status**: ✅ Backend Pronto | ⏳ Frontend Pendente

---

## ✅ BACKEND STAGING

### URL Principal
```
https://finaflow-backend-staging-642830139828.us-central1.run.app
```

### Health Check
```
https://finaflow-backend-staging-642830139828.us-central1.run.app/health
```
**Resposta esperada:**
```json
{
  "status": "healthy",
  "service": "finaflow-backend",
  "version": "1.0.0"
}
```

### API Documentation (Swagger)
```
https://finaflow-backend-staging-642830139828.us-central1.run.app/docs
```

### ReDoc
```
https://finaflow-backend-staging-642830139828.us-central1.run.app/redoc
```

---

## ✅ FRONTEND STAGING

**Status**: ✅ Criado e deployado na Vercel

**URL**: 
```
https://finaflow-lcz5.vercel.app/
```

**Projeto Vercel**: `finaflow-lcz5` (ou nome configurado)

---

## 🗄️ BANCO DE DADOS STAGING

**Instância**: `finaflow-db-staging`  
**Região**: `us-central1`  
**Tipo**: PostgreSQL 14  
**Banco**: `finaflow`  
**Usuário**: `finaflow_user`  
**Unix Socket**: `/cloudsql/trivihair:us-central1:finaflow-db-staging`

---

## 📊 CONFIGURAÇÕES

### Backend
- **Serviço**: `finaflow-backend-staging`
- **Região**: `us-central1`
- **Memória**: 2Gi
- **CPU**: 2
- **Min Instances**: 1
- **Max Instances**: 10
- **CORS**: `*` (permitindo todos os domínios)

### Variáveis de Ambiente
- `DATABASE_URL`: Configurado com Unix Socket
- `CORS_ORIGINS`: `*`
- `JWT_SECRET`: `finaflow-secret-key-2024-staging`
- `ENVIRONMENT`: `staging`

---

## 🔍 LOGS

### Backend Logs
```bash
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=finaflow-backend-staging" --project=trivihair
```

### Banco Logs
```bash
gcloud logging tail "resource.type=cloudsql_database AND resource.labels.database_id=trivihair:us-central1:finaflow-db-staging" --project=trivihair
```

### Console GCP
- Backend: https://console.cloud.google.com/run/detail/us-central1/finaflow-backend-staging/logs?project=trivihair
- Banco: https://console.cloud.google.com/sql/instances/finaflow-db-staging/logs?project=trivihair

---

## ✅ CHECKLIST DE VALIDAÇÃO

### Backend
- [x] Serviço criado no Cloud Run
- [x] Health check respondendo
- [x] Banco de dados criado
- [x] Usuário configurado
- [x] Unix Socket conectado
- [x] CORS configurado
- [ ] Tabelas inicializadas (pode precisar execução manual)

### Frontend
- [x] Projeto criado na Vercel
- [x] Branch staging conectada
- [ ] Variáveis de ambiente configuradas (verificar `NEXT_PUBLIC_API_URL`)
- [x] Deploy concluído
- [x] URL pública gerada: https://finaflow-lcz5.vercel.app/

---

## 🚀 PRÓXIMOS PASSOS

1. **Criar frontend staging na Vercel** (ver `VERCEL_STAGING_SETUP.md`)
2. **Configurar variável `NEXT_PUBLIC_API_URL`** com a URL do backend
3. **Realizar deploy do frontend**
4. **Testar integração frontend ↔ backend**
5. **Inicializar tabelas do banco** (se necessário)
6. **Notificar PM e QA com URLs finais**

---

**Última atualização**: Janeiro 2025

