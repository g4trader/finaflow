# 📊 COMPARAÇÃO: PLANO DE CONTAS - PLANILHA vs SISTEMA

**Data**: 21 de Outubro de 2025

---

## 🔍 ANÁLISE

### **Planilha Google Sheets**
- **Total**: 96 contas marcadas como "Usar"
- **Estrutura**: Conta, Subgrupo, Grupo
- **Tenant**: LLM Lavanderia

### **Sistema Atual**
- **Total**: 120 contas
- **Tenant ID**: 40293540-a928-49da-8b1f-6eaf49a6662a
- **Business Unit ID**: 21de180d-8143-4ab3-9c6a-af16a00d13ac

---

## ❌ PROBLEMA IDENTIFICADO

O sistema tem **24 contas a mais** do que a planilha (120 vs 96).

**Possíveis causas**:
1. ✅ **Importação de dados antigos** - Havia um plano de contas de teste
2. ✅ **Contas de outro tenant misturadas** - Possível vazamento de dados
3. ✅ **Duplicatas na importação** - Contas criadas múltiplas vezes

---

## ✅ SOLUÇÃO

### **Opção 1: Limpar e Reimportar** (RECOMENDADO)

**Passos**:
1. Limpar lançamentos e previsões (já feito ✅)
2. Limpar plano de contas do tenant
3. Reimportar plano de contas da planilha
4. Reimportar lançamentos
5. Reimportar previsões

**Problema**: Foreign key constraints bloqueando

### **Opção 2: Investigar e Corrigir Manualmente**

Identificar as 24 contas extras e remover manualmente.

### **Opção 3: Aceitar e Usar** (TEMPORÁRIO)

Manter as 120 contas mas usar apenas as 96 da planilha.

---

## 🔧 FOREIGN KEY CONSTRAINTS ENCONTRADOS

### **Impedindo Limpeza**:
1. `business_unit_chart_accounts_chart_account_id_fkey`
2. `financial_transactions_chart_account_id_fkey`
3. `lancamentos_diarios_conta_id_fkey`
4. `lancamentos_previstos_conta_id_fkey`

### **Solução**:
Limpar na ordem correta:
1. ✅ business_unit_chart_accounts
2. ✅ lancamentos_diarios
3. ✅ lancamentos_previstos
4. ✅ financial_transactions (se existir)
5. ❌ chart_accounts ← Ainda com problemas

---

## 📋 PLANO DE CONTAS DA PLANILHA (96 CONTAS)

### **Receita** (4 contas)
1. Noiva
2. Serviços Buritis
3. Serviço Ivone
4. Diversos

### **Receita Financeira** (2 contas)
5. Rendimentos de Aplicações Financeiras
6. Outras Receitas Financeiras

### **Deduções** (3 contas)
7. Simples Nacional
8. Tributos parcelados
9. Devoluções

### **Custos com Serviços Prestados** (7 contas)
10. Comissão sobre serviços-CSP
11. Serviços de terceiros-CSP
12. Compra de material para consumo-CSP
13. Manutenção Equipamentos
14. Outros custos com Serviços
15. Energia Elétrica
16. Água

### **Custos com Mão de Obra** (12 contas)
17. Salário
18. Pró-Labore
19. Décimo terceiro
20. Férias
21. Rescisão
22. INSS
23. FGTS
24. Alimentação
25. Vale transporte
26. Treinamento e Desenvolvimento
27. Outras Custos com Mão de Obra Direta
28. Exames ocupacionais

### **Despesas Financeiras** (6 contas)
29-34. Tarifas, IOF, Juros, etc.

### **Despesas Administrativas** (23 contas)
35-57. Telefone, Energia, Aluguel, etc.

### **Despesas com Pessoal** (14 contas)
58-71. Salário-ADM, Pró-Labore-ADM, etc.

### **Despesas Comerciais** (7 contas)
72-78. Telefone, Celular, Viagens, etc.

### **Despesas Marketing** (6 contas)
79-84. Anúncios, Agências, Eventos, etc.

### **Investimentos** (5 contas)
85-89. Máquinas, Reformas, Veículos, etc.

### **Movimentações Não Operacionais** (7 contas)
90-96. Empréstimos, Aportes, Distribuição, etc.

---

## 🎯 PRÓXIMA AÇÃO

**RECOMENDAÇÃO**: 
1. Criar endpoint que limpa TODAS as tabelas relacionadas
2. Reimportar plano de contas correto (96 contas)
3. Reimportar lançamentos
4. Reimportar previsões

**Objetivo**: Ter exatamente 96 contas conforme a planilha!

