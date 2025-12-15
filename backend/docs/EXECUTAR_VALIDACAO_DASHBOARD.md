# 🚀 Executar Validação do Dashboard

**Fluxo Recomendado (v2.0)**:
1. **Script unificado de Seed + Validação** (Cloud Shell / Local)
2. **Cloud Run Jobs** (Opcional / Futuro)

**Data**: 2025-12-12

---

## ✅ Fluxo recomendado (v2.0) – Script Unificado

### Pré-requisitos

- ✅ Acessar o Cloud Shell no projeto `trivihair`
- ✅ Repositório `finaflow` já clonado em `~/finaflow`
- ✅ Banco STAGING acessível via `DATABASE_URL` (ou usar default)

### Passos

```bash
cd ~/finaflow/backend
./scripts/run_seed_and_validate.sh --year 2025
```

### O que o script faz

1. Lê (ou assume) as variáveis:
   - `DATABASE_URL` (default: `postgresql://finaflow_user:Finaflow123!@127.0.0.1:5432/finaflow`)
   - `BACKEND_URL` (default: `https://finaflow-backend-staging-642830139828.us-central1.run.app`)
2. Executa:
   - `python3 -m scripts.seed_from_client_sheet --file data/fluxo_caixa_2025.xlsx`
   - `python3 -m scripts.validate_dashboard_against_client_sheet --file data/fluxo_caixa_2025.xlsx --year 2025 --backend-url \"$BACKEND_URL\"` (com log em `logs/validate_dashboard_YYYYMMDD_HHMMSS.log`)

### Critério de aprovação (v2.0)

- ✅ Exit code `0`
- ✅ Mensagem:
  - `✅ Seed + validação concluídos sem mismatches.`
  - `✅ Versão 2.0 consistente entre planilha, banco e API.`
- ✅ Nenhum mismatch `BANCO→API` no resumo da validação

### Em caso de erro

- Exit code `1`: falha no seed (`scripts.seed_from_client_sheet`)
- Exit code `2`: falha na validação (`scripts.validate_dashboard_against_client_sheet`)

Ver detalhes no log indicado pelo script (em `backend/logs/`).

---

## 🚀 EXECUÇÃO VIA CLOUD RUN JOB (STAGING) – OPCIONAL / FUTURO

### Pré-requisitos

- ✅ Jobs já criados no projeto GCP (executar `setup_cloud_run_jobs.sh` uma vez)
- ✅ Arquivo Excel em `backend/data/fluxo_caixa_2025.xlsx` (deve estar na imagem)
- ✅ Acesso ao projeto GCP `trivihair`

### Criar/Atualizar Jobs (Primeira vez ou após mudanças)

```bash
cd ~/finaflow/backend
./scripts/setup_cloud_run_jobs.sh
```

Este script:
- ✅ Descobre configuração do serviço `finaflow-backend-staging`
- ✅ Cria/atualiza job `finaflow-seed-staging-job`
- ✅ Cria/atualiza job `finaflow-validate-dashboard-staging-job`
- ✅ Reutiliza mesma imagem, service account e env vars do serviço

### Executar Validação

```bash
gcloud run jobs execute finaflow-validate-dashboard-staging-job \
  --region=us-central1 \
  --wait
```

**O que acontece:**
- ✅ Job conecta ao Cloud SQL nativamente (sem proxy)
- ✅ Executa validação completa
- ✅ Compara Planilha → Banco → API
- ✅ Retorna exit code 0 se sem mismatches, ≠0 se houver problemas

### Executar Seed (se necessário)

```bash
gcloud run jobs execute finaflow-seed-staging-job \
  --region=us-central1 \
  --wait
```

### Ver Logs

**Via Console:**
1. Acesse: https://console.cloud.google.com/run/jobs
2. Selecione o job
3. Clique em "Execuções" → Selecione execução → "Logs"

**Via CLI:**
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

### Interpretar Resultado

**Exit Code 0 (SUCCESS):**
```
✅ FILTRO→BANCO: 0 ocorrências
✅ BANCO→API: 0 ocorrências
✅ Nenhuma inconsistência de totais
```

**Exit Code ≠0 (FAILURE):**
- Verificar logs para detalhes dos mismatches
- Investigar usando modo drill down (se necessário)

