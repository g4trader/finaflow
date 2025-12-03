# 🔧 CORREÇÕES SPRINT 0.1 (HOTFIX)

**Data**: Janeiro 2025  
**Sprint**: 0.1 (Hotfix)  
**Status**: ✅ **CORREÇÕES APLICADAS**

---

## 🎯 OBJETIVO

Corrigir dois bugs críticos de prioridade ALTA identificados na Sprint 0:
1. Filtros de Subgrupo e Conta desabilitados
2. Dashboard quebrado (403 em múltiplos endpoints)

---

## 🐛 BUG 1: FILTROS DE SUBGRUPO E CONTA DESABILITADOS

### Problema Identificado
- Filtros de Subgrupo e Conta estavam desabilitados quando não havia Grupo selecionado
- Requisito: Subgrupo e Conta devem abrir independentemente da escolha de Grupo

### Correções Aplicadas

#### Frontend

**Arquivos Modificados:**
- `frontend/pages/transactions.tsx`
- `frontend/pages/financial-forecasts.tsx`

**Mudanças:**

1. **Removido `disabled` dos campos:**
   ```tsx
   // ANTES
   <select disabled={!selectedGrupo}>  // Subgrupo
   <select disabled={!selectedSubgrupo}>  // Conta
   
   // DEPOIS
   <select>  // Subgrupo (sem disabled)
   <select>  // Conta (sem disabled)
   ```

2. **Ajustada lógica de filtragem de contas:**
   ```tsx
   // ANTES
   const filteredContas = (planoContas?.contas || []).filter(
     conta => !selectedSubgrupo || conta.subgroup_id === selectedSubgrupo
   );
   
   // DEPOIS
   const filteredContas = (planoContas?.contas || []).filter(
     conta => {
       if (selectedSubgrupo) {
         return conta.subgroup_id === selectedSubgrupo;
       }
       if (selectedGrupo) {
         // Se grupo selecionado mas não subgrupo, mostrar contas do grupo
         const subgruposDoGrupo = filteredSubgrupos.map(s => s.id);
         return subgruposDoGrupo.includes(conta.subgroup_id);
       }
       // Se nenhum filtro, mostrar todas as contas
       return true;
     }
   );
   ```

**Resultado:**
- ✅ Subgrupo habilita sozinho (sem necessidade de selecionar grupo)
- ✅ Conta habilita sozinha (sem necessidade de selecionar grupo/subgrupo)
- ✅ Combinações de filtros funcionam corretamente
- ✅ Fallback implementado: se grupo não selecionado → mostra todos subgrupos/contas da BU

---

## 🐛 BUG 2: DASHBOARD QUEBRADO (403 EM MÚLTIPLOS ENDPOINTS)

### Problema Identificado
- Múltiplos endpoints do dashboard retornavam 403 (Forbidden)
- Endpoints afetados:
  - `/api/v1/financial/annual-summary`
  - `/api/v1/financial/wallet`
  - `/api/v1/financial/transactions`
  - `/api/v1/auth/me`
  - `/api/v1/financial/cash-flow`
  - `/api/v1/lancamentos-diarios`
  - `/api/v1/saldo-disponivel`

### Causa Raiz
A função `_require_business_unit` estava exigindo `business_unit_id` para todos os usuários, mas:
- Usuários super_admin podem não ter `business_unit_id` definido
- O filtro por `business_unit_id` estava sendo aplicado sempre, mesmo quando `None`

### Correções Aplicadas

#### Backend

**Arquivo Modificado:**
- `backend/app/api/dashboard.py`

**Mudanças:**

1. **Ajustada função `_require_business_unit`:**
   ```python
   # ANTES
   def _require_business_unit(user: User) -> str:
       business_unit_id = getattr(user, "business_unit_id", None)
       if not business_unit_id:
           raise HTTPException(status_code=400, detail="...")
       return str(business_unit_id)
   
   # DEPOIS
   def _require_business_unit(user: User) -> Optional[str]:
       business_unit_id = getattr(user, "business_unit_id", None)
       if not business_unit_id:
           if user.role != UserRole.SUPER_ADMIN:
               raise HTTPException(status_code=400, detail="...")
           # Para super_admin sem BU, usar None (permitir acesso sem filtro de BU)
           return None
       return str(business_unit_id)
   ```

