# 🧪 QA - Dashboard Operacional (V3)

**Data**: 2025-12-12  
**Versão**: 3.0  
**Status**: ✅ Implementado

---

## 📋 CHECKLIST DE VALIDAÇÃO

### ✅ 1. BLOCO — Composição das Disponibilidades de Caixa

**Endpoint**: `GET /api/v1/dashboard/operational/availability`

**Validações**:
- [ ] Valores vêm do banco (não mockados)
- [ ] Total = soma de bancos + caixa + investimentos
- [ ] Se total ≤ 0 → destaque visual negativo no frontend
- [ ] Layout destacado no topo da página

**Como validar**:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "$BACKEND_URL/api/v1/dashboard/operational/availability"
```

**Valores esperados**:
- `banks`: Soma de `saldo_atual` de todas as contas bancárias ativas
- `cash`: Soma de `saldo_atual` de todos os caixas ativos
- `investments`: Soma de `valor_atual` de todos os investimentos ativos
- `total`: `banks + cash + investments`

---

### ✅ 2. BLOCO — Alertas Financeiros Rápidos

**Endpoint**: `GET /api/v1/dashboard/operational/alerts`

**Validações**:
- [ ] Contas vencidas a pagar: quantidade e valor total corretos
- [ ] Contas vencidas a receber: quantidade e valor total corretos
- [ ] Projeção negativa de caixa: calculada corretamente (próximos 30 dias)
- [ ] Se não houver alerta → mostrar estado neutro ("Tudo em dia")
- [ ] Ícones simples (vermelho/amarelo)
- [ ] Clique leva para tela filtrada correspondente (implementar navegação)

**Como validar**:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "$BACKEND_URL/api/v1/dashboard/operational/alerts"
```

**Valores esperados**:
- `overdue_payables.count`: Quantidade de lançamentos previstos (DESPESA/CUSTO) com `data_prevista < hoje` e `status != CANCELADO`
- `overdue_payables.value`: Soma dos valores das contas vencidas a pagar
- `overdue_receivables.count`: Quantidade de lançamentos previstos (RECEITA) com `data_prevista < hoje` e `status != CANCELADO`
- `overdue_receivables.value`: Soma dos valores das contas vencidas a receber
- `negative_cash_forecast.has_alert`: `true` se `saldo_atual + receitas_previstas_30d - despesas_previstas_30d < 0`
- `negative_cash_forecast.projected_balance`: Saldo projetado nos próximos 30 dias

---

### ✅ 3. BLOCO — Previsto × Realizado (Gráfico Central)

**Endpoint**: `GET /api/v1/dashboard/operational/forecast-vs-realized?months=6`

**Validações**:
- [ ] Linha sólida → Realizado (verde)
- [ ] Linha tracejada → Previsto (azul)
- [ ] Área sombreada quando previsto < realizado ou previsto < 0
- [ ] Totais exibidos abaixo do gráfico:
  - Saldo realizado do período
  - Saldo previsto do período
  - Diferença (com cor: verde se positivo, vermelho se negativo)

**Como validar**:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "$BACKEND_URL/api/v1/dashboard/operational/forecast-vs-realized?months=6"
```

**Valores esperados**:
- `months[]`: Array com últimos N meses (padrão: 6)
- Cada mês contém:
  - `realized`: Saldo realizado (receita - despesa - custo) do mês
  - `forecast`: Saldo previsto (receita - despesa - custo) do mês
- `totals.realized`: Soma dos saldos realizados
- `totals.forecast`: Soma dos saldos previstos
- `totals.difference`: `realized - forecast`

**Fórmulas**:
- Realizado: `soma(LancamentoDiario.tipo == RECEITA) - soma(LancamentoDiario.tipo IN [DESPESA, CUSTO])`
- Previsto: `soma(LancamentoPrevisto.tipo == RECEITA) - soma(LancamentoPrevisto.tipo IN [DESPESA, CUSTO])` (apenas não cancelados)

---

### ✅ 4. BLOCO — Posição de Contas a Receber

**Endpoint**: `GET /api/v1/dashboard/operational/receivables-summary`

**Validações**:
- [ ] A receber hoje: valor correto
- [ ] A receber próximos 7 dias: valor correto
- [ ] A receber próximos 30 dias: valor correto
- [ ] Vencidos sempre em destaque (amarelo)
- [ ] Clique leva para lista filtrada (implementar navegação)

**Como validar**:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "$BACKEND_URL/api/v1/dashboard/operational/receivables-summary"
```

