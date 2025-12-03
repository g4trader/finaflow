# 🔧 Variáveis de Ambiente - Vercel Staging

## ⚠️ Variável OBRIGATÓRIA para FinaFlow Staging

### Adicionar na Vercel:

**Nome da Variável:**
```
NEXT_PUBLIC_API_URL
```

**Valor:**
```
https://finaflow-backend-staging-642830139828.us-central1.run.app
```

**Ambientes:**
- ✅ Production
- ✅ Preview  
- ✅ Development

## 📋 Passo a Passo

1. Na interface da Vercel (onde você está vendo as variáveis)
2. Clique no botão **"Add New"** ou **"Add Variable"**
3. Preencha:
   - **Key**: `NEXT_PUBLIC_API_URL`
   - **Value**: `https://finaflow-backend-staging-642830139828.us-central1.run.app`
   - **Environments**: Selecione todos (Production, Preview, Development)
4. Clique em **"Save"**

## 🔍 Verificação

Após adicionar, você deve ver na lista:
- `NEXT_PUBLIC_API_URL` com valor mascarado (dots)
- Scope: "All Environments"

## ⚠️ Observação

As variáveis que aparecem na imagem (`NEXT_PUBLIC_PROJECT_ENV`, `DIPAM_MOCK_ENABLED`, `NEXT_PUBLIC_DIPAM_ENV`) parecem ser de outro projeto. 

Se você quiser limpar essas variáveis antigas:
1. Clique nos três pontos (⋯) ao lado de cada variável
2. Selecione "Delete"
3. Confirme a exclusão

Mas o importante é **adicionar a variável `NEXT_PUBLIC_API_URL`** antes de fazer o deploy.

