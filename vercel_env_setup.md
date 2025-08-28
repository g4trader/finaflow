# Configuração de Variáveis de Ambiente - Vercel

## 🔧 **Problema Atual**
O frontend está tentando acessar `http://localhost:8000` em vez da URL de produção do Google Cloud Run.

## 🛠️ **Solução: Configurar Variáveis de Ambiente no Vercel**

### **Passo 1: Acessar o Dashboard do Vercel**
1. Vá para: https://vercel.com/dashboard
2. Clique no projeto `finaflow`

### **Passo 2: Configurar Variável de Ambiente**
1. Clique em **Settings** (no menu superior)
2. Clique em **Environment Variables** (no menu lateral)
3. Clique em **Add New** ou edite a variável existente

### **Passo 3: Adicionar a Variável**
- **Name**: `NEXT_PUBLIC_API_URL`
- **Value**: `https://finaflow-backend-609095880025.us-central1.run.app`
- **Environment**: 
  - ✅ Production
  - ✅ Preview (opcional)
  - ❌ Development (deixe desmarcado para usar localhost em desenvolvimento)

### **Passo 4: Salvar e Fazer Deploy**
1. Clique em **Save**
2. Vá para **Deployments**
3. Clique em **Redeploy** no último deployment ou faça um novo commit

## 🔍 **Verificação**

Após o deploy, o frontend deve usar a URL correta do backend. Você pode verificar:

1. Abra o DevTools do navegador (F12)
2. Vá para a aba **Network**
3. Tente fazer login
4. Verifique se a requisição vai para: `https://finaflow-backend-609095880025.us-central1.run.app/auth/login`

## 📋 **URLs Importantes**

- **Frontend**: https://finaflow.vercel.app
- **Backend**: https://finaflow-backend-609095880025.us-central1.run.app
- **Documentação da API**: https://finaflow-backend-609095880025.us-central1.run.app/docs

## 🚀 **Próximos Passos**

1. Configure a variável de ambiente no Vercel
2. Faça o redeploy
3. Teste o login novamente
4. Crie o usuário super admin no BigQuery (se ainda não fez)
