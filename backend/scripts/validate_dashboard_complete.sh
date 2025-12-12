#!/bin/bash
# Script completo de validação do dashboard
# Garante conexão correta com Cloud SQL e executa validação completa

set -e  # Parar em caso de erro

echo "🚀 Iniciando validação completa do dashboard..."
echo ""

# Verificar se estamos no diretório correto
if [ ! -f "scripts/validate_dashboard_against_client_sheet.py" ]; then
    echo "❌ Erro: Execute este script a partir do diretório backend/"
    exit 1
fi

# 1. Verificar Cloud SQL Proxy
echo "1️⃣ Verificando Cloud SQL Proxy..."
if pgrep -x cloud_sql_proxy > /dev/null || pgrep -f "cloud.*sql.*proxy" > /dev/null; then
    echo "✅ Cloud SQL Proxy já está rodando"
else
    echo "⚠️  Cloud SQL Proxy não está rodando"
    echo "   Execute: cloud-sql-proxy --port 5432 trivihair:us-central1:finaflow-db-staging &"
    echo "   Ou configure DATABASE_URL para usar Unix Socket (Cloud Run)"
    exit 1
fi

# 2. Verificar DATABASE_URL
echo ""
echo "2️⃣ Verificando DATABASE_URL..."
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  DATABASE_URL não está configurada"
    echo "   Configurando para Cloud SQL Proxy local..."
    export DATABASE_URL="postgresql://finaflow_user:Finaflow123!@127.0.0.1:5432/finaflow"
    echo "   DATABASE_URL=$DATABASE_URL"
else
    echo "✅ DATABASE_URL já está configurada"
    echo "   DATABASE_URL=$DATABASE_URL"
fi

# 3. Verificar BACKEND_URL
echo ""
echo "3️⃣ Verificando BACKEND_URL..."
if [ -z "$BACKEND_URL" ]; then
    export BACKEND_URL="https://finaflow-backend-staging-642830139828.us-central1.run.app"
    echo "✅ BACKEND_URL configurada para staging"
    echo "   BACKEND_URL=$BACKEND_URL"
else
    echo "✅ BACKEND_URL já está configurada"
    echo "   BACKEND_URL=$BACKEND_URL"
fi

# 4. Testar conexão com banco
echo ""
echo "4️⃣ Testando conexão com banco..."
python3 << EOF
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.database import SessionLocal
try:
    db = SessionLocal()
    result = db.execute("SELECT 1").scalar()
    db.close()
    if result == 1:
        print("✅ Conexão com banco OK")
        sys.exit(0)
    else:
        print("❌ Conexão com banco falhou")
        sys.exit(1)
except Exception as e:
    print(f"❌ Erro ao conectar ao banco: {e}")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo "❌ Falha na conexão com banco. Verifique:"
    echo "   - Cloud SQL Proxy está rodando?"
    echo "   - DATABASE_URL está correta?"
    exit 1
fi

# 5. Executar validação
echo ""
echo "5️⃣ Executando validação completa..."
echo ""

python3 -m scripts.validate_dashboard_against_client_sheet \
    --file data/fluxo_caixa_2025.xlsx \
    --year 2025 \
    --backend-url "$BACKEND_URL"

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Validação concluída com sucesso!"
else
    echo "❌ Validação encontrou inconsistências (exit code: $EXIT_CODE)"
fi

exit $EXIT_CODE

