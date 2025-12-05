# 📋 Comandos Exatos para Executar Seed no Cloud Shell

**Copie e cole estes comandos diretamente no Cloud Shell**

---

## 🚀 EXECUÇÃO COMPLETA (Copiar Tudo de Uma Vez)

```bash
# 1. Iniciar Cloud SQL Proxy
curl -o cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64
chmod +x cloud_sql_proxy
./cloud_sql_proxy -instances=trivihair:us-central1:finaflow-db-staging=tcp:5432 &

# 2. Clonar repositório
cd ~
rm -rf finaflow
git clone https://github.com/g4trader/finaflow.git
cd finaflow
git checkout staging
cd backend

# 3. Instalar dependências
pip3 install -r requirements.txt
pip3 install pandas openpyxl

# 4. Configurar DATABASE_URL
export DATABASE_URL="postgresql://finaflow_user:Finaflow123!@127.0.0.1:5432/finaflow"

# 5. Executar seed (primeira vez)
python3 -m scripts.seed_from_client_sheet --file data/fluxo_caixa_2025.xlsx

# 6. Executar seed (segunda vez - idempotência)
python3 -m scripts.seed_from_client_sheet --file data/fluxo_caixa_2025.xlsx

# 7. Parar proxy
pkill cloud_sql_proxy
```

---

## 📊 OU USAR SCRIPT AUTOMÁTICO

```bash
curl -s https://raw.githubusercontent.com/g4trader/finaflow/staging/scripts/execute_seed_with_proxy.sh | bash
```

---

## ✅ VALIDAÇÃO

Após execução, verificar:

1. **Primeira execução**: Mostra itens "criados"
2. **Segunda execução**: Mostra itens "existentes" (idempotência)
3. **Mensagem final**: "✅ SEED CONCLUÍDO COM SUCESSO!"

---

**Status**: ⏳ Aguardando execução manual no Cloud Shell

