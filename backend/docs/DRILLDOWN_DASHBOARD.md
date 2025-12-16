# Drill Down do Dashboard - Épico 2

## Objetivo

Permitir que o usuário faça drill down do dashboard anual para ver detalhes diários e lançamentos específicos de um mês.

## Endpoints

### 1. GET `/api/v1/financial/monthly-daily-summary`

Retorna resumo diário de um mês específico.

#### Parâmetros

- `year` (int, obrigatório): Ano (ex: 2025)
- `month` (int, obrigatório): Mês (1-12)

#### Resposta

```json
{
  "year": 2025,
  "month": 1,
  "currency": "BRL",
  "days": [
    {
      "date": "2025-01-01",
      "day": 1,
      "revenue": "1234.56",
      "expense": "789.10",
      "cost": "500.00",
      "balance": "-54.54"
    },
    {
      "date": "2025-01-02",
      "day": 2,
      "revenue": "0",
      "expense": "0",
      "cost": "0",
      "balance": "0"
    },
    ...
  ],
  "metadata": {
    "saldo_formula": "receita - despesa - custo",
    "month_total_revenue": "10000.00",
    "month_total_expense": "5000.00",
    "month_total_cost": "2000.00",
    "month_total_balance": "3000.00"
  }
}
```

#### Características

- Retorna **todos os dias do mês**, mesmo sem lançamentos
- Valores retornados como strings (Decimal) para precisão
- Totais mensais (`month_total_*`) devem bater com `/annual-summary`

#### Exemplo de Request

```bash
curl -X GET "https://api.finaflow.com/api/v1/financial/monthly-daily-summary?year=2025&month=1" \
  -H "Authorization: Bearer <token>"
```

---

### 2. GET `/api/v1/financial/monthly-transactions`

Retorna lançamentos detalhados de um mês específico com filtros e paginação.

#### Parâmetros

- `year` (int, obrigatório): Ano (ex: 2025)
- `month` (int, obrigatório): Mês (1-12)
- `type` (string, opcional): Tipo de transação (`RECEITA`, `DESPESA`, `CUSTO`)
- `group_id` (string, opcional): ID do grupo
- `subgroup_id` (string, opcional): ID do subgrupo
- `account_id` (string, opcional): ID da conta
- `page` (int, opcional, default=1): Página (começa em 1)
- `page_size` (int, opcional, default=50, máx=200): Itens por página

#### Resposta

```json
{
  "year": 2025,
  "month": 1,
  "page": 1,
  "page_size": 50,
  "total_items": 123,
  "total_pages": 3,
  "summary": {
    "revenue": "10000.00",
    "expense": "5000.00",
    "cost": "2000.00",
    "balance": "3000.00"
  },
  "items": [
    {
      "id": "uuid-123",
      "date": "2025-01-04",
      "description": "Noiva",
      "type": "RECEITA",
      "group": "Serviços",
      "subgroup": "Casamento",
      "account": "Receita principal",
      "amount": "160.51"
    },
    ...
  ]
}
```

#### Características

- **Paginação**: `page` e `page_size` controlam quantos itens são retornados
- **Summary**: Totais do mês considerando os filtros aplicados
- **Consistência**: Se nenhum filtro for aplicado, `summary.*` deve bater com `/annual-summary`
- Valores retornados como strings (Decimal) para precisão

#### Exemplo de Request

```bash
# Sem filtros
curl -X GET "https://api.finaflow.com/api/v1/financial/monthly-transactions?year=2025&month=1&page=1&page_size=50" \
  -H "Authorization: Bearer <token>"

# Com filtro por tipo
curl -X GET "https://api.finaflow.com/api/v1/financial/monthly-transactions?year=2025&month=1&type=RECEITA" \
  -H "Authorization: Bearer <token>"

# Com filtro por grupo
curl -X GET "https://api.financial/monthly-transactions?year=2025&month=1&group_id=grupo-123" \
  -H "Authorization: Bearer <token>"
```

---

## Garantias de Consistência

### 1. Totais Mensais

