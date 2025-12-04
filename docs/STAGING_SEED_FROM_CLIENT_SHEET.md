# 📊 Seed de Dados STAGING - Planilha do Cliente

Este documento descreve como popular o ambiente STAGING com dados reais da planilha do cliente.

## 📋 Fonte de Dados

**Planilha Google Sheets do Cliente**:
- **Nome**: Fluxo de Caixa 2025 | LLM
- **URL**: https://docs.google.com/spreadsheets/d/1rWMdDhwiNoC7iMycmQGWWDIacrePr1gB7c_mbt1patQ/edit?gid=1158090564#gid=1158090564

## 🎯 Objetivo

Popular o ambiente STAGING com:
1. **Plano de Contas completo**: Grupos, Subgrupos e Contas
2. **Lançamentos Previstos**: Previsões futuras de transações
3. **Lançamentos Diários**: Histórico de transações realizadas

## 📁 Preparação do Arquivo

### Passo 1: Download da Planilha

1. Acesse a planilha Google Sheets no link acima
2. Vá em **Arquivo → Fazer download → Microsoft Excel (.xlsx)**
3. Salve o arquivo com o nome: `fluxo_caixa_2025.xlsx`

### Passo 2: Colocar Arquivo no Repositório

1. Coloque o arquivo `fluxo_caixa_2025.xlsx` na pasta:
   ```
   backend/data/fluxo_caixa_2025.xlsx
   ```

2. **IMPORTANTE**: O arquivo `.xlsx` **NÃO deve ser versionado** no Git (deve estar no `.gitignore`)

### Passo 3: Verificar Estrutura

O arquivo deve conter as seguintes abas:
- ✅ `Plano de contas|LLM` (ou `Plano de contas`)
- ✅ `Lançamentos Previstos`
- ✅ `Lançamento Diário` (ou `Lançamento Diario`)

## 🔧 Pré-requisitos

1. **Python 3.8+**
2. **Dependências instaladas**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
   
   O script requer:
   - `pandas` (para ler Excel)
   - `openpyxl` (engine para ler .xlsx)

3. **Variáveis de ambiente**:
   ```bash
   export DATABASE_URL="postgresql://user:pass@host:port/db"
   ```

## 🚀 Como Executar

### Opção 1: Execução Local

```bash
cd backend
python -m scripts.seed_from_client_sheet --file data/fluxo_caixa_2025.xlsx
```

### Opção 2: Com IDs Customizados

```bash
python -m scripts.seed_from_client_sheet \
  --file data/fluxo_caixa_2025.xlsx \
  --tenant-id "uuid-do-tenant" \
  --business-unit-id "uuid-da-bu" \
  --user-id "uuid-do-usuario"
```

### Opção 3: Cloud Shell / Cloud Run

Se estiver executando no Cloud Shell ou container:

```bash
# No Cloud Shell, após fazer upload do arquivo
python -m backend.scripts.seed_from_client_sheet --file backend/data/fluxo_caixa_2025.xlsx
```

## 📊 O que o Script Faz

### 1. Plano de Contas

- Lê a aba `Plano de contas|LLM`
- Cria/atualiza:
  - **Grupos** (de-duplicação por nome)
  - **Subgrupos** (de-duplicação por grupo + subgrupo)
  - **Contas** (vinculadas ao subgrupo correto)
- Todos vinculados ao `tenant_id` e `business_unit_id` de STAGING

### 2. Lançamentos Previstos

- Lê a aba `Lançamentos Previstos`
- Cria registros de previsões futuras
- **Validação crítica**: Nunca cria conta nova, sempre busca na estrutura do Plano de Contas
- Se conta não encontrada, registra em log para revisão

### 3. Lançamentos Diários

- Lê a aba `Lançamento Diário`
- Cria registros de transações realizadas
- Usa a estrutura de Plano de Contas já criada
- Status padrão: `LIQUIDADO`

## ✅ Idempotência

O script é **idempotente**, ou seja:

- ✅ Pode ser executado múltiplas vezes sem duplicar dados
- ✅ Verifica existência antes de criar:
  - Grupos/Subgrupos/Contas: por nome + tenant_id
  - Lançamentos: por data + conta + valor + tenant + BU
- ✅ Reutiliza registros existentes em vez de criar duplicados

## 📝 Logs e Estatísticas

O script exibe logs detalhados:

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
✅ Aba encontrada: Plano de contas|LLM
✅ Grupo criado: Receita
✅ Subgrupo criado: Receita (Grupo: Receita)
✅ Conta criada: Noiva (Subgrupo: Receita)
...

------------------------------------------------------------
3. Seed de Lançamentos Previstos...
✅ Aba encontrada: Lançamentos Previstos
✅ Lançamentos previstos criados: 50
...

------------------------------------------------------------
4. Seed de Lançamentos Diários...
✅ Aba encontrada: Lançamento Diário
✅ Lançamentos diários criados: 100
...

