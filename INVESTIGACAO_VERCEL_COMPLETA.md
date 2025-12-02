# 🔍 Investigação Completa do Problema SSR no Vercel

## Problema Identificado

O erro 500 no Vercel é causado por **importações diretas de `api` no top-level** de 10 páginas, fazendo com que o módulo `api.ts` seja carregado durante SSR.

## Causa Raiz

Quando o Next.js faz SSR, ele tenta pré-renderizar todas as páginas. Se uma página importa `api` diretamente:
```typescript
import api from '../services/api';
```

O módulo `api.ts` é carregado, o que:
1. Inicializa o axios
2. Configura interceptors que usam `localStorage` e `window`
3. Causa erro 500 no servidor

## Solução Implementada

### 1. Criado `utils/api-client.ts`
Utilitário para importação dinâmica do `api`:
```typescript
export const getApi = async () => {
  if (typeof window === 'undefined') {
    throw new Error('API só pode ser usada no cliente');
  }
  const apiModule = await import('../services/api');
  return apiModule.default;
};
```

### 2. Corrigidas 2 páginas
- ✅ `frontend/pages/caixa.tsx`
- ✅ `frontend/pages/investimentos.tsx`

### 3. Configurações Vercel
- `vercel.json` simplificado para Next.js 13
- `next.config.js` limpo (removido experimental features)

## Páginas Pendentes (8)

Ainda precisam ser corrigidas:
1. `frontend/pages/transactions.tsx`
2. `frontend/pages/lancamentos-diarios.tsx`
3. `frontend/pages/financial-forecasts.tsx`
4. `frontend/pages/contas-bancarias.tsx`
5. `frontend/pages/cash-flow.tsx`
6. `frontend/pages/daily-cash-flow.tsx`
7. `frontend/pages/extrato-conta.tsx`
8. `frontend/pages/totalizadores-mensais.tsx`

## Padrão de Correção

Para cada página:

1. **Substituir import:**
   ```typescript
   // ANTES
   import api from '../services/api';
   
   // DEPOIS
   import { getApi } from '../utils/api-client';
   ```

2. **Adicionar `const api = await getApi();` no início de cada função async:**
   ```typescript
   const fetchData = async () => {
     const api = await getApi(); // ADICIONAR ESTA LINHA
     const response = await api.get('/endpoint');
   };
   ```

## Status

- ✅ Utilitário criado
- ✅ 2 páginas corrigidas
- ⚠️ 8 páginas pendentes
- ✅ Configurações Vercel atualizadas
- ✅ Commit realizado

## Próximos Passos

1. Corrigir as 8 páginas restantes
2. Testar build: `npm run build`
3. Commit e push
4. Aguardar deploy do Vercel
5. Validar que não há mais erro 500