Os totais mensais retornados por ambos os endpoints devem bater com `/annual-summary`:

```python
# monthly-daily-summary
month_total_revenue == annual_summary["monthly"][month-1]["revenue"]
month_total_expense == annual_summary["monthly"][month-1]["expense"]
month_total_cost == annual_summary["monthly"][month-1]["cost"]
month_total_balance == annual_summary["monthly"][month-1]["balance"]
```

### 2. Soma dos Dias

A soma dos valores diários deve igualar os totais mensais:

```python
# monthly-daily-summary
sum(day["revenue"] for day in days) == month_total_revenue
sum(day["expense"] for day in days) == month_total_expense
sum(day["cost"] for day in days) == month_total_cost
sum(day["balance"] for day in days) == month_total_balance
```

### 3. Soma dos Lançamentos

Se nenhum filtro for aplicado em `monthly-transactions`:

```python
# monthly-transactions (sem filtros)
summary["revenue"] == annual_summary["monthly"][month-1]["revenue"]
summary["expense"] == annual_summary["monthly"][month-1]["expense"]
summary["cost"] == annual_summary["monthly"][month-1]["cost"]
summary["balance"] == annual_summary["monthly"][month-1]["balance"]
```

### 4. Filtros

Quando filtros são aplicados, o `summary` reflete apenas os lançamentos que passam pelos filtros:

```python
# monthly-transactions (com filtro type=RECEITA)
summary["revenue"] == soma de todas as receitas do mês
summary["expense"] == "0"
summary["cost"] == "0"
summary["balance"] == summary["revenue"]
```

---

## Validação de Consistência

### Script de Validação

```python
import requests

# 1. Buscar annual-summary
annual = requests.get("/api/v1/financial/annual-summary?year=2025").json()

# 2. Para cada mês, validar consistência
for month in range(1, 13):
    # Buscar daily-summary
    daily = requests.get(f"/api/v1/financial/monthly-daily-summary?year=2025&month={month}").json()
    
    # Validar totais
    assert daily["metadata"]["month_total_revenue"] == str(annual["monthly"][month-1]["revenue"])
    assert daily["metadata"]["month_total_expense"] == str(annual["monthly"][month-1]["expense"])
    assert daily["metadata"]["month_total_cost"] == str(annual["monthly"][month-1]["cost"])
    assert daily["metadata"]["month_total_balance"] == str(annual["monthly"][month-1]["balance"])
    
    # Validar soma dos dias
    total_revenue = sum(Decimal(day["revenue"]) for day in daily["days"])
    assert total_revenue == Decimal(daily["metadata"]["month_total_revenue"])
    
    # Buscar transactions (sem filtros)
    transactions = requests.get(f"/api/v1/financial/monthly-transactions?year=2025&month={month}").json()
    
    # Validar summary
    assert transactions["summary"]["revenue"] == daily["metadata"]["month_total_revenue"]
    assert transactions["summary"]["expense"] == daily["metadata"]["month_total_expense"]
    assert transactions["summary"]["cost"] == daily["metadata"]["month_total_cost"]
    assert transactions["summary"]["balance"] == daily["metadata"]["month_total_balance"]
```

---

## Implementação Técnica

### Serviço

`MonthlyDrilldownService` em `backend/app/services/monthly_drilldown_service.py`

- `aggregate_daily_summary()`: Agregação diária
- `get_monthly_transactions()`: Listagem detalhada com filtros

### Endpoints

`backend/app/api/dashboard.py`

- `monthly_daily_summary()`: Endpoint de resumo diário
- `monthly_transactions()`: Endpoint de lançamentos detalhados

### Testes

`backend/tests/test_monthly_drilldown_service.py`

- Testes unitários cobrindo principais cenários
- Validação de consistência
- Testes de paginação e filtros

---

## Próximos Passos (Frontend)

1. Adicionar botão "Ver Detalhes" na tabela mensal
2. Modal/página mostrando resumo diário
3. Tabela de lançamentos com filtros
4. Validação visual de consistência (totais batendo)

