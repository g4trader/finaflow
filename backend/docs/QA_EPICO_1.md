# QA Funcional - Épico 1: Saldo Acumulado Confiável

## Objetivo

Garantir que todas as funcionalidades do Épico 1 estão funcionando corretamente em STAGING.

## Pré-requisitos

1. Migration executada: `dashboard_validation_status` criada
2. Backend rodando em STAGING
3. Frontend acessível

---

## 1. Executar Seed + Validação

### Comando

```bash
cd ~/finaflow/backend
./scripts/run_seed_and_validate.sh --year 2025
echo $?
```

### Resultado Esperado

```
✅ Seed + validação concluídos sem mismatches.
Exit code: 0
```

### Verificações

- [ ] Seed executou sem erros
- [ ] Validação executou sem erros
- [ ] Nenhum mismatch encontrado
- [ ] Exit code = 0

---

## 2. Verificar API `/api/v1/financial/annual-summary`

### Request

```bash
curl -X GET "https://finaflow-backend-staging-642830139828.us-central1.run.app/api/v1/financial/annual-summary?year=2025" \
  -H "Authorization: Bearer <token>"
```

### Verificações

#### 2.1. Estrutura Básica

- [ ] Response contém `year: 2025`
- [ ] Response contém `totals` com: `revenue`, `expense`, `cost`, `balance`
- [ ] Response contém `monthly` array com 12 elementos

#### 2.2. Campos por Mês

Para cada mês em `monthly`, verificar:

- [ ] `month`: número de 1 a 12
- [ ] `revenue`: número (pode ser 0)
- [ ] `expense`: número (pode ser 0)
- [ ] `cost`: número (pode ser 0)
- [ ] `balance`: número (receita - despesa - custo)
- [ ] `accumulated_balance`: número (soma progressiva)

#### 2.3. Metadata Explicativa

- [ ] `metadata.saldo_formula`: "receita - despesa - custo"
- [ ] `metadata.saldo_acumulado_formula`: "soma progressiva dos saldos mensais"
- [ ] `metadata.saldo_acumulado_explanation`: string explicativa
- [ ] `metadata.calculation_precision`: "Decimal (precisão absoluta)"
- [ ] `metadata.empty_months_behavior`: string explicativa

#### 2.4. Validação de Cálculo

Verificar manualmente para Janeiro, Junho e Dezembro:

- [ ] Janeiro: `balance = revenue - expense - cost`
- [ ] Janeiro: `accumulated_balance = balance` (primeiro mês)
- [ ] Junho: `accumulated_balance = accumulated_balance[maio] + balance[junho]`
- [ ] Dezembro: `accumulated_balance = accumulated_balance[novembro] + balance[dezembro]`

---

## 3. Verificar API `/api/v1/system/validation-status`

### Request

```bash
curl -X GET "https://finaflow-backend-staging-642830139828.us-central1.run.app/api/v1/system/validation-status?year=2025" \
  -H "Authorization: Bearer <token>"
```

### Verificações

- [ ] Response contém `status: "SUCCESS"`
- [ ] Response contém `year: 2025`
- [ ] Response contém `last_validation_at`: data/hora ISO
- [ ] `last_validation_at` é compatível com a última execução da validação
- [ ] `validation_details` contém estatísticas (se disponível)

---

## 4. Verificar Frontend

### 4.1. Tabela de Resumo Mensal

Acessar: Dashboard → Tabela "Resumo Mensal"

#### Verificações Visuais

- [ ] Tabela exibe coluna "Saldo Mensal"
- [ ] Tabela exibe coluna "Saldo Acumulado"
- [ ] Saldo positivo: cor verde
- [ ] Saldo negativo: cor vermelha
- [ ] Saldo zero: cor neutra (cinza/preto)
- [ ] Saldo Acumulado tem background diferenciado

#### Verificações de Dados

- [ ] Valores exibidos batem com a API
- [ ] Formatação de moeda brasileira (R$)
- [ ] 12 meses exibidos (Janeiro a Dezembro)

### 4.2. Tooltip Explicativo

- [ ] Ícone de informação visível no cabeçalho da tabela
- [ ] Ao passar o mouse, tooltip aparece
- [ ] Tooltip mostra `saldo_formula`
- [ ] Tooltip mostra `saldo_acumulado_formula`
- [ ] Tooltip mostra explicação completa

### 4.3. Badge de Validação

- [ ] Badge visível no header do dashboard
- [ ] Badge mostra status "SUCCESS" (verde)
- [ ] Badge mostra data da última validação
- [ ] Data é formatada em português (dd/mm/yyyy hh:mm)

---

## 5. Testes de Casos Edge

### 5.1. Meses Vazios

- [ ] Mês sem lançamentos: `balance = 0`
- [ ] Mês sem lançamentos: `accumulated_balance` se propaga (mantém valor anterior)

### 5.2. Valores Negativos

- [ ] Saldo negativo exibido em vermelho
- [ ] Saldo acumulado negativo exibido em vermelho
- [ ] Cálculo correto mesmo com valores negativos

### 5.3. Virada de Saldo

- [ ] Saldo positivo → negativo: cores mudam corretamente
- [ ] Saldo negativo → positivo: cores mudam corretamente

---

## Checklist Final

- [ ] Seed + validação executam sem erro
- [ ] API `/annual-summary` retorna todos os campos corretamente
- [ ] API `/annual-summary` retorna metadata explicativa
- [ ] API `/validation-status` retorna status SUCCESS
- [ ] Frontend exibe saldo acumulado corretamente
- [ ] Frontend não recalcula nada (usa dados da API)
- [ ] Cores aplicadas corretamente (verde/vermelho)
- [ ] Tooltip explicativo funciona
- [ ] Badge de validação visível e correto
- [ ] Comparação manual Janeiro/Junho/Dezembro confere

---

## Resultado Esperado

✅ **Épico 1 = DONE de verdade**

Todos os itens acima devem estar funcionando corretamente. Se algum item falhar, documentar o erro e corrigir antes de considerar o épico completo.

