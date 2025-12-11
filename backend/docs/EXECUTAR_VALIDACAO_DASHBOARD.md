# 🚀 Executar Validação do Dashboard - Cloud SQL Proxy

**Método**: Cloud SQL Proxy + Script Python  
**Ambiente**: Cloud Shell ou Local (com proxy)  
**Data**: 2025-12-11

---

## ⚡ EXECUÇÃO RÁPIDA (RECOMENDADO)

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

**Última atualização**: 2025-12-11  
**Status**: ✅ Pronto para uso

