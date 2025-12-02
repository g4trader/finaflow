# ✅ Checklist - Criar Projeto Vercel Staging

## 🎯 Antes de Criar o Projeto

### ✅ Verificações Realizadas

- [x] `frontend/vercel.json` configurado para Next.js
- [x] `frontend/package.json` com scripts corretos
- [x] `frontend/next.config.js` sem configurações problemáticas
- [x] Build local passa sem erros
- [x] Código commitado na branch `staging`

## 📋 Passo a Passo para Criar o Projeto

### 1. Acessar Vercel Dashboard
- URL: https://vercel.com/dashboard
- Clique em "Add New Project"

### 2. Importar Repositório
- Selecione: `g4trader/finaflow`
- Ou conecte o repositório se ainda não estiver conectado

### 3. Configurar Projeto

**Nome do Projeto:**
```
finaflow-stg
```
ou
```
finaflow-staging
```

**Framework Preset:**
```
Next.js
```
⚠️ **IMPORTANTE**: Selecione Next.js, não FastAPI ou outro

**Root Directory:**
```
frontend
```
⚠️ **CRÍTICO**: Configure como `frontend` para que a Vercel construa apenas a pasta do Next.js

**Build Command:**
```
npm run build
```
(ou deixar default do Next.js)

**Output Directory:**
```
.next
```
(ou deixar default do Next.js)

**Install Command:**
```
npm install
```
(ou deixar default)

### 4. Configurar Branch

**Production Branch:**
```
staging
```

**Ou selecionar branch:**
```
staging
```

### 5. Variáveis de Ambiente ⚠️ OBRIGATÓRIAS

**Antes de fazer deploy, adicione estas variáveis:**

| Nome | Valor |
|------|-------|
| `NEXT_PUBLIC_API_URL` | `https://finaflow-backend-staging-642830139828.us-central1.run.app` |

**Como adicionar:**
1. Antes de clicar em "Deploy", clique em "Environment Variables"
2. Adicione `NEXT_PUBLIC_API_URL`
3. Valor: `https://finaflow-backend-staging-642830139828.us-central1.run.app`
4. Selecione: Production, Preview, Development
5. Salve

### 6. Deploy

1. Clique em "Deploy"
2. Aguarde o build completar
3. Anote a URL gerada

### 7. Validar

Após deploy, acesse a URL e verifique:
- ✅ Aplicação carrega sem erro 500
- ✅ Nenhuma Serverless Function quebra
- ✅ Layout aparece corretamente
- ✅ Conecta ao backend staging

## 🔍 Troubleshooting

### Se der erro de build:
1. Verificar se Root Directory está como `frontend`
2. Verificar se Framework Preset está como `Next.js`
3. Verificar logs do build na Vercel

### Se der erro 500:
1. Verificar se `NEXT_PUBLIC_API_URL` está configurada
2. Verificar logs das Serverless Functions
3. Verificar se o backend staging está acessível

## ✅ Checklist Final

- [ ] Projeto criado na Vercel
- [ ] Framework Preset = Next.js
- [ ] Root Directory = `frontend`
- [ ] Branch = `staging`
- [ ] `NEXT_PUBLIC_API_URL` configurada
- [ ] Deploy concluído sem erro
- [ ] URL staging acessível
- [ ] Aplicação carrega sem erro 500

