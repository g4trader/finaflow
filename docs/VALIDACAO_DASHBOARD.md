# Validação Profunda - Dashboard vs Planilha vs Banco

**Objetivo**: Validar se os totais mensais (receita, despesa, custo, saldo) calculados pelo dashboard estão consistentes com a planilha do cliente e o banco de dados.

---

## O que o script faz

O script `validate_dashboard_against_client_sheet.py` compara os totais mensais entre três fontes:

1. **Planilha do cliente** (`backend/data/fluxo_caixa_2025.xlsx`):
   - Lê as abas "Lançamento Diário" e "Lançamentos Previstos"
   - Aplica as **mesmas regras de filtro** do seed script
   - Normaliza e agrega por mês/tipo

2. **Banco de dados STAGING**:
   - Consulta `LancamentoDiario` via SQLAlchemy
   - Filtra por `tenant_id` e `business_unit_id` (FinaFlow Staging / Matriz)
   - Agrega por mês/tipo usando a mesma lógica do endpoint

3. **API de Dashboard** (`/api/v1/financial/annual-summary`):
   - Faz login com credenciais QA
   - Consome o endpoint de resumo anual
   - Extrai os totais mensais retornados

---

## Como executar

### Pré-requisitos

1. Cloud SQL Proxy rodando (se executando localmente)
2. Variável `DATABASE_URL` configurada
3. Variável `BACKEND_URL` configurada (opcional, default: staging)

### Execução no Cloud Shell

```bash
# 1. Clonar repositório (se necessário)
cd ~
git clone https://github.com/g4trader/finaflow.git
cd finaflow
git checkout staging

# 2. Iniciar Cloud SQL Proxy (se necessário)
if ! pgrep -x cloud_sql_proxy > /dev/null; then
    curl -o cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64
    chmod +x cloud_sql_proxy
    ./cloud_sql_proxy -instances=trivihair:us-central1:finaflow-db-staging=tcp:5432 &
    sleep 5
fi

# 3. Instalar dependências
cd ~/finaflow/backend
pip3 install -r requirements.txt

# 4. Configurar DATABASE_URL
export DATABASE_URL="postgresql://finaflow_user:Finaflow123!@127.0.0.1:5432/finaflow"

# 5. Executar validação
python3 -m scripts.validate_dashboard_against_client_sheet \
    --file data/fluxo_caixa_2025.xlsx \
    --year 2025
```

### Parâmetros

- `--file` (obrigatório): Caminho do arquivo Excel
- `--year` (opcional, default=2025): Ano para validação
- `--log-file` (opcional): Caminho do arquivo de log (default: `backend/logs/validate_dashboard_YYYYMMDD_HHMMSS.log`)
- `--backend-url` (opcional): URL do backend (default: staging)

---

## Interpretação dos resultados

### Status: ✅ OK

Todos os totais estão consistentes entre as três fontes (dentro das tolerâncias):
- Diferença absoluta ≤ R$ 0,05
- Diferença percentual ≤ 0,1%

### Status: ❌ MISMATCH

Foram encontradas inconsistências. O script exibe:
- Tabela completa de comparação
- Lista de inconsistências (mês, tipo, valores, deltas)

### Tolerâncias

- **Tolerância absoluta**: R$ 0,05 (diferenças menores são ignoradas)
- **Tolerância percentual**: 0,1% (diferenças percentuais menores são ignoradas)

---

## Estrutura do relatório

O script gera:

1. **Tabela de comparação**:
   ```
   ANO-MÊS | TIPO    | PLANILHA | BANCO | API   | Δ PLAN→BAN | Δ% | Δ BAN→API | Δ%
   2025-01 | RECEITA | ...      | ...   | ...   | ...        | .. | ...       | ..
   ```

2. **Resumo final**:
   - Status geral (OK ou MISMATCH)
   - Lista de inconsistências (se houver)

3. **Log detalhado**:
   - Parâmetros usados
   - Estatísticas por fonte
   - Tabela completa de comparação

---

## Código de saída

- **0**: Todas as validações passaram (OK)
- **1**: Foram encontradas inconsistências (MISMATCH)

Útil para automação e CI/CD.

---

## Notas importantes

1. **Reutilização de lógica**: O script reutiliza as funções do seed (`parse_currency`, `parse_date`, `determine_transaction_type`) para garantir consistência.

2. **Apenas leitura**: O script **não altera dados**, apenas lê e compara.

3. **Filtros do seed**: A planilha é normalizada usando **exatamente as mesmas regras** do seed, garantindo que apenas linhas válidas sejam consideradas.

4. **Endpoint usado**: O script consome `/api/v1/financial/annual-summary`, que retorna apenas `LancamentoDiario` (não inclui previstos). Isso está alinhado com o comportamento atual do dashboard.

---

**Última atualização**: 2025-12-08  
**Script**: `backend/scripts/validate_dashboard_against_client_sheet.py`  
**Planilha**: `backend/data/fluxo_caixa_2025.xlsx`