**Valores esperados**:
- `overdue`: Soma de lançamentos previstos (RECEITA) com `data_prevista < hoje` e `status != CANCELADO`
- `due_today`: Soma de lançamentos previstos (RECEITA) com `data_prevista == hoje` e `status != CANCELADO`
- `next_7_days`: Soma de lançamentos previstos (RECEITA) com `data_prevista` entre amanhã e 7 dias e `status != CANCELADO`
- `next_30_days`: Soma de lançamentos previstos (RECEITA) com `data_prevista` entre amanhã e 30 dias e `status != CANCELADO`

---

### ✅ 5. BLOCO — Posição de Contas a Pagar

**Endpoint**: `GET /api/v1/dashboard/operational/payables-summary`

**Validações**:
- [ ] Vencido: valor correto (sempre em vermelho)
- [ ] Vence hoje: valor correto
- [ ] Próximos 7 dias: valor correto
- [ ] Próximos 30 dias: valor correto
- [ ] Clique leva para lista filtrada (implementar navegação)

**Como validar**:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "$BACKEND_URL/api/v1/dashboard/operational/payables-summary"
```

**Valores esperados**:
- `overdue`: Soma de lançamentos previstos (DESPESA/CUSTO) com `data_prevista < hoje` e `status != CANCELADO`
- `due_today`: Soma de lançamentos previstos (DESPESA/CUSTO) com `data_prevista == hoje` e `status != CANCELADO`
- `next_7_days`: Soma de lançamentos previstos (DESPESA/CUSTO) com `data_prevista` entre amanhã e 7 dias e `status != CANCELADO`
- `next_30_days`: Soma de lançamentos previstos (DESPESA/CUSTO) com `data_prevista` entre amanhã e 30 dias e `status != CANCELADO`

---

## 🔍 VALIDAÇÃO COM DADOS SEEDADOS

### Pré-requisitos
1. Dados seedados da planilha (`backend/data/fluxo_caixa_2025.xlsx`)
2. Acesso ao banco de dados staging
3. Token de autenticação válido

### Passos

1. **Validar disponibilidades**:
   ```bash
   # Comparar com valores da planilha (seção "Verificação de saldo")
   # Total disponível deve bater com a planilha
   ```

2. **Validar alertas**:
   ```bash
   # Verificar se contas vencidas aparecem corretamente
   # Verificar se projeção negativa é calculada corretamente
   ```

3. **Validar previsto vs realizado**:
   ```bash
   # Comparar com valores mensais da planilha
   # Realizado deve bater com lançamentos diários
   # Previsto deve bater com lançamentos previstos
   ```

4. **Validar contas a receber/pagar**:
   ```bash
   # Comparar com valores da planilha de lançamentos previstos
   # Verificar se filtros de data estão corretos
   ```

---

## 🎯 CRITÉRIOS DE APROVAÇÃO

### ✅ Backend
- [ ] Todos os endpoints retornam dados corretos
- [ ] Valores usam `Decimal` para precisão
- [ ] Filtros por `tenant_id` e `business_unit_id` funcionam
- [ ] Status `CANCELADO` é excluído dos cálculos
- [ ] Documentação (docstring) clara em cada endpoint

### ✅ Frontend
- [ ] Visual limpo e direto
- [ ] Ícones simples e semânticos
- [ ] Cores semânticas (verde, amarelo, vermelho)
- [ ] Zero poluição visual
- [ ] Layout responsivo
- [ ] Loading states implementados
- [ ] Error handling implementado

### ✅ Integração
- [ ] Dados do backend são exibidos corretamente no frontend
- [ ] Formatação de moeda (R$) correta
- [ ] Navegação entre telas funciona (quando implementada)

---

## 🚨 PROBLEMAS CONHECIDOS

### Pendências
- [ ] Navegação para telas filtradas ao clicar em alertas (TODO no código)
- [ ] Navegação para lista de contas a pagar/receber (TODO no código)

---

## 📝 NOTAS

- Todos os cálculos usam `Decimal` para precisão absoluta
- Filtros por `business_unit_id` são aplicados quando disponível
- Status `CANCELADO` é sempre excluído dos cálculos
- Datas são comparadas em UTC para consistência

---

**Última atualização**: 2025-12-12  
**Status**: ✅ Pronto para validação






