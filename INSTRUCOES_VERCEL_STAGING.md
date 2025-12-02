# 📋 Instruções para Configurar Vercel Staging

## 🎯 Objetivo

Ajustar o projeto STAGING na Vercel para usar Next.js com root directory `frontend`, alinhado com a configuração de produção.

## 📝 Passo a Passo

### 1. Acessar Dashboard da Vercel

1. Acesse: https://vercel.com/dashboard
2. Abra o projeto **finaflow-stg** (ou o nome que você criou para o frontend staging)

### 2. Configurar Framework Preset

1. Vá em **Settings → General → Project Settings → Framework Settings**
2. No campo **Framework Preset**, selecione **Next.js**
3. Se houver mensagem sobre diferenças com Production, ignore por enquanto

### 3. Configurar Root Directory

1. Ainda em **Project Settings**, procure pelo campo **Root Directory**
2. Configure como: `frontend`
3. Isso garante que a Vercel construa apenas a pasta do app Next.js

### 4. Verificar Build/Install/Dev Commands

Deixar no default do Next.js:
- **Build Command**: `npm run build` (ou default)
- **Output Directory**: `.next` (default do Next.js)
- **Install Command**: `npm install` (default)
- **Development Command**: `next dev` (default)

### 5. Conferir Variáveis de Ambiente

1. Vá em **Settings → Environment Variables**
2. Garantir que existe:
   - **NEXT_PUBLIC_API_URL**: `https://finaflow-backend-staging-642830139828.us-central1.run.app`
3. Se o projeto de produção tiver outras variáveis, replicar no staging

### 6. Salvar e Fazer Redeploy

1. Clique em **Save** nas áreas alteradas
2. Vá em **Deployments**
3. Clique em **Redeploy** no último deployment OU faça um novo push:

```bash
git checkout staging
git commit --allow-empty -m "chore: trigger redeploy for staging frontend"
git push origin staging
```

### 7. Validar o Staging

Após o deploy terminar, acesse:
- **URL**: https://finaflow-stg.vercel.app/

Confirmar que:
- ✅ Aplicação carrega sem tela de 500 da Vercel
- ✅ Nenhuma Serverless Function está quebrando na home
- ✅ O app está se comportando como produção (mesmo layout/telas)
- ✅ Conecta ao backend staging

## ✅ Checklist Final

- [ ] Framework Preset = Next.js
- [ ] Root Directory = `frontend`
- [ ] Build/Install/Dev Commands = default do Next.js
- [ ] NEXT_PUBLIC_API_URL configurado
- [ ] Deploy concluído sem erro
- [ ] URL staging acessível e funcional

## 📞 Próximos Passos

Quando estiver tudo OK:
1. Confirmar para o PM que:
   - Projeto STAGING está com Framework = Next.js
   - Root Directory = `frontend`
   - Deploy concluído sem erro
   - URL staging acessível
2. PM vai acionar o Codex para iniciar testes da Sprint 0