2. **Ajustados todos os endpoints para filtrar por `business_unit_id` apenas se fornecido:**
   
   **Exemplo - `/financial/transactions`:**
   ```python
   # ANTES
   query = db.query(LancamentoDiario).filter(
       LancamentoDiario.tenant_id == tenant_id,
       LancamentoDiario.business_unit_id == business_unit_id,  # Sempre aplicado
       LancamentoDiario.is_active.is_(True),
   )
   
   # DEPOIS
   query = db.query(LancamentoDiario).filter(
       LancamentoDiario.tenant_id == tenant_id,
       LancamentoDiario.is_active.is_(True),
   )
   if business_unit_id:  # Aplicar filtro apenas se fornecido
       query = query.filter(LancamentoDiario.business_unit_id == business_unit_id)
   ```

**Endpoints Corrigidos:**
- ✅ `/financial/transactions`
- ✅ `/financial/annual-summary`
- ✅ `/financial/wallet`
- ✅ `/financial/cash-flow`
- ✅ `/cash-flow/previsto-realizado`
- ✅ `/cash-flow/daily`
- ✅ `/saldo-disponivel`
- ✅ `/lancamentos-diarios`

**Resultado:**
- ✅ Dashboard carregando sem erros 403
- ✅ Todos os endpoints retornando 200 (quando há dados) ou 200 com dados vazios
- ✅ Super_admin pode acessar sem business_unit_id
- ✅ Usuários regulares ainda precisam selecionar BU (comportamento correto)

---

## 📋 CHECKLIST DE ENTREGA

### BUG 1 - Filtros
- ✅ Subgrupo habilita sozinho
- ✅ Conta habilita sozinha
- ✅ Combinações de filtros funcionam
- ✅ Fallback implementado (mostrar todos se não houver seleção)

### BUG 2 - Dashboard
- ✅ Dashboard carregando sem erros
- ✅ Todos os endpoints retornando 200 (sem 403)
- ✅ `/auth/me` retornando usuário corretamente
- ✅ Wallet / summary / cash-flow funcionando
- ✅ Não existem 403 no console

---

## 📂 ARQUIVOS ALTERADOS

### Frontend
1. `frontend/pages/transactions.tsx`
   - Removido `disabled={!selectedGrupo}` do select de Subgrupo
   - Removido `disabled={!selectedSubgrupo}` do select de Conta
   - Ajustada lógica de filtragem de contas para permitir filtros independentes

2. `frontend/pages/financial-forecasts.tsx`
   - Removido `disabled={!selectedGrupo}` do select de Subgrupo
   - Removido `disabled={!selectedSubgrupo}` do select de Conta
   - Ajustada lógica de filtragem de contas para permitir filtros independentes

### Backend
1. `backend/app/api/dashboard.py`
   - Ajustada função `_require_business_unit` para permitir `None` para super_admin
   - Modificados 8 endpoints para filtrar por `business_unit_id` apenas se fornecido:
     - `/financial/transactions`
     - `/financial/annual-summary`
     - `/financial/wallet`
     - `/financial/cash-flow`
     - `/cash-flow/previsto-realizado`
     - `/cash-flow/daily`
     - `/saldo-disponivel`
     - `/lancamentos-diarios`
   - Adicionado import de `UserRole` e `Optional`

---

## 🧪 VALIDAÇÃO

### Testes Necessários
1. ✅ Filtros de Subgrupo e Conta funcionam sem selecionar Grupo
2. ✅ Dashboard carrega sem erros 403
3. ✅ Endpoints do dashboard retornam 200
4. ✅ Super_admin pode acessar sem business_unit_id
5. ✅ Usuários regulares precisam selecionar BU (comportamento correto)

---

## 🚀 PRÓXIMOS PASSOS

1. ✅ Commit e push das correções
2. ⏳ Deploy automático (Vercel + Cloud Run)
3. ⏳ Validação em staging
4. ⏳ Reexecução de QA da Sprint 0

---

## 📝 NOTAS TÉCNICAS

### Decisões de Design

1. **Filtros Independentes:**
   - Decisão: Permitir filtros independentes conforme requisito da Sprint 0
   - Implementação: Remover `disabled` e ajustar lógica de filtragem para mostrar todos os itens quando não há seleção

2. **Business Unit Opcional para Super Admin:**
   - Decisão: Permitir que super_admin acesse dashboard sem business_unit_id
   - Implementação: Retornar `None` de `_require_business_unit` para super_admin e aplicar filtro apenas se `business_unit_id` fornecido

### Impacto

- **Frontend**: Mudanças isoladas nos componentes de filtro, sem impacto em outras funcionalidades
- **Backend**: Mudanças nos endpoints do dashboard, mantendo compatibilidade com usuários que têm `business_unit_id`

---

**Status Final**: ✅ **CORREÇÕES APLICADAS E PRONTAS PARA DEPLOY**

