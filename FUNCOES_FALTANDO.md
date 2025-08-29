# 📋 Funções Faltando no api.ts

## 🔍 Análise das Importações

### Páginas que importam do api.ts:
1. **accounts.tsx**
   - getAccounts ✅
   - createAccount ✅
   - updateAccount ✅
   - deleteAccount ✅
   - getSubgroups ✅

2. **dashboard.tsx**
   - getCashFlow ✅
   - getTransactions ✅

3. **forecast.tsx**
   - getForecasts ✅ (já adicionada)
   - createForecast ✅ (já adicionada)
   - updateForecast ✅ (já adicionada)
   - deleteForecast ✅ (já adicionada)
   - getAccounts ✅

4. **groups.tsx**
   - getGroups ❌ (FALTANDO)
   - createGroup ❌ (FALTANDO)
   - updateGroup ❌ (FALTANDO)
   - deleteGroup ❌ (FALTANDO)

5. **import-csv.tsx**
   - importCsv ❌ (FALTANDO)

6. **reports.tsx**
   - getCashFlowReport ❌ (FALTANDO)

7. **settings.tsx**
   - updateUser ❌ (FALTANDO)
   - updateTenant ❌ (FALTANDO)

8. **subgroups.tsx**
   - getSubgroups ✅
   - createSubgroup ❌ (FALTANDO)
   - updateSubgroup ❌ (FALTANDO)
   - deleteSubgroup ❌ (FALTANDO)
   - getGroups ❌ (FALTANDO)

9. **transactions.tsx**
   - getTransactions ✅
   - createTransaction ✅
   - updateTransaction ❌ (FALTANDO)
   - deleteTransaction ❌ (FALTANDO)

## ❌ Funções Faltando:

### Grupos
- getGroups
- createGroup
- updateGroup
- deleteGroup

### Subgrupos
- createSubgroup
- updateSubgroup
- deleteSubgroup

### Transações
- updateTransaction
- deleteTransaction

### Importação
- importCsv

### Relatórios
- getCashFlowReport

### Usuários/Tenants
- updateUser
- updateTenant

## ✅ Próximos Passos:
1. Adicionar todas as funções faltantes ao api.ts
2. Testar build
3. Fazer deploy
