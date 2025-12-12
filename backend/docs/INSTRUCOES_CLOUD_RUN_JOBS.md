# 🚀 Instruções Rápidas - Cloud Run Jobs

## 📋 Resumo

Foram criados 2 Cloud Run Jobs para automatizar seed e validação:

1. **`finaflow-seed-staging-job`**: Popula banco com dados da planilha
2. **`finaflow-validate-dashboard-staging-job`**: Valida consistência Planilha→Banco→API

---

## 🎯 Primeira Vez (Criar Jobs)

Execute no Cloud Shell ou localmente com gcloud configurado:

```bash
cd ~/finaflow/backend
./scripts/setup_cloud_run_jobs.sh
```

Este script:
- ✅ Descobre configuração do serviço `finaflow-backend-staging`
- ✅ Cria/atualiza os 2 jobs automaticamente
- ✅ Reutiliza mesma imagem, service account e env vars

---

## 🌱 Executar Seed

```bash
gcloud run jobs execute finaflow-seed-staging-job \
  --region=us-central1 \
  --wait
```

**Quando usar**: Quando precisar popular ou atualizar o banco com dados da planilha.

---

## ✅ Executar Validação

```bash
gcloud run jobs execute finaflow-validate-dashboard-staging-job \
  --region=us-central1 \
  --wait
```

**Resultado esperado**:
- Exit code 0: ✅ Sem mismatches
- Exit code ≠0: ❌ Mismatches detectados (ver logs)

**Critérios de sucesso**:
- ✅ FILTRO→BANCO: 0 ocorrências
- ✅ BANCO→API: 0 ocorrências

---

## 📊 Ver Logs

### Via Console
1. Acesse: https://console.cloud.google.com/run/jobs
2. Selecione o job
3. Clique em "Execuções" → Selecione execução → "Logs"

### Via CLI
```bash
gcloud logging read \
  "resource.type=cloud_run_job AND resource.labels.job_name=finaflow-validate-dashboard-staging-job" \
  --limit=50 \
  --format="value(textPayload)" \
  --region=us-central1
```

---

## ✅ Vantagens

- ✅ **Sem Cloud Shell**: Execute via CLI ou Console
- ✅ **Sem Proxy**: Acesso nativo ao Cloud SQL
- ✅ **Reprodutível**: Mesma imagem do serviço
- ✅ **CI/CD Ready**: Exit codes padronizados

---

## 📚 Documentação Completa

- **Setup**: `backend/scripts/setup_cloud_run_jobs.sh`
- **Resumo**: `backend/docs/RESUMO_CLOUD_RUN_JOBS.md`
- **Validação**: `backend/docs/EXECUTAR_VALIDACAO_DASHBOARD.md`

---

**Status**: ✅ Pronto para uso

