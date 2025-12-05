# 🚀 Executar Seed STAGING Diretamente pelo Script

## ⚠️ LIMITAÇÃO LOCAL

**Problema**: Execução local bloqueada por incompatibilidade de arquitetura (psycopg2 x86_64 vs ARM64).

**Solução**: Executar no **Cloud Shell** onde o ambiente está configurado corretamente.

---

## 📋 EXECUÇÃO NO CLOUD SHELL

### Opção 1: Script Automático (Recomendado)

1. **Abrir Cloud Shell**: https://shell.cloud.google.com/

2. **Executar script**:
   ```bash
   curl -s https://raw.githubusercontent.com/g4trader/finaflow/staging/scripts/execute_seed_staging_cloudshell.sh | bash
   ```

   **OU** copiar e colar o conteúdo de `scripts/execute_seed_staging_cloudshell.sh`

### Opção 2: Execução Manual Passo a Passo

```bash
# 1. Preparar repositório
cd ~
git clone https://github.com/g4trader/finaflow.git
cd finaflow
git checkout staging

# 2. Instalar dependências
cd backend
pip3 install -r requirements.txt
pip3 install pandas openpyxl

# 3. Configurar DATABASE_URL
export DATABASE_URL="postgresql://finaflow_user:Finaflow123!@/finaflow?host=/cloudsql/trivihair:us-central1:finaflow-db-staging"

# 4. Executar seed (primeira vez)
python3 -m scripts.seed_from_client_sheet --file data/fluxo_caixa_2025.xlsx

# 5. Executar seed (segunda vez - idempotência)
python3 -m scripts.seed_from_client_sheet --file data/fluxo_caixa_2025.xlsx

# 6. Validar via API
BACKEND_URL="https://finaflow-backend-staging-642830139828.us-central1.run.app"
TOKEN=$(curl -s -X POST "$BACKEND_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"qa@finaflow.test","password":"QaFinaflow123!"}' | jq -r '.access_token')

# Plano de contas
curl -s -X GET "$BACKEND_URL/api/v1/chart-accounts/hierarchy" \
  -H "Authorization: Bearer $TOKEN" | jq '.[0:5]'

# Lançamentos diários
curl -s -X GET "$BACKEND_URL/api/v1/lancamentos-diarios?limit=5" \
  -H "Authorization: Bearer $TOKEN" | jq '.[0:5]'

# Lançamentos previstos
curl -s -X GET "$BACKEND_URL/api/v1/lancamentos-previstos?limit=5" \
  -H "Authorization: Bearer $TOKEN" | jq '.[0:5]'
```

---

## ✅ CRITÉRIOS DE ACEITE

### Primeira Execução

- ✅ Mensagem: "🌱 INICIANDO SEED DO AMBIENTE STAGING"
- ✅ Estatísticas mostram itens "criados"
- ✅ Mensagem: "✅ SEED CONCLUÍDO COM SUCESSO!"

### Segunda Execução (Idempotência)

- ✅ Estatísticas mostram itens "existentes" (não "criados")
- ✅ Nenhum registro duplicado criado
- ✅ Mensagem: "✅ SEED CONCLUÍDO COM SUCESSO!"

### Validação via API

- ✅ `/chart-accounts/hierarchy` retorna registros
- ✅ `/lancamentos-diarios` retorna registros
- ✅ `/lancamentos-previstos` retorna registros

---

## 📝 REGISTRAR EVIDÊNCIAS

Após execução bem-sucedida:

1. **Criar log**:
   ```bash
   mkdir -p backend/logs
   LOG_FILE="backend/logs/seed_staging_from_client_sheet_$(date +%Y%m%d_%H%M%S).log"
   # Copiar output do seed para o arquivo
   ```

2. **Atualizar `docs/SEED_STAGING_STATUS.md`** com:
   - Data/hora da execução
   - Resultado da primeira execução
   - Resultado da segunda execução (idempotência)
   - Contagens finais
   - Status: **SEED STAGING APROVADO**

3. **Commit e push**:
   ```bash
   git add backend/logs docs/SEED_STAGING_STATUS.md
   git commit -m "qa(seed): executar seed do STAGING a partir da planilha do cliente e registrar evidências"
   git push origin staging
   ```

---

## 🚨 TROUBLESHOOTING

### Erro: "Arquivo não encontrado"
- Verificar se `backend/data/fluxo_caixa_2025.xlsx` existe
- Executar: `ls -lh backend/data/fluxo_caixa_2025.xlsx`

### Erro: "Connection refused"
- Verificar se Cloud SQL Proxy está configurado
- Verificar se DATABASE_URL está correta

### Erro: "pandas não instalado"
- Executar: `pip3 install pandas openpyxl`

---

**Status**: ⏳ Aguardando execução no Cloud Shell

