# 📋 Mapeamento de Dados - Seed STAGING

## 📊 Fonte de Dados

**Planilha Google Sheets**: https://docs.google.com/spreadsheets/d/1rWMdDhwiNoC7iMycmQGWWDIacrePr1gB7c_mbt1patQ

O script lê dados diretamente da planilha online, não de arquivos CSV locais.

## ✅ Confirmação dos Dados Mapeados

### 1. Plano de Contas

**Estrutura CSV:**
- `Conta` → `ChartAccount.name`
- `Subgrupo` → `ChartAccountSubgroup.name`
- `Grupo` → `ChartAccountGroup.name`
- `Escolha` → Filtro (apenas "Usar" é processado)

**Mapeamento para Banco:**
```
CSV                    → Modelo ORM
─────────────────────────────────────────────────────────
Conta                  → ChartAccount.name
Subgrupo               → ChartAccountSubgroup.name
Grupo                  → ChartAccountGroup.name
(gerado)               → ChartAccount.code (auto-gerado)
(gerado)               → ChartAccountSubgroup.code (auto-gerado)
(gerado)               → ChartAccountGroup.code (auto-gerado)
(gerado)               → ChartAccount.account_type (baseado no Grupo)
tenant_id              → Do tenant staging
```

**Regras de Negócio Aplicadas:**
- ✅ Hierarquia: Conta pertence ao Subgrupo, Subgrupo pertence ao Grupo
- ✅ Tenant: Todos vinculados ao tenant staging
- ✅ Códigos: Gerados automaticamente baseados no nome
- ✅ Tipo de Conta: Determinado pelo nome do Grupo (Receita/Custo/Despesa)

### 2. Lançamentos Diários

**Estrutura CSV:**
- `Data Movimentação` → `LancamentoDiario.data_movimentacao`
- `Subgrupo` → Busca `ChartAccountSubgroup` pelo nome
- `Grupo` → Busca `ChartAccountGroup` pelo nome
- `Valor` → `LancamentoDiario.valor` (convertido de formato brasileiro)
- `Observações` → `LancamentoDiario.observacoes`

**Mapeamento para Banco:**
```
CSV                    → Modelo ORM
─────────────────────────────────────────────────────────
Data Movimentação      → LancamentoDiario.data_movimentacao
Subgrupo               → LancamentoDiario.subgrupo_id (via lookup)
Grupo                  → LancamentoDiario.grupo_id (via lookup)
Valor                  → LancamentoDiario.valor (parse de "R$ 1.234,56")
Observações            → LancamentoDiario.observacoes
(gerado)               → LancamentoDiario.conta_id (primeira conta do subgrupo)
(gerado)               → LancamentoDiario.transaction_type (baseado em Grupo/Subgrupo)
(gerado)               → LancamentoDiario.status = LIQUIDADO
tenant_id              → Do tenant staging
business_unit_id       → Da business unit staging
created_by             → Do usuário QA
```

**Regras de Negócio Aplicadas:**
- ✅ Hierarquia: Valida que Subgrupo pertence ao Grupo
- ✅ Conta: Usa a primeira conta encontrada do Subgrupo
- ✅ Tipo: Determinado automaticamente (RECEITA/CUSTO/DESPESA)
- ✅ Status: Padrão LIQUIDADO para lançamentos históricos
- ✅ Tenant/BU: Vinculados ao staging
- ✅ Idempotência: Verifica duplicatas por data + conta + valor + tenant + BU

### 3. Lançamentos Previstos

**Estrutura CSV:**
- `Mês` (ou `Data Prevista`) → `LancamentoPrevisto.data_prevista`
- `Conta` → Busca `ChartAccount` pelo nome
- `Subgrupo` → Busca `ChartAccountSubgroup` pelo nome
- `Grupo` → Busca `ChartAccountGroup` pelo nome
- `Valor` → `LancamentoPrevisto.valor` (convertido de formato brasileiro)

**Mapeamento para Banco:**
```
CSV                    → Modelo ORM
─────────────────────────────────────────────────────────
Mês / Data Prevista    → LancamentoPrevisto.data_prevista
Conta                  → LancamentoPrevisto.conta_id (via lookup)
Subgrupo               → LancamentoPrevisto.subgrupo_id (via lookup)
Grupo                  → LancamentoPrevisto.grupo_id (via lookup)
Valor                  → LancamentoPrevisto.valor (parse de "R$ 1.234,56")
(gerado)               → LancamentoPrevisto.transaction_type (baseado em Grupo/Subgrupo)
(gerado)               → LancamentoPrevisto.status = PENDENTE
(gerado)               → LancamentoPrevisto.observacoes (descritivo)
tenant_id              → Do tenant staging
business_unit_id       → Da business unit staging
created_by             → Do usuário QA
```

**Regras de Negócio Aplicadas:**
- ✅ Hierarquia: Valida que Conta pertence ao Subgrupo, Subgrupo pertence ao Grupo
- ✅ Tipo: Determinado automaticamente (RECEITA/CUSTO/DESPESA)
- ✅ Status: Padrão PENDENTE para previsões
- ✅ Tenant/BU: Vinculados ao staging
- ✅ Idempotência: Verifica duplicatas por data + conta + valor + tenant + BU

