# Validação Profunda - Dashboard vs Planilha vs Banco

**Objetivo**: Validar se os totais mensais (receita, despesa, custo, saldo) calculados pelo dashboard estão consistentes com a planilha do cliente e o banco de dados.

---

## O que o script faz

O script `validate_dashboard_against_client_sheet.py` compara os totais mensais entre **quatro fontes**:

1. **Planilha BRUTA** (sem filtros):
   - Lê as abas "Lançamento Diário" e "Lançamentos Previstos"
   - Normaliza sem aplicar filtros do seed
   - Agrega por mês/tipo

2. **Planilha FILTRADA** (com regras do seed):
   - Lê as mesmas abas
   - Aplica **exatamente as mesmas regras de filtro** do seed script
   - Normaliza e agrega por mês/tipo

3. **Banco de dados STAGING**:
   - Consulta `LancamentoDiario` via SQLAlchemy
   - Filtra por `tenant_id` e `business_unit_id` (FinaFlow Staging / Matriz)
   - Agrega por mês/tipo usando a mesma lógica do endpoint

4. **API de Dashboard** (`/api/v1/financial/annual-summary`):
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

# 5. Executar validação (modo normal - ano inteiro)
python3 -m scripts.validate_dashboard_against_client_sheet \
    --file data/fluxo_caixa_2025.xlsx \
    --year 2025 \
    --backend-url "$BACKEND_URL"
```

### Modo Normal (Ano Inteiro)

Valida todos os meses do ano especificado:

```bash
python3 -m scripts.validate_dashboard_against_client_sheet \
    --file data/fluxo_caixa_2025.xlsx \
    --year 2025 \
    --backend-url "$BACKEND_URL"
```

### Modo Drill Down (Mês e Tipo Específico)

Gera CSVs detalhados para análise conta a conta de um mês/tipo específico:

```bash
python3 -m scripts.validate_dashboard_against_client_sheet \
    --file data/fluxo_caixa_2025.xlsx \
    --year 2025 \
    --backend-url "$BACKEND_URL" \
    --debug-month 1 \
    --debug-type RECEITA
