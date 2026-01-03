# Análise: Diferença em Custos com Mão de Obra

**Data:** 2025-01-XX  
**Problema:** Diferença de R$ 48.872,03 entre planilha e sistema

## Valores

| Fonte | Valor | Diferença |
|-------|-------|-----------|
| Planilha "Fluxo de caixa-2025" | R$ 264.679,75 | - |
| Sistema (API) | R$ 215.807,72 | R$ -48.872,03 |

## Análise Realizada

### 1. Verificação de Classificação
✅ **Nenhum lançamento está em DESPESA**  
✅ Todos os lançamentos de "Custos com Mão de Obra" estão classificados como CUSTO

### 2. Verificação de Seed
✅ **Todos os lançamentos foram seedados** (0 faltantes encontrados)  
⚠️ **Mas há diferença de 61 lançamentos:**
- Planilha: 357 lançamentos
- Sistema: 296 lançamentos
- Diferença: 61 lançamentos

### 3. Verificação de Contas
✅ **Há 12 contas no subgrupo "Custos com Mão de Obra"**  
✅ O seed busca a primeira conta do subgrupo (linha 1082)

### 4. Verificação de Status
✅ **Todos os lançamentos estão ativos** (status N/A na API)

## Possíveis Causas

1. **Lançamentos seedados com valores diferentes**
   - Problemas de parse de valores (formato brasileiro vs internacional)
   - Arredondamentos diferentes
   - Valores negativos sendo ignorados

2. **Lançamentos seedados mas depois excluídos**
   - Idempotência: lançamentos duplicados sendo ignorados
   - Lançamentos sendo atualizados com valores diferentes

3. **Problema na agregação da API**
   - Filtros aplicados incorretamente
   - Agregação não considerando todos os lançamentos

## Próximos Passos

1. **Verificar lançamentos com valores diferentes**
   - Comparar linha a linha os valores da planilha com os do sistema
   - Identificar lançamentos com diferenças de arredondamento

2. **Verificar idempotência**
   - Verificar se há lançamentos duplicados sendo ignorados
   - Verificar se a lógica de idempotência está correta

3. **Re-seed se necessário**
   - Limpar lançamentos de "Custos com Mão de Obra" do ano 2025
   - Re-seed com COST_DEBUG=1 para identificar problemas

4. **Verificar agregação da API**
   - Verificar se os filtros estão sendo aplicados corretamente
   - Verificar se a agregação está considerando todos os lançamentos

## Comandos Úteis

```bash
# Rodar script de debug
cd backend && python3 scripts/debug_missing_custos.py

# Verificar totais mensais
cd backend && python3 scripts/reconcile_fluxo_caixa.py --year 2025

# Investigar diferenças detalhadas
cd backend && python3 scripts/investigate_differences.py --year 2025 --type custo
```

