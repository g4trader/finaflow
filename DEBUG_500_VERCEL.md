# 🔍 Debug do Erro 500 no Vercel

## Status das Correções Aplicadas

### ✅ Correções Implementadas:
1. **Removido `res.setTimeout`** - Não existe no Next.js API routes
2. **Implementado AbortController** - Para timeout de 25 segundos
3. **Validação de body e campos** - Validação completa antes de processar
4. **Try/finally para timeout** - Garantir limpeza mesmo em caso de erro
5. **Melhor tratamento de erros** - Diferenciação entre timeout e outros erros
6. **Validação de content-type** - Verificar se resposta é JSON antes de parsear
7. **URLs atualizadas** - Todas apontando para staging backend

### 📝 Arquivos Modificados:
- `frontend/pages/api/proxy-login.ts`
- `frontend/pages/api/proxy-select-bu.ts`
- `frontend/pages/api/proxy-business-units.ts`

## 🔍 Possíveis Causas do Erro 500

### 1. Backend Staging Não Responde
**Verificar:**
```bash
curl -X POST https://finaflow-backend-staging-642830139828.us-central1.run.app/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test&password=test"
```

### 2. Variável de Ambiente Não Configurada
**Verificar no Vercel:**
- Dashboard → Projeto → Settings → Environment Variables
- `NEXT_PUBLIC_API_URL` deve estar configurada
- Valor: `https://finaflow-backend-staging-642830139828.us-central1.run.app`

### 3. CORS Não Configurado no Backend
**Verificar no backend:**
- `CORS_ORIGINS` deve incluir o domínio do Vercel
- Ou estar configurado como `*` para staging

### 4. Timeout do Backend
**Verificar:**
- Backend pode estar demorando mais de 25 segundos
- Verificar logs do Cloud Run

## 🛠️ Próximos Passos para Debug

### 1. Verificar Logs do Vercel
- Dashboard → Projeto → Functions → Ver logs da função que está falhando
- Procurar por mensagens de erro específicas

### 2. Testar Backend Diretamente
```bash
# Testar health check
curl https://finaflow-backend-staging-642830139828.us-central1.run.app/health

# Testar login
curl -X POST https://finaflow-backend-staging-642830139828.us-central1.run.app/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin"
```

### 3. Verificar Variáveis de Ambiente
- Acessar Vercel Dashboard
- Verificar se `NEXT_PUBLIC_API_URL` está configurada
- Verificar se está no ambiente correto (Production/Preview/Development)

### 4. Adicionar Logs Detalhados
Adicionar mais logs nas API routes para identificar onde está falhando:
```typescript
console.log('🔍 [Proxy] Iniciando requisição');
console.log('🔍 [Proxy] BACKEND_URL:', BACKEND_URL);
console.log('🔍 [Proxy] Body:', req.body);
```

## 📊 Status Atual

- ✅ Código corrigido e commitado
- ✅ Timeout implementado corretamente
- ✅ Validações adicionadas
- ⚠️ Erro 500 ainda ocorrendo (necessário verificar logs)

## 🎯 Ação Imediata

1. **Verificar logs do Vercel** para identificar erro específico
2. **Testar backend staging** diretamente via curl
3. **Verificar variáveis de ambiente** no Vercel
4. **Verificar CORS** no backend staging

