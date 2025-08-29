#!/bin/bash

echo "🔧 Resolvendo problema de build do FinaFlow..."

# Navegar para o diretório do frontend
cd frontend

# Limpar cache do Next.js
echo "🧹 Limpando cache do Next.js..."
rm -rf .next
rm -rf node_modules/.cache

# Limpar cache do TypeScript
echo "🧹 Limpando cache do TypeScript..."
find . -name "*.tsbuildinfo" -delete

# Reinstalar dependências
echo "📦 Reinstalando dependências..."
npm install

# Fazer build
echo "🏗️ Fazendo build..."
npm run build

echo "✅ Build concluído!"
