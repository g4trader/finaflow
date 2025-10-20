#!/bin/bash

echo "🚀 Fazendo deploy do frontend com correções..."
echo ""

cd /Users/lucianoterres/Documents/GitHub/finaflow

# Deploy no Vercel
vercel --prod --yes

echo ""
echo "✅ Deploy concluído!"
echo ""
echo "🔗 Teste em: https://finaflow.vercel.app/login"
echo ""
echo "📋 Correções aplicadas:"
echo "   ✅ Token check melhorado"
echo "   ✅ Delay de 100ms adicionado antes do redirect"
echo "   ✅ Logs detalhados para debug"
echo ""
echo "🧪 Teste:"
echo "   1. Acesse https://finaflow.vercel.app/login"
echo "   2. Login: admin / admin123"
echo "   3. Verifique se carrega as empresas disponíveis"
echo "   4. Selecione a empresa"
echo "   5. Acesse o dashboard"