## 📝 Campos Ignorados

### Plano de Contas
- ✅ Linhas com `Escolha` diferente de "Usar"
- ✅ Linhas vazias
- ✅ Linhas sem Conta, Subgrupo ou Grupo

### Lançamentos Diários
- ✅ Linhas sem Data Movimentação
- ✅ Linhas sem Subgrupo ou Grupo
- ✅ Linhas sem Valor ou com valor <= 0
- ✅ Colunas extras após "Valor" (ignoradas)

### Lançamentos Previstos
- ✅ Linhas sem Mês/Data Prevista
- ✅ Linhas sem Conta, Subgrupo ou Grupo
- ✅ Linhas sem Valor ou com valor <= 0

## 🔄 Transformações Aplicadas

### 1. Conversão de Valores
```
"R$ 1.234,56" → Decimal("1234.56")
"1.234,56"    → Decimal("1234.56")
"1234.56"     → Decimal("1234.56")
```

### 2. Conversão de Datas
```
"02/01/2025"  → datetime(2025, 1, 2)
"02-01-2025"  → datetime(2025, 1, 2)
"2025-01-02"  → datetime(2025, 1, 2)
```

### 3. Geração de Códigos
```
"Receita"           → "G" + "REC" = "GREC"
"Despesas Operacionais" → "G" + "DES" = "GDES"
"Vendas Cursos"     → "C" + "VEN" = "CVEN"
```

### 4. Determinação de Tipo de Transação
```
Grupo contém "Receita" → TransactionType.RECEITA
Grupo contém "Custo"   → TransactionType.CUSTO
Grupo contém "Despesa" → TransactionType.DESPESA
```

### 5. Determinação de Tipo de Conta
```
Grupo contém "Receita" → account_type = "Receita"
Grupo contém "Custo"   → account_type = "Custo"
Grupo contém "Despesa" → account_type = "Despesa"
```

## ✅ Validações Implementadas

1. **Integridade Hierárquica**
   - ✅ Conta deve pertencer ao Subgrupo informado
   - ✅ Subgrupo deve pertencer ao Grupo informado
   - ✅ Grupo deve existir no tenant

2. **Integridade de Dados**
   - ✅ Datas válidas e no formato correto
   - ✅ Valores numéricos válidos e > 0
   - ✅ Nomes não vazios

3. **Idempotência**
   - ✅ Verifica existência antes de criar
   - ✅ Usa chaves únicas para evitar duplicatas
   - ✅ Transações atômicas (commit/rollback)

4. **Multi-tenancy**
   - ✅ Todos os registros vinculados ao tenant staging
   - ✅ Todos os lançamentos vinculados à BU staging
   - ✅ Isolamento de dados garantido

## 📊 Logs Simulados de Execução

```
============================================================
🌱 INICIANDO SEED DO AMBIENTE STAGING
============================================================
ℹ️  Arquivos CSV:
  - Plano de Contas: backend/csv/Plano de contas.csv
  - Lançamentos Diários: backend/csv/Lançamento Diário.csv
  - Lançamentos Previstos: backend/csv/Lançamentos Previstos.csv
📋 Inicializando banco de dados...
✅ Banco de dados inicializado

------------------------------------------------------------
1. Configurando Tenant, Business Unit e Usuário...
✅ Tenant encontrado: FinaFlow Staging (ID: abc-123...)
✅ Business Unit encontrada: Matriz (ID: def-456...)
✅ Usuário encontrado: qa@finaflow.test (ID: ghi-789...)

------------------------------------------------------------
2. Seed do Plano de Contas...
✅ Grupo criado: Receita
✅ Subgrupo criado: Receita (Grupo: Receita)
✅ Conta criada: Vendas Cursos pelo o comercial (Subgrupo: Receita)
...
✅ Seed do Plano de Contas concluído!

------------------------------------------------------------
3. Seed de Lançamentos Diários...
✅ Lançamentos diários criados: 100
✅ Lançamentos diários criados: 200
...
✅ Seed de Lançamentos Diários concluído!

------------------------------------------------------------
4. Seed de Lançamentos Previstos...
✅ Lançamentos previstos criados: 100
...
✅ Seed de Lançamentos Previstos concluído!

============================================================
📊 ESTATÍSTICAS DO SEED
============================================================
Grupos: 5 criados, 0 existentes
Subgrupos: 15 criados, 0 existentes
Contas: 45 criadas, 0 existentes
Lançamentos Diários: 250 criados, 0 existentes
Lançamentos Previstos: 120 criados, 0 existentes
============================================================

============================================================
✅ SEED CONCLUÍDO COM SUCESSO!
============================================================
```

## 🎯 Próximos Passos

1. ✅ Script criado e testado
2. ⏳ Aguardar PO enviar planilha final (se diferente dos CSVs existentes)
3. ⏳ Executar seed no ambiente STAGING
4. ⏳ Validar dados no frontend STAGING
5. ⏳ Reexecutar QA funcional com dados populados

