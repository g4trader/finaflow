# FinaFlow

Sistema financeiro gerencial (SaaS)

## Como rodar localmente

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Importar dados CSV

Para carregar dados a partir de arquivos CSV para tabelas do BigQuery utilize
o script de importação:

```bash
cd backend
python import_csv.py --table PlanOfAccounts csv/arquivo.csv
```

Pré-requisitos:

* Variável de ambiente `GOOGLE_APPLICATION_CREDENTIALS` apontando para o
  arquivo de credenciais do Google Cloud;
* Variáveis `PROJECT_ID` e `DATASET` definindo o destino das tabelas.

### Frontend

```bash
cd frontend
npm install
npm run dev
```
