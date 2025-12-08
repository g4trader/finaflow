# Validação de Dados - Planilha x STAGING

**Objetivo**: Validar se os dados do seed no banco STAGING estão compatíveis com a planilha original do cliente.

---

## Objetivo da Validação

O script `validate_seed_against_client_sheet.py` compara os dados populados no banco STAGING pelo seed com a planilha Excel original (`backend/data/fluxo_caixa_2025.xlsx`), garantindo que:

1. **Plano de Contas**: Todos os grupos, subgrupos e contas da planilha foram importados corretamente
2. **Lançamentos Diários**: Total de registros e soma de valores batem com a planilha
3. **Lançamentos Previstos**: Total de registros e soma de valores batem com a planilha

---

## Como Executar no Cloud Shell

### Pré-requisitos

1. Cloud SQL Proxy rodando (se ainda não estiver):
   ```bash
   gcloud config set project trivihair
   curl -o cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64
   chmod +x cloud_sql_proxy
   ./cloud_sql_proxy -instances=trivihair:us-central1:finaflow-db-staging=tcp:5432 &
   ```

2. Aguardar alguns segundos para o proxy iniciar

### Executar Validação

```bash
# Configurar projeto
gcloud config set project trivihair

# Clonar/atualizar repositório
cd ~
rm -rf finaflow
git clone https://github.com/g4trader/finaflow.git
cd finaflow
git checkout staging
cd backend

# Instalar dependências
pip3 install -r requirements.txt
pip3 install pandas openpyxl

# Configurar DATABASE_URL
export DATABASE_URL="postgresql://finaflow_user:Finaflow123!@127.0.0.1:5432/finaflow"

# Executar validação
python3 -m scripts.validate_seed_against_client_sheet --file data/fluxo_caixa_2025.xlsx
```

---

## Como Interpretar a Saída

### Status: ✅ OK

Indica que os dados da planilha e do banco estão compatíveis (dentro da tolerância de R$ 0,01 para valores).

**Exemplo**:
```
[Plano de Contas] Grupos: planilha=7 | banco=7 -> ✅ OK
[Lançamentos Diários] Total: planilha=2950 | banco=2950 -> ✅ OK
[Lançamentos Diários] Soma total: planilha=R$ 135.194.077,00 | banco=R$ 135.194.077,00 -> ✅ OK
```

### Status: ❌ MISMATCH

Indica que há diferenças entre a planilha e o banco.

**Possíveis causas**:
- Linhas da planilha foram ignoradas durante o seed (valores inválidos, datas inválidas, etc.)
- Erro no processamento de valores (conversão de moeda)
- Erro no processamento de datas
- Dados duplicados ou faltantes no banco

**Exemplo**:
```
[Plano de Contas] Grupos: planilha=7 | banco=6 -> ❌ MISMATCH
[Lançamentos Diários] Total: planilha=2950 | banco=2945 -> ❌ MISMATCH
  ⚠️  Diferença: R$ 1.234,56
```

### Tolerância

Para valores monetários, é usada uma tolerância de **R$ 0,01** (um centavo). Diferenças menores que isso são consideradas OK, pois podem ser causadas por arredondamentos.

---

## Estrutura do Relatório

O script gera um relatório completo com:

1. **Validação do Plano de Contas**:
   - Contagem de grupos (planilha vs banco)
   - Contagem de subgrupos (planilha vs banco)
   - Contagem de contas (planilha vs banco)

2. **Validação de Lançamentos Diários**:
   - Total de registros (planilha vs banco)
   - Soma total de valores (planilha vs banco)
   - Detalhamento por mês (quantidade e soma)

3. **Validação de Lançamentos Previstos**:
   - Total de registros (planilha vs banco)
   - Soma total de valores (planilha vs banco)
   - Detalhamento por mês (quantidade e soma)

4. **Resumo Final**:
   - Status geral de cada validação (OK / MISMATCH)
   - Detalhes consolidados

---

## Logs

O script gera um log completo em:
```
backend/logs/validate_seed_<timestamp>.log
```

Onde `<timestamp>` é no formato `YYYYMMDD_HHMMSS`.

---

## Código de Saída

- **0**: Todas as validações passaram (OK)
- **1**: Pelo menos uma validação falhou (MISMATCH)

Útil para automação e CI/CD.

---

## Primeiro Resultado Real da Validação

_Resultado será preenchido após primeira execução no Cloud Shell_

---

**Última atualização**: 2025-12-08  
**Script**: `backend/scripts/validate_seed_against_client_sheet.py`  
**Planilha**: `backend/data/fluxo_caixa_2025.xlsx`

