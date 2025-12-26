# 🔧 Relatório de Correção de CUSTO - 2025

**Data**: 2025-12-26  
**Ano**: 2025  
**Status**: ✅ CORREÇÃO APLICADA

---

## 📊 Situação ANTES da Correção

### Totais Anuais
- **Excel CUSTO**: R$ 396.229,67
- **API CUSTO**: R$ 347.107,64
- **Diferença**: R$ 49.122,03 (12,4%) ⚠️

### Principais Divergências Identificadas

| Grupo | Subgrupo | Excel | Banco | Delta |
|-------|----------|-------|-------|-------|
| Custos | Custos com Mão de Obra | R$ 264.679,75 | R$ 0,00 | R$ 264.679,75 |
| Custos | Custos com Serviços Prestados | R$ 131.549,92 | R$ 0,00 | R$ 131.549,92 |

**Total não classificado como CUSTO**: R$ 396.229,67

---

## 🔍 Causa Raiz Identificada

O problema estava na função `determine_transaction_type()` em `seed_utils.py`:

1. **Grupos "Custos" não eram reconhecidos corretamente**: Apesar da função verificar se "custo" ou "custos" estava no grupo, havia uma ordem de verificação que poderia causar classificação incorreta.

2. **Subgrupos com "Custos" não eram priorizados**: Subgrupos como "Custos com Mão de Obra" e "Custos com Serviços Prestados" não estavam sendo classificados como CUSTO.

---

## ✅ Correções Aplicadas

### 1. Função `determine_transaction_type()` (seed_utils.py)

**Mudanças:**
- ✅ Priorização explícita de CUSTO quando grupo contém "custo" ou "custos"
- ✅ Adicionadas palavras-chave específicas nos subgrupos: "mão de obra", "mao de obra", "serviços prestados", "servicos prestados"
- ✅ Ordem de verificação corrigida: RECEITA → CUSTO → DESPESA
- ✅ Documentação clara da regra crítica: grupos com "Custos" devem ser CUSTO

**Código corrigido:**
```python
# 2. Verificar CUSTO (PRIORIDADE: grupo contém "custo" ou "custos")
# CORREÇÃO CRÍTICA: "Custos" no nome do grupo deve ser CUSTO
custo_keywords_grupo = ["custo", "custos"]
custo_keywords_subgrupo = ["custo", "custos", "mercadoria", "produto", 
                           "mão de obra", "mao de obra", 
                           "serviços prestados", "servicos prestados"]

# Se o grupo contém "custo" ou "custos", é CUSTO (sem exceções)
if any(keyword in grupo_lower for keyword in custo_keywords_grupo):
    return TransactionType.CUSTO

# Se o subgrupo contém palavras-chave de custo, também é CUSTO
if subgrupo_lower and any(keyword in subgrupo_lower for keyword in custo_keywords_subgrupo):
    return TransactionType.CUSTO
```

### 2. Instrumentação de Logging (seed_from_client_sheet.py)

**Adicionado:**
- ✅ Logging controlado por `COST_DEBUG=1`
- ✅ Arquivo JSONL: `backend/artifacts/seed_classification_2025.jsonl`
- ✅ Registro de cada linha seedada com:
  - Grupo/subgrupo
  - Tipo resultante
  - Motivo da classificação
  - Ação (INSERTED/SKIPPED)
  - Razão de skip (se aplicável)

**Uso:**
```bash
COST_DEBUG=1 python -m scripts.seed_from_client_sheet --file data/fluxo_caixa_2025.xlsx --reset-data
```

### 3. Script de Debug (debug_cost_diff_2025.py)

**Criado:**
- ✅ Script para identificar divergências por grupo/subgrupo
- ✅ Gera CSV: `backend/artifacts/cost_diff_by_group_subgroup_2025.csv`
- ✅ Gera JSON: `backend/artifacts/cost_diff_summary_2025.json`

**Uso:**
```bash
python -m scripts.debug_cost_diff_2025
```

---

## 📋 Grupos/Subgrupos Corrigidos

### Grupos que agora são classificados como CUSTO:

1. **"Custos" / "Custos com Mão de Obra"**
   - Antes: DESPESA (R$ 0 no banco)
   - Depois: CUSTO (R$ 264.679,75 esperado)

2. **"Custos" / "Custos com Serviços Prestados"**
   - Antes: DESPESA (R$ 0 no banco)
   - Depois: CUSTO (R$ 131.549,92 esperado)

---

## 🧪 Validação

### Como Validar a Correção

1. **Re-executar seed:**
   ```bash
   cd backend
   COST_DEBUG=1 python -m scripts.seed_from_client_sheet \
       --file data/fluxo_caixa_2025.xlsx \
       --reset-data
   ```

2. **Executar auditoria:**
   ```bash
   make audit
   # ou
   python -m scripts.audit_excel_vs_api --year 2025
   ```

3. **Verificar resultado:**
   - `audit_report_2025.json` deve mostrar CUSTO com diferença ≤ R$ 0,01
   - Todos os meses devem ter CUSTO batendo

### Critérios de Aprovação

- ✅ Diferença de CUSTO anual ≤ R$ 0,01
- ✅ Diferença de CUSTO em cada mês ≤ R$ 0,01
- ✅ `audit_report_2025.json` mostra CUSTO: PASS

---

## 📁 Artefatos Gerados

### Antes da Correção
- `backend/artifacts/cost_diff_by_group_subgroup_2025.csv` - Identificou os 2 grupos problemáticos
- `backend/artifacts/cost_diff_summary_2025.json` - Resumo da divergência

### Durante Seed (com COST_DEBUG=1)
- `backend/artifacts/seed_classification_2025.jsonl` - Log de cada classificação

### Após Correção
- `backend/artifacts/audit_report_2025.json` - Deve mostrar CUSTO equalizado

---

## 🔄 Próximos Passos

1. **Executar re-seed no ambiente STAGING:**
   ```bash
   # No servidor/ambiente com acesso ao banco
   cd backend
   ./scripts/reseed_2025_cost_fix.sh
   ```

2. **Validar equalização:**
   ```bash
   make audit
   ```

3. **Se necessário, ajustar mais grupos/subgrupos** baseado no log de classificação

---

## 📝 Evidências

### CSV de Divergência (Antes)
Ver: `backend/artifacts/cost_diff_by_group_subgroup_2025.csv`

### Log de Classificação (Durante Seed)
Ver: `backend/artifacts/seed_classification_2025.jsonl` (quando COST_DEBUG=1)

### Relatório de Auditoria (Depois)
Ver: `backend/artifacts/audit_report_2025.json`

---

## ✅ Resultado Esperado

Após re-seed e validação:

```
Total Excel CUSTO: R$ 396.229,67
Total API CUSTO:   R$ 396.229,67
Diferença:         R$ 0,00 ✅
```

**Status Final**: ⏳ Aguardando re-seed e validação

