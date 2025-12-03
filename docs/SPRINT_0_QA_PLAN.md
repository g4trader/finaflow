# 📋 PLANO DE QA - SPRINT 0 - ESTABILIZAÇÃO

**Data**: Janeiro 2025  
**Ambiente**: STAGING  
**Responsável**: Dev Principal (QA Funcional UI)  
**Objetivo**: Validar todas as correções estruturais da Sprint 0

---

## 🎯 OBJETIVO DA SPRINT 0

Corrigir filtros, hierarquia contábil, módulos inoperantes, validações e inconsistências de token/BU, garantindo que o sistema esteja ESTÁVEL para iniciar o núcleo financeiro na Sprint 1.

---

## 📋 BLOCO A: FILTROS

### Módulos a Testar:
1. **Lançamentos Financeiros** (realizados)
2. **Lançamentos Previstos**
3. **Fluxo de Caixa Mensal**
4. **Fluxo de Caixa Diário**

### Testes por Módulo:

#### A.1 - Filtros Isolados
- [ ] Data inicial
- [ ] Data final
- [ ] Grupo
- [ ] Subgrupo (deve abrir mesmo sem selecionar grupo)
- [ ] Conta (deve abrir mesmo sem selecionar grupo)
- [ ] Tipo (receita/despesa)
- [ ] Status (previsto/realizado)
- [ ] Centro de custo (se disponível)

#### A.2 - Combinações de Filtros
- [ ] Grupo + Conta
- [ ] Subgrupo + Datas
- [ ] Conta + Datas
- [ ] Grupo + Subgrupo + Datas
- [ ] Todos os filtros combinados

#### A.3 - Validações
- [ ] Retorna 200 (sem erro de API)
- [ ] Dados exibidos fazem sentido
- [ ] Filtro não "gruda" entre telas (reset funciona)
- [ ] Filtros persistem durante navegação na mesma tela

---

## 📋 BLOCO B: HIERARQUIA CONTÁBIL

### Testes:
- [ ] Abrir tela que exibe o plano de contas / hierarquia
- [ ] Verificar ordem: grupo → subgrupo → conta
- [ ] Verificar se não há buracos estranhos
- [ ] Comparar com planilha-modelo (conferência visual)
- [ ] Verificar se todas as contas aparecem
- [ ] Verificar ordenação correta

---

## 📋 BLOCO C: LANÇAMENTOS (PREVISTOS E REALIZADOS)

### Para cada tipo (Previsto e Realizado):

#### C.1 - CRUD Completo
- [ ] Criar lançamento manual
- [ ] Verificar se aparece imediatamente na listagem
- [ ] Editar lançamento
- [ ] Verificar atualização na listagem
- [ ] Excluir lançamento
- [ ] Confirmar remoção da listagem

#### C.2 - Filtros e Validação
- [ ] Aplicar filtro por período
- [ ] Aplicar filtro por tipo
- [ ] Confirmar que lançamento aparece/desaparece conforme esperado
- [ ] Validar persistência após recarregar página

---

## 📋 BLOCO D: BUSINESS UNIT / TOKEN

### Testes:
- [ ] Fazer login
- [ ] Selecionar BU 1
- [ ] Interagir com módulos (registrar 1-2 lançamentos)
- [ ] Trocar para BU 2
- [ ] Conferir isolamento: dados da BU 1 não aparecem na BU 2
- [ ] Inspecionar token JWT no navegador
- [ ] Confirmar que `tenant_id` e `business_unit_id` mudam corretamente ao trocar de BU
- [ ] Verificar se não há vazamento de dados entre BUs

---

## 📋 BLOCO E: CAIXA FÍSICO E INVESTIMENTOS

### Caixa Físico:
- [ ] Acessar módulo
- [ ] Criar registro
- [ ] Editar registro
- [ ] Excluir registro
- [ ] Recarregar página e validar persistência
- [ ] Verificar se valores aparecem nos relatórios/fluxos onde deveriam

### Investimentos:
- [ ] Acessar módulo
- [ ] Criar registro
- [ ] Editar registro
- [ ] Excluir registro
- [ ] Recarregar página e validar persistência
- [ ] Verificar se valores aparecem nos relatórios/fluxos onde deveriam

---

## 📋 BLOCO F: FLUXOS DE CAIXA (MENSAL E DIÁRIO)

### Preparação:
- [ ] Gerar lançamentos de teste que permitam ver diferenças entre dias e meses

### Fluxo Mensal:
- [ ] Abrir Fluxo Mensal
- [ ] Conferir agrupamento por grupo/subgrupo/conta
- [ ] Verificar totais do mês
- [ ] Verificar acumulado
- [ ] Validar ordenação (grupo, subgrupo, conta)

### Fluxo Diário:
- [ ] Abrir Fluxo Diário
- [ ] Conferir valores por dia
- [ ] Verificar linha a linha coerente com lançamentos criados
- [ ] Validar ordenação (grupo, subgrupo, conta)

---

## 📋 BLOCO G: REGRESSÃO SPRINT 0

### Tour Completo:
- [ ] Login
- [ ] Seleção de BU
- [ ] Dashboard
- [ ] Lançamentos Financeiros
- [ ] Lançamentos Previstos
- [ ] Fluxo de Caixa Mensal
- [ ] Fluxo de Caixa Diário
- [ ] Caixa Físico
- [ ] Investimentos
- [ ] Contas Bancárias
- [ ] Totalizadores Mensais

### Validações:
- [ ] Sem erros de JavaScript no console
- [ ] Sem falhas de navegação
- [ ] Sem crashes
- [ ] UX fluida e responsiva

---

## ✅ CRITÉRIOS DE APROVAÇÃO

A Sprint 0 é **APROVADA** se:
- ✅ Todos os filtros funcionam isoladamente e combinados
- ✅ Hierarquia contábil está correta
- ✅ Caixa e Investimentos salvam corretamente
- ✅ Token com BU funciona em toda a aplicação
- ✅ Fluxos (mensal/diário) ordenados e íntegros
- ✅ Nenhum endpoint retorna erro silencioso
- ✅ Não há bugs críticos ou altos

A Sprint 0 é **REPROVADA** se:
- ❌ Há bugs críticos ou altos
- ❌ Filtros não funcionam corretamente
- ❌ CRUD de Caixa/Investimentos não persiste
- ❌ Há vazamento de dados entre BUs
- ❌ Fluxos de caixa com cálculos incorretos

---

## 📊 PRIORIZAÇÃO DE BUGS

- **CRÍTICO**: Bloqueia funcionalidade principal
- **ALTO**: Impacta funcionalidade importante
- **MÉDIO**: Impacta funcionalidade secundária
- **BAIXO**: Cosmético ou melhoria

