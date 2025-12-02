# 🎯 Estratégia de Correção Completa do SSR

## Problema Identificado

**10 páginas importam `api` diretamente no top-level**, causando carregamento do módulo `api.ts` durante SSR no Vercel.

## Status Atual

✅ **Corrigidas:**
- `frontend/pages/caixa.tsx`
- `frontend/pages/investimentos.tsx`

⚠️ **Pendentes (8 páginas):**
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

2. **Adicionar `const api = await getApi();` no início de cada função async que usa `api`:**
   ```typescript
   // ANTES
   const fetchData = async () => {
     const response = await api.get('/endpoint');
   };
   
   // DEPOIS
   const fetchData = async () => {
     const api = await getApi();
     const response = await api.get('/endpoint');
   };
   ```

## Próximos Passos

1. Corrigir as 8 páginas restantes seguindo o padrão acima
2. Testar build local: `npm run build`
3. Commit e push
4. Aguardar deploy do Vercel
5. Validar que não há mais erro 500

## Configurações Vercel

- `vercel.json` simplificado para Next.js 13
- `next.config.js` limpo (removido experimental features)

