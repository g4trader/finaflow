#!/bin/bash
# Script para monitorar e avisar quando onboarding concluir

cd "$(dirname "$0")/.."

echo "🔔 Monitorando onboarding LLM..."
echo "   (Vou avisar quando concluir)"
echo ""

# Executar monitor em loop até concluir
while true; do
    python3 scripts/monitor_onboarding_llm.py
    
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo ""
        echo "✅✅✅ ONBOARDING CONCLUÍDO! ✅✅✅"
        echo ""
        
        # Tocar som de notificação (macOS)
        if command -v afplay &> /dev/null; then
            for i in {1..3}; do
                afplay /System/Library/Sounds/Glass.aiff 2>/dev/null
                sleep 0.5
            done
        fi
        
        # Mostrar notificação visual (macOS)
        if command -v osascript &> /dev/null; then
            osascript -e 'display notification "Onboarding LLM concluído com sucesso!" with title "FinaFlow" sound name "Glass"' 2>/dev/null
        fi
        
        break
    elif [ $EXIT_CODE -eq 1 ]; then
        echo ""
        echo "⏳ Ainda em andamento... Verificando novamente em 30 segundos"
        echo ""
        sleep 30
    else
        echo ""
        echo "⚠️  Erro ou onboarding não encontrado. Tentando novamente em 60 segundos..."
        echo ""
        sleep 60
    fi
done




