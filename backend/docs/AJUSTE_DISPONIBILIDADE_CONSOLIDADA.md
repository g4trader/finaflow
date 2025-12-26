# Ajuste de Disponibilidade Consolidada

## Contexto

Conforme análise da planilha do cliente, a visão de disponibilidade está associada com:
- **Apuração de resultado de lucro/prejuízo líquido** até hoje
- **+ Saldo final do exercício anterior** (se houver)

A planilha está na aba "Fluxo de caixa-2025" do Google Sheets.

## Problema Anterior

O sistema estava tentando separar disponibilidades por:
- Bancos
- Caixa / Dinheiro
- Aplicações / Investimentos

Mas ainda não há um processo de baixa de contas a pagar e receber para definir a bancária de liquidação.

## Solução Implementada

### Backend (`/api/v1/dashboard/operational/availability`)

Ajustado para calcular disponibilidade como **resultado líquido consolidado**:

```python
# Fórmula:
saldo_consolidado = receitas_realizadas - despesas_realizadas - custos_realizados
total_disponivel = saldo_inicial + saldo_consolidado
```

**Características:**
- Considera apenas lançamentos **realizados** até hoje (status != CANCELADO)
- Não separa por tipo de conta de liquidação
- Retorna um valor consolidado único
- Inclui detalhamento de receitas, despesas e custos

**Resposta da API:**
```json
{
  "total": 29884.63,
  "receitas": 1148993.27,
  "despesas": 500000.00,
  "custos": 396229.67,
  "saldo_consolidado": 252763.60,
  "saldo_inicial": 0.0,
  "banks": 29884.63,  // Compatibilidade (mesmo valor de total)
  "cash": 0.0,        // Compatibilidade
  "investments": 0.0  // Compatibilidade
}
```

### Frontend (`CashAvailabilityCards.tsx`)

Ajustado para exibir:
1. **Total Disponível** (destaque principal)
2. **Detalhamento do Resultado Líquido:**
   - Receitas Realizadas
   - Despesas Realizadas
   - Custos Realizados
   - Resultado Líquido (receitas - despesas - custos)

**Removido:**
- Cards separados de Bancos, Caixa e Investimentos
- Separação visual por tipo de conta

## Próximos Passos (Futuro)

Quando houver processo de baixa de contas a pagar/receber:
1. Implementar lógica de liquidação por conta bancária
2. Separar disponibilidades por tipo de conta
3. Atualizar endpoint para retornar breakdown detalhado

## Validação

Para validar se os valores estão corretos:
1. Comparar com a planilha do cliente (aba "Fluxo de caixa-2025")
2. Verificar se o resultado líquido bate com: Receitas - Despesas - Custos
3. Confirmar que apenas lançamentos realizados até hoje estão sendo considerados

## Arquivos Modificados

- `backend/app/api/dashboard.py` - Endpoint `operational_availability`
- `frontend/components/cards/CashAvailabilityCards.tsx` - Componente visual
- `frontend/lib/api/finance.ts` - Tipo TypeScript `OperationalAvailability`

