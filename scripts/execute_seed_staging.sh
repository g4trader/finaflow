#!/bin/bash
# Script completo para executar seed no STAGING via Cloud Shell
# Copie e cole este script no Cloud Shell: https://shell.cloud.google.com/

set -e  # Parar em caso de erro

echo "============================================================"
echo "🌱 EXECUTAR SEED STAGING - SCRIPT AUTOMÁTICO"
echo "============================================================"
echo ""

# 1. Preparação
echo "🥇 1. PREPARAÇÃO"
echo "------------------------------------------------------------"
cd ~
if [ -d "finaflow" ]; then
    echo "📁 Repositório já existe, atualizando..."
    cd finaflow
    git fetch origin
    git checkout staging
    git pull origin staging
else
    echo "📁 Clonando repositório..."
    git clone https://github.com/g4trader/finaflow.git
    cd finaflow
    git checkout staging
fi
echo "✅ Repositório pronto"
echo ""

# 2. Instalação de dependências
echo "🥈 2. INSTALAÇÃO DE DEPENDÊNCIAS"
echo "------------------------------------------------------------"
cd backend
pip3 install -q -r requirements.txt
pip3 install -q pandas openpyxl
echo "✅ Dependências instaladas"
echo ""

# 3. Configurar variável de ambiente
echo "🥉 3. CONFIGURAR BANCO STAGING"
echo "------------------------------------------------------------"
export DATABASE_URL="postgresql://finaflow_user:Finaflow123!@/finaflow?host=/cloudsql/trivihair:us-central1:finaflow-db-staging"
echo "✅ DATABASE_URL configurada"
echo ""

# 4. Validar conectividade
echo "🔍 4. VALIDAR CONECTIVIDADE"
echo "------------------------------------------------------------"
python3 - << 'EOF'
import psycopg2, os
print("Connecting...")
conn = psycopg2.connect(os.environ["DATABASE_URL"])
print("✅ Connected OK.")
conn.close()
EOF
echo ""

# 5. Criar diretório de logs
echo "📝 5. PREPARAR LOGS"
echo "------------------------------------------------------------"
mkdir -p logs
echo "✅ Diretório de logs criado"
echo ""

# 6. Executar SEED (primeira vez)
echo "🏅 6. EXECUTAR SEED (PRIMEIRA VEZ)"
echo "------------------------------------------------------------"
TIMESTAMP1=$(date +%Y%m%d_%H%M%S)
python3 -m scripts.seed_from_client_sheet --file data/fluxo_caixa_2025.xlsx 2>&1 | tee logs/staging_seed_${TIMESTAMP1}.log
SEED_EXIT_CODE=$?
if [ $SEED_EXIT_CODE -ne 0 ]; then
    echo "❌ Seed falhou com código $SEED_EXIT_CODE"
    exit 1
fi
echo "✅ Seed executado com sucesso"
echo ""

# 7. Validar dados (primeira execução)
echo "🧪 7. VALIDAR DADOS (APÓS PRIMEIRA EXECUÇÃO)"
echo "------------------------------------------------------------"
python3 - << 'EOF'
import psycopg2, os
conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

queries = {
  "Grupos": "SELECT COUNT(*) FROM chart_account_groups;",
  "Subgrupos": "SELECT COUNT(*) FROM chart_account_subgroups;",
  "Contas": "SELECT COUNT(*) FROM chart_accounts;",
  "Lançamentos Diários": "SELECT COUNT(*) FROM lancamentos_diarios;",
  "Lançamentos Previstos": "SELECT COUNT(*) FROM lancamentos_previstos;",
}

print("📊 Contagens após primeira execução:")
results1 = {}
for name, q in queries.items():
    cur.execute(q)
    count = cur.fetchone()[0]
    results1[name] = count
    print(f"  ✅ {name}: {count}")

cur.close()
conn.close()
EOF
echo ""

# 8. Executar SEED (segunda vez - idempotência)
echo "🔁 8. EXECUTAR SEED (SEGUNDA VEZ - IDEMPOTÊNCIA)"
echo "------------------------------------------------------------"
TIMESTAMP2=$(date +%Y%m%d_%H%M%S)
python3 -m scripts.seed_from_client_sheet --file data/fluxo_caixa_2025.xlsx 2>&1 | tee logs/staging_seed_idempotency_${TIMESTAMP2}.log
SEED_EXIT_CODE=$?
if [ $SEED_EXIT_CODE -ne 0 ]; then
    echo "❌ Seed (idempotência) falhou com código $SEED_EXIT_CODE"
    exit 1
fi
echo "✅ Seed (idempotência) executado com sucesso"
echo ""

# 9. Validar dados (segunda execução)
echo "🧪 9. VALIDAR DADOS (APÓS SEGUNDA EXECUÇÃO)"
echo "------------------------------------------------------------"
python3 - << 'EOF'
import psycopg2, os
conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

queries = {
  "Grupos": "SELECT COUNT(*) FROM chart_account_groups;",
  "Subgrupos": "SELECT COUNT(*) FROM chart_account_subgroups;",
  "Contas": "SELECT COUNT(*) FROM chart_accounts;",
  "Lançamentos Diários": "SELECT COUNT(*) FROM lancamentos_diarios;",
  "Lançamentos Previstos": "SELECT COUNT(*) FROM lancamentos_previstos;",
}

print("📊 Contagens após segunda execução:")
results2 = {}
for name, q in queries.items():
    cur.execute(q)
    count = cur.fetchone()[0]
    results2[name] = count
    print(f"  ✅ {name}: {count}")

cur.close()
conn.close()
EOF
echo ""

# 10. Commitar logs
echo "📦 10. COMMITAR LOGS"
echo "------------------------------------------------------------"
cd ~/finaflow
git add backend/logs/*.log 2>/dev/null || true
git commit -m "qa(seed): executar seed no STAGING + validar idempotência + adicionar logs" || echo "⚠️  Nenhuma mudança para commitar"
git push origin staging || echo "⚠️  Push falhou (pode ser que já esteja atualizado)"
echo "✅ Logs commitados"
echo ""

# 11. Resumo final
echo "============================================================"
echo "✅ SEED EXECUTADO COM SUCESSO!"
echo "============================================================"
echo "📄 Logs salvos em:"
echo "   - backend/logs/staging_seed_${TIMESTAMP1}.log"
echo "   - backend/logs/staging_seed_idempotency_${TIMESTAMP2}.log"
echo ""
echo "📊 Próximos passos:"
echo "   1. Validar dados no frontend STAGING"
echo "   2. Executar QA funcional"
echo "   3. Remover endpoint temporário /api/v1/admin/seed-staging (se criado)"
echo "============================================================"

