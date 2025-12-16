# Correção do Dashboard 2.0 - Resumo da Implementação

## Objetivo

Corrigir o endpoint `/api/v1/financial/annual-summary` para garantir consistência absoluta entre:
- Lançamentos filtrados pelo seed
- Dados agregados do banco
- Valores retornados pela API

## Implementação

### 1. Novo Serviço de Agregação

**Arquivo:** `backend/app/services/financial_aggregation_service.py`

**Classe:** `FinancialAggregationService`

**Métodos:**
- `aggregate_monthly_summary()`: Agrega receitas, despesas e custos por mês
- `get_debug_summary()`: Retorna resumo detalhado para QA/debug

**Características:**
- Usa `Decimal` para cálculos precisos (sem perda de precisão)
- Retorna 12 meses completos (mesmo sem lançamentos)
- Calcula saldo mensal: `receita - despesa - custo`
- Calcula saldo acumulado: `acumulado[jan] = saldo[jan]`, `acumulado[fev] = acumulado[jan] + saldo[fev]`, etc.
- Ignora transações sem `transaction_type`

### 2. Endpoint Refatorado

**Arquivo:** `backend/app/api/dashboard.py`

**Endpoint:** `GET /api/v1/financial/annual-summary`

**Mudanças:**
- Refatorado para usar `FinancialAggregationService.aggregate_monthly_summary()`
- Retorna estrutura completa com saldo acumulado
- Documentação atualizada com fórmulas de cálculo

**Resposta:**
```json
{
  "year": 2025,
  "totals": {
    "revenue": 1098490.83,
    "expense": 712606.65,
    "cost": 347107.64,
    "balance": 38776.54
  },
  "monthly": [
    {
      "month": 1,
      "revenue": 86153.06,
      "expense": 56231.57,
      "cost": 28443.42,
      "balance": 1478.07,
      "accumulated_balance": 1478.07
    },
    ...
  ]
}
```

### 3. Endpoint de Debug

**Endpoint:** `GET /api/v1/financial/annual-summary/debug`

**Funcionalidade:**
- Compara agregação SQL direta vs agregação em memória
- Retorna contagem de lançamentos por tipo
- Útil para identificar discrepâncias entre métodos de cálculo

**Resposta:**
```json
{
  "year": 2025,
  "tenant_id": "...",
  "business_unit_id": "...",
  "date_range": {
    "start": "2025-01-01T00:00:00",
    "end": "2025-12-31T23:59:59"
  },
  "total_transactions": 2863,
  "transactions_with_type": 2863,
  "annual_totals": {
    "sql": {
      "revenue": "1098490.83",
      "expense": "712606.65",
      "cost": "347107.64"
    },
    "memory": {
      "revenue": "1098490.83",
      "expense": "712606.65",
      "cost": "347107.64"
    }
  },
  "monthly_comparison": [...]
}
```

### 4. Testes Unitários

**Arquivo:** `backend/tests/test_financial_aggregation_service.py`

**Cobertura:**
- ✅ Mês com lançamentos
- ✅ Mês sem lançamentos
- ✅ Saldo acumulado
- ✅ Soma de receita/despesa/custo
- ✅ Totais anuais
- ✅ Ignorar transações sem tipo
- ✅ Estrutura do endpoint de debug

## Fórmulas de Cálculo

### Saldo Mensal
```
saldo_mensal[mês] = receita[mês] - despesa[mês] - custo[mês]
```

**Regras:**
- Sempre calculado, mesmo para meses sem lançamentos (resulta em 0)
- Usa `Decimal` para precisão absoluta
- Valores podem ser positivos, negativos ou zero

### Saldo Acumulado
```
saldo_acumulado[jan] = saldo_mensal[jan]
saldo_acumulado[fev] = saldo_acumulado[jan] + saldo_mensal[fev]
saldo_acumulado[mar] = saldo_acumulado[fev] + saldo_mensal[mar]
...
```

**Regras:**
- Sempre começa no primeiro mês do ano (janeiro)
- Meses sem lançamentos: saldo_acumulado se propaga (mantém valor do mês anterior)
- Soma progressiva: cada mês acumula o saldo do mês anterior
- Pode mudar de sinal (positivo → negativo ou vice-versa)
- Usa `Decimal` para precisão absoluta

### Metadata Explicativa (BLOCO 2)

O endpoint `/api/v1/financial/annual-summary` agora retorna metadata explicativa:

```json
{
  "metadata": {
    "saldo_formula": "receita - despesa - custo",
    "saldo_acumulado_formula": "soma progressiva dos saldos mensais",
    "saldo_acumulado_explanation": "O saldo acumulado de cada mês é a soma do saldo acumulado do mês anterior com o saldo mensal do mês atual. Janeiro não tem mês anterior, então o saldo acumulado é igual ao saldo mensal.",
    "calculation_precision": "Decimal (precisão absoluta)",
    "empty_months_behavior": "Meses sem lançamentos têm saldo_mensal = 0, mas o saldo_acumulado se propaga (mantém o valor do mês anterior)"
  }
}
```

Esta metadata pode ser usada pelo frontend para:
- Tooltips explicativos
- Modais de ajuda
- Documentação inline

### Totais Anuais
```
total_receita = Σ receita[mês] para mês = 1..12
total_despesa = Σ despesa[mês] para mês = 1..12
total_custo = Σ custo[mês] para mês = 1..12
total_saldo = total_receita - total_despesa - total_custo
```

## Validação

Para validar a correção, execute:

```bash
python -m scripts.validate_dashboard_against_client_sheet \
  --file data/fluxo_caixa_2025.xlsx \
  --year 2025
```

**Critérios de Aceite:**
- ✅ Script roda sem nenhum mismatch
- ✅ Todos os meses batem 100% entre API e banco
- ✅ Acumulado confere com cálculo manual
- ✅ Valores monetários formatados corretamente (float com 2 casas decimais)

## Arquivos Modificados

1. `backend/app/services/financial_aggregation_service.py` (novo)
2. `backend/app/api/dashboard.py` (refatorado)
3. `backend/tests/test_financial_aggregation_service.py` (novo)

## Próximos Passos

1. Executar script de validação em STAGING
2. Verificar se todos os meses batem 100%
3. Validar saldo acumulado manualmente
4. Atualizar documentação da API se necessário

