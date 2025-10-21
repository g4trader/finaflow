# 📊 ANÁLISE - MELHORIAS FLUXO DE CAIXA

**Data**: 21 de Outubro de 2025

---

## 🎯 OBJETIVOS

1. **Fluxo de Caixa Mensal**: Detalhamento completo com hierarquia da planilha
2. **UX - Expandir/Retrair**: Funcionalidade de colapsar grupos/subgrupos
3. **Contas Bancárias**: Gestão de contas, saldos e movimentações
4. **Caixa/Dinheiro**: Gestão de caixa físico
5. **Investimentos**: Gestão de aplicações financeiras

---

## 📋 ESTRUTURA DO FLUXO DE CAIXA MENSAL (Planilha)

### **Hierarquia Identificada**:

```
📁 RECEITA
   📂 Receita (Subgrupo)
      • Noiva
      • Serviços Buritis
      • Serviço Ivone
      • Diversos
   📂 Receita Financeira
      • Rendimentos de Aplicações Financeiras
      • Outras Receitas Financeiras
   📂 Deduções
      • Simples Nacional
      • Tributos parcelados
      • Devoluções
   🟩 (=) Receita Líquida

📁 CUSTOS
   📂 Custos com Serviços Prestados
      • Comissão sobre serviços-CSP
      • Serviços de terceiros-CSP
      • Compra de material para consumo-CSP
      • Manutenção Equipamentos
      • Outros custos com Serviços
      • Energia Elétrica
      • Água
   📂 Custos com Mão de Obra
      • Salário
      • Pró-Labore
      • Décimo terceiro
      • Férias
      • Rescisão
      • INSS
      • FGTS
      • Alimentação
      • Vale transporte
      • Treinamento e Desenvolvimento
      • Outras Custos com Mão de Obra Direta
      • Exames ocupacionais
   🟩 (=) Lucro Bruto

📁 DESPESAS OPERACIONAIS
   📂 Despesas Administrativas
      • 18 contas...
   📂 Despesas com Pessoal
      • 14 contas...
   📂 Despesas Comerciais
      • 9 contas...
   📂 Despesas Marketing
      • 6 contas...
   📂 Despesas Financeiras
      • 6 contas...
   🟩 (=) Lucro antes dos investimentos

📁 INVESTIMENTOS
   📂 Investimentos em Bens Materiais
      • 5 contas...
   📂 Outros Investimentos
   🟩 (=) Desembolso Total
   🟩 (=) LUCRO OPERACIONAL

📁 MOVIMENTAÇÕES NÃO OPERACIONAIS
   📂 Entradas não Operacionais
      • 4 contas...
   📂 Saídas não Operacionais
      • 5 contas...
   🟩 (=) Lucro Líquido de caixa mensal
   🟩 (=) Lucro líquido acumulado (Reservas)
   🟩 (=) Saldo do ano anterior
```

### **Colunas por Mês**:
- Previsto
- Realizado
- AH (Análise Horizontal - %)
- AV (Análise Vertical - %)

---

## 💰 SEÇÃO DE CONTAS BANCÁRIAS E CAIXA

### **Estrutura no Fluxo Diário** (Linhas 174-184):

```
📊 Verificação de saldo
   💳 CEF             | 483,84
   💳 SICOOB          | 12.630,76
   💰 Aplicação       | 0,00
   💵 Caixa/Dinheiro  | 0,00
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━
   💎 Saldo disponibilidades | 13.114,60
   
   ⚠️ Diferença de fluxo | 0,00
```

### **Campos Identificados**:
1. **Contas Bancárias**: Nome do banco + saldo
2. **Aplicações/Investimentos**: Valor
3. **Caixa/Dinheiro**: Valor em espécie
4. **Saldo Total**: Soma de tudo
5. **Diferença de Fluxo**: Validação (deve ser 0)

---

## 🗂️ MODELOS A CRIAR

### **1. ContaBancaria**
```python
- id: UUID
- tenant_id: UUID
- business_unit_id: UUID
- banco: String (ex: "CEF", "SICOOB", "Banco do Brasil")
- agencia: String (opcional)
- numero_conta: String (opcional)
- tipo: Enum (corrente, poupança, investimento)
- saldo_inicial: Decimal
- saldo_atual: Decimal (calculado)
- is_active: Boolean
- created_at: DateTime
- updated_at: DateTime
```

### **2. MovimentacaoBancaria**
```python
- id: UUID
- conta_bancaria_id: UUID
- tenant_id: UUID
- business_unit_id: UUID
- data_movimentacao: Date
- tipo: Enum (entrada, saida, transferencia)
- valor: Decimal
- descricao: String
- conta_destino_id: UUID (para transferências)
- lancamento_diario_id: UUID (vinculo)
- created_by: UUID
- created_at: DateTime
```

### **3. Caixa**
```python
- id: UUID
- tenant_id: UUID
- business_unit_id: UUID
- nome: String (ex: "Caixa Principal", "Caixa Filial")
- saldo_inicial: Decimal
- saldo_atual: Decimal (calculado)
- is_active: Boolean
- created_at: DateTime
```

