# 🚀 Executar Seed STAGING - Cloud SQL Proxy

**Método**: Cloud SQL Proxy + Script Python  
**Ambiente**: Cloud Shell  
**Data**: 2025-12-05

---

## ⚡ EXECUÇÃO RÁPIDA (Copiar e Colar)

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
```

---

## 📋 PASSO A PASSO DETALHADO

### 1. Abrir Cloud Shell
👉 **https://shell.cloud.google.com/**

### 2. Iniciar Cloud SQL Proxy

```bash
curl -o cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64
chmod +x cloud_sql_proxy
./cloud_sql_proxy -instances=trivihair:us-central1:finaflow-db-staging=tcp:5432 &
```

**Validar**: Proxy deve iniciar sem erros. Aguardar 5 segundos.

### 3. Clonar Repositório

```bash
cd ~
rm -rf finaflow
git clone https://github.com/g4trader/finaflow.git
cd finaflow
git checkout staging
cd backend
```

**Validar**: Arquivo `data/fluxo_caixa_2025.xlsx` deve existir:
```bash
ls -lh data/fluxo_caixa_2025.xlsx
```

### 4. Instalar Dependências

```bash
pip3 install -r requirements.txt
pip3 install pandas openpyxl
```

**Validar**: Sem erros de instalação.

### 5. Configurar DATABASE_URL

```bash
export DATABASE_URL="postgresql://finaflow_user:Finaflow123!@127.0.0.1:5432/finaflow"
echo $DATABASE_URL
```

**Validar**: Deve exibir a string acima.

### 6. Executar Seed (Primeira Vez)

```bash
python3 -m scripts.seed_from_client_sheet --file data/fluxo_caixa_2025.xlsx
```

**Critérios de sucesso**:
- ✅ Mensagem: "🌱 INICIANDO SEED DO AMBIENTE STAGING"
- ✅ Estatísticas mostram itens "criados"
- ✅ Mensagem: "✅ SEED CONCLUÍDO COM SUCESSO!"

### 7. Executar Seed (Segunda Vez - Idempotência)

```bash
python3 -m scripts.seed_from_client_sheet --file data/fluxo_caixa_2025.xlsx
```

**Critérios de sucesso**:
- ✅ Estatísticas mostram itens "existentes" (não "criados")
- ✅ Nenhum registro duplicado criado
- ✅ Mensagem: "✅ SEED CONCLUÍDO COM SUCESSO!"

### 8. Parar Cloud SQL Proxy

```bash
# Encontrar PID do proxy
ps aux | grep cloud_sql_proxy

# Parar proxy (substituir PID pelo número real)
kill <PID>
```

---

## 📊 RESULTADO ESPERADO

### Primeira Execução

```
============================================================
🌱 INICIANDO SEED DO AMBIENTE STAGING
============================================================
📁 Arquivo Excel: backend/data/fluxo_caixa_2025.xlsx

------------------------------------------------------------
1. Configurando Tenant, Business Unit e Usuário...
✅ Tenant encontrado: FinaFlow Staging
✅ Business Unit encontrada: Matriz
✅ Usuário encontrado: qa@finaflow.test

------------------------------------------------------------
2. Seed do Plano de Contas...
✅ Grupo criado: Receita
✅ Subgrupo criado: Receita (Grupo: Receita)
✅ Conta criada: Noiva (Subgrupo: Receita)
...

------------------------------------------------------------
3. Seed de Lançamentos Previstos...
✅ Lançamentos previstos criados: X
...

------------------------------------------------------------
4. Seed de Lançamentos Diários...
✅ Lançamentos diários criados: Y
...

============================================================
📊 ESTATÍSTICAS DO SEED
============================================================
Grupos: X criados, 0 existentes
Subgrupos: Y criados, 0 existentes
Contas: Z criadas, 0 existentes
Lançamentos Diários: A criados, 0 existentes
Lançamentos Previstos: B criados, 0 existentes
Linhas ignoradas: C
============================================================

✅ SEED CONCLUÍDO COM SUCESSO!
```

### Segunda Execução (Idempotência)

```
============================================================
📊 ESTATÍSTICAS DO SEED
============================================================
Grupos: 0 criados, X existentes
Subgrupos: 0 criados, Y existentes
Contas: 0 criadas, Z existentes
Lançamentos Diários: 0 criados, A existentes
Lançamentos Previstos: 0 criados, B existentes
Linhas ignoradas: C
============================================================

✅ SEED CONCLUÍDO COM SUCESSO!
```

---

## ✅ VALIDAÇÃO PÓS-EXECUÇÃO

### 1. Validar via API

```bash
BACKEND_URL="https://finaflow-backend-staging-642830139828.us-central1.run.app"
TOKEN=$(curl -s -X POST "$BACKEND_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"qa@finaflow.test","password":"QaFinaflow123!"}' | jq -r '.access_token')

# Plano de contas
curl -s -X GET "$BACKEND_URL/api/v1/chart-accounts/hierarchy" \
  -H "Authorization: Bearer $TOKEN" | jq 'length'

# Lançamentos diários
curl -s -X GET "$BACKEND_URL/api/v1/lancamentos-diarios?limit=5" \
  -H "Authorization: Bearer $TOKEN" | jq 'length'

# Lançamentos previstos
curl -s -X GET "$BACKEND_URL/api/v1/lancamentos-previstos?limit=5" \
  -H "Authorization: Bearer $TOKEN" | jq 'length'
```

### 2. Validar no Frontend

👉 **https://finaflow-lcz5.vercel.app/**
- Login: `qa@finaflow.test` / `QaFinaflow123!`
- Verificar dados carregados

---

## 🚨 TROUBLESHOOTING

### Erro: "Connection refused"
- Verificar se Cloud SQL Proxy está rodando: `ps aux | grep cloud_sql_proxy`
- Verificar se porta 5432 está livre: `netstat -tuln | grep 5432`
- Reiniciar proxy se necessário

### Erro: "Arquivo não encontrado"
- Verificar: `ls -lh ~/finaflow/backend/data/fluxo_caixa_2025.xlsx`
- Se não existir, o repositório foi clonado corretamente?

### Erro: "pandas não instalado"
- Executar: `pip3 install pandas openpyxl`

### Erro: "Permission denied" no proxy
- Verificar permissões: `chmod +x cloud_sql_proxy`
- Verificar se está autenticado: `gcloud auth list`

---

## 📝 INFORMAÇÕES PARA RELATÓRIO

Após execução bem-sucedida, registrar:

- **Grupos**: X criados, Y existentes
- **Subgrupos**: X criados, Y existentes
- **Contas**: X criadas, Y existentes
- **Lançamentos Diários**: X criados, Y existentes
- **Lançamentos Previstos**: X criados, Y existentes
- **Linhas ignoradas**: Z

---

**Status**: ⏳ Aguardando execução manual no Cloud Shell

**Tempo estimado**: 5-10 minutos

