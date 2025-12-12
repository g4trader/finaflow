# 📋 Resumo - Cloud Run Jobs para Seed e Validação

**Data**: 2025-12-11  
**Status**: ✅ **IMPLEMENTADO**

---

## 🎯 Objetivo

Automatizar o processo de seed e validação do dashboard, eliminando a dependência do Cloud Shell e permitindo execução via Cloud Run Jobs.

---

## ✅ Jobs Criados

### 1. finaflow-seed-staging-job

**Função**: Popula o banco de dados STAGING com dados da planilha Excel do cliente.

**Configuração**:
- Imagem: Mesma do serviço `finaflow-backend-staging`
- Service Account: Mesma do serviço
- Env Vars: Mesmas do serviço + variáveis específicas do seed
- Memória: 1Gi
- CPU: 1
- Max Retries: 0

**Variáveis de Ambiente**:
- `SEED_EXCEL_FILE`: Caminho do arquivo Excel (default: `data/fluxo_caixa_2025.xlsx`)
- `SEED_TENANT_NAME`: Nome do tenant (default: "FinaFlow Staging")
- `SEED_RESET_DATA`: Se deve resetar dados antes do seed (default: false)

**Comando de Execução**:
```bash
gcloud run jobs execute finaflow-seed-staging-job --region=us-central1 --wait
```

### 2. finaflow-validate-dashboard-staging-job

**Função**: Valida consistência entre Planilha → Banco → API.

**Configuração**:
- Imagem: Mesma do serviço `finaflow-backend-staging`
- Service Account: Mesma do serviço
- Env Vars: Mesmas do serviço + variáveis específicas da validação
- Memória: 1Gi
- CPU: 1
- Max Retries: 0

**Variáveis de Ambiente**:
- `VALIDATION_EXCEL_FILE`: Caminho do arquivo Excel (default: `data/fluxo_caixa_2025.xlsx`)
- `VALIDATION_YEAR`: Ano para validação (default: 2025)
- `BACKEND_URL`: URL do serviço de backend (extraída automaticamente)

**Comando de Execução**:
```bash
gcloud run jobs execute finaflow-validate-dashboard-staging-job --region=us-central1 --wait
```

**Exit Codes**:
- `0`: ✅ Sem mismatches (FILTRO→BANCO = 0, BANCO→API = 0)
- `≠0`: ❌ Mismatches detectados

---

## 🚀 Como Criar/Atualizar os Jobs

Execute o script de setup (uma vez ou após mudanças):

```bash
cd ~/finaflow/backend
./scripts/setup_cloud_run_jobs.sh
```

O script:
1. Descobre automaticamente a configuração do serviço `finaflow-backend-staging`
2. Extrai imagem, service account e env vars
3. Cria/atualiza os jobs com as mesmas configurações
4. Garante acesso nativo ao Cloud SQL

---

## 📊 Como Ver Logs

### Via Console GCP

1. Acesse: https://console.cloud.google.com/run/jobs
2. Selecione o job desejado
3. Clique em "Execuções" → Selecione execução → "Logs"

### Via CLI

```bash
# Logs do job de validação
gcloud logging read \
  "resource.type=cloud_run_job AND resource.labels.job_name=finaflow-validate-dashboard-staging-job" \
  --limit=50 \
  --format="value(textPayload)" \
  --region=us-central1

# Logs do job de seed
gcloud logging read \
  "resource.type=cloud_run_job AND resource.labels.job_name=finaflow-seed-staging-job" \
  --limit=50 \
  --format="value(textPayload)" \
  --region=us-central1
```

---

## ✅ Critérios de Aceite

- [x] Jobs criados em `us-central1`
- [x] Jobs usam mesma imagem do serviço `finaflow-backend-staging`
- [x] Jobs usam mesma service account
- [x] Jobs usam mesmas env vars de banco
- [x] Job de validação conecta ao banco sem Cloud SQL Proxy
- [x] Job de validação chama backend via BACKEND_URL
- [x] Job de validação retorna exit code 0 quando sem mismatches
- [x] Documentação atualizada

---

## 📚 Arquivos Criados

1. **`backend/scripts/run_validation_job.py`**: Wrapper para job de validação
2. **`backend/scripts/run_seed_job.py`**: Wrapper para job de seed
3. **`backend/scripts/setup_cloud_run_jobs.sh`**: Script para criar/atualizar jobs
4. **`backend/docs/EXECUTAR_VALIDACAO_DASHBOARD.md`**: Documentação atualizada
5. **`backend/docs/RELATORIO_FINAL_PO_FABIANO.md`**: Relatório atualizado

---

## 🎯 Benefícios

- ✅ **Elimina Cloud Shell**: Validação pode ser feita via CLI ou Console
- ✅ **Acesso Nativo**: Jobs conectam diretamente ao Cloud SQL (sem proxy)
- ✅ **Reprodutível**: Mesma imagem e configuração do serviço
- ✅ **CI/CD Ready**: Exit codes padronizados para automação futura
- ✅ **Logs Centralizados**: Fácil de debugar e monitorar

---

**Última atualização**: 2025-12-11  
**Status**: ✅ Pronto para uso

