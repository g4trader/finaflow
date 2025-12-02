# 🔴 PROBLEMA SSR IDENTIFICADO

## Causa Raiz

**10 páginas ainda importam `api` diretamente no top-level**, causando carregamento do módulo `api.ts` durante SSR:

1. `frontend/pages/caixa.tsx` ✅ CORRIGIDO
2. `frontend/pages/investimentos.tsx` ⚠️ PENDENTE
3. `frontend/pages/transactions.tsx` ⚠️ PENDENTE
4. `frontend/pages/lancamentos-diarios.tsx` ⚠️ PENDENTE
5. `frontend/pages/financial-forecasts.tsx` ⚠️ PENDENTE
6. `frontend/pages/contas-bancarias.tsx` ⚠️ PENDENTE
7. `frontend/pages/cash-flow.tsx` ⚠️ PENDENTE
8. `frontend/pages/daily-cash-flow.tsx` ⚠️ PENDENTE
9. `frontend/pages/extrato-conta.tsx` ⚠️ PENDENTE
10. `frontend/pages/totalizadores-mensais.tsx` ⚠️ PENDENTE

## Solução

Cada página precisa:
1. Substituir `import api from '../services/api'` por `import { getApi } from '../utils/api-client'`
2. Adicionar `const api = await getApi();` no início de cada função async que usa `api`

## Configurações Vercel

- `vercel.json` atualizado para Next.js 13
- `next.config.js` atualizado (removido serverActions experimental)

