# Correção: Buscar Conta Específica da Planilha

**Data:** 2025-01-XX  
**Problema:** R$ 48.872,03 faltantes em "Custos com Mão de Obra"

## Problema Identificado

O seed estava usando apenas a **primeira conta do subgrupo** para todos os lançamentos, mesmo quando a planilha tinha contas diferentes para o mesmo subgrupo.

### Exemplo do Problema

Na planilha "Lançamento Diário", há 8 contas diferentes no subgrupo "Custos com Mão de Obra":
- Salário (227 lançamentos)
- Vale transporte (76 lançamentos)
- Alimentação (26 lançamentos)
- Décimo terceiro (8 lançamentos)
- FGTS (7 lançamentos)
- Férias (6 lançamentos)
- Rescisão (4 lançamentos)
- Pró-Labore (3 lançamentos)

Mas o seed estava usando apenas a primeira conta encontrada para todos os lançamentos, causando:
- **60 lançamentos duplicados** sendo ignorados por idempotência
- **Diferença de R$ 48.872,03** entre planilha e sistema

## Solução Implementada

### Antes
```python
# Buscar primeira conta do subgrupo
conta = db.query(ChartAccount).filter(
    ChartAccount.subgroup_id == subgrupo.id,
    ChartAccount.tenant_id == tenant.id
).first()
```

### Depois
```python
# Buscar conta específica da planilha (se informada), senão usar primeira conta do subgrupo
conta = None
if conta_nome:
    # Buscar conta específica pelo nome no subgrupo
    conta = db.query(ChartAccount).filter(
        ChartAccount.name == conta_nome,
        ChartAccount.subgroup_id == subgrupo.id,
        ChartAccount.tenant_id == tenant.id
    ).first()

# Se não encontrou conta específica, usar primeira conta do subgrupo (fallback)
if not conta:
    conta = db.query(ChartAccount).filter(
        ChartAccount.subgroup_id == subgrupo.id,
        ChartAccount.tenant_id == tenant.id
    ).first()
```

## Mudanças no Código

1. **Adicionado mapeamento da coluna 'Conta'** (linha ~917):
   ```python
   if 'conta' in col_lower and 'subgrupo' not in col_lower and 'grupo' not in col_lower and 'conta' not in column_map:
       column_map['conta'] = col
   ```

2. **Parse da coluna 'Conta'** (linha ~953):
   ```python
   if 'conta' in column_map:
       conta_nome = str(row[column_map['conta']]).strip() if pd.notna(row[column_map['conta']]) else ""
   ```

3. **Busca da conta específica** (linha ~1081):
   - Primeiro tenta buscar pela conta específica da planilha
   - Se não encontrar, usa fallback para primeira conta do subgrupo

## Próximos Passos

1. **Re-seed dos dados:**
   ```bash
   # Limpar lançamentos de Custos com Mão de Obra do ano 2025
   # Re-seed com a correção aplicada
   ```

2. **Validar correção:**
   ```bash
   cd backend && python3 scripts/reconcile_fluxo_caixa.py --year 2025
   ```

3. **Verificar se diferença foi corrigida:**
   - Planilha: R$ 264.679,75
   - Sistema esperado: R$ 264.679,75
   - Diferença esperada: R$ 0,00

## Impacto Esperado

- ✅ **60 lançamentos duplicados** agora serão seedados corretamente
- ✅ **R$ 48.872,03** devem ser recuperados
- ✅ **Total de Custos com Mão de Obra** deve bater com a planilha

