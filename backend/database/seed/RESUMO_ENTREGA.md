# 📦 Resumo da Entrega - Seed STAGING

## ✅ Script Criado

**Arquivo**: `backend/database/seed/seed_staging.py`

**Características**:
- ✅ Lê dados diretamente do Google Sheets (não precisa de CSVs locais)
- ✅ Idempotente (pode executar múltiplas vezes sem duplicar)
- ✅ Validações de integridade hierárquica
- ✅ Logs detalhados e estatísticas
- ✅ Transações atômicas (commit/rollback)
- ✅ Multi-tenancy (aplica tenant_id e business_unit_id)

## 📊 Fonte de Dados

**Planilha Google Sheets**: 
- URL: https://docs.google.com/spreadsheets/d/1rWMdDhwiNoC7iMycmQGWWDIacrePr1gB7c_mbt1patQ
- ID: `1rWMdDhwiNoC7iMycmQGWWDIacrePr1gB7c_mbt1patQ`

**Abas processadas**:
1. `Plano de contas|LLM` (ou `Plano de contas`) - Plano de Contas completo
2. `Lançamento Diário` - Lançamentos financeiros históricos
3. `Lançamentos Previstos` - Previsões futuras

## 🔧 Requisitos

1. **Arquivo de credenciais Google**:
   - `google_credentials.json` na raiz do backend
   - Ou variável `GOOGLE_APPLICATION_CREDENTIALS` apontando para o arquivo
   - Deve ter permissão de leitura na planilha

2. **Variáveis de ambiente** (opcionais):
   - `DATABASE_URL`: URL do banco PostgreSQL STAGING
   - `STAGING_TENANT_ID`: (opcional) ID do tenant
   - `STAGING_BUSINESS_UNIT_ID`: (opcional) ID da BU
   - `STAGING_USER_ID`: (opcional) ID do usuário

## 🚀 Como Executar

```bash
cd backend
python database/seed/seed_staging.py
```

## 📋 Dados Mapeados

### 1. Plano de Contas
- **Colunas**: `Conta`, `Subgrupo`, `Grupo`, `LLM` (ou `Escolha`)
- **Modelos**: `ChartAccountGroup`, `ChartAccountSubgroup`, `ChartAccount`
- **Regras**: Hierarquia validada, códigos gerados, tipo determinado pelo grupo

### 2. Lançamentos Diários
- **Colunas**: `Data Movimentação`, `Subgrupo`, `Grupo`, `Valor`, `Observações`
- **Modelo**: `LancamentoDiario`
- **Regras**: Tipo determinado automaticamente, status = LIQUIDADO

### 3. Lançamentos Previstos
- **Colunas**: `Mês` (ou `Data Prevista`), `Conta`, `Subgrupo`, `Grupo`, `Valor`
- **Modelo**: `LancamentoPrevisto`
- **Regras**: Tipo determinado automaticamente, status = PENDENTE

## 📝 Campos Ignorados

- Linhas vazias
- Linhas com `LLM`/`Escolha` diferente de "Usar" (plano de contas)
- Valores zerados ou inválidos
- Datas inválidas ou vazias
- Registros duplicados (idempotência)

## ✅ Validações Implementadas

1. **Integridade Hierárquica**: Conta → Subgrupo → Grupo
2. **Integridade de Dados**: Datas e valores válidos
3. **Idempotência**: Verifica existência antes de criar
4. **Multi-tenancy**: Todos vinculados ao tenant/BU staging

## 📊 Logs Esperados

```
============================================================
🌱 INICIANDO SEED DO AMBIENTE STAGING
============================================================
ℹ️  Planilha Google Sheets:
  - ID: 1rWMdDhwiNoC7iMycmQGWWDIacrePr1gB7c_mbt1patQ
  - URL: https://docs.google.com/spreadsheets/d/...
✅ Autenticação com Google Sheets realizada com sucesso

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
3. Seed de Lançamentos Diários...
✅ Aba encontrada: Lançamento Diário
✅ Lançamentos diários criados: 100
...

------------------------------------------------------------
4. Seed de Lançamentos Previstos...
✅ Aba encontrada: Lançamentos Previstos
✅ Lançamentos previstos criados: 50
...

============================================================
📊 ESTATÍSTICAS DO SEED
============================================================
Grupos: X criados, Y existentes
Subgrupos: X criados, Y existentes
Contas: X criadas, Y existentes
Lançamentos Diários: X criados, Y existentes
Lançamentos Previstos: X criados, Y existentes
============================================================

✅ SEED CONCLUÍDO COM SUCESSO!
```

## 🎯 Status

✅ **Script criado e pronto para uso**
✅ **Documentação completa**
✅ **Mapeamento validado**
✅ **Aguardando autorização para execução**

## ⚠️ Importante

- **NÃO executar em produção**
- **Exclusivo para STAGING**
- **Sempre fazer backup antes** (mesmo sendo idempotente)
- **Verificar credenciais Google antes de executar**