```

**Parâmetros de drill down**:
- `--debug-month` (1-12): Mês para análise detalhada
- `--debug-type` (RECEITA, DESPESA, CUSTO): Tipo de transação

**Nota**: `--debug-month` e `--debug-type` devem ser fornecidos juntos.

### Parâmetros Gerais

- `--file` (obrigatório): Caminho do arquivo Excel
- `--year` (opcional, default=2025): Ano para validação
- `--log-file` (opcional): Caminho do arquivo de log (default: `backend/logs/validate_dashboard_YYYYMMDD_HHMMSS.log`)
- `--backend-url` (opcional): URL do backend (default: staging)

---

## Interpretação dos resultados

### Status: ✅ OK

Todos os totais estão consistentes entre as quatro fontes (dentro das tolerâncias):
- Diferença absoluta ≤ R$ 0,05
- Diferença percentual ≤ 0,1%

**Mensagem esperada**:
> ✅ Todas as regras do seed estão sendo respeitadas no dashboard.  
> ✅ As diferenças entre planilha bruta e sistema são exclusivamente de linhas filtradas/ignoradas pelo seed.

### Status: ❌ MISMATCH

Foram encontradas inconsistências. O script exibe:
- Tabela completa de comparação
- Estatísticas de mismatches por tipo (BRUTA→FILTRO, FILTRO→BANCO, BANCO→API)
- Lista de inconsistências (mês, tipo, valores, deltas)

**Interpretação das estatísticas**:
- **BRUTA→FILTRO**: Diferenças explicadas por regras do seed (esperado)
- **FILTRO→BANCO**: Possível bug no seed (dados não foram persistidos corretamente)
- **BANCO→API**: Possível bug no dashboard/endpoint (cálculo incorreto na API)

### Tolerâncias

- **Tolerância absoluta**: R$ 0,05 (diferenças menores são ignoradas)
- **Tolerância percentual**: 0,1% (diferenças percentuais menores são ignoradas)

---

## Estrutura do relatório

### Modo Normal

O script gera:

1. **Tabela de comparação expandida**:
   ```
   ANO-MÊS | TIPO    | PLAN_BRUTA | PLAN_FILTRO | BANCO | API   | 
   Δ BRUT→FILT | Δ% | Δ FILT→BAN | Δ% | Δ BAN→API | Δ% | ⚠️
   2025-01 | RECEITA | ...        | ...         | ...   | ...   | ...
   ```
   - **PLAN_BRUTA**: Totais da planilha sem filtros
   - **PLAN_FILTRO**: Totais da planilha com filtros do seed
   - **BANCO**: Totais do banco de dados
   - **API**: Totais do endpoint de dashboard
   - **⚠️**: Indica mismatch acima da tolerância

2. **Resumo final com estatísticas**:
   - Quantos meses têm mismatch **BRUTA→FILTRO** (regras do seed explicam diferença)
   - Quantos meses têm mismatch **FILTRO→BANCO** (possível bug no seed)
   - Quantos meses têm mismatch **BANCO→API** (possível bug no dashboard)
   - Lista de inconsistências (se houver)

3. **Log detalhado**:
   - Parâmetros usados
   - Estatísticas por fonte
   - Tabela completa de comparação

### Modo Drill Down

Quando `--debug-month` e `--debug-type` são fornecidos, o script gera **3 CSVs** em `backend/logs/`:

1. **`debug_YYYY_MM_TIPO_planilha.csv`**:
   - Todas as entradas filtradas da planilha para o mês/tipo
   - Colunas: `ano,mes,grupo,subgrupo,conta,tipo,origem,valor`

2. **`debug_YYYY_MM_TIPO_banco.csv`**:
   - Todos os lançamentos do banco para o mês/tipo
   - Colunas: `ano,mes,grupo,subgrupo,conta,tipo,valor`

3. **`debug_YYYY_MM_TIPO_comparativo.csv`**:
   - Comparação conta a conta entre planilha e banco
   - Colunas: `grupo,subgrupo,conta,valor_planilha,valor_banco,delta_abs,delta_pct,status`
   - **Ordenado por `delta_abs` desc** (maiores diferenças primeiro)
   - **Status**:
     - `AMBOS`: Presente na planilha e no banco
     - `SO_PLANILHA`: Presente apenas na planilha
     - `SO_BANCO`: Presente apenas no banco

### Como interpretar os CSVs de debug

1. **Abra o CSV comparativo** (`debug_YYYY_MM_TIPO_comparativo.csv`)

2. **Identifique as maiores diferenças**:
   - As primeiras linhas mostram as contas com maiores deltas
   - Verifique se são diferenças esperadas (regras do seed) ou bugs

3. **Compare com os CSVs individuais**:
   - Use `debug_YYYY_MM_TIPO_planilha.csv` para ver o que está na planilha
   - Use `debug_YYYY_MM_TIPO_banco.csv` para ver o que está no banco

4. **Analise o status**:
   - `SO_PLANILHA`: Linha foi filtrada pelo seed (não deveria estar no banco)
   - `SO_BANCO`: Linha está no banco mas não na planilha filtrada (possível bug)
   - `AMBOS` com delta grande: Valores diferentes (possível bug de cálculo)

---

## Código de saída

- **0**: Todas as validações passaram (OK)
- **1**: Foram encontradas inconsistências (MISMATCH)

Útil para automação e CI/CD.

---

## Notas importantes

1. **Reutilização de lógica**: O script reutiliza as funções do `seed_utils.py` (`parse_currency`, `parse_date`, `determine_transaction_type`) para garantir consistência total entre seed e validação.

2. **Apenas leitura**: O script **não altera dados**, apenas lê e compara.

3. **Filtros do seed**: A planilha FILTRADA é normalizada usando **exatamente as mesmas regras** do seed, garantindo que apenas linhas válidas sejam consideradas.

4. **Planilha BRUTA vs FILTRADA**: A comparação entre BRUTA e FILTRADA mostra quantas linhas foram ignoradas pelo seed (esperado). A comparação entre FILTRADA e BANCO mostra se o seed persistiu corretamente.

5. **Endpoint usado**: O script consome `/api/v1/financial/annual-summary`, que retorna apenas `LancamentoDiario` (não inclui previstos). Isso está alinhado com o comportamento atual do dashboard.

6. **Modo Drill Down**: Use quando precisar investigar diferenças específicas. Os CSVs permitem análise conta a conta para identificar exatamente onde estão os problemas.

---

## Exemplo de uso completo

### 1. Validação geral do ano

```bash
python3 -m scripts.validate_dashboard_against_client_sheet \
    --file data/fluxo_caixa_2025.xlsx \
    --year 2025 \
    --backend-url "$BACKEND_URL"
```

### 2. Identificar mês/tipo com problema

Analise a tabela de comparação e identifique, por exemplo:
- `2025-01 | RECEITA` com mismatch `FILTRO→BANCO`

### 3. Drill down detalhado

```bash
python3 -m scripts.validate_dashboard_against_client_sheet \
    --file data/fluxo_caixa_2025.xlsx \
    --year 2025 \
    --backend-url "$BACKEND_URL" \
    --debug-month 1 \
    --debug-type RECEITA
```

### 4. Analisar CSVs gerados

Abra `backend/logs/debug_2025_01_RECEITA_comparativo.csv` e identifique:
- Contas com maiores deltas
- Contas presentes apenas na planilha (`SO_PLANILHA`)
- Contas presentes apenas no banco (`SO_BANCO`)

---

**Última atualização**: 2025-12-08  
**Script**: `backend/scripts/validate_dashboard_against_client_sheet.py`  
**Planilha**: `backend/data/fluxo_caixa_2025.xlsx`  
**Módulo compartilhado**: `backend/scripts/seed_utils.py`

