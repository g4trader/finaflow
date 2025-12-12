# 📋 Instruções para Executar Validação Completa

## 🚀 Execução no Cloud Shell

### Passo 1: Acessar Cloud Shell

```bash
# No navegador, acesse: https://shell.cloud.google.com/
# Ou use o comando:
gcloud cloud-shell ssh
```

### Passo 2: Navegar para o diretório

```bash
cd ~/finaflow/backend
```

### Passo 3: Executar script de validação

```bash
./scripts/run_validation_with_proxy.sh --year 2025
```

## 📊 O que o script faz

1. ✅ Verifica se está no diretório correto
2. ✅ Configura projeto GCP (trivihair)
3. ✅ Inicia Cloud SQL Proxy (se não estiver rodando)
4. ✅ Configura variável `DATABASE_URL`
5. ✅ Testa conexão com banco
6. ✅ Verifica se arquivo Excel existe (`data/fluxo_caixa_2025.xlsx`)
7. ✅ Executa validação completa
8. ✅ Para o proxy (se foi iniciado pelo script)

## ⚠️ Requisitos

- ✅ Arquivo Excel em `backend/data/fluxo_caixa_2025.xlsx`
- ✅ Permissões para acessar Cloud SQL
- ✅ Dependências Python instaladas (`pandas`, `openpyxl`, `requests`)

## 📋 Critérios de Sucesso

Após execução, você deve ver:

```
✅ FILTRO→BANCO: 0 ocorrências
✅ BANCO→API: 0 ocorrências
✅ Nenhuma exceção Python
✅ Nenhuma inconsistência de totais
```

## 🔍 Debug

Se houver problemas:

1. **Verificar logs do proxy**:
   ```bash
   tail -50 /tmp/cloud_sql_proxy.log
   ```

2. **Verificar conexão manualmente**:
   ```bash
   export DATABASE_URL="postgresql://finaflow_user:Finaflow123!@127.0.0.1:5432/finaflow"
   python3 -c "from app.database import SessionLocal; db = SessionLocal(); db.execute('SELECT 1'); print('OK')"
   ```

3. **Verificar arquivo Excel**:
   ```bash
   ls -lh data/fluxo_caixa_2025.xlsx
   ```

## 📝 Saída Esperada

O script deve gerar:

- ✅ Tabela de comparação no console
- ✅ CSVs de debug em `backend/data/validation/` (se houver mismatches)
- ✅ Resumo final com totais

## 🎯 Próximos Passos

Após validação bem-sucedida:

1. ✅ Executar QA automatizado: `python3 scripts/qa_completo_v2.py`
2. ✅ Validar frontend manualmente
3. ✅ Gerar relatório final

