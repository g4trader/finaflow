# Status da Conciliação - 2025

**Data:** 2025-01-XX  
**Última atualização:** Após implementação de filtros na query SQL

## Correções Implementadas

### ✅ 1. Filtros de Exclusão na Query SQL

**Arquivos modificados:**
- `backend/app/services/financial_aggregation_service.py`
- `backend/app/services/monthly_drilldown_service.py`

**Implementação:**
- Filtro aplicado diretamente na query SQL usando `join` com `ChartAccountGroup`
- Exclui grupos:
  - "Deduções" (todas as variações)
  - "Movimentações Não Operacionais" (todas as variações)

**Código:**
```python
query = query.filter(
    ~ChartAccountGroup.name.ilike('%dedução%'),
    ~ChartAccountGroup.name.ilike('%deducao%'),
    ~ChartAccountGroup.name.ilike('%deduções%'),
    ~ChartAccountGroup.name.ilike('%deducoes%'),
    ~ChartAccountGroup.name.ilike('%movimentações não operacionais%'),
    ~ChartAccountGroup.name.ilike('%movimentacoes nao operacionais%'),
    ~ChartAccountGroup.name.ilike('%movimentações nao operacionais%'),
    ~ChartAccountGroup.name.ilike('%movimentacoes não operacionais%'),
)
```

### ✅ 2. Tolerância ZERO

Todos os scripts de validação agora usam tolerância ZERO.

### ✅ 3. Scripts de Investigação

- `investigate_differences.py` criado e funcionando
- Usa `summary` da API (já filtrado) ao invés de somar itens

## Diferenças Restantes

### Totais Anuais (após filtros)

| Categoria | Planilha | Sistema | Diferença | Status |
|-----------|----------|---------|-----------|--------|
| **Receita** | R$ 1.092.261,12 | R$ 1.098.490,83 | R$ -6.229,71 | ❌ |
| **Despesa** | R$ 488.812,69 | R$ 712.606,65 | R$ -223.793,96 | ❌ |
| **Custo** | R$ 396.229,67 | R$ 347.107,64 | R$ 49.122,03 | ❌ |

### Análise das Diferenças

#### Despesas (R$ 223.793,96)

**Causa provável:**
- O sistema tem R$ 712.606,65 em despesas
- A planilha tem R$ 488.812,69 na linha "Despesas Operacionais"
- Diferença: R$ 223.793,96

**Observações:**
- Filtros de exclusão foram aplicados
- "Movimentações Não Operacionais" e "Deduções" devem estar excluídas
- Ainda há diferença significativa

**Próximos passos:**
1. Verificar se o filtro está sendo aplicado corretamente (testar API)
2. Verificar se há outras categorias que devem ser excluídas
3. Comparar linha a linha os subitens da planilha vs sistema

#### Custos (R$ 49.122,03)

**Causa provável:**
- Classificação incorreta de alguns grupos/subgrupos
- Alguns custos podem estar sendo classificados como despesas

**Próximos passos:**
1. Identificar grupos/subgrupos classificados incorretamente
2. Corrigir `determine_transaction_type`
3. Re-seed se necessário

#### Receitas (R$ 6.229,71)

**Causa provável:**
- Diferença menor, pode ser:
  - Arredondamentos
  - Lançamentos não seedados
  - Classificação incorreta

**Próximos passos:**
1. Investigar lançamentos individuais
2. Comparar linha a linha

## Comandos para Validação

```bash
# Conciliação geral
cd backend && python3 scripts/reconcile_fluxo_caixa.py --year 2025

# Investigação detalhada
cd backend && python3 scripts/investigate_differences.py --year 2025 --type despesa
cd backend && python3 scripts/investigate_differences.py --year 2025 --type custo
cd backend && python3 scripts/investigate_differences.py --year 2025 --type receita

# Verificar API diretamente
curl -H "Authorization: Bearer $TOKEN" \
  "https://finaflow-backend-staging-642830139828.us-central1.run.app/api/v1/financial/annual-summary?year=2025"
```

## Próximas Ações

1. ⏳ **Verificar se filtros estão funcionando** - Testar API após deploy
2. ⏳ **Investigar diferença de despesas** - Comparar linha a linha
3. ⏳ **Corrigir classificação de custos** - Identificar grupos incorretos
4. ⏳ **Ajustar receitas** - Investigar diferença menor

## Notas Técnicas

- Filtros aplicados na query SQL são mais eficientes que filtrar depois
- `summary` da API já tem filtros aplicados
- Scripts de investigação usam `summary` ao invés de somar itens
- Tolerância ZERO garante que qualquer diferença é reportada

