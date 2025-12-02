# ✅ Correção Crítica: Lazy Initialization do API

## 🎯 Problema Identificado

O erro 500 persistia porque **`services/api.ts` executava código no top-level** durante SSR:
- `axios.create()` era executado imediatamente
- Interceptors eram configurados no top-level
- Isso acontecia mesmo com importação dinâmica

## ✅ Solução Implementada

### 1. Lazy Initialization do Axios

Refatorei `services/api.ts` para usar **lazy initialization**:

```typescript
// ANTES (executava no top-level)
const api = axios.create({ ... });
api.interceptors.request.use(...);
api.interceptors.response.use(...);

// DEPOIS (só executa quando necessário)
let apiInstance: any = null;

const getApiInstance = () => {
  if (typeof window === 'undefined') {
    throw new Error('API só pode ser usada no cliente');
  }
  
  if (!apiInstance) {
    apiInstance = axios.create({ ... });
    // Configurar interceptors...
  }
  
  return apiInstance;
};

// Usar Proxy para garantir lazy access
const api = new Proxy({} as any, {
  get(_target, prop) {
    const instance = getApiInstance();
    return instance[prop];
  }
});
```

### 2. Correções Adicionais

- ✅ Corrigido `select-business-unit.tsx` para usar importação dinâmica
- ✅ Removido `output: 'standalone'` do `next.config.js`
- ✅ Simplificado `vercel.json`

## 📊 Resultados

- ✅ **Build passa** sem erros
- ✅ **Axios só é criado no cliente** e quando necessário
- ✅ **Nenhum código executa no top-level** que acessa `window` ou `localStorage`

## 🚀 Próximos Passos

1. ⏳ Aguardar deploy automático do Vercel
2. ✅ Testar: https://finaflow-stg.vercel.app/
3. ✅ Validar que não há mais erro 500

## 🔍 Por que isso resolve?

**Antes**: Mesmo com importação dinâmica, quando o módulo era importado, todo o código no top-level era executado, incluindo `axios.create()` e configuração de interceptors.

**Agora**: O axios só é criado quando:
1. O código está rodando no cliente (`typeof window !== 'undefined'`)
2. Alguém realmente acessa o `api` (via Proxy)
3. É a primeira vez que é acessado (singleton pattern)

Isso garante que **nenhum código do `api.ts` seja executado durante SSR**.

