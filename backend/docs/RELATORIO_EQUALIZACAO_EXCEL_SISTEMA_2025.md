# 📊 Relatório de Equalização Excel vs Sistema - 2025

**Data**: 2025-12-26  
**Ano Alvo**: 2025  
**Status**: ⚠️ DIVERGÊNCIAS IDENTIFICADAS

---

## 📋 Resumo Executivo

Foram identificadas **divergências significativas** entre o Excel (fonte da verdade) e o sistema:

- **Receita**: Diferença de R$ 6.101,80 (0,55%)
- **Despesa**: Diferença de R$ 2.338,35 (0,33%)
- **Custo**: Diferença de R$ 49.122,03 (12,4%) ⚠️ **CRÍTICO**
- **Saldo**: Diferença de R$ 45.358,58 ⚠️ **CRÍTICO**

### Principais Causas Identificadas

1. **Categorização de CUSTO vs DESPESA**: Muitos itens classificados como CUSTO no Excel estão sendo classificados como DESPESA no sistema (ou vice-versa)
2. **Linhas não seedadas**: Algumas linhas do Excel podem não ter sido processadas pelo seed
3. **Filtros de status**: A API pode estar filtrando por `is_active` ou `status` de forma diferente do baseline

---

## 🔍 Análise Detalhada

### Totais Anuais

| Campo | Excel | API | Diferença | % |
|-------|-------|-----|-----------|---|
| Receita | R$ 1.104.592,63 | R$ 1.098.490,83 | R$ 6.101,80 | 0,55% |
| Despesa | R$ 714.945,00 | R$ 712.606,65 | R$ 2.338,35 | 0,33% |
| Custo | R$ 396.229,67 | R$ 347.107,64 | R$ 49.122,03 | 12,4% ⚠️ |
| Saldo | R$ -6.582,04 | R$ 38.776,54 | R$ 45.358,58 | - |

### Mismatches Mensais (Principais)

**Janeiro:**
- Receita: -R$ 827,80
- Custo: -R$ 5.611,11 ⚠️
- Saldo: +R$ 4.783,31

**Fevereiro:**
- Custo: -R$ 4.828,71 ⚠️
- Saldo: +R$ 4.828,71

**Março:**
- Receita: -R$ 1.000,00
- Custo: -R$ 3.121,69 ⚠️

**Novembro:**
- Custo: -R$ 11.233,78 ⚠️ **MAIOR DIVERGÊNCIA**

---

## 📁 Artefatos Gerados

### Baseline (Fonte da Verdade)
- `backend/artifacts/baseline_excel_2025.json` - Totais e metadados
- `backend/artifacts/baseline_order_2025.csv` - Ordem do plano de contas

### Relatório de Auditoria
- `backend/artifacts/audit_report_2025.json` - Comparação completa Excel vs API

### Hash do Excel
- MD5: `f5dcd9156da4dc8edba7f3e538f33f47`

---

## 🔧 Scripts Criados

### 1. `generate_baseline_excel.py`
Gera o baseline (mapa de verdade) da planilha Excel.

**Uso:**
```bash
python -m scripts.generate_baseline_excel --file data/fluxo_caixa_2025.xlsx --year 2025
```

**Saída:**
- `backend/artifacts/baseline_excel_2025.json`
- `backend/artifacts/baseline_order_2025.csv`

### 2. `audit_excel_vs_api.py`
Compara baseline Excel com API e identifica divergências.

**Uso:**
```bash
python -m scripts.audit_excel_vs_api --year 2025 --backend-url <url>
```

**Saída:**
- `backend/artifacts/audit_report_2025.json`
- Exit code: 0 = OK, 2 = mismatch, 1 = erro

---

## 🎯 Próximos Passos Recomendados

### 1. Investigar Categorização de CUSTO
- Verificar função `determine_transaction_type()` em `seed_utils.py`
- Comparar classificação Excel vs banco para itens com maior divergência
- Ajustar regras de categorização se necessário

### 2. Validar Linhas Não Seedadas
- Executar seed com logs detalhados
- Identificar quais linhas foram ignoradas e por quê
- Verificar se há filtros que excluem dados válidos

### 3. Revisar Filtros da API
- Verificar se `FinancialAggregationService` está usando os mesmos filtros do seed
- Confirmar que `is_active=True` e `status` estão corretos
- Validar filtros de `business_unit_id` e `tenant_id`

### 4. Re-executar Seed
- Após correções, executar seed novamente com `--reset-data`
- Re-executar auditoria
- Validar que divergências foram resolvidas

---

## 📊 Evidências

### Baseline Excel (Totais Anuais)
```json
{
  "receita": 1104592.62915,
  "despesa": 714945.0,
  "custo": 396229.67,
  "saldo": -6582.04085
}
```

