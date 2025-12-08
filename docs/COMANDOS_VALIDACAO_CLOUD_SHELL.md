# Comandos para Executar Validação no Cloud Shell

## Passo a Passo Completo

### 1. Clonar/Atualizar Repositório

```bash
cd ~
rm -rf finaflow
git clone https://github.com/g4trader/finaflow.git
cd finaflow
git checkout staging
```

### 2. Iniciar Cloud SQL Proxy (se ainda não estiver rodando)

```bash
# Verificar se já está rodando
if pgrep -x cloud_sql_proxy > /dev/null; then
    echo "✅ Cloud SQL Proxy já está rodando"
else
    # Baixar e iniciar proxy
    curl -o cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64
    chmod +x cloud_sql_proxy
    ./cloud_sql_proxy -instances=trivihair:us-central1:finaflow-db-staging=tcp:5432 &
    sleep 5
    echo "✅ Cloud SQL Proxy iniciado"
fi
```

### 3. Instalar Dependências

```bash
cd ~/finaflow/backend
pip3 install -r requirements.txt
pip3 install pandas openpyxl
```

### 4. Configurar DATABASE_URL

```bash
export DATABASE_URL="postgresql://finaflow_user:Finaflow123!@127.0.0.1:5432/finaflow"
```

### 5. Executar Validação

```bash
cd ~/finaflow/backend
python3 -m scripts.validate_seed_against_client_sheet --file data/fluxo_caixa_2025.xlsx
```

---

## Comando Único (Script Automatizado)

Execute tudo de uma vez:

```bash
curl -s https://raw.githubusercontent.com/g4trader/finaflow/staging/scripts/execute_validation_with_proxy.sh | bash
```

---

## Verificar Resultados

Após a execução, os arquivos estarão em:

```bash
ls -lh ~/finaflow/backend/logs/
```

Principais arquivos gerados:
- `validate_seed_YYYYMMDD_HHMMSS.log` - Log completo da execução
- `diarios_missing_in_db_YYYYMMDD_HHMMSS.csv` - Linhas faltando no banco (diários)
- `diarios_ignored_YYYYMMDD_HHMMSS.csv` - Linhas ignoradas por regras do seed (diários)
- `previstos_missing_in_db_YYYYMMDD_HHMMSS.csv` - Linhas faltando no banco (previstos)
- `previstos_ignored_YYYYMMDD_HHMMSS.csv` - Linhas ignoradas por regras do seed (previstos)

---

**Última atualização**: 2025-12-08

