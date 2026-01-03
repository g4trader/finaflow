# Relatório de Deploy e Resultados - Conciliação 2025

**Data:** 2025-01-XX  
**Deploy:** Concluído com sucesso

## Deploy Realizado

✅ **Deploy concluído:** `finaflow-backend-staging-00042-k49`  
✅ **URL:** https://finaflow-backend-staging-642830139828.us-central1.run.app  
✅ **Filtros aplicados:** Deduções e Movimentações Não Operacionais excluídas

## Resultados Após Deploy

### Melhoria Significativa em Despesas

| Métrica | Antes do Deploy | Após Deploy | Melhoria |
|---------|----------------|-------------|----------|
| **Despesa Sistema** | R$ 712.606,65 | R$ 491.183,31 | ✅ -R$ 221.423,34 |
| **Diferença vs Planilha** | R$ -223.793,96 | R$ -2.370,62 | ✅ **99% de redução** |

### Totais Atuais (Após Filtros)

| Categoria | Planilha | Sistema | Diferença | Status |
|-----------|----------|---------|-----------|--------|
| **Receita** | R$ 1.092.261,12 | R$ 1.098.490,83 | R$ -6.229,71 | ⚠️ |
| **Despesa** | R$ 488.812,69 | R$ 491.183,31 | R$ -2.370,62 | ⚠️ |
| **Custo** | R$ 396.229,67 | R$ 347.107,64 | R$ 49.122,03 | ❌ |
| **Saldo** | R$ 207.218,76 | R$ 260.199,88 | R$ -52.981,12 | ⚠️ |

## Análise das Diferenças Restantes

### 1. Despesas (R$ 2.370,62) - ⚠️ Quase Concilado

**Progresso:** 99% de redução na diferença!

**Causa provável:**
- Pequenas diferenças de arredondamento
- Possíveis lançamentos não seedados
- Diferenças de classificação em subitens específicos

**Próximos passos:**
- Investigar linha a linha os R$ 2.370,62 restantes
- Verificar se há lançamentos duplicados ou faltantes

### 2. Custos (R$ 49.122,03) - ❌ Precisa Correção

**Causa provável:**
- Classificação incorreta de grupos/subgrupos
- Alguns custos sendo classificados como despesas
- Ou alguns despesas sendo classificados como custos

**Próximos passos:**
- Identificar grupos/subgrupos classificados incorretamente
- Corrigir `determine_transaction_type`
- Re-seed se necessário

### 3. Receitas (R$ 6.229,71) - ⚠️ Pequena Diferença

**Causa provável:**
- Lançamentos não seedados
- Arredondamentos
- Classificação incorreta

**Próximos passos:**
- Investigar lançamentos individuais
- Comparar linha a linha

## Correções Implementadas

### ✅ Filtros na Query SQL

- `FinancialAggregationService`: Filtro aplicado
- `MonthlyDrilldownService`: Filtro aplicado
- Exclui "Deduções" e "Movimentações Não Operacionais"

### ✅ Tolerância ZERO

- Todos os scripts configurados
- Qualquer diferença é reportada

### ✅ Scripts de Investigação

- `investigate_differences.py` funcionando
- Usa `summary` da API (já filtrado)

## Comandos para Validação

```bash
# Conciliação geral
cd backend && python3 scripts/reconcile_fluxo_caixa.py --year 2025

# Investigação detalhada
cd backend && python3 scripts/investigate_differences.py --year 2025 --type despesa
cd backend && python3 scripts/investigate_differences.py --year 2025 --type custo
cd backend && python3 scripts/investigate_differences.py --year 2025 --type receita
```

## Status Final

- ✅ Deploy concluído
- ✅ Filtros funcionando (99% de redução em despesas)
- ⚠️ Despesas: R$ 2.370,62 de diferença (quase conciliado)
- ❌ Custos: R$ 49.122,03 de diferença (precisa correção)
- ⚠️ Receitas: R$ 6.229,71 de diferença (pequena)

**Próxima ação:** Investigar e corrigir diferenças de custos e receitas.

