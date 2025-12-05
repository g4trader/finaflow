# 🚀 Executar Seed STAGING no Cloud Shell - Passo a Passo

## ⚠️ IMPORTANTE

Este processo **DEVE** ser executado manualmente no Cloud Shell devido a limitações de acesso via API.

---

## 📋 PASSO 1: Abrir Cloud Shell

1. Acesse: **https://shell.cloud.google.com/**
2. Aguarde o Cloud Shell inicializar

---

## 📋 PASSO 2: Configurar Projeto

No terminal do Cloud Shell, execute:

```bash
gcloud config set project trivihair
gcloud config list
```

**Critério de aceite**: `project = trivihair` deve aparecer no output.

---

## 📋 PASSO 3: Executar Script Automático

No mesmo terminal do Cloud Shell, execute:

```bash
curl -s https://raw.githubusercontent.com/g4trader/finaflow/staging/scripts/execute_seed_staging_cloudshell.sh | bash
```

**O que o script faz automaticamente**:
- ✅ Clona/atualiza repositório (branch staging)
- ✅ Instala dependências (requirements.txt, pandas, openpyxl)
- ✅ Exporta DATABASE_URL do STAGING
- ✅ Executa seed (primeira vez)
- ✅ Executa seed (segunda vez - idempotência)
- ✅ Valida dados via API
- ✅ Gera logs
- ✅ Commita e faz push das evidências

**Critério de aceite**: 
- Script termina sem erro
- Mensagem: "✅ SEED CONCLUÍDO COM SUCESSO!"
- Estatísticas mostram dados criados/existentes

---

## 📋 PASSO 4: Validação Manual (Opcional - Sanity Check)

Se quiser validar manualmente após o script:

```bash
cd ~/finaflow/backend

BACKEND_URL="https://finaflow-backend-staging-642830139828.us-central1.run.app"

TOKEN=$(curl -s -X POST "$BACKEND_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"qa@finaflow.test","password":"QaFinaflow123!"}' | jq -r '.access_token')

# Plano de contas (amostra)
echo "📊 Plano de Contas:"
curl -s -X GET "$BACKEND_URL/api/v1/chart-accounts/hierarchy" \
  -H "Authorization: Bearer $TOKEN" | jq '.[0:5]'

# Lançamentos diários (amostra)
echo ""
echo "📊 Lançamentos Diários:"
curl -s -X GET "$BACKEND_URL/api/v1/lancamentos-diarios?limit=5" \
  -H "Authorization: Bearer $TOKEN" | jq '.[0:5]'

# Lançamentos previstos (amostra)
echo ""
echo "📊 Lançamentos Previstos:"
curl -s -X GET "$BACKEND_URL/api/v1/lancamentos-previstos?limit=5" \
  -H "Authorization: Bearer $TOKEN" | jq '.[0:5]'
```

**Critério de aceite**: Respostas não vazias, registros reais aparecem.

---

## 📋 PASSO 5: Validar no Frontend

1. Acesse: **https://finaflow-lcz5.vercel.app/**
2. Login: `qa@finaflow.test` / `QaFinaflow123!`
3. Selecionar Business Unit (ex.: "Matriz")

**Validar**:
- ✅ **Plano de Contas**: Grupos, subgrupos e contas presentes
- ✅ **Lançamentos Diários**: Tabela com registros (não vazia)
- ✅ **Lançamentos Previstos**: Tabela com registros (não vazia)
- ✅ **Fluxo de Caixa**: Telas mensal/diária com dados

---

## 📋 PASSO 6: Verificar Commits (Se Necessário)

Se o script não fez commit automaticamente:

```bash
cd ~/finaflow
git status

# Se houver mudanças não commitadas:
git add backend/logs docs/SEED_STAGING_STATUS.md
git commit -m "qa(seed): executar seed do STAGING a partir da planilha do cliente e registrar evidências"
git push origin staging
```

---

## ✅ CHECKLIST FINAL

- [ ] Cloud Shell aberto e configurado
- [ ] Script executado com sucesso
- [ ] Seed executado (primeira vez) - dados criados
- [ ] Seed executado (segunda vez) - idempotência validada
- [ ] Dados validados via API
- [ ] Dados visíveis no frontend STAGING
- [ ] Logs commitados
- [ ] Documentação atualizada

---

## 🚨 TROUBLESHOOTING

### Erro: "Arquivo não encontrado"
- Verificar se repositório foi clonado corretamente
- Executar: `ls -lh ~/finaflow/backend/data/fluxo_caixa_2025.xlsx`

### Erro: "Connection refused"
- Verificar se DATABASE_URL está correta
- Verificar se Cloud SQL Proxy está configurado

### Erro: "pandas não instalado"
- Executar manualmente: `pip3 install pandas openpyxl`

### Script não faz commit
- Executar manualmente os comandos do Passo 6

---

## 📝 LOGS ESPERADOS

### Primeira Execução
```
============================================================
🌱 INICIANDO SEED DO AMBIENTE STAGING
============================================================
...
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
============================================================
✅ SEED CONCLUÍDO COM SUCESSO!
```

---

**Status**: ⏳ Aguardando execução manual no Cloud Shell

**Próximo passo**: Acessar Cloud Shell e executar o script automático

