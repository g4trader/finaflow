#!/bin/bash
# Script para verificar status do onboarding e avisar quando concluir

cd "$(dirname "$0")/.."

echo "🔍 Verificando status do onboarding LLM..."
echo ""

python3 scripts/monitor_onboarding_llm.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Onboarding concluído com sucesso!"
    # Tocar som de notificação (macOS)
    if command -v afplay &> /dev/null; then
        afplay /System/Library/Sounds/Glass.aiff 2>/dev/null || true
    fi
else
    echo ""
    echo "⚠️  Onboarding ainda em andamento ou com erro"
fi




