# 🚀 Executar Seed STAGING - Instruções Manuais

Devido a limitações de acesso ao Cloud Shell via API, a execução do seed deve ser feita **manualmente no Cloud Shell**.

## 📋 Método 1: Script Automático (Recomendado)

### Passo 1: Abrir Cloud Shell

Acesse: **https://shell.cloud.google.com/**

### Passo 2: Copiar e Colar o Script

Copie o conteúdo do arquivo `scripts/execute_seed_staging.sh` e cole no Cloud Shell.

**OU** execute diretamente:

```bash
curl -s https://raw.githubusercontent.com/g4trader/finaflow/staging/scripts/execute_seed_staging.sh | bash
```

### Passo 3: Aguardar Conclusão

O script executa automaticamente:
- ✅ Clona/atualiza repositório
- ✅ Instala dependências
- ✅ Executa seed (primeira vez)
- ✅ Valida dados
- ✅ Executa seed (segunda vez - idempotência)
- ✅ Valida dados novamente
- ✅ Commita logs

---

## 📋 Método 2: Execução Manual Passo a Passo

### 1. Abrir Cloud Shell

```bash
# Acesse: https://shell.cloud.google.com/
```

### 2. Clonar Repositório

```bash
cd ~
git clone https://github.com/g4trader/finaflow.git
cd finaflow
git checkout staging
```

### 3. Instalar Dependências

```bash
cd backend
pip3 install -r requirements.txt
pip3 install pandas openpyxl
```

### 4. Configurar Banco STAGING

```bash
export DATABASE_URL="postgresql://finaflow_user:Finaflow123!@/finaflow?host=/cloudsql/trivihair:us-central1:finaflow-db-staging"
```

### 5. Validar Conectividade

```bash
python3 - << 'EOF'
import psycopg2, os
print("Connecting...")
conn = psycopg2.connect(os.environ["DATABASE_URL"])
print("✅ Connected OK.")
conn.close()
EOF
```

### 6. Executar Seed (Primeira Vez)

```bash
mkdir -p logs
python3 -m scripts.seed_from_client_sheet --file data/fluxo_caixa_2025.xlsx | tee logs/staging_seed_$(date +%Y%m%d_%H%M%S).log
```

### 7. Validar Dados

```bash
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

for name, q in queries.items():
    cur.execute(q)
    count = cur.fetchone()[0]
    print(f"{name}: {count}")

cur.close()
conn.close()
EOF
```

### 8. Executar Seed (Segunda Vez - Idempotência)

```bash
python3 -m scripts.seed_from_client_sheet --file data/fluxo_caixa_2025.xlsx | tee logs/staging_seed_idempotency_$(date +%Y%m%d_%H%M%S).log
```

### 9. Validar Idempotência

```bash
# Executar novamente o script de validação (passo 7)
# Comparar contagens - devem ser iguais
```

### 10. Commitar Logs

```bash
cd ~/finaflow
git add backend/logs/*.log
git commit -m "qa(seed): executar seed no STAGING + validar idempotência + adicionar logs"
git push origin staging
```

---

## ✅ Validação Esperada

### Logs da Primeira Execução

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

============================================================
📊 ESTATÍSTICAS DO SEED
============================================================
Grupos: X criados, 0 existentes
Subgrupos: Y criados, 0 existentes
Contas: Z criadas, 0 existentes
Lançamentos Diários: A criados, 0 existentes
Lançamentos Previstos: B criados, 0 existentes
============================================================

✅ SEED CONCLUÍDO COM SUCESSO!
```

### Logs da Segunda Execução (Idempotência)

```
============================================================
📊 ESTATÍSTICAS DO SEED
============================================================
Grupos: 0 criados, X existentes
Subgrupos: 0 criados, Y existentes
Contas: 0 criadas, Z existentes
Lançamentos Diários: 0 criados, A existentes
Lançamentos Previstos: 0 criados, B existentes
============================================================

✅ SEED CONCLUÍDO COM SUCESSO!
```

**Importante**: Na segunda execução, deve mostrar **"existentes"** em vez de **"criados"**, confirmando idempotência.

---

## 🧪 Validação de Dados

Após execução, validar contagens:

```bash
Grupos: [número > 0]
Subgrupos: [número > 0]
Contas: [número > 0]
Lançamentos Diários: [número > 0]
Lançamentos Previstos: [número > 0]
```

**Idempotência**: Contagens da primeira e segunda execução devem ser **idênticas**.

---

## 📊 Atualizar Relatório

Após execução bem-sucedida, atualizar `docs/SEED_STAGING_STATUS.md` com:

- Data e hora do seed
- Resultado da primeira execução
- Resultado da segunda execução (idempotência)
- Contagens finais de tabelas
- Status final: **SEED APROVADO** ou **SEED APROVADO COM RESSALVAS**

---

## 🚨 Troubleshooting

### Erro: "Arquivo não encontrado"

**Solução**: Verificar se o arquivo está em `backend/data/fluxo_caixa_2025.xlsx`

### Erro: "Aba não encontrada"

**Solução**: Verificar se as abas existem no arquivo Excel

### Erro: "Connection refused"

**Solução**: Verificar se o Cloud SQL Proxy está configurado corretamente

### Muitas linhas ignoradas

**Solução**: Revisar logs para identificar padrões de erro

---

## ✅ Checklist Final

- [ ] Seed executado (primeira vez)
- [ ] Dados validados (contagens > 0)
- [ ] Seed executado (segunda vez - idempotência)
- [ ] Idempotência validada (contagens idênticas)
- [ ] Logs commitados
- [ ] Relatório atualizado
- [ ] Dados visíveis no frontend STAGING

---

**Status**: ⏳ Aguardando execução manual no Cloud Shell

