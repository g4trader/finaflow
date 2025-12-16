# E2E: Consistência Planilha → API → UI

Este documento descreve como executar o fluxo E2E completo que valida que os números da planilha do cliente estão replicados corretamente no sistema (DB + API + UI).

## Objetivo

Rodar um único comando e obter **PASS/FAIL** garantindo que:
- Seed a partir do Excel funciona corretamente
- API retorna valores consistentes com a planilha
- UI exibe valores consistentes com a API

## Pré-requisitos

### Backend
- Python 3.8+
- Dependências: `pip install pandas openpyxl requests`
- Arquivo Excel em `backend/data/fluxo_caixa_2025.xlsx` (ou caminho customizado)
- `DATABASE_URL` configurada (PostgreSQL)

### Frontend
- Node.js 18+
- Playwright instalado: `npm install` (já inclui `@playwright/test`)
- Frontend rodando em `http://localhost:3000` (ou `FRONTEND_URL` customizado)

## Como Rodar Localmente

### 1. Backend E2E (Planilha → API)

```bash
cd backend
./scripts/run_e2e_sheet_to_api.sh --year 2025
```

Ou diretamente:

```bash
cd backend
python3 scripts/e2e_sheet_to_api.py --file data/fluxo_caixa_2025.xlsx --year 2025
```

**Parâmetros:**
- `--file`: Caminho do arquivo Excel (default: `data/fluxo_caixa_2025.xlsx`)
- `--year`: Ano a validar (default: 2025)
- `--backend-url`: URL do backend (default: via env `BACKEND_URL`)
- `--run-seed`: Executar seed antes de validar (default: True)
- `--no-seed`: Não executar seed (usar dados existentes)
- `--tolerance`: Tolerância em centavos (default: 0.01)

**Exit Codes:**
- `0`: PASS - Todos os valores batem
- `1`: Erro de execução
- `2`: FAIL - Mismatches encontrados

### 2. Frontend E2E (API → UI)

```bash
cd frontend
npm run e2e:consistency
```

Ou todos os testes E2E:

```bash
npm run e2e
```

**Variáveis de Ambiente:**
- `FRONTEND_URL`: URL do frontend (default: `http://localhost:3000`)
- `NEXT_PUBLIC_API_URL`: URL do backend (default: staging)

## Como Rodar Contra STAGING

### Backend

```bash
export DATABASE_URL="postgresql://user:pass@staging-db:5432/finaflow"
export BACKEND_URL="https://finaflow-backend-staging-642830139828.us-central1.run.app"

cd backend
./scripts/run_e2e_sheet_to_api.sh --year 2025 --no-seed
```

**Nota:** Se usar `--no-seed`, os dados devem já estar populados no banco.

### Frontend

```bash
export FRONTEND_URL="https://finaflow-frontend-staging.example.com"
export NEXT_PUBLIC_API_URL="https://finaflow-backend-staging-642830139828.us-central1.run.app"

cd frontend
npm run e2e:consistency
```

## Como Interpretar Falhas

### Backend E2E

**Erro de Execução (exit 1):**
- Verificar `DATABASE_URL`
- Verificar se o arquivo Excel existe
- Verificar dependências Python

**Mismatches (exit 2):**
- O script imprime diffs detalhados:
  ```
  ❌ MES=2025-01 TIPO=RECEITA esperado=1000.00 obtido=999.99 delta=0.01
  ```
- Verificar:
  - Se o seed foi executado corretamente
  - Se há diferenças de arredondamento (aumentar `--tolerance` se necessário)
  - Se a planilha foi atualizada mas o seed não foi reexecutado

### Frontend E2E

**Falha nos Totais:**
- Verificar se a API está retornando dados corretos
- Verificar se os seletores CSS estão corretos (podem precisar ajuste conforme estrutura do frontend)

**Falha nos Meses:**
- Verificar se a tabela mensal está renderizando corretamente
- Verificar se os índices das células estão corretos (podem variar conforme estrutura)

## Dependências Mínimas

### Backend
- `pandas`: Leitura de Excel
- `openpyxl`: Suporte a .xlsx
- `requests`: Chamadas HTTP à API
- `sqlalchemy`: Conexão com banco

### Frontend
- `@playwright/test`: Framework de testes E2E
- Frontend Next.js rodando (para testes locais)

## Comando Único (Makefile opcional)

Criar `Makefile` na raiz do projeto:

```makefile
.PHONY: e2e
e2e:
	@echo "🚀 Executando E2E completo..."
	@cd backend && ./scripts/run_e2e_sheet_to_api.sh --year 2025
	@cd frontend && npm run e2e:consistency
```

Então:

```bash
make e2e
```

## Troubleshooting

### Backend não consegue conectar ao banco
- Verificar `DATABASE_URL`
- Verificar se o banco está acessível
- Se usar Cloud SQL, verificar se o proxy está rodando

### Frontend não encontra elementos
- Verificar se o frontend está rodando
- Verificar se os seletores CSS estão corretos
- Executar `npx playwright codegen` para gerar seletores atualizados

### Valores não batem
- Verificar tolerância (default: 0.01 centavos)
- Verificar se o seed foi executado após atualizar a planilha
- Verificar logs do seed para erros de parsing

## Exemplo de Saída (PASS)

```
🚀 E2E: VALIDAÇÃO PLANILHA → API
================================================================================
Arquivo: backend/data/fluxo_caixa_2025.xlsx
Ano: 2025
Backend: https://finaflow-backend-staging-642830139828.us-central1.run.app
Executar seed: True
Tolerância: 0.01
================================================================================

📥 EXECUTANDO SEED
================================================================================
✅ Seed executado com sucesso

📖 LENDO PLANILHA E AGREGANDO
================================================================================
✅ Planilha lida: 1234 lançamentos

🔐 FAZENDO LOGIN NA API
================================================================================
✅ Login realizado com sucesso

📡 CONSUMINDO API
================================================================================
✅ API consumida com sucesso

📊 VALIDANDO TOTAIS ANUAIS
================================================================================
✅ RECEITA: 100000.00 (delta: 0.00)
✅ DESPESA: 50000.00 (delta: 0.00)
✅ CUSTO: 20000.00 (delta: 0.00)
✅ SALDO: 30000.00 (delta: 0.00)

📅 VALIDANDO TODOS OS 12 MESES
================================================================================
✅ Todos os 12 meses estão consistentes

📋 RESUMO FINAL
================================================================================
✅ PASS: Todos os valores batem!

Totais Anuais:
  Receita: 100000.00
  Despesa: 50000.00
  Custo: 20000.00
  Saldo: 30000.00

Meses verificados: Jan, Jun, Dez
```

## Exemplo de Saída (FAIL)

```
❌ MES=2025-01 TIPO=RECEITA esperado=1000.00 obtido=999.99 delta=0.01
❌ MES=2025-06 TIPO=DESPESA esperado=500.00 obtido=501.00 delta=1.00

📋 RESUMO FINAL
================================================================================
❌ FAIL: Mismatches encontrados
  - Totais anuais não batem
  - Alguns meses não batem
```

