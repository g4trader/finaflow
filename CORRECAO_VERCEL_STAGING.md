# 🔧 Correção Vercel Staging - Branch Config

## 📅 Data: Janeiro 2025

## 🔴 Problema Identificado

O projeto `finaflow-lcz5` na Vercel está configurado para fazer deploy da branch `main` em vez da branch `staging`. Isso causa divergência entre backend e frontend.

## ✅ Solução

### Opção 1: Corrigir Branch no Projeto Existente (Recomendado)

1. Acessar Vercel Dashboard:
   - https://vercel.com/dashboard
   - Projeto: `finaflow-lcz5`
   - Settings → Git

2. Alterar Production Branch:
   - De: `main`
   - Para: `staging`

3. Salvar e aguardar redeploy automático

### Opção 2: Criar Novo Projeto (Se não for possível editar)

1. Remover projeto `finaflow-lcz5` (opcional)

2. Criar novo projeto:
   - Nome: `finaflow-staging`
   - Repo: `g4trader/finaflow`
   - Branch: `staging`
   - Root Directory: `frontend`
   - Framework: `Next.js`

3. Variáveis de Ambiente:
   ```
   NEXT_PUBLIC_API_URL=https://finaflow-backend-staging-642830139828.us-central1.run.app
   ENVIRONMENT=staging
   ```

4. Deploy automático: Habilitado

## 📋 Checklist

- [ ] Branch configurada para `staging`
- [ ] Root Directory: `frontend`
- [ ] Framework: `Next.js`
- [ ] Variáveis de ambiente configuradas
- [ ] Deploy concluído usando branch staging
- [ ] URL funcionando corretamente

## 🔗 URLs

- **Frontend Staging**: https://finaflow-lcz5.vercel.app/ (ou nova URL se criar novo projeto)
- **Backend Staging**: https://finaflow-backend-staging-642830139828.us-central1.run.app

## ⚠️ Importante

Após corrigir a branch, o frontend staging estará sincronizado com o backend staging e o login QA deve funcionar corretamente.

