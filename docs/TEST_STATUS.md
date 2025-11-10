# 🧪 STATUS DOS TESTES - FinaFlow

**Atualizado em**: 07/11/2025  
**Responsável**: Equipe FinaFlow  
**Objetivo**: Consolidar o estado atual da suíte de testes e apontar lacunas para que o sistema esteja operacional com confiança.

---

## 🔄 Como Executar os Testes Hoje

### Backend (pytest)
1. Criar e ativar um ambiente virtual Python 3.10+.
2. Instalar dependências:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Exportar variáveis essenciais (exemplos):
   ```bash
   export JWT_SECRET=testing-secret
   export PROJECT_ID=test-project
   export DATASET=test-dataset
   export DATABASE_URL=postgresql://usuario:senha@localhost:5432/finaflow
   ```
4. Executar a suíte:
   ```bash
   pytest backend/tests
   ```

> ⚠️ **Bloqueio atual**: o comando `pytest` não está disponível por padrão no ambiente local. É necessário instalar as dependências antes de rodar.

### Frontend (Jest + Testing Library)
1. Na pasta `frontend/`, instalar dependências: `npm install`.
2. Executar testes: `npm test`.
3. Para cobertura: `npm test -- --coverage`.

---

## ✅ Cobertura Existente

| Camada | Arquivo / Pasta | O que cobre | Observações |
|--------|-----------------|-------------|-------------|
| Backend | `backend/tests/test_account_import.py` | Importação de contas via BigQuery (sucesso/erro) | Usa stubs para BigQuery e valida resumo do import. |
| Backend | `backend/tests/test_csv_importer.py` | Serviço genérico de importação CSV | Cobre sucesso, erro do GoogleCloud e arquivo inexistente. |
| Backend | `backend/tests/test_finance_api.py` | Endpoints `/accounts`, `/transactions`, `/forecast`, `/reports` | Valida RBAC básico, validações de payload e isolamento por tenant. |
| Backend | `backend/tests/test_groups_api.py` | Endpoints de grupos | Testa RBAC (tenant vs super_admin) e operações de update/delete. |
| Backend | `backend/tests/test_import_csv_cli.py` | CLI `import_csv.py` | Garante que cada CSV recebido é enviado ao loader com os parâmetros corretos. |
| Backend | `backend/tests/test_reporting.py` | Serviço de relatórios (cash flow) | Valida agregação mensal/diária e isolamento por tenant. |
| Backend | `tests/test_transactions_postgres.py` (raiz) | Fluxo CRUD completo em `/transactions` usando Postgres real | Requer banco acessível; cria/derruba tabelas. |
| Frontend | `frontend/__tests__/AuthContext.test.tsx` | Contexto de autenticação | Cobre login, logout, signup com/sem token. |
| Frontend | `frontend/__tests__/reports.test.tsx` | Página de relatórios | Garante fetch de dados e renderização básica do gráfico. |
| Scripts | `test_select_endpoint.py`, `backend/test_users_endpoint.py` | Smoke tests manuais | Dependem de serviços externos (Cloud Run/Postgres remoto). |

---

## ❗ Lacunas Identificadas

- **Ausência de testes automáticos para autenticação completa**: não há cobertura para `/api/v1/auth/login`, `/refresh`, seleção de Business Unit ou fluxo multi-tenant end-to-end.
- **Cobertura limitada de RBAC**: testes garantem negação de acesso, mas não validam concessão para cada role (ex.: `tenant_admin`, `finance_manager`).
- **Integrações externas**:
  - Importadores via Google Sheets (`services/google_sheets_importer.py` e `services/llm_sheet_importer.py`).
  - Serviços de dashboard/analytics (`services/dashboard_service.py`).
- **Models e migrações**: não há testes garantindo criação de tabelas e constraints (ex.: Alembic/migrations).
- **Frontend**: somente AuthContext e Reports possuem testes. Páginas críticas (`login`, `select-business-unit`, `transactions`, `dashboard`) não estão cobertas.
- **CI/CD**: não existe pipeline automatizado (GitHub Actions/Cloud Build) executando as suítes em cada PR.
- **Dependências reais**: testes como `test_transactions_postgres.py` dependem de um banco pré-configurado (`DATABASE_URL`). Não há fixture para banco temporário (ex.: PostgreSQL container).
- **Cobertura de regressões recentes**: correção de `select-business-unit` e `fix_login_issue` não possuem testes dedicados.

---

## 🛠️ Plano de Ação Recomendado

1. **Setup e Padronização**
   - [ ] Adicionar `requirements-dev.txt` com pytest, coverage e plugins.
   - [ ] Criar `Makefile` ou scripts (`npm run test:backend`) para execução unificada.
   - [ ] Configurar `.env.test` com variáveis seguras e banco local (ex.: Docker Compose).

2. **Backend**
   - [ ] Criar testes para `/api/v1/auth/login`, `/refresh`, `/select-business-unit` e `/users/me`.
   - [ ] Adicionar testes de permissões para cada role em endpoints principais.
   - [ ] Cobrir serviços de importação Google Sheets e dashboards com mocks.
   - [ ] Garantir fixtures reutilizáveis para criação de dados (tenants, usuários, contas).
   - [ ] Incorporar testes de integração que usem um PostgreSQL efêmero (ex.: `pytest-postgresql`).

3. **Frontend**
   - [ ] Testar fluxo de login/logout (pages `login.tsx`, `select-business-unit.tsx`).
   - [ ] Cobrir componentes críticos (`ProtectedRoute`, tabelas de transações, dashboards).
   - [ ] Validar interações em `csv-import.tsx` e `transactions.tsx` (mock da API).
   - [ ] Configurar `msw` ou mocks centralizados para chamadas HTTP.

4. **CI/CD e Qualidade**
   - [ ] Configurar GitHub Action ou Cloud Build para rodar `pytest` e `npm test`.
   - [ ] Adicionar badge de status de testes no `README.md`.
   - [ ] Definir meta de cobertura (ex.: 70%) e integrar com `coverage.py` e `jest --coverage`.

---

## 📋 Checklist Rápido Para Operacionalizar

- [ ] Ambiente de testes configurado (venv + dependências + banco local).
- [ ] Suíte `pytest backend/tests` executando com sucesso.
- [ ] Suíte `npm test` executando com sucesso.
- [ ] Testes críticos de autenticação e multi-tenant adicionados.
- [ ] Fluxo de deploy inclui execução automática dos testes.
- [ ] Documentação atualizada (`README`, `docs/`) com instruções de testes.

---

## 🧭 Próximos Passos Imediatos

1. Preparar ambiente local: `pip install -r backend/requirements.txt` + `npm install`.
2. Garantir banco PostgreSQL local ou container para testes (`docker compose up db`).
3. Criar fixtures/factories reutilizáveis e refatorar testes existentes para usá-las.
4. Escrever testes automatizados para os últimos bugs críticos (login/BUs) antes de novos deploys.

---

> **Resumo**: Há uma boa base de testes para importações e algumas APIs, mas faltam casos críticos (autenticação, seleção de unidade, fluxo multi-tenant) e integração com banco local/CI. Após cobrir esses pontos, o sistema terá uma suíte confiável para operações e deploys contínuos.

