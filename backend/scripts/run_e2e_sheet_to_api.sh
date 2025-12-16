#!/bin/bash
# Wrapper bash para executar E2E Sheet → API

set -e

# Diretório do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Exportar envs default se ausentes
export DATABASE_URL="${DATABASE_URL:-postgresql://user:pass@localhost:5432/finaflow}"
export BACKEND_URL="${BACKEND_URL:-https://finaflow-backend-staging-642830139828.us-central1.run.app}"

# Mensagens claras
echo "🚀 Executando E2E: Planilha → API"
echo "=================================="
echo "DATABASE_URL: ${DATABASE_URL}"
echo "BACKEND_URL: ${BACKEND_URL}"
echo ""

# Mudar para diretório backend
cd "$BACKEND_DIR"

# Executar script Python
python3 scripts/e2e_sheet_to_api.py "$@"

# Exit code será propagado do Python
exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✅ E2E concluído com sucesso!"
elif [ $exit_code -eq 2 ]; then
    echo ""
    echo "❌ E2E falhou: Mismatches encontrados"
else
    echo ""
    echo "❌ E2E falhou: Erro de execução"
fi

exit $exit_code