### **4. MovimentacaoCaixa**
```python
- id: UUID
- caixa_id: UUID
- tenant_id: UUID
- business_unit_id: UUID
- data_movimentacao: Date
- tipo: Enum (entrada, saida)
- valor: Decimal
- descricao: String
- lancamento_diario_id: UUID (vinculo)
- created_by: UUID
- created_at: DateTime
```

### **5. Investimento**
```python
- id: UUID
- tenant_id: UUID
- business_unit_id: UUID
- tipo: Enum (renda_fixa, renda_variavel, fundo, cdb, lci, lca, tesouro, outro)
- instituicao: String
- descricao: String
- valor_aplicado: Decimal
- valor_atual: Decimal
- data_aplicacao: Date
- data_vencimento: Date (opcional)
- taxa_rendimento: Decimal (opcional)
- is_active: Boolean
- created_at: DateTime
```

---

## 🎨 UX - FUNCIONALIDADE DE EXPANDIR/RETRAIR

### **Requisitos**:
1. Cada grupo deve poder ser expandido/retraído
2. Cada subgrupo deve poder ser expandido/retraído
3. Estado deve ser persistido (localStorage)
4. Ícones visuais: ▼ (expandido) ▶ (retraído)
5. Ao retrair, mostrar apenas o totalizador do grupo

### **Implementação Frontend**:
- Hook `useState` para controlar estado de cada grupo/subgrupo
- `localStorage` para persistir preferências
- CSS transitions para animação suave
- Classes condicionais para aplicar indentação

---

## 📊 ENDPOINTS NECESSÁRIOS

### **Backend - Contas Bancárias**:
```
POST   /api/v1/contas-bancarias              - Criar conta
GET    /api/v1/contas-bancarias              - Listar contas
GET    /api/v1/contas-bancarias/{id}         - Detalhe
PUT    /api/v1/contas-bancarias/{id}         - Atualizar
DELETE /api/v1/contas-bancarias/{id}         - Remover
GET    /api/v1/contas-bancarias/{id}/saldo   - Saldo atual
GET    /api/v1/contas-bancarias/{id}/extrato - Extrato/movimentações
POST   /api/v1/contas-bancarias/transferencia - Transferência entre contas
```

### **Backend - Caixa**:
```
POST   /api/v1/caixa                         - Criar caixa
GET    /api/v1/caixa                         - Listar caixas
PUT    /api/v1/caixa/{id}                    - Atualizar
DELETE /api/v1/caixa/{id}                    - Remover
GET    /api/v1/caixa/{id}/saldo              - Saldo atual
```

### **Backend - Investimentos**:
```
POST   /api/v1/investimentos                 - Criar
GET    /api/v1/investimentos                 - Listar
PUT    /api/v1/investimentos/{id}            - Atualizar
DELETE /api/v1/investimentos/{id}            - Remover
GET    /api/v1/investimentos/resumo          - Resumo total
```

### **Backend - Fluxo de Caixa Melhorado**:
```
GET    /api/v1/cash-flow/mensal-detalhado    - FC mensal com hierarquia completa
GET    /api/v1/cash-flow/saldo-disponivel    - Contas + Caixa + Investimentos
```

---

## 🚀 PLANO DE IMPLEMENTAÇÃO

### **Fase 1: Modelos e Migração** ✅
1. Criar modelos SQLAlchemy
2. Criar migrations
3. Testar criação de tabelas

### **Fase 2: Backend - Contas Bancárias** ✅
1. CRUD completo
2. Endpoint de saldo
3. Endpoint de extrato
4. Endpoint de transferência

### **Fase 3: Backend - Caixa e Investimentos** ✅
1. CRUD de Caixa
2. CRUD de Investimentos
3. Endpoint de resumo financeiro

### **Fase 4: Backend - Fluxo de Caixa Melhorado** ✅
1. Endpoint mensal detalhado com hierarquia
2. Endpoint de saldo disponível (integração)

### **Fase 5: Frontend - CRUD** ✅
1. Páginas de Contas Bancárias
2. Páginas de Caixa
3. Páginas de Investimentos

### **Fase 6: Frontend - Fluxo de Caixa UX** ✅
1. Componente de expandir/retrair
2. Integração no FC Mensal
3. Integração no FC Diário
4. Seção de Saldo Disponível

### **Fase 7: Testes e Ajustes** ✅
1. Testes end-to-end
2. Ajustes de UX
3. Validação com planilha

---

## ✅ CHECKLIST DE VALIDAÇÃO

- [ ] FC Mensal mostra hierarquia completa (Grupo > Subgrupo > Conta)
- [ ] Grupos podem ser expandidos/retraídos
- [ ] Subgrupos podem ser expandidos/retraídos
- [ ] Estado de expand/collapse é persistido
- [ ] CRUD de Contas Bancárias funcional
- [ ] CRUD de Caixa funcional
- [ ] CRUD de Investimentos funcional
- [ ] Seção "Saldo Disponível" mostra: Bancos + Caixa + Investimentos
- [ ] Totalizadores calculados corretamente
- [ ] Interface igual à planilha

