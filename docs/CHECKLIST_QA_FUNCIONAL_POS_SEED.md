# ✅ Checklist de QA Funcional Pós-Seed

**Data**: 2025-12-05  
**Ambiente**: STAGING  
**Frontend**: https://finaflow-lcz5.vercel.app/  
**Backend**: https://finaflow-backend-staging-642830139828.us-central1.run.app/  
**Usuário QA**: `qa@finaflow.test` / `QaFinaflow123!`

---

## 📋 PRÉ-REQUISITOS

- [ ] Seed executado com sucesso no STAGING
- [ ] Dados carregados (plano de contas, lançamentos diários e previstos)
- [ ] Frontend acessível e funcionando
- [ ] Login QA funcionando

---

## 🧪 1. LANÇAMENTOS DIÁRIOS (CRUD Completo)

### 1.1 Criar Lançamento
- [ ] Acessar módulo "Lançamentos Diários"
- [ ] Criar novo lançamento com:
  - [ ] Data dentro de um dia já existente na planilha
  - [ ] Grupo/Subgrupo/Conta existentes
  - [ ] Valor válido
  - [ ] Observações
- [ ] **Validar**: Lançamento aparece imediatamente na tabela

### 1.2 Editar Lançamento
- [ ] Editar o lançamento criado:
  - [ ] Alterar valor
  - [ ] Alterar descrição/observações
- [ ] **Validar**: 
  - [ ] Atualização imediata na tabela
  - [ ] Valores corretos após edição

### 1.3 Excluir Lançamento
- [ ] Excluir o lançamento criado/editado
- [ ] **Validar**:
  - [ ] Lançamento desaparece da tabela
  - [ ] Não aparece após refresh da página

### 1.4 Persistência
- [ ] Após criar/editar, fazer refresh da página (F5)
- [ ] **Validar**: Dados persistem após refresh

### 1.5 Filtros
- [ ] **Filtros isolados**:
  - [ ] `start_date` - filtrar por data inicial
  - [ ] `end_date` - filtrar por data final
  - [ ] `group_id` - filtrar por grupo
  - [ ] `subgroup_id` - filtrar por subgrupo (sem grupo selecionado)
  - [ ] `account_id` - filtrar por conta (sem grupo/subgrupo selecionado)
  - [ ] `transaction_type` - filtrar por tipo (receita/despesa)
  - [ ] `status` - filtrar por status
  - [ ] `text_search` - buscar por texto nas observações
- [ ] **Combinações de filtros**:
  - [ ] Grupo + Conta
  - [ ] Subgrupo + datas
  - [ ] Conta + datas
  - [ ] Grupo + Subgrupo + datas
- [ ] **Validar via Network**:
  - [ ] Filtros enviados como query params
  - [ ] Backend retorna dados coerentes
  - [ ] Frontend exibe resultados corretos

---

## 🧪 2. LANÇAMENTOS PREVISTOS (CRUD + Hierarquia)

### 2.1 Criar Previsão
- [ ] Acessar módulo "Lançamentos Previstos"
- [ ] Criar nova previsão com:
  - [ ] Data futura
  - [ ] Grupo/Subgrupo/Conta existentes (hierarquia válida)
  - [ ] Valor válido
- [ ] **Validar**: Previsão aparece na tabela

### 2.2 Testar Hierarquia Inválida
- [ ] Tentar criar previsão com:
  - [ ] Conta de um subgrupo diferente do subgrupo selecionado
  - [ ] Subgrupo de um grupo diferente do grupo selecionado
- [ ] **Validar**: 
  - [ ] Backend recusa (HTTP 400)
  - [ ] Mensagem de erro clara
  - [ ] Previsão não é criada

### 2.3 Editar Previsão
- [ ] Editar previsão existente:
  - [ ] Alterar grupo/subgrupo/conta (mantendo hierarquia válida)
  - [ ] Alterar valor
- [ ] **Validar**: 
  - [ ] Atualização aceita
  - [ ] Dados corretos após edição

### 2.4 Excluir Previsão
- [ ] Excluir previsão criada/editada
- [ ] **Validar**: Previsão desaparece da tabela

### 2.5 Persistência e Filtros
- [ ] **Validar**:
  - [ ] Dados persistem após refresh
  - [ ] Filtros funcionam corretamente (mesmos do item 1.5)

---

## 🧪 3. FILTROS (Backend + Frontend)

### 3.1 Filtros Isolados
- [ ] `start_date` - funciona isoladamente
- [ ] `end_date` - funciona isoladamente
- [ ] `group_id` - funciona isoladamente
- [ ] `subgroup_id` - funciona isoladamente (sem grupo)
- [ ] `account_id` - funciona isoladamente (sem grupo/subgrupo)
- [ ] `transaction_type` - funciona isoladamente
- [ ] `status` - funciona isoladamente
- [ ] `text_search` - funciona isoladamente