============================================================
📊 ESTATÍSTICAS DO SEED
============================================================
Grupos: X criados, Y existentes
Subgrupos: X criados, Y existentes
Contas: X criadas, Y existentes
Lançamentos Diários: X criados, Y existentes
Lançamentos Previstos: X criados, Y existentes
Linhas ignoradas: Z
============================================================

✅ SEED CONCLUÍDO COM SUCESSO!
```

## ⚠️ Tratamento de Erros

### Conta Não Encontrada

Se uma conta mencionada em `Lançamentos Previstos` não existir no `Plano de Contas`:

- ⚠️ A linha é **ignorada** (não cria registro)
- 📝 Log registrado: `"Conta não encontrada: NomeDaConta (linha X)"`
- 📊 Contador de `linhas_ignoradas` incrementado

**Ação**: Revisar a planilha e garantir que todas as contas usadas em previsões existam no Plano de Contas.

### Data Inválida

Se uma data não puder ser convertida:

- ⚠️ A linha é **ignorada**
- 📝 Log registrado: `"Erro ao converter data: valor (linha X)"`

### Valor Inválido

Se um valor for zero ou inválido:

- ⚠️ A linha é **ignorada**
- 📝 Log registrado

## 🔍 Validações Implementadas

1. **Integridade Hierárquica**:
   - ✅ Conta pertence ao Subgrupo informado
   - ✅ Subgrupo pertence ao Grupo informado
   - ✅ Grupo pertence ao tenant

2. **Integridade de Dados**:
   - ✅ Datas válidas e no formato correto
   - ✅ Valores numéricos válidos e > 0
   - ✅ Nomes não vazios

3. **Idempotência**:
   - ✅ Verifica existência antes de criar
   - ✅ Usa chaves únicas para evitar duplicatas
   - ✅ Transações atômicas (commit/rollback)

4. **Multi-tenancy**:
   - ✅ Todos os registros vinculados ao tenant staging
   - ✅ Todos os lançamentos vinculados à BU staging
   - ✅ Isolamento de dados garantido

## 🎯 Critérios de Aceite (para QA)

Após executar o seed, validar:

- ✅ Plano de contas em STAGING contém todos os grupos/subgrupos/contas da aba "Plano de contas"
- ✅ Lançamentos previstos presentes em STAGING correspondem à aba "Lançamentos Previstos" (amostragem)
- ✅ Lançamentos diários presentes em STAGING correspondem à aba "Lançamento Diário" (amostragem)
- ✅ Todos os registros criados têm `tenant_id` e `business_unit_id` consistentes
- ✅ Rodar o script duas vezes não cria registros duplicados

## 🚨 Importante

- **NÃO executar em produção**
- **Exclusivo para STAGING**
- **Sempre fazer backup antes** (mesmo sendo idempotente)
- **Verificar arquivo Excel antes de executar**
- **Revisar logs de linhas ignoradas**

## 📞 Troubleshooting

### Erro: "Arquivo não encontrado"

**Solução**: Verifique se o arquivo está em `backend/data/fluxo_caixa_2025.xlsx`

### Erro: "Aba não encontrada"

**Solução**: Verifique se as abas existem no arquivo Excel. O script tenta diferentes variações de nomes automaticamente.

### Erro: "pandas não está instalado"

**Solução**: 
```bash
pip install pandas openpyxl
```

### Muitas linhas ignoradas

**Solução**: 
1. Revisar os logs para identificar padrões
2. Verificar se todas as contas usadas em previsões existem no Plano de Contas
3. Verificar formato de datas e valores

## 📚 Estrutura Esperada das Abas

### Plano de Contas

| Conta | Subgrupo | Grupo | LLM | Observação |
|-------|----------|-------|-----|------------|
| Noiva | Receita | Receita | Usar | |
| Salário | Custos com Mão de Obra | Custos | Usar | |

### Lançamentos Previstos

| Mês | Conta | Subgrupo | Grupo | Valor |
|-----|-------|----------|-------|-------|
| 10/01/2025 | Água | Despesas Administrativas | Despesas Operacionais | R$ 80,0 |

### Lançamento Diário

| Data Movimentação | Subgrupo | Grupo | Valor | Observações |
|-------------------|----------|-------|-------|-------------|
| 02/01/2025 | Despesas com Pessoal | Despesas Operacionais | 3.200,00 | Vale Alimentação-ADM |

## ✅ Checklist de Execução

- [ ] Planilha baixada do Google Sheets
- [ ] Arquivo salvo como `backend/data/fluxo_caixa_2025.xlsx`
- [ ] Dependências instaladas (`pandas`, `openpyxl`)
- [ ] `DATABASE_URL` configurada para STAGING
- [ ] Script executado com sucesso
- [ ] Logs revisados (verificar linhas ignoradas)
- [ ] Dados validados no frontend STAGING

