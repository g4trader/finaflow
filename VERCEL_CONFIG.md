# Configuração do Vercel para FinaFlow

## Variáveis de Ambiente Necessárias

Para que o frontend funcione corretamente no Vercel, você precisa configurar as seguintes variáveis de ambiente:

### 1. URL do Backend (Obrigatória)

**Nome:** `NEXT_PUBLIC_API_URL`  
**Valor:** `https://finaflow-backend-staging-556803510516.us-central1.run.app`  
**Descrição:** URL do backend Cloud Run no novo projeto GCP

### Como Configurar no Vercel

1. Acesse o [Dashboard do Vercel](https://vercel.com/dashboard)
2. Selecione o projeto `finaflow` (ou o nome do seu projeto)
3. Vá em **Settings** → **Environment Variables**
4. Adicione a variável:
   - **Key:** `NEXT_PUBLIC_API_URL`
   - **Value:** `https://finaflow-backend-staging-556803510516.us-central1.run.app`
   - **Environment:** Selecione todas (Production, Preview, Development)
5. Clique em **Save**
6. **Importante:** Após adicionar/modificar variáveis, você precisa fazer um novo deploy:
   - Vá em **Deployments**
   - Clique nos três pontos (...) do último deployment
   - Selecione **Redeploy**

### Verificação

Após configurar, você pode verificar se está funcionando:

1. Acesse a aplicação no Vercel
2. Abra o Console do navegador (F12)
3. Procure por logs que mostram a URL da API:
   ```
   🔧 [API Config] API Base URL: https://finaflow-backend-staging-556803510516.us-central1.run.app
   ```

### Fallback

Se a variável `NEXT_PUBLIC_API_URL` não estiver configurada, o código usará automaticamente a URL do novo backend como fallback. No entanto, é recomendado configurar explicitamente no Vercel para maior controle.

## URLs Atualizadas

- **Backend Staging:** `https://finaflow-backend-staging-556803510516.us-central1.run.app`
- **Projeto GCP:** `project-c6f9c72d-aca4-476d-82f`
- **Região:** `us-central1`

## Notas Importantes

- Variáveis que começam com `NEXT_PUBLIC_` são expostas ao cliente (browser)
- Após adicionar variáveis de ambiente, sempre faça um redeploy
- O frontend usa a variável `NEXT_PUBLIC_API_URL` em vários arquivos:
  - `frontend/services/api.ts`
  - `frontend/lib/api/finance.ts`
  - `frontend/pages/api/proxy-login.ts`
  - `frontend/pages/signup.tsx`
  - `frontend/e2e/dashboard-sheet-consistency.spec.ts`