### 3.2 Combinações de Filtros
- [ ] Grupo + Conta
- [ ] Subgrupo + datas
- [ ] Conta + datas
- [ ] Grupo + Subgrupo + datas
- [ ] Múltiplos filtros simultâneos

### 3.3 Validação via Network
- [ ] Abrir DevTools → Network
- [ ] Aplicar filtros
- [ ] **Validar**:
  - [ ] Filtros enviados como query params na URL
  - [ ] Backend retorna HTTP 200
  - [ ] Resposta contém dados coerentes
  - [ ] Frontend exibe resultados corretos

---

## 🧪 4. FLUXO DE CAIXA MENSAL E DIÁRIO

### 4.1 Fluxo de Caixa Mensal
- [ ] Acessar "Fluxo de Caixa Mensal"
- [ ] **Validar**:
  - [ ] Pelo menos 2 meses distintos exibidos
  - [ ] Totais exibidos batem com amostras da planilha
  - [ ] Ordenação correta: grupo → subgrupo → conta
  - [ ] Valores coerentes com lançamentos seedados

### 4.2 Fluxo de Caixa Diário
- [ ] Acessar "Fluxo de Caixa Diário"
- [ ] **Validar**:
  - [ ] Pelo menos 3 dias em sequência exibidos
  - [ ] Totais exibidos batem com amostras da planilha
  - [ ] Ordenação correta: grupo → subgrupo → conta
  - [ ] Valores coerentes com lançamentos seedados

### 4.3 Comparação com Planilha
- [ ] Selecionar amostra de dados da planilha original
- [ ] Comparar com valores exibidos no sistema
- [ ] **Validar**: Valores batem (ou diferenças explicáveis)

---

## 🧪 5. DASHBOARD

### 5.1 Cards e Gráficos
- [ ] Acessar Dashboard
- [ ] **Validar cards/gráficos**:
  - [ ] `/financial/wallet` - valores exibidos
  - [ ] `/financial/annual-summary` - resumo anual
  - [ ] `/financial/transactions` - transações recentes
  - [ ] `/cash-flow/*` - fluxo de caixa
  - [ ] `/saldo-disponivel` - saldo disponível

### 5.2 Coerência de Dados
- [ ] **Validar**:
  - [ ] Valores exibidos são coerentes com lançamentos seedados
  - [ ] Não há valores zerados quando deveria haver dados
  - [ ] Gráficos renderizam corretamente
  - [ ] Cards atualizam ao criar/editar lançamentos

---

## 🧪 6. PLANO DE CONTAS

### 6.1 Hierarquia
- [ ] Acessar tela de Plano de Contas
- [ ] **Validar**:
  - [ ] Ordenação: grupo → subgrupo → conta
  - [ ] Todos os grupos da planilha presentes
  - [ ] Todos os subgrupos presentes
  - [ ] Todas as contas presentes
  - [ ] Hierarquia correta (conta pertence ao subgrupo, subgrupo pertence ao grupo)

### 6.2 Visualização
- [ ] **Validar**:
  - [ ] Descrições completas (sem truncamento)
  - [ ] Códigos gerados corretamente
  - [ ] Tipos de conta corretos (receita/despesa/custo)

---

## 📊 RESUMO DE VALIDAÇÃO

### Status por Módulo

- [ ] **Lançamentos Diários**: ✅ APROVADO / ❌ REPROVADO
- [ ] **Lançamentos Previstos**: ✅ APROVADO / ❌ REPROVADO
- [ ] **Filtros**: ✅ APROVADO / ❌ REPROVADO
- [ ] **Fluxo de Caixa Mensal**: ✅ APROVADO / ❌ REPROVADO
- [ ] **Fluxo de Caixa Diário**: ✅ APROVADO / ❌ REPROVADO
- [ ] **Dashboard**: ✅ APROVADO / ❌ REPROVADO
- [ ] **Plano de Contas**: ✅ APROVADO / ❌ REPROVADO

### Bugs Encontrados

| Prioridade | Módulo | Descrição | Status |
|------------|--------|-----------|--------|
| ALTA | | | |
| MÉDIA | | | |
| BAIXA | | | |

### Status Final

- [ ] **SPRINT 1 - QA Funcional Pós-Seed**: ✅ APROVADO / ❌ REPROVADO

---

## 📝 OBSERVAÇÕES

_Adicionar observações adicionais, screenshots, logs relevantes, etc._

---

**Data de Execução**: _______________  
**Executado por**: _______________  
**Ambiente**: STAGING

