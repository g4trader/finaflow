# Relatório Final de Conciliação 2025

**Data:** 2025-01-XX  
**Status:** Em Progresso

## Correções Aplicadas

### 1. ✅ Filtros de Deduções e Movimentações Não Operacionais
- **Status:** Aplicado e funcionando
- **Impacto:** Redução de 99% na diferença de Despesas

### 2. ✅ Buscar Conta Específica da Planilha
- **Status:** Aplicado
- **Impacto:** Permite múltiplas contas no mesmo subgrupo

### 3. ✅ Idempotência com Número da Linha
- **Status:** Aplicado
- **Impacto:** Deve permitir múltiplos lançamentos legítimos

## Diferenças Atuais

### Custos
- **Total:** R$ 49.122,03
- **Custos com Mão de Obra:** R$ 48.872,03
  - Salário: R$ 42.675,94 (55 lançamentos faltantes)
  - Décimo terceiro: R$ 3.842,32
  - Férias: R$ 2.353,77

### Despesas
- **Total:** R$ 2.370,62
- **Outubro:** R$ 2.469,00 (maior diferença)

### Receitas
- **Total:** R$ 10.229,71
- **Novembro:** R$ 9.777,20 (maior diferença)

## Próximos Passos

1. Verificar se re-seed foi executado com código atualizado
2. Investigar por que 55 lançamentos de Salário ainda não foram seedados
3. Corrigir diferenças restantes em Despesas e Receitas
4. Validar 100% de conciliação

## Comandos Úteis

```bash
# Conciliação
cd backend && python3 scripts/reconcile_fluxo_caixa.py --year 2025

# Investigação detalhada
cd backend && python3 scripts/investigate_differences.py --year 2025 --type custo
```

