# 🚀 Instruções Finais - Executar Seed STAGING

**Data**: 2025-12-05  
**Status**: ✅ **PRONTO PARA EXECUÇÃO**

---

## ⚡ EXECUÇÃO RÁPIDA (2 comandos)

### 1. Abrir Cloud Shell
👉 **https://shell.cloud.google.com/**

### 2. Executar Script Automático
```bash
gcloud config set project trivihair
curl -s https://raw.githubusercontent.com/g4trader/finaflow/staging/scripts/execute_seed_staging_cloudshell.sh | bash
```

**Pronto!** O script faz tudo automaticamente.

---

## 📋 O QUE O SCRIPT FAZ

1. ✅ Clona/atualiza repositório (branch staging)
2. ✅ Instala dependências (requirements.txt, pandas, openpyxl)
3. ✅ Configura DATABASE_URL do STAGING
4. ✅ Executa seed (primeira vez) - cria dados
5. ✅ Executa seed (segunda vez) - valida idempotência
6. ✅ Valida dados via API
7. ✅ Atualiza `docs/SEED_STAGING_STATUS.md`
8. ✅ Commita logs e evidências
9. ✅ Faz push para branch staging

---

## ✅ VALIDAÇÃO PÓS-EXECUÇÃO

### 1. Validar no Frontend
👉 **https://finaflow-lcz5.vercel.app/**
- Login: `qa@finaflow.test` / `QaFinaflow123!`
- Selecionar BU: "Matriz" (ou equivalente)

**Verificar**:
- ✅ Plano de Contas: grupos, subgrupos e contas presentes
- ✅ Lançamentos Diários: tabela com registros
- ✅ Lançamentos Previstos: tabela com registros
- ✅ Fluxo de Caixa: valores exibidos

### 2. Executar QA Funcional
Seguir checklist completo em: `docs/CHECKLIST_QA_FUNCIONAL_POS_SEED.md`

---

## 📊 RESULTADO ESPERADO

Após execução bem-sucedida:

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

**Segunda execução (idempotência)**:
```
Grupos: 0 criados, X existentes
Subgrupos: 0 criados, Y existentes
Contas: 0 criadas, Z existentes
...
```

---

## 📝 MENSAGEM FINAL (Após Execução)

Quando o seed estiver concluído e validado:

```
SEED STAGING EXECUTADO ✔️
Dados do cliente carregados (plano de contas, lançamentos diários e previstos) ✔️
Frontend e backend validados com massa real ✔️

Staging pronto para QA funcional completo da Sprint 1 com dados.
```

---

## 🚨 TROUBLESHOOTING

### Erro: "Arquivo não encontrado"
- Verificar: `ls -lh ~/finaflow/backend/data/fluxo_caixa_2025.xlsx`
- Se não existir, o script clona o repositório automaticamente

### Erro: "Connection refused"
- Verificar DATABASE_URL
- Verificar se Cloud SQL Proxy está configurado

### Erro: "pandas não instalado"
- O script instala automaticamente
- Se falhar, executar manualmente: `pip3 install pandas openpyxl`

---

## 📚 DOCUMENTAÇÃO RELACIONADA

- **Guia Passo a Passo**: `docs/EXECUTAR_SEED_CLOUD_SHELL_PASSO_A_PASSO.md`
- **Checklist QA**: `docs/CHECKLIST_QA_FUNCIONAL_POS_SEED.md`
- **Status Atual**: `docs/SEED_STAGING_STATUS.md`

---

**Tempo estimado**: 5-10 minutos  
**Próximo passo**: Executar no Cloud Shell