### Vantagens do Cloud Run Job

- ✅ **Sem Cloud SQL Proxy**: Acesso nativo ao banco
- ✅ **Automatizado**: Pode ser integrado em CI/CD
- ✅ **Isolado**: Não depende de Cloud Shell
- ✅ **Reprodutível**: Mesma imagem e configuração do serviço
- ✅ **Logs centralizados**: Fácil de debugar

---

## ⚡ EXECUÇÃO MANUAL (Cloud SQL Proxy)

### Opção 1: Script Helper Automático

```bash
cd ~/finaflow/backend
./scripts/run_validation_with_proxy.sh --year 2025
```

**O script faz tudo automaticamente:**
- ✅ Verifica/inicia Cloud SQL Proxy
- ✅ Configura DATABASE_URL
- ✅ Testa conexão com banco
- ✅ Executa validação
- ✅ Para proxy ao final (se iniciado pelo script)

### Opção 2: Execução Manual

```bash
# 1. Iniciar Cloud SQL Proxy
cd ~/finaflow/backend
curl -o cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64
chmod +x cloud_sql_proxy
./cloud_sql_proxy -instances=trivihair:us-central1:finaflow-db-staging=tcp:5432 &

# 2. Configurar variáveis
export DATABASE_URL="postgresql://finaflow_user:Finaflow123!@127.0.0.1:5432/finaflow"
export BACKEND_URL="https://finaflow-backend-staging-642830139828.us-central1.run.app"

# 3. Executar validação
python3 -m scripts.validate_dashboard_against_client_sheet \
    --file data/fluxo_caixa_2025.xlsx \
    --year 2025 \
    --backend-url "$BACKEND_URL"
```

---

## 📋 PRÉ-REQUISITOS

1. **Cloud SQL Proxy** (para acesso ao banco)
2. **Python 3.8+** com dependências:
   - `pandas`
   - `openpyxl`
   - `requests`
   - `sqlalchemy`
   - `psycopg2-binary`
3. **Arquivo Excel**: `backend/data/fluxo_caixa_2025.xlsx`
4. **Acesso ao projeto GCP**: `trivihair`

---

## 🔍 VALIDAÇÃO NORMAL (Ano Inteiro)

Valida todos os meses do ano especificado:

```bash
python3 -m scripts.validate_dashboard_against_client_sheet \
    --file data/fluxo_caixa_2025.xlsx \
    --year 2025 \
    --backend-url "$BACKEND_URL"
```

**Critérios de Aceite:**
- ✅ Script termina sem exceções
- ✅ `BANCO→API: 0 ocorrências`
- ✅ `FILTRO→BANCO: 0 ocorrências`
- ✅ Todos os meses batem 100% entre API e banco

---

## 🔬 VALIDAÇÃO COM DRILL DOWN

Gera CSVs detalhados para análise conta a conta:

```bash
python3 -m scripts.validate_dashboard_against_client_sheet \
    --file data/fluxo_caixa_2025.xlsx \
    --year 2025 \
    --backend-url "$BACKEND_URL" \
    --debug-month 1 \
    --debug-type RECEITA
```

**Parâmetros:**
- `--debug-month` (1-12): Mês para análise detalhada
- `--debug-type` (RECEITA, DESPESA, CUSTO): Tipo de transação

**CSVs gerados em `backend/logs/`:**
- `debug_YYYY_MM_TIPO_planilha.csv`
- `debug_YYYY_MM_TIPO_banco.csv`
- `debug_YYYY_MM_TIPO_comparativo.csv`

---

## 🚨 TROUBLESHOOTING

### Erro: "Connection refused"

**Causa**: Cloud SQL Proxy não está rodando ou porta 5432 não está acessível.

**Solução**:
```bash
# Verificar se proxy está rodando
ps aux | grep cloud_sql_proxy

# Se não estiver, iniciar
./cloud_sql_proxy -instances=trivihair:us-central1:finaflow-db-staging=tcp:5432 &

# Aguardar 5 segundos
sleep 5

# Verificar porta
nc -z 127.0.0.1 5432
```

### Erro: "DATABASE_URL não configurado"

**Solução**:
```bash
export DATABASE_URL="postgresql://finaflow_user:Finaflow123!@127.0.0.1:5432/finaflow"
echo $DATABASE_URL
```

