#!/bin/bash
# Script para corrigir todas as importações diretas de api para dinâmicas

PAGES=(
  "frontend/pages/totalizadores-mensais.tsx"
  "frontend/pages/extrato-conta.tsx"
  "frontend/pages/financial-forecasts.tsx"
  "frontend/pages/transactions.tsx"
  "frontend/pages/contas-bancarias.tsx"
  "frontend/pages/investimentos.tsx"
  "frontend/pages/daily-cash-flow.tsx"
  "frontend/pages/cash-flow.tsx"
  "frontend/pages/lancamentos-diarios.tsx"
)

for page in "${PAGES[@]}"; do
  if [ -f "$page" ]; then
    echo "Corrigindo $page..."
    # Substituir import
    sed -i '' "s|import api from '../services/api';|import { getApi } from '../utils/api-client';|g" "$page"
    # Adicionar await getApi() antes de cada uso de api
    # Isso precisa ser feito manualmente para cada arquivo
  fi
done

echo "Importações corrigidas. Agora é necessário adicionar 'const api = await getApi();' antes de cada uso de api em cada arquivo."

