# Correções Necessárias para Dados Reais de Disponibilidade

## Status Atual (26/12/2025)

### ✅ O que está funcionando:
- **Contas de liquidação criadas**: 3 contas (SCB, CEF, CX)
- **Lançamentos associados**: 2681 de 2863 (93.64%)
- **Saldos sendo calculados**: Bancos R$ 33.012,53 | Caixa R$ -3.127,90 | Total R$ 29.884,63

### ⚠️ O que precisa ser corrigido:

#### 1. Lançamentos sem `liquidation_account_id` (182 lançamentos - 6.36%)

**Problema:**
- 182 lançamentos não têm conta de liquidação associada
- Provavelmente são lançamentos que não têm valor na coluna "Liquidação" do Excel

**Solução:**
- Opção A: Executar re-seed para associar os lançamentos restantes (se a coluna "Liquidação" foi preenchida posteriormente)
- Opção B: Criar uma conta de liquidação padrão para lançamentos sem liquidação
- Opção C: Verificar se esses lançamentos devem ter liquidação e preencher manualmente no Excel

**Comando para verificar:**
```bash
python3 scripts/check_liquidation_via_api.py
```

#### 2. Saldo negativo de Caixa (R$ -3.127,90)

**Problema:**
- O saldo de caixa está negativo, o que pode indicar:
  - Mais saídas do que entradas na conta CX
  - Classificação incorreta de alguns lançamentos
  - Dados reais do Excel (pode ser correto se houver mais despesas do que receitas em caixa)

**Solução:**
- Verificar no Excel se o saldo negativo está correto
- Se estiver correto, manter (é um dado real)
- Se estiver incorreto, verificar classificação de lançamentos na conta CX

**Verificação:**
```bash
# Verificar lançamentos da conta CX
python3 scripts/check_liquidation_via_api.py
# Verificar no Excel: filtrar por Liquidação = "CX" e somar entradas - saídas
```

#### 3. Investimentos zerados (R$ 0,00)

**Problema:**
- Não há investimentos sendo calculados
- Pode ser que não haja código de investimento no Excel ou que não haja lançamentos de investimento

**Solução:**
- Verificar se há códigos de investimento no Excel (ex: "INV", "INVESTIMENTO", "APLICAÇÃO")
- Se houver, verificar se estão sendo classificados corretamente
- Se não houver, está correto (zero)

## Ações Recomendadas

### Prioridade 1: Verificar dados do Excel
1. Abrir `backend/data/fluxo_caixa_2025.xlsx`
2. Filtrar linhas sem valor na coluna "Liquidação"
3. Verificar se essas linhas devem ter liquidação ou não

### Prioridade 2: Re-seed (se necessário)
Se houver lançamentos que devem ter liquidação mas não têm:
```bash
cd backend
./scripts/run_migration_and_seed.sh
```

### Prioridade 3: Validar saldo negativo
1. Verificar no Excel se o saldo negativo de caixa está correto
2. Se estiver correto, manter
3. Se estiver incorreto, investigar classificação

## Endpoints de Debug

- **Status de liquidação**: `GET /api/v1/dashboard/operational/availability/liquidation-status`
- **Debug de disponibilidades**: `GET /api/v1/dashboard/operational/availability/debug`

## Scripts Úteis

- `scripts/check_liquidation_via_api.py` - Verificar status via API
- `scripts/check_liquidation_status.py` - Verificar status diretamente no banco (requer acesso local)
- `scripts/run_migration_and_seed.sh` - Executar re-seed completo

