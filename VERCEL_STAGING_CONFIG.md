# ✅ Configuração Vercel Staging - Next.js

## 🎯 Configuração Correta

### Framework Preset
- **Framework**: `Next.js`
- **Preset**: `nextjs`

### Root Directory
- **Root Directory**: `frontend`
- Isso garante que a Vercel construa apenas a pasta do app Next.js, não o repositório inteiro

### Build Settings
- **Build Command**: `npm run build` (ou deixar default do Next.js)
- **Output Directory**: `.next` (default do Next.js)
- **Install Command**: `npm install` (default)
- **Development Command**: `next dev` (default)

### Environment Variables
- **NEXT_PUBLIC_API_URL**: `https://finaflow-backend-staging-642830139828.us-central1.run.app`

## 📝 Arquivo vercel.json

O arquivo `frontend/vercel.json` foi configurado com:

```json
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "installCommand": "npm install",
  "devCommand": "next dev"
}
```

## ⚠️ Importante

**O Root Directory deve ser configurado na interface da Vercel**, não no `vercel.json`:

1. Acesse: https://vercel.com/dashboard
2. Abra o projeto `finaflow-stg`
3. Vá em **Settings → General → Project Settings**
4. Configure **Root Directory** como: `frontend`
5. Configure **Framework Preset** como: `Next.js`

## 🚀 Deploy

Após configurar na interface da Vercel, faça um novo deploy:

```bash
git checkout staging
git commit --allow-empty -m "chore: trigger redeploy for staging frontend"
git push origin staging
```

## ✅ Validação

Após o deploy, validar:
- ✅ Aplicação carrega sem erro 500
- ✅ Nenhuma Serverless Function quebra na home
- ✅ App se comporta como produção (mesmo layout/telas)
- ✅ Conecta ao backend staging

