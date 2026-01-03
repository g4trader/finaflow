# Plano de Re-Seed 2025

**Data:** 2025-01-XX  
**Objetivo:** Corrigir todas as diferenças entre planilha e sistema

## Correções Aplicadas

### 1. ✅ Buscar Conta Específica da Planilha
- **Problema:** Seed usava apenas primeira conta do subgrupo
- **Impacto:** 60 lançamentos duplicados ignorados
- **Diferença:** R$ 48.872,03 em Custos com Mão de Obra
- **Status:** Código corrigido e commitado

### 2. ✅ Filtros de Deduções e Movimentações Não Operacionais
- **Problema:** Essas categorias estavam sendo contadas como despesas
- **Impacto:** Diferença de R$ 223.793,96 em Despesas
- **Status:** Filtros aplicados (99% de redução)

## Diferenças Restantes

### Custos
- **Total:** R$ 49.122,03
- **Custos com Mão de Obra:** R$ 48.872,03 (deve ser corrigido após re-seed)
- **Outros:** R$ 250,00

### Despesas
- **Total:** R$ 2.370,62
- **Outubro:** R$ 2.469,00 (maior diferença)
- **Outros meses:** Pequenas diferenças

### Receitas
- **Total:** R$ 6.229,71
- **Novembro:** R$ 9.777,20 (maior diferença)
- **Outros meses:** Pequenas diferenças

## Plano de Re-Seed

### Opção 1: Re-Seed Completo (Recomendado)
```bash
# 1. Limpar todos os lançamentos do ano 2025
# 2. Re-seed completo com todas as correções
# 3. Validar conciliação
```

### Opção 2: Re-Seed Parcial (Apenas Custos)
```bash
# 1. Limpar apenas lançamentos de Custos do ano 2025
# 2. Re-seed apenas Custos
# 3. Validar se diferença foi corrigida
```

## Comandos para Re-Seed

### Via API (Recomendado)
```bash
# Fazer login e obter token
TOKEN=$(curl -X POST "https://finaflow-backend-staging-642830139828.us-central1.run.app/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"qa@finaflow.test","password":"QaFinaflow123!"}' | jq -r '.access_token')

# Executar seed com reset
curl -X POST "https://finaflow-backend-staging-642830139828.us-central1.run.app/api/v1/admin/seed-staging" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reset_data": true, "year": 2025}'
```

### Via Script Local
```bash
cd backend
python3 -m scripts.seed_from_client_sheet \
  --file data/fluxo_caixa_2025.xlsx \
  --year 2025 \
  --reset
```

## Validação Após Re-Seed

```bash
# 1. Conciliação geral
cd backend && python3 scripts/reconcile_fluxo_caixa.py --year 2025

# 2. Investigação detalhada
cd backend && python3 scripts/investigate_differences.py --year 2025 --type custo
cd backend && python3 scripts/investigate_differences.py --year 2025 --type despesa
cd backend && python3 scripts/investigate_differences.py --year 2025 --type receita

# 3. Validar tolerância ZERO
# Todas as diferenças devem ser R$ 0,00
```

## Critérios de Aceite

- ✅ **Custos:** Diferença = R$ 0,00
- ✅ **Despesas:** Diferença = R$ 0,00
- ✅ **Receitas:** Diferença = R$ 0,00
- ✅ **Saldo:** Diferença = R$ 0,00
- ✅ **Todos os meses:** Diferença = R$ 0,00

## Próximos Passos

1. **Fazer deploy da correção** (conta específica)
2. **Executar re-seed do ano 2025**
3. **Validar conciliação**
4. **Investigar e corrigir diferenças restantes** (se houver)
5. **Documentar resultado final**