### API Atual (Totais Anuais)
```json
{
  "revenue": 1098490.83,
  "expense": 712606.65,
  "cost": 347107.64,
  "balance": 38776.54
}
```

### Principais Mismatches Mensais
Ver `backend/artifacts/audit_report_2025.json` seção `mismatches.monthly`

---

## ✅ O Que Foi Implementado

- ✅ Script de baseline do Excel
- ✅ Script de auditoria Excel vs API
- ✅ Relatórios JSON estruturados
- ✅ CSV de ordem do plano de contas
- ✅ Validação de totais anuais e mensais
- ✅ Tolerância de R$ 0,01 configurável

---

## ⚠️ Problemas Conhecidos

1. **Monthly-Daily-Summary retornando zeros**: O endpoint `/api/v1/financial/monthly-daily-summary` está retornando totais zerados. Investigar se há dados diários seedados ou se o endpoint precisa de ajuste.

2. **Custo subestimado**: A diferença de R$ 49k em custos indica que muitos itens estão sendo classificados incorretamente ou não estão sendo seedados.

3. **Ordem do plano de contas**: Ainda não foi validada na UI. Implementar validação E2E (FASE 4).

---

## 🔄 Como Re-executar

```bash
# 1. Gerar baseline
cd backend
python -m scripts.generate_baseline_excel --year 2025

# 2. Executar auditoria
python -m scripts.audit_excel_vs_api --year 2025

# 3. Verificar relatório
cat artifacts/audit_report_2025.json | jq '.mismatches'
```

---

**Status Final**: ⚠️ DIVERGÊNCIAS IDENTIFICADAS - Requer correções no seed e/ou na API

---

## 📦 Entregas Realizadas

### ✅ FASE 0 - Preparar ambiente
- Ambiente preparado e atualizado
- Arquivo Excel confirmado: `backend/data/fluxo_caixa_2025.xlsx` (1.7MB)

### ✅ FASE 1 - Baseline do Excel
- Script `generate_baseline_excel.py` criado
- Baseline JSON gerado com totais anuais e mensais
- CSV de ordem do plano de contas gerado
- Hash MD5 do Excel calculado para rastreabilidade

### ✅ FASE 3 - Auditoria Excel vs API
- Script `audit_excel_vs_api.py` criado
- Comparação de totais anuais e mensais implementada
- Validação de monthly-daily-summary implementada
- Relatório JSON estruturado gerado
- Endpoints operacionais validados

### ✅ FASE 6 - Automação
- Makefile criado com comandos:
  - `make baseline` - Gera baseline
  - `make audit` - Executa auditoria
  - `make qa-equalizacao` - Processo completo

### ⏳ FASE 2 - Seed determinístico (Pendente)
- Seed atual funciona, mas precisa de revisão para garantir determinismo
- Adicionar logs detalhados de linhas ignoradas
- Adicionar hash do input Excel no relatório de seed

### ⏳ FASE 4 - Equalização UI (Pendente)
- Teste E2E de ordem do fluxo de caixa não implementado
- Validação de valores na UI não implementada
- Implementar campo `display_order` se necessário

### ⏳ FASE 5 - Dashboard Operacional (Pendente)
- Validação de coerência básica não implementada
- Teste E2E do dashboard operacional não implementado

---

## 🚀 Como Usar

### Executar Equalização Completa
```bash
make qa-equalizacao
```

### Executar Passo a Passo
```bash
# 1. Gerar baseline
make baseline

# 2. Executar auditoria
make audit

# 3. Verificar relatórios
cat backend/artifacts/audit_report_2025.json | jq '.mismatches'
```

### Variáveis de Ambiente
```bash
export YEAR=2025
export BACKEND_URL=https://finaflow-backend-staging-642830139828.us-central1.run.app
export QA_EMAIL=qa@finaflow.test
export QA_PASSWORD=QaFinaflow123!
```

---

## 📝 Commits Realizados

- `4ccea08`: `feat(baseline): adicionar scripts de baseline e auditoria Excel vs API`
- `c0807fa`: `feat(qa): adicionar Makefile para automação de equalização`

---

## 🎯 Próximas Ações Recomendadas

1. **Investigar divergência de CUSTO** (prioridade alta)
   - Revisar função `determine_transaction_type()`
   - Comparar classificação Excel vs banco
   - Ajustar regras se necessário

2. **Re-executar seed com logs detalhados**
   - Identificar linhas ignoradas
   - Validar que todas as linhas válidas foram processadas

3. **Implementar FASE 4 e 5**
   - Testes E2E de UI
   - Validação de ordem do plano de contas
   - Validação de coerência do dashboard operacional

4. **Re-executar auditoria após correções**
   - Validar que divergências foram resolvidas
   - Confirmar que todos os totais batem