### Erro: "Tenant 'FinaFlow Staging' não encontrado"

**Causa**: Seed não foi executado ou banco está vazio.

**Solução**: Executar seed primeiro:
```bash
python3 -m scripts.seed_from_client_sheet --file data/fluxo_caixa_2025.xlsx
```

### Erro: "pandas não instalado"

**Solução**:
```bash
pip3 install pandas openpyxl requests
```

---

## 📊 INTERPRETAÇÃO DOS RESULTADOS

### Status: ✅ OK

```
✅ Todas as regras do seed estão sendo respeitadas no dashboard.
✅ As diferenças entre planilha bruta e sistema são exclusivamente de linhas filtradas/ignoradas pelo seed.
```

**Significado**: Tudo está consistente!

### Status: ❌ MISMATCH

O script exibe:
- Tabela completa de comparação
- Estatísticas de mismatches:
  - **BRUTA→FILTRO**: Diferenças explicadas por regras do seed (esperado)
  - **FILTRO→BANCO**: Possível bug no seed (dados não foram persistidos)
  - **BANCO→API**: Possível bug no dashboard/endpoint (cálculo incorreto)

**Ação**: Investigar usando modo drill down.

---

## 📝 ESTRUTURA DO RELATÓRIO

### Tabela de Comparação

```
ANO-MÊS | TIPO    | PLAN_BRUTA | PLAN_FILTRO | BANCO | API   | 
Δ BRUT→FILT | Δ% | Δ FILT→BAN | Δ% | Δ BAN→API | Δ% | ⚠️
```

- **PLAN_BRUTA**: Totais da planilha sem filtros
- **PLAN_FILTRO**: Totais da planilha com filtros do seed
- **BANCO**: Totais do banco de dados
- **API**: Totais do endpoint de dashboard
- **⚠️**: Indica mismatch acima da tolerância (R$ 0,05 ou 0,1%)

### Resumo Final

```
📊 ESTATÍSTICAS DE MISMATCHES:
   BRUTA→FILTRO: X ocorrências (regras do seed)
   FILTRO→BANCO: Y ocorrências (possível bug no seed)
   BANCO→API: Z ocorrências (possível bug no dashboard)
```

---

## ✅ VALIDAÇÃO PÓS-EXECUÇÃO

Após validação bem-sucedida, verificar:

1. **Endpoint de debug**:
   ```bash
   curl -H "Authorization: Bearer $TOKEN" \
     "$BACKEND_URL/api/v1/financial/annual-summary/debug?year=2025"
   ```

2. **Endpoint principal**:
   ```bash
   curl -H "Authorization: Bearer $TOKEN" \
     "$BACKEND_URL/api/v1/financial/annual-summary?year=2025"
   ```

3. **Frontend**: Verificar se dashboard exibe valores corretos

---

## 📚 REFERÊNCIAS

- **Script**: `backend/scripts/validate_dashboard_against_client_sheet.py`
- **Documentação completa**: `docs/VALIDACAO_DASHBOARD.md`
- **Script helper**: `backend/scripts/run_validation_with_proxy.sh`
- **Planilha**: `backend/data/fluxo_caixa_2025.xlsx`

---

---

## 📚 REFERÊNCIAS ADICIONAIS

### Scripts Criados

- **`backend/scripts/run_validation_job.py`**: Wrapper para Cloud Run Job de validação
- **`backend/scripts/run_seed_job.py`**: Wrapper para Cloud Run Job de seed
- **`backend/scripts/setup_cloud_run_jobs.sh`**: Script para criar/atualizar jobs

### Jobs Cloud Run

- **`finaflow-validate-dashboard-staging-job`**: Job de validação
- **`finaflow-seed-staging-job`**: Job de seed

### Configuração

Os jobs usam:
- ✅ Mesma imagem do serviço `finaflow-backend-staging`
- ✅ Mesma service account
- ✅ Mesmas env vars de banco (acesso nativo ao Cloud SQL)
- ✅ Memória: 1Gi, CPU: 1

---

**Última atualização**: 2025-12-11  
**Status**: ✅ Pronto para uso (Cloud Run Jobs + Cloud SQL Proxy)

