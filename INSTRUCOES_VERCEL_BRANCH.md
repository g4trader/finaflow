# 📋 Instruções para Corrigir Branch Vercel Staging

## 🎯 Objetivo

Configurar o projeto Vercel `finaflow-lcz5` para usar a branch `staging` em vez de `main`.

## 🔧 Passo a Passo

### 1. Acessar Configurações do Projeto

1. Acesse: https://vercel.com/dashboard
2. Clique no projeto: **finaflow-lcz5**
3. Vá em: **Settings** → **Git**

### 2. Alterar Production Branch

1. Localize a seção **"Connected Git Repository"**
2. Encontre o campo **"Production Branch"**
3. Se estiver configurado como `main`, altere para: **`staging`**
4. Clique em **Save**

### 3. Verificar Configuração

Após salvar, confirme que aparece:
- **Connected Git Branch**: `staging`
- **Production Branch**: `staging`

### 4. Disparar Redeploy

1. Vá em: **Deployments**
2. Clique em **"Redeploy"** no último deployment
3. OU faça um commit vazio na branch staging:
   ```bash
   git checkout staging
   git commit --allow-empty -m "chore: trigger redeploy for staging"
   git push origin staging
   ```

### 5. Validar Deploy

No log do deployment, confirme:
- **Cloning ... (Branch: staging)**
- Build concluído com sucesso
- URL funcionando

## 🔄 Alternativa: Criar Novo Projeto

Se não for possível editar o projeto existente:

### Passo 1: Criar Novo Projeto

1. Vercel Dashboard → **Add New Project**
2. Importar repositório: `g4trader/finaflow`
3. Configurar:
   - **Project Name**: `finaflow-staging`
   - **Framework Preset**: `Next.js`
   - **Root Directory**: `frontend`
   - **Production Branch**: `staging`

### Passo 2: Configurar Variáveis

Em **Settings** → **Environment Variables**, adicionar:

```
NEXT_PUBLIC_API_URL=https://finaflow-backend-staging-642830139828.us-central1.run.app
ENVIRONMENT=staging
```

### Passo 3: Deploy

1. Clique em **Deploy**
2. Aguarde conclusão
3. Anote a nova URL

## ✅ Validação Final

Após correção:

1. ✅ Branch configurada para `staging`
2. ✅ Deploy usando código da branch staging
3. ✅ Frontend conectado ao backend staging
4. ✅ Login QA funcionando

## 🔗 URLs

- **Frontend Staging**: https://finaflow-lcz5.vercel.app/ (ou nova URL)
- **Backend Staging**: https://finaflow-backend-staging-642830139828.us-central1.run.app

