#!/bin/bash
echo "🚀 Iniciando deploy do frontend..."

# Apenas commitar os arquivos essenciais
git add pages/transactions.tsx
git add components/layout/Layout.tsx
git commit -m "feat: Sistema espelhando planilha - Lançamentos com Grupo/Subgrupo/Conta"

# Push
git push origin main

echo "✅ Deploy iniciado!"
