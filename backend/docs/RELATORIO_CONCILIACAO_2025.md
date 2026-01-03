# Relatório de Conciliação - Fluxo de Caixa 2025

## Resumo Executivo

Este relatório apresenta a conciliação entre os dados da planilha Excel (aba "Fluxo de caixa-2025") e os dados do sistema (API/annual-summary).

**Data da Conciliação:** 26/12/2025  
**Ano Analisado:** 2025

## Totais Anuais

| Categoria | Planilha | Sistema | Diferença | % Diferença |
|-----------|----------|---------|-----------|-------------|
| **Receitas** | R$ 1.092.261,12 | R$ 1.098.490,83 | R$ -6.229,71 | -0,6% |
| **Despesas** | R$ 488.812,69 | R$ 712.606,65 | R$ -223.793,96 | **-45,8%** ⚠️ |
| **Custos** | R$ 396.229,67 | R$ 347.107,64 | R$ 49.122,03 | 14,2% |
| **Saldo** | R$ 207.218,76 | R$ 38.776,54 | R$ 168.442,22 | 81,3% |

## Principais Diferenças

### 1. Despesas (CRÍTICO)
- **Diferença:** R$ 223.793,96 (45,8%)
- **Causa Provável:** 
  - Sistema tem mais despesas do que a planilha mostra
  - Pode haver despesas duplicadas no sistema
  - Pode haver despesas que não estão na linha "Despesas Operacionais" da planilha

### 2. Custos
- **Diferença:** R$ 49.122,03 (14,2%)
- **Causa Conhecida:** Alguns grupos/subgrupos não estão sendo classificados como CUSTO

### 3. Receitas
- **Diferença:** R$ 6.229,71 (0,6%)
- **Status:** Diferença pequena, dentro da tolerância

## Diferenças Mensais

### Janeiro
- Receitas: -R$ 126,77 ✅
- Despesas: -R$ 14.692,87 ⚠️
- Custos: R$ 5.611,11 ⚠️

### Fevereiro
- Receitas: OK ✅
- Despesas: -R$ 34.449,20 ⚠️
- Custos: R$ 4.828,71 ⚠️

### Março
- Receitas: R$ 1.000,00 ⚠️
- Despesas: -R$ 29.352,89 ⚠️
- Custos: R$ 3.121,69 ⚠️

### Abril
- Receitas: R$ 1.000,00 ⚠️
- Despesas: -R$ 40.137,73 ⚠️
- Custos: R$ 2.342,37 ⚠️

### Maio
- Receitas: -R$ 200,00 ✅
- Despesas: -R$ 50.281,01 ⚠️
- Custos: R$ 1.516,94 ⚠️

### Junho
- Receitas: R$ 289,70 ✅
- Despesas: -R$ 46.719,84 ⚠️
- Custos: R$ 3.386,86 ⚠️

### Julho
- Receitas: R$ 259,70 ✅
- Despesas: -R$ 33.220,52 ⚠️
- Custos: R$ 3.296,25 ⚠️

### Agosto
- Receitas: R$ 204,80 ✅
- Despesas: -R$ 43.814,34 ⚠️
- Custos: R$ 5.665,27 ⚠️

### Setembro
- Receitas: OK ✅
- Despesas: -R$ 47.495,36 ⚠️
- Custos: R$ 2.470,18 ⚠️

### Outubro
- Receitas: R$ 1.120,06 ✅
- Despesas: -R$ 53.023,00 ⚠️
- Custos: R$ 5.648,87 ⚠️

### Novembro
- Receitas: OK ✅
- Despesas: -R$ 54.012,92 ⚠️
- Custos: OK ✅

### Dezembro
- Receitas: OK ✅
- Despesas: -R$ 14.767,18 ⚠️
- Custos: OK ✅

## Ações Recomendadas

### Prioridade 1: Investigar Despesas
1. Verificar se há despesas duplicadas no sistema
2. Comparar linha a linha os lançamentos de despesas
3. Verificar se todas as despesas da planilha estão sendo seedadas
4. Verificar se há despesas no sistema que não estão na planilha

### Prioridade 2: Corrigir Custos
1. Revisar classificação de grupos/subgrupos como CUSTO
2. Verificar se os R$ 49.122,03 faltantes estão sendo classificados como DESPESA

### Prioridade 3: Ajustar Receitas
1. Investigar as pequenas diferenças (R$ 1.000,00 em alguns meses)
2. Verificar se há receitas duplicadas ou faltantes

## Como Executar a Conciliação

```bash
cd backend
python3 scripts/reconcile_fluxo_caixa.py --year 2025 --output artifacts/reconcile_report_2025.json
```

## Próximos Passos

1. ✅ Script de conciliação criado
2. ⏳ Analisar diferenças de despesas linha a linha
3. ⏳ Verificar duplicações no banco de dados
4. ⏳ Corrigir classificação de custos
5. ⏳ Re-seed após correções
6. ⏳ Re-executar conciliação para validar

