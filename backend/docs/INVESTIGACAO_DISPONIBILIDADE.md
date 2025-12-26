# Investigação: Diferença na Disponibilidade

## Situação Atual

**Sistema:** R$ 38.776,54  
**Planilha (Lucro líquido acumulado - Reservas):** R$ 157.181,30  
**Diferença:** R$ 118.404,76

## Cálculo Atual do Sistema

O sistema está calculando:
```
Saldo Consolidado = Receitas - Despesas - Custos
Total Disponível = Saldo Inicial + Saldo Consolidado
```

**Valores atuais:**
- Receitas: R$ 1.098.490,83
- Despesas: R$ 712.606,65
- Custos: R$ 347.107,64
- Saldo Consolidado: R$ 38.776,54
- Saldo Inicial: R$ 0,00

## Possíveis Causas da Diferença

### 1. Lançamentos Previstos vs Realizados
A planilha pode estar incluindo lançamentos **previstos** além dos realizados.

**Verificar:**
- A planilha usa apenas "Realizado" ou também "Previsto"?
- O sistema está filtrando apenas `status != CANCELADO` e `data <= hoje`

### 2. Saldo Inicial do Exercício
A planilha pode estar considerando um **saldo inicial** diferente de zero.

**Verificar:**
- Há saldo inicial do exercício anterior na planilha?
- Onde está esse valor na planilha?

### 3. Filtros Diferentes
A planilha pode estar usando filtros diferentes:
- Status de lançamentos
- Datas (competência vs data de movimentação)
- Tipos de transação (incluindo outros tipos além de RECEITA/DESPESA/CUSTO)

### 4. Fórmula Diferente
A planilha pode estar usando uma fórmula diferente:
- Incluindo outras categorias
- Excluindo algumas categorias
- Usando agrupamento diferente

## Próximos Passos

1. **Verificar na planilha:**
   - Como a linha "Lucro líquido acumulado (Reservas)" é calculada
   - Se inclui previstos ou apenas realizados
   - Se há saldo inicial considerado
   - Quais filtros são aplicados

2. **Comparar dados:**
   - Verificar se todos os lançamentos da planilha estão no sistema
   - Verificar se há diferença nos totais de receitas/despesas/custos
   - Verificar se há lançamentos com status diferente

3. **Ajustar cálculo:**
   - Uma vez identificada a causa, ajustar o endpoint para usar a mesma lógica da planilha

## Comandos Úteis

```bash
# Verificar disponibilidade atual
python3 scripts/check_liquidation_via_api.py

# Verificar annual summary
curl -H "Authorization: Bearer $TOKEN" \
  "$BACKEND_URL/api/v1/financial/annual-summary?year=2025"

# Verificar disponibilidade
curl -H "Authorization: Bearer $TOKEN" \
  "$BACKEND_URL/api/v1/dashboard/operational/availability"
```

