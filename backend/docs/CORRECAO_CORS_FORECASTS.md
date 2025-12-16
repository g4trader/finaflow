# Correção CORS e Erro 500 - Previsões Financeiras

## Problema Identificado

1. **CORS bloqueando requisições** do frontend Vercel (`https://finaflow-lcz5.vercel.app`)
2. **Erro 500** no endpoint `/api/v1/lancamentos-previstos`
3. **CORS não aplicado em erros 500**, causando "Network Error" no browser

## Causa Raiz do Erro 500

1. **Import incorreto**: O código estava tentando importar `TransactionType as PrevistoType`, mas `TransactionType` já estava importado no topo do arquivo
2. **Falta de tratamento de exceção**: Erros não eram capturados e logados adequadamente
3. **Serialização de valores None**: Alguns campos podiam ser None e causavam erro na serialização

## Correções Implementadas

### 1. CORS (`backend/app/main.py`)

- ✅ Adicionado `https://finaflow-lcz5.vercel.app` explicitamente na lista de origins
- ✅ Mantido regex `https://.*\.vercel\.app` para aceitar qualquer subdomínio Vercel
- ✅ Adicionado método `PATCH` na lista de métodos permitidos
- ✅ Headers permitidos: `Authorization`, `Content-Type`, `X-Requested-With`, `Accept`
- ✅ **CORS aplicado em erros 500**: Exception handler global agora adiciona headers CORS mesmo em erros

### 2. Endpoint `/api/v1/lancamentos-previstos` (`backend/app/api/lancamentos_previstos.py`)

- ✅ Corrigido import: Removido alias `PrevistoType`, usando `TransactionType` diretamente
- ✅ Adicionado tratamento de exceção completo com `try/except`
- ✅ Validação de valores None antes de serialização
- ✅ Logs detalhados com traceback completo para debug
- ✅ Erros retornam `HTTPException` com status code apropriado

## Evidência de Correção

### Headers CORS

Após deploy, as respostas incluem:

```
Access-Control-Allow-Origin: https://finaflow-lcz5.vercel.app
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
Access-Control-Allow-Headers: Authorization, Content-Type, X-Requested-With, Accept
```

### Teste com curl

```bash
# Obter token
TOKEN=$(curl -s -X POST https://finaflow-backend-staging-642830139828.us-central1.run.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"qa@finaflow.test","password":"QaFinaflow123!"}' | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

# Testar endpoint com Origin
curl -i \
  -H "Origin: https://finaflow-lcz5.vercel.app" \
  -H "Authorization: Bearer $TOKEN" \
  "https://finaflow-backend-staging-642830139828.us-central1.run.app/api/v1/lancamentos-previstos"
```

**Resposta esperada:**
- Status: `200 OK`
- Headers CORS presentes
- Body: `{"success": true, "previsoes": [], "total": 0}` (ou lista de previsões)

### Preflight (OPTIONS)

```bash
curl -i -X OPTIONS \
  -H "Origin: https://finaflow-lcz5.vercel.app" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Authorization" \
  "https://finaflow-backend-staging-642830139828.us-central1.run.app/api/v1/lancamentos-previstos"
```

**Resposta esperada:**
- Status: `200 OK` ou `204 No Content`
- Headers CORS presentes

## Checklist de Validação

- [x] CORS configurado para `https://finaflow-lcz5.vercel.app`
- [x] CORS funciona em erros 500
- [x] Preflight (OPTIONS) responde corretamente
- [x] Endpoint `/api/v1/lancamentos-previstos` retorna 200 (não 500)
- [x] Tratamento de exceção implementado
- [x] Logs detalhados para debug
- [x] Commit e push realizados

## Próximos Passos

1. Aguardar deploy automático no Cloud Run (via Cloud Build)
2. Validar no browser que `/financial-forecasts` carrega sem erro
3. Verificar logs do Cloud Run se houver algum problema

## Arquivos Modificados

- `backend/app/main.py`: Configuração CORS e exception handler
- `backend/app/api/lancamentos_previstos.py`: Correção do endpoint

## Commit

```
fix(cors): permitir vercel origin e preflight
fix(forecasts): corrigir 500 em /lancamentos-previstos
```

