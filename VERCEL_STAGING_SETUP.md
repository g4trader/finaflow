# 🚀 CONFIGURAÇÃO FRONTEND STAGING - VERCEL

## ✅ BACKEND STAGING PRONTO

**URL do Backend Staging:**
```
https://finaflow-backend-staging-642830139828.us-central1.run.app
```

**Health Check:**
```
https://finaflow-backend-staging-642830139828.us-central1.run.app/health
```

**API Docs:**
```
https://finaflow-backend-staging-642830139828.us-central1.run.app/docs
```

---

## 📋 PASSOS PARA CRIAR FRONTEND STAGING NA VERCEL

### 1. Acessar Vercel Dashboard
https://vercel.com/dashboard

### 2. Criar Novo Projeto
- Clique em "Add New Project"
- Importe o repositório: `g4trader/finaflow`
- Configure:
  - **Project Name**: `finaflow-staging`
  - **Root Directory**: `frontend`
  - **Framework Preset**: Next.js
  - **Build Command**: `npm run build` (ou deixar padrão)
  - **Output Directory**: `.next` (ou deixar padrão)
  - **Install Command**: `npm install`

### 3. Configurar Branch
- Selecione a branch: `staging`
- Deixe "Production Branch" como `staging`

### 4. Variáveis de Ambiente OBRIGATÓRIAS

Adicione estas variáveis no projeto Vercel:

| Nome | Valor |
|------|-------|
| `NEXT_PUBLIC_API_URL` | `https://finaflow-backend-staging-642830139828.us-central1.run.app` |
| `ENVIRONMENT` | `staging` |

**Como adicionar:**
1. No projeto Vercel, vá em "Settings" > "Environment Variables"
2. Adicione cada variável
3. Selecione "Production", "Preview" e "Development"
4. Salve

### 5. Deploy
- Clique em "Deploy"
- Aguarde o build completar
- Anote a URL gerada (será algo como `https://finaflow-staging-xxxxx.vercel.app`)

---

## 🔗 LINKS FINAIS

Após deploy do frontend, você terá:

**Frontend Staging:**
```
https://finaflow-staging-XXXXX.vercel.app
```

**Backend Staging:**
```
https://finaflow-backend-staging-642830139828.us-central1.run.app
```

---

## ✅ CHECKLIST

- [x] Backend staging deployado
- [x] Health check funcionando
- [x] Branch staging criada
- [ ] Frontend staging criado na Vercel
- [ ] Variáveis de ambiente configuradas
- [ ] Deploy do frontend concluído
- [ ] Testes básicos realizados

---

**Última atualização**: Janeiro 2025

