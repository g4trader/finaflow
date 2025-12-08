# Comando Único para Validação no Cloud Shell

Execute este comando no Cloud Shell para validar os dados do seed contra a planilha:

```bash
curl -s https://raw.githubusercontent.com/g4trader/finaflow/staging/scripts/execute_validation_with_proxy.sh | bash
```

Este comando irá:
1. Configurar o projeto gcloud
2. Iniciar o Cloud SQL Proxy (se necessário)
3. Clonar/atualizar o repositório
4. Instalar dependências
5. Executar a validação
6. Gerar relatório completo
7. Salvar logs em `~/finaflow/backend/logs/validate_seed_*.log`

---

## Execução Manual (Alternativa)

Se preferir executar manualmente:

```bash
# 1. Configurar projeto
gcloud config set project trivihair

# 2. Iniciar Cloud SQL Proxy (se não estiver rodando)
curl -o cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64
chmod +x cloud_sql_proxy
./cloud_sql_proxy -instances=trivihair:us-central1:finaflow-db-staging=tcp:5432 &

# 3. Aguardar alguns segundos
sleep 5

# 4. Clonar/atualizar repositório
cd ~
rm -rf finaflow
git clone https://github.com/g4trader/finaflow.git
cd finaflow
git checkout staging
cd backend

# 5. Instalar dependências
pip3 install -r requirements.txt
pip3 install pandas openpyxl

# 6. Configurar DATABASE_URL
export DATABASE_URL="postgresql://finaflow_user:Finaflow123!@127.0.0.1:5432/finaflow"

# 7. Executar validação
python3 -m scripts.validate_seed_against_client_sheet --file data/fluxo_caixa_2025.xlsx
```

---

**Última atualização**: 2025-12-08

