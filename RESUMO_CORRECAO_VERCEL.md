# ✅ Resumo - Correção Branch Vercel Staging

## 📅 Data: Janeiro 2025

## 🔴 Problema Identificado

O projeto `finaflow-lcz5` na Vercel está configurado para fazer deploy da branch `main` em vez de `staging`, causando divergência entre backend e frontend.

## ✅ Ações Realizadas

1. ✅ **Documentação criada**:
   - `CORRECAO_VERCEL_STAGING.md` - Análise do problema
   - `INSTRUCOES_VERCEL_BRANCH.md` - Instruções passo a passo

2. ✅ **Commit vazio na branch staging**:
   - Disparado para trigger de redeploy (se Vercel já estiver configurado)

3. ✅ **Status atualizado**:
   - `docs/STATUS_STAGING_FINAL.md` - Documentado problema e solução

## 📋 Instruções para PM

### Opção 1: Corrigir Branch no Projeto Existente (Recomendado)

1. Acesse: https://vercel.com/dashboard
2. Projeto: `finaflow-lcz5`
3. Settings → Git
4. Alterar **Production Branch**: `main` → `staging`
5. Salvar
6. Aguardar redeploy automático

### Opção 2: Criar Novo Projeto

Se não for possível editar:

1. Criar novo projeto: `finaflow-staging`
2. Repo: `g4trader/finaflow`
3. Branch: `staging`
4. Root Directory: `frontend`
5. Framework: `Next.js`
6. Variáveis:
   - `NEXT_PUBLIC_API_URL=https://finaflow-backend-staging-642830139828.us-central1.run.app`
   - `ENVIRONMENT=staging`

## ✅ Validação Após Correção

1. Verificar no deployment log: "Cloning ... (Branch: staging)"
2. Testar login QA no frontend
3. Confirmar que frontend está conectado ao backend staging

## 🔗 URLs

- **Frontend Staging**: https://finaflow-lcz5.vercel.app/ (ou nova URL)
- **Backend Staging**: https://finaflow-backend-staging-642830139828.us-central1.run.app

## 📝 Status Atual

- ✅ **Backend staging**: Funcionando
- ✅ **Login QA via API**: Funcionando
- ⏳ **Frontend staging**: Aguardando correção de branch Vercel
- ⏳ **Login QA via frontend**: Aguardando correção de branch

---

**Próximo passo**: PM corrigir branch na Vercel e validar login QA no frontend.

