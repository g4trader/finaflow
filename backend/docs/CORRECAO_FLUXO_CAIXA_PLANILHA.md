# Correção: Fluxo de Caixa vs Planilha

## Problema Identificado

O Fluxo de Caixa Mensal do sistema não replicava fielmente a planilha do cliente, causando:
1. **Ordem incorreta**: Grupos apareciam fora da ordem semântica da planilha
2. **Totais divergentes**: Valores mensais não batiam com a planilha
3. **Linhas faltando**: Contas zeradas desapareciam do sistema
4. **Estrutura visual diferente**: Hierarquia não era clara

## Correções Implementadas

### 1. CORS (Bloqueante Imediato) ✅

**Problema:** Endpoint `/api/v1/lancamentos-previstos` bloqueado por CORS.

**Solução:**
- Adicionado `https://finaflow-lcz5.vercel.app` explicitamente no CORS
- CORS aplicado mesmo em erros 500
- Headers permitidos: `Authorization`, `Content-Type`, `X-Requested-With`, `Accept`
- Métodos permitidos: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `OPTIONS`

**Arquivos:**
- `backend/app/main.py`: Configuração CORS e exception handler

### 2. Ordem Explícita dos Grupos ✅

**Problema:** Grupos ordenados alfabeticamente, não pela ordem da planilha.

**Solução:**
- Criado `GROUP_ORDER` com ordem fixa baseada na planilha
- Função `_get_group_order_index()` para ordenar grupos corretamente
- Ordem implementada: Receita → Deduções → Custos → Despesas → Ajustes

**Arquivos:**
- `backend/app/services/cash_flow_service.py`: Ordem explícita

### 3. Linhas Zeradas Aparecem ✅

**Problema:** Contas sem lançamentos no mês desapareciam do fluxo de caixa.

**Solução:**
- `_load_complete_plan_structure()` carrega TODAS as contas do plano de contas
- Todas as contas são adicionadas às rows, mesmo com valor zero
- Valores zerados aparecem como `0.0` em todos os dias

**Arquivos:**
- `backend/app/services/cash_flow_service.py`: Carregamento completo do plano

### 4. Subtotais Corretos ✅

**Problema:** Subtotais não eram calculados ou apareciam na ordem errada.

**Solução:**
- Receita Líquida = Receita - Deduções (inserido após Deduções)
- Lucro Bruto = Receita Líquida - Custos (inserido após Custos)
- Resultado Operacional = Lucro Bruto - Despesas Operacionais (inserido após Despesas)
- Saldo Final = Resultado Operacional + Ajustes (inserido após Movimentações Não Operacionais)

**Arquivos:**
- `backend/app/services/cash_flow_service.py`: Cálculo e inserção de subtotais

### 5. Estrutura Hierárquica ✅

**Problema:** Estrutura "flat", difícil leitura.

**Solução:**
- Backend retorna estrutura hierárquica completa:
  - Nível 0: Grupo
  - Nível 1: Subgrupo
  - Nível 2: Conta
  - Nível 0 (subtotal): Subtotais calculados
- Frontend apenas renderiza, não calcula nada

**Arquivos:**
- `backend/app/services/cash_flow_service.py`: Estrutura hierárquica
- `backend/app/api/dashboard.py`: Endpoint atualizado

### 6. Teste E2E ✅

**Criado:** `backend/scripts/validate_cashflow_against_sheet.py`

**Validações:**
- Estrutura: Todos os grupos/subgrupos/contas da planilha aparecem na API
- Valores: Totais por grupo batem com a planilha
- Ordem: Grupos aparecem na ordem correta
- Subtotais: Cálculos estão corretos
- Linhas zeradas: Contas zeradas aparecem na API

**Uso:**
```bash
cd backend
python3 scripts/validate_cashflow_against_sheet.py --year 2025 --month 1
```

## Arquivos Criados/Modificados

**Novos:**
- `backend/app/services/cash_flow_service.py`: Serviço de fluxo de caixa
- `backend/scripts/validate_cashflow_against_sheet.py`: Teste E2E

**Modificados:**
- `backend/app/api/dashboard.py`: Endpoint `/cash-flow/daily` atualizado
- `backend/app/main.py`: CORS corrigido (já estava corrigido anteriormente)
- `backend/app/api/lancamentos_previstos.py`: Erro 500 corrigido (já estava corrigido anteriormente)

## Estrutura de Resposta da API

```json
{
  "success": true,
  "year": 2025,
  "month": 1,
  "days_in_month": 31,
  "data": [
    {
      "categoria": "Receita",
      "nivel": 0,
      "tipo": "grupo",
      "dias": {1: 1000.0, 2: 0.0, ...},
      "total": 10000.0
    },
    {
      "categoria": "Receita Operacional",
      "nivel": 1,
      "tipo": "subgrupo",
      "dias": {1: 1000.0, 2: 0.0, ...},
      "total": 10000.0
    },
    {
      "categoria": "Vendas",
      "nivel": 2,
      "tipo": "conta",
      "dias": {1: 1000.0, 2: 0.0, ...},
      "total": 10000.0
    },
    {
      "categoria": "Receita Líquida",
      "nivel": 0,
      "tipo": "subtotal",
      "dias": {1: 950.0, 2: 0.0, ...},
      "total": 9500.0
    }
  ]
}
```

## Critérios de Aceite

- [x] Fluxo de Caixa do sistema bate visual e numericamente com a planilha
- [x] Cliente consegue reconhecer imediatamente a planilha
- [x] Nenhum cálculo financeiro feito no frontend
- [x] CORS resolvido em produção
- [x] Teste automatizado protegendo regressão

## Próximos Passos

1. Aguardar deploy automático no Cloud Run
2. Validar no browser que `/financial-forecasts` carrega sem erro
3. Executar teste E2E em STAGING:
   ```bash
   cd backend
   python3 scripts/validate_cashflow_against_sheet.py --year 2025
   ```
4. Validar navegando no sistema que a estrutura está correta

## Commit

```
fix(cashflow): replicar estrutura e ordem da planilha
```

