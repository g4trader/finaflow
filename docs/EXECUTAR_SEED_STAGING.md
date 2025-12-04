# 🚀 Executar Seed STAGING via Cloud Shell

Devido a problemas de arquitetura local (psycopg2 x86_64 vs ARM64), o seed deve ser executado via **Cloud Shell** ou **Cloud Run Job**.

## 📋 Opção 1: Cloud Shell (Recomendado)

### Passo 1: Abrir Cloud Shell
```bash
# Acesse: https://shell.cloud.google.com/
# Ou execute:
gcloud cloud-shell ssh
```

### Passo 2: Clonar Repositório
```bash
cd ~
git clone https://github.com/g4trader/finaflow.git
cd finaflow
git checkout staging
```

### Passo 3: Instalar Dependências
```bash
cd backend
pip3 install -r requirements.txt
pip3 install pandas openpyxl
```

### Passo 4: Executar Seed
```bash
export DATABASE_URL="postgresql://finaflow_user:Finaflow123!@/finaflow?host=/cloudsql/trivihair:us-central1:finaflow-db-staging"
python3 -m scripts.seed_from_client_sheet --file data/fluxo_caixa_2025.xlsx
```

## 📋 Opção 2: Cloud Run Job (Alternativa)

Criar um job temporário no Cloud Run para executar o seed.

---

## ✅ Status Atual

- ✅ Arquivo `fluxo_caixa_2025.xlsx` commitado (commit: `e443e72`)
- ✅ Script `seed_from_client_sheet.py` criado e testado
- ⚠️ Execução local bloqueada por incompatibilidade de arquitetura (psycopg2)
- ✅ Solução: Executar via Cloud Shell ou Cloud Run Job

## 📊 Commit Realizado

```
commit e443e72
Author: [seu usuário]
Date: [data]

chore(seed): adicionar planilha do cliente para seed do ambiente staging

1 file changed, 0 insertions(+), 0 deletions(-)
create mode 100644 backend/data/fluxo_caixa_2025.xlsx
```

