#!/bin/bash

echo "🚀 INICIANDO TESTES PROFISSIONAIS DE QA - FinaFlow"
echo "=================================================="

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não está instalado. Instalando..."
    brew install python3
fi

# Verificar se pip está instalado
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 não está instalado. Instalando..."
    python3 -m ensurepip --upgrade
fi

# Instalar dependências
echo "📦 Instalando dependências de QA..."
pip3 install -r requirements_qa.txt

# Verificar se Chrome está instalado
if ! command -v google-chrome &> /dev/null && ! command -v chromium-browser &> /dev/null; then
    echo "❌ Chrome não está instalado. Instalando..."
    brew install --cask google-chrome
fi

# Executar testes
echo "🧪 Executando testes automatizados..."
python3 qa_test_plan.py

# Verificar resultado
if [ $? -eq 0 ]; then
    echo "✅ Todos os testes passaram!"
    exit 0
else
    echo "❌ Alguns testes falharam. Verifique o relatório acima."
    exit 1
fi
