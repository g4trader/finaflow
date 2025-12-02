# 📋 DOCUMENTO COMPLETO DO SISTEMA FINAFLOW
## Para Product Manager (ChatGPT5)

**Data de Criação**: Janeiro 2025  
**Versão do Sistema**: 1.0.0  
**Status**: ✅ Sistema em Produção  
**Última Atualização**: Janeiro 2025

---

## 📌 ÍNDICE

1. [Visão Geral do Projeto](#visão-geral-do-projeto)
2. [Arquitetura do Sistema](#arquitetura-do-sistema)
3. [Stack Tecnológica](#stack-tecnológica)
4. [Estrutura do Projeto](#estrutura-do-projeto)
5. [Modelo de Dados](#modelo-de-dados)
6. [Funcionalidades Implementadas](#funcionalidades-implementadas)
7. [Estado Atual - Local e Produção](#estado-atual---local-e-produção)
8. [Configurações e Variáveis de Ambiente](#configurações-e-variáveis-de-ambiente)
9. [APIs e Endpoints](#apis-e-endpoints)
10. [Processo de Deploy](#processo-de-deploy)
11. [Estrutura de Autenticação e Autorização](#estrutura-de-autenticação-e-autorização)
12. [Problemas Conhecidos e Histórico](#problemas-conhecidos-e-histórico)
13. [Próximos Passos e Roadmap](#próximos-passos-e-roadmap)
14. [Comandos Úteis](#comandos-úteis)

---

## 🎯 VISÃO GERAL DO PROJETO

### O que é o FinaFlow?

**FinaFlow** é um sistema SaaS (Software as a Service) de gestão financeira empresarial com as seguintes características principais:

- **Multi-tenant**: Suporte a múltiplas empresas (tenants) isoladas
- **Multi-filial**: Suporte a múltiplas unidades de negócio (Business Units) por empresa
- **Controle Granular de Acesso**: Sistema RBAC (Role-Based Access Control) com permissões por tenant e business unit
- **Gestão Financeira Completa**: Transações, plano de contas, fluxo de caixa, relatórios, previsões
- **Importação de Dados**: Suporte a importação via CSV e Google Sheets
- **Dashboard Executivo**: Visualizações e métricas financeiras

### Objetivo do Sistema

Fornecer uma plataforma completa para gestão financeira empresarial, permitindo que empresas gerenciem suas finanças de forma centralizada, com controle de acesso granular e suporte a múltiplas filiais.

---

## 🏗️ ARQUITETURA DO SISTEMA

### Arquitetura Geral

```
┌─────────────────────────────────────────────────────────────┐
│                        USUÁRIOS                              │
└───────────────────────┬───────────────────────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────────────┐
        │     FRONTEND (Next.js)                │
        │     Vercel - CDN Global               │
        │     https://finaflow.vercel.app       │
        └───────────────┬───────────────────────┘
                        │
                        │ HTTPS/REST API
                        │
        ┌───────────────▼───────────────────────┐
        │     BACKEND (FastAPI)                 │
        │     Google Cloud Run                  │
        │     https://finaflow-backend-...      │
        └───────────────┬───────────────────────┘
                        │
                        │ PostgreSQL (via Unix Socket)
                        │
        ┌───────────────▼───────────────────────┐
        │     BANCO DE DADOS                    │
        │     Google Cloud SQL (PostgreSQL)     │
        │     Projeto: trivihair                │
        └───────────────────────────────────────┘
```

### Componentes Principais

1. **Frontend (Next.js)**
   - Deploy: Vercel
   - Framework: Next.js 13 com App Router
   - Linguagem: TypeScript
   - UI: Tailwind CSS
   - Estado: Context API (AuthContext)

2. **Backend (FastAPI)**
   - Deploy: Google Cloud Run
   - Framework: FastAPI
   - Linguagem: Python 3.11
   - ORM: SQLAlchemy 2.0
   - Autenticação: JWT (python-jose)

3. **Banco de Dados**
   - Tipo: PostgreSQL 14
   - Host: Google Cloud SQL
   - Conexão: Unix Socket (produção) / TCP (desenvolvimento)

---

## 💻 STACK TECNOLÓGICA

### Frontend

| Tecnologia | Versão | Uso |
|-----------|--------|-----|
| Next.js | 13.5.11 | Framework React com SSR |
| React | 18.2.0 | Biblioteca UI |
| TypeScript | 5.4.0 | Type safety |
| Tailwind CSS | 3.4.9 | Estilização |
| Axios | 1.6.7 | Cliente HTTP |
| Chart.js | 4.5.1 | Gráficos |
| Recharts | 2.10.3 | Gráficos alternativos |
| Framer Motion | 11.3.12 | Animações |
| JWT Decode | 3.1.2 | Decodificação de tokens |

### Backend

| Tecnologia | Versão | Uso |
|-----------|--------|-----|
| FastAPI | 0.104.1 | Framework web assíncrono |
| Python | 3.11 | Linguagem |
| SQLAlchemy | 2.0.23 | ORM |
| PostgreSQL | 14 | Banco de dados |
| psycopg2-binary | 2.9.9 | Driver PostgreSQL |
| python-jose | 3.3.0 | JWT tokens |
| passlib | 1.7.4 | Hash de senhas |
| Pydantic | 2.5.0 | Validação de dados |
| Uvicorn | 0.24.0 | ASGI server |

### Infraestrutura

| Serviço | Uso |
|--------|-----|
| Vercel | Deploy frontend (CDN global) |
| Google Cloud Run | Deploy backend (containers) |
| Google Cloud SQL | Banco de dados gerenciado |
| Google Cloud Build | CI/CD |
| Docker | Containerização |

---

## 📁 ESTRUTURA DO PROJETO

### Estrutura Completa

```
finaflow/
├── frontend/                          # Aplicação Next.js
│   ├── pages/                        # Páginas da aplicação
│   │   ├── login.tsx                 # Página de login
│   │   ├── dashboard.tsx             # Dashboard principal
│   │   ├── transactions.tsx          # Gestão de transações
│   │   ├── accounts.tsx              # Gestão de contas
│   │   ├── select-business-unit.tsx # Seleção de BU após login
│   │   ├── admin/                    # Páginas administrativas
│   │   │   ├── companies.tsx
│   │   │   ├── onboard-company.tsx
│   │   │   └── onboard-simple.tsx
│   │   └── api/                      # API Routes (proxies)
│   │       ├── proxy-login.ts
│   │       ├── proxy-business-units.ts
│   │       └── proxy-select-bu.ts
│   ├── components/                   # Componentes React
│   │   ├── cards/                    # Cards do dashboard
│   │   ├── charts/                   # Gráficos
│   │   ├── forms/                    # Formulários
│   │   ├── layout/                   # Layout principal
│   │   └── ui/                       # Componentes UI base
│   ├── context/                      # Context API
│   │   └── AuthContext.tsx           # Context de autenticação
│   ├── services/                     # Serviços
│   │   └── api.ts                    # Cliente API (axios)
│   ├── lib/                          # Utilitários
│   │   ├── api/                      # Funções de API
│   │   └── hooks/                    # React hooks
│   ├── types/                        # TypeScript types
│   ├── styles/                       # Estilos globais
│   └── public/                       # Assets estáticos
│
├── backend/                          # Aplicação FastAPI
│   ├── app/
│   │   ├── main.py                   # Entry point FastAPI
│   │   ├── database.py               # Configuração DB
│   │   ├── config.py                 # Configurações
│   │   ├── api/                      # Endpoints REST
│   │   │   ├── __init__.py           # Router principal
│   │   │   ├── auth.py               # Autenticação
│   │   │   ├── transactions.py       # Transações
│   │   │   ├── accounts.py           # Contas
│   │   │   ├── financial.py         # Financeiro
│   │   │   ├── dashboard.py          # Dashboard
│   │   │   ├── bank_accounts.py      # Contas bancárias
│   │   │   ├── chart_accounts.py     # Plano de contas
│   │   │   ├── csv_import.py         # Importação CSV
│   │   │   ├── users.py              # Usuários
│   │   │   ├── tenants.py            # Empresas
│   │   │   ├── caixa.py              # Caixa/Fluxo
│   │   │   ├── investments.py        # Investimentos
│   │   │   └── ...
│   │   ├── models/                   # Modelos SQLAlchemy
│   │   │   ├── auth.py               # Usuários, Tenants, BUs
│   │   │   ├── financial_transactions.py
│   │   │   ├── chart_of_accounts.py
│   │   │   ├── conta_bancaria.py
│   │   │   ├── caixa.py
│   │   │   ├── investimento.py
│   │   │   └── ...
│   │   ├── services/                 # Lógica de negócio
│   │   │   ├── security.py           # Autenticação/JWT
│   │   │   ├── financial_service.py
│   │   │   ├── dashboard_service.py
│   │   │   ├── csv_importer.py
│   │   │   └── ...
│   │   └── middleware/               # Middlewares
│   │       └── auth.py               # Auth middleware
│   ├── cloudbuild.yaml               # CI/CD Cloud Build
│   ├── Dockerfile                    # Container Docker
│   └── requirements.txt              # Dependências Python
│
├── infrastructure/                   # Infraestrutura como código
│   └── cloudbuild.yaml
│
├── docs/                             # Documentação
├── scripts/                          # Scripts utilitários
├── csv/                              # Dados de exemplo/teste
└── migrations/                       # Migrations do banco (se houver)
```

### Arquivos Importantes na Raiz

- `README.md` - Visão geral do projeto
- `OVERVIEW_PROJETO.md` - Overview detalhado
- `API_DOCUMENTATION.md` - Documentação da API
- `Dockerfile` - Container do backend
- `vercel.json` - Configuração Vercel
- `requirements.txt` - Dependências Python (raiz)

---

## 🗄️ MODELO DE DADOS

### Entidades Principais e Relacionamentos

#### 1. **Tenant (Empresa)**
```python
- id: UUID (PK)
- name: String
- domain: String (unique)
- status: String (active/inactive)
- created_at, updated_at: DateTime
```

**Relacionamentos:**
- 1:N com Users
- 1:N com BusinessUnits
- 1:N com FinancialTransactions
- 1:N com ContaBancaria
- 1:N com Caixa
- 1:N com Investimento

#### 2. **BusinessUnit (Unidade de Negócio/Filial)**
```python
- id: UUID (PK)
- tenant_id: UUID (FK -> Tenant)
- name: String
- code: String
- status: String
- created_at, updated_at: DateTime
```

**Relacionamentos:**
- N:1 com Tenant
- 1:N com Users
- 1:N com FinancialTransactions
- 1:N com ContaBancaria
- 1:N com Caixa

#### 3. **User (Usuário)**
```python
- id: UUID (PK)
- tenant_id: UUID (FK -> Tenant)
- business_unit_id: UUID (FK -> BusinessUnit, nullable)
- department_id: UUID (FK -> Department, nullable)
- username: String (unique)
- email: String (unique)
- hashed_password: String
- first_name, last_name: String
- phone: String (nullable)
- role: String (admin/tenant_admin/tenant_user)
- status: String (active/pending_activation/suspended)
- last_login: DateTime
- failed_login_attempts: Integer
- locked_until: DateTime
- created_at, updated_at: DateTime
```

**Relacionamentos:**
- N:1 com Tenant
- N:1 com BusinessUnit
- N:1 com Department
- 1:N com UserSession
- 1:N com UserTenantAccess
- 1:N com UserBusinessUnitAccess

#### 4. **ChartAccount (Plano de Contas)**
```python
- id: UUID (PK)
- tenant_id: UUID (FK -> Tenant)
- business_unit_id: UUID (FK -> BusinessUnit)
- group_id: UUID (FK -> AccountGroup)
- subgroup_id: UUID (FK -> AccountSubgroup)
- code: String
- name: String
- account_type: String (receita/despesa/ativo/passivo)
- is_active: Boolean
- created_at, updated_at: DateTime
```

**Hierarquia:**
- AccountGroup (Grupo)
  - AccountSubgroup (Subgrupo)
    - ChartAccount (Conta)

#### 5. **FinancialTransaction (Transação Financeira)**
```python
- id: UUID (PK)
- tenant_id: UUID (FK -> Tenant)
- business_unit_id: UUID (FK -> BusinessUnit)
- chart_account_id: UUID (FK -> ChartAccount)
- liquidation_account_id: UUID (FK -> LiquidationAccount, nullable)
- reference: String
- description: Text
- amount: Decimal(15,2)
- transaction_date: DateTime
- transaction_type: Enum (receita/despesa)
- status: Enum (pendente/aprovada/cancelada)
- created_by: UUID (FK -> User)
- approved_by: UUID (FK -> User, nullable)
- is_active: Boolean
- notes: Text
- created_at, updated_at, approved_at: DateTime
```

#### 6. **ContaBancaria (Conta Bancária)**
```python
- id: UUID (PK)
- tenant_id: UUID (FK -> Tenant)
- business_unit_id: UUID (FK -> BusinessUnit)
- bank_name: String
- account_number: String
- agency: String
- account_type: String
- balance: Decimal
- is_active: Boolean
```

#### 7. **Caixa (Fluxo de Caixa)**
```python
- id: UUID (PK)
- tenant_id: UUID (FK -> Tenant)
- business_unit_id: UUID (FK -> BusinessUnit)
- date: Date
- opening_balance: Decimal
- closing_balance: Decimal
- total_revenue: Decimal
- total_expenses: Decimal
```

#### 8. **LancamentoDiario (Lançamento Diário)**
```python
- id: UUID (PK)
- tenant_id: UUID (FK -> Tenant)
- business_unit_id: UUID (FK -> BusinessUnit)
- date: Date
- description: String
- amount: Decimal
- transaction_type: Enum
- status: Enum
```

#### 9. **Investimento (Investimentos)**
```python
- id: UUID (PK)
- tenant_id: UUID (FK -> Tenant)
- business_unit_id: UUID (FK -> BusinessUnit)
- name: String
- type: String
- amount: Decimal
- start_date: Date
- end_date: Date (nullable)
```

### Permissões e Acesso

#### UserTenantAccess
- Vincula usuário a tenant com permissões específicas
- Permite que um usuário tenha acesso a múltiplas empresas

#### UserBusinessUnitAccess
- Vincula usuário a business unit com permissões específicas
- Permite controle granular por filial

---

## ✅ FUNCIONALIDADES IMPLEMENTADAS

### Autenticação e Autorização
- ✅ Login/Logout com JWT
- ✅ Refresh tokens
- ✅ Seleção de Business Unit após login
- ✅ Controle de acesso baseado em roles (RBAC)
- ✅ Middleware de autenticação
- ✅ Proteção de rotas no frontend

### Dashboard
- ✅ Métricas financeiras (receitas, despesas, saldo)
- ✅ Gráficos de receitas/despesas (Chart.js, Recharts)
- ✅ Visão mensal/anual
- ✅ Cards de resumo financeiro
- ✅ Filtros por período

### Gestão Financeira
- ✅ CRUD de transações financeiras
- ✅ CRUD de plano de contas (grupos, subgrupos, contas)
- ✅ CRUD de contas bancárias
- ✅ Lançamentos diários
- ✅ Previsões financeiras
- ✅ Fluxo de caixa

### Multi-tenant e Multi-filial
- ✅ Isolamento de dados por tenant
- ✅ Gestão de empresas (tenants)
- ✅ Gestão de unidades de negócio (business units)
- ✅ Onboarding de empresas
- ✅ Seleção de business unit no login

### Importação de Dados
- ✅ Importação CSV genérica
- ✅ Importação específica (contas, transações, plano de contas)
- ✅ Importação Google Sheets
- ✅ Templates para download
- ✅ Validação de dados

### Relatórios
- ✅ Fluxo de caixa diário/mensal
- ✅ Relatórios financeiros
- ✅ Análises mensais/anuais
- ✅ Totalizadores mensais
- ✅ Extrato de contas bancárias
- ✅ Exportação de dados

### Gestão de Usuários
- ✅ CRUD de usuários
- ✅ Permissões por tenant
- ✅ Permissões por business unit
- ✅ Gestão de roles
- ✅ Ativação/suspensão de usuários

### Investimentos
- ✅ CRUD de investimentos
- ✅ Vinculação a tenant e business unit

---

## 🌐 ESTADO ATUAL - LOCAL E PRODUÇÃO

### Produção

#### Frontend
- **URL**: https://finaflow.vercel.app
- **Plataforma**: Vercel
- **Status**: ✅ Online
- **Deploy**: Automático via Vercel (push para main)
- **Variáveis de Ambiente**:
  - `NEXT_PUBLIC_API_URL`: URL do backend

#### Backend
- **URL**: https://finaflow-backend-642830139828.us-central1.run.app
- **Plataforma**: Google Cloud Run
- **Projeto GCP**: `trivihair`
- **Região**: `us-central1`
- **Status**: ✅ Online
- **Recursos**:
  - Memória: 2Gi
  - CPU: 2
  - Timeout: 600s
  - Concorrência: 80
  - Min Instances: 1
  - Max Instances: 10
  - CPU Boost: Habilitado

#### Banco de Dados
- **Tipo**: PostgreSQL 14
- **Plataforma**: Google Cloud SQL
- **Instância**: `finaflow-db`
- **Projeto**: `trivihair`
- **Região**: `us-central1`
- **Conexão Produção**: Unix Socket (`/cloudsql/trivihair:us-central1:finaflow-db`)
- **Conexão Desenvolvimento**: TCP (`34.41.169.224:5432`)

### Desenvolvimento Local

#### Frontend
```bash
cd frontend
npm install
npm run dev
# Acessa em http://localhost:3000
```

#### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# Acessa em http://localhost:8000
```

#### Banco de Dados Local
- Configurar `DATABASE_URL` no `.env` ou variáveis de ambiente
- Executar migrations: `python backend/create_tables.py`

---

## ⚙️ CONFIGURAÇÕES E VARIÁVEIS DE AMBIENTE

### Backend (Cloud Run)

Variáveis configuradas no `cloudbuild.yaml`:

```bash
DATABASE_URL=postgresql://finaflow_user:finaflow_password@/finaflow_db?host=/cloudsql/trivihair:us-central1:finaflow-db
SECRET_KEY=finaflow-secret-key-2024
JWT_SECRET=finaflow-secret-key-2024
CORS_ORIGINS=https://finaflow.vercel.app
ALLOWED_HOSTS=finaflow.vercel.app
PROJECT_ID=trivihair
DATASET=finaflow
ENABLE_BIGQUERY=true
```

### Frontend (Vercel)

Variáveis de ambiente (configurar no painel Vercel):

```bash
NEXT_PUBLIC_API_URL=https://finaflow-backend-642830139828.us-central1.run.app
```

### Desenvolvimento Local

#### Backend (.env)
```bash
DATABASE_URL=postgresql://finaflow_user:finaflow_password@34.41.169.224:5432/finaflow_db
JWT_SECRET=your-secret-key-here
CORS_ORIGINS=http://localhost:3000
ALLOWED_HOSTS=localhost,127.0.0.1
```

#### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🔌 APIS E ENDPOINTS

### Base URLs

- **Produção Backend**: `https://finaflow-backend-642830139828.us-central1.run.app`
- **Produção Frontend**: `https://finaflow.vercel.app`
- **Local Backend**: `http://localhost:8000`
- **Local Frontend**: `http://localhost:3000`

### Autenticação

#### POST `/api/v1/auth/login`
Login do usuário
```json
{
  "username": "string",
  "password": "string"
}
```
**Resposta:**
```json
{
  "access_token": "jwt-token",
  "refresh_token": "refresh-token",
  "token_type": "bearer"
}
```

#### POST `/api/v1/auth/select-business-unit`
Seleciona business unit após login
```json
{
  "business_unit_id": "uuid"
}
```

#### GET `/api/v1/auth/user-business-units`
Lista business units disponíveis para o usuário

#### GET `/api/v1/auth/me`
Informações do usuário atual

#### POST `/api/v1/auth/logout`
Logout do usuário

### Transações Financeiras

#### GET `/api/v1/financial/transactions`
Lista transações (com filtros: start_date, end_date, account_id, transaction_type)

#### POST `/api/v1/financial/transactions`
Cria nova transação
```json
{
  "chart_account_id": "uuid",
  "amount": 1000.00,
  "description": "Descrição",
  "transaction_date": "2025-01-15T00:00:00",
  "transaction_type": "receita",
  "liquidation_account_id": "uuid"
}
```

#### PUT `/api/v1/financial/transactions/{id}`
Atualiza transação

#### DELETE `/api/v1/financial/transactions/{id}`
Deleta transação

### Plano de Contas

#### GET `/api/v1/chart-accounts/hierarchy`
Hierarquia completa (grupos → subgrupos → contas)

#### GET `/api/v1/chart-accounts/groups`
Lista grupos

#### GET `/api/v1/chart-accounts/subgroups?group_id={id}`
Lista subgrupos

#### GET `/api/v1/chart-accounts/accounts?subgroup_id={id}`
Lista contas

#### POST `/api/v1/chart-accounts/import`
Importa plano de contas via CSV

### Contas Bancárias

#### GET `/api/v1/financial/bank-accounts`
Lista contas bancárias

#### POST `/api/v1/financial/bank-accounts`
Cria conta bancária

### Fluxo de Caixa

#### GET `/api/v1/financial/cash-flow?start_date={date}&end_date={date}&period_type={type}`
Fluxo de caixa no período

### Dashboard

#### GET `/api/v1/dashboard/summary?start_date={date}&end_date={date}`
Resumo do dashboard

### Usuários

#### GET `/api/v1/users`
Lista usuários (requer autenticação)

#### POST `/api/v1/users`
Cria usuário

#### PUT `/api/v1/users/{id}`
Atualiza usuário

#### DELETE `/api/v1/users/{id}`
Deleta usuário

### Tenants (Empresas)

#### GET `/api/v1/tenants`
Lista empresas

#### POST `/api/v1/tenants`
Cria empresa

### Business Units

#### GET `/api/v1/business-units?tenant_id={id}`
Lista business units

#### POST `/api/v1/business-units`
Cria business unit

### Importação CSV

#### POST `/api/v1/csv/import-csv`
Importação genérica
```
Content-Type: multipart/form-data
file: arquivo.csv
table: nome_da_tabela
```

#### POST `/api/v1/csv/import/accounts`
Importa contas

#### POST `/api/v1/csv/import/transactions`
Importa transações

#### POST `/api/v1/csv/import/plan-accounts`
Importa plano de contas

### Health Check

#### GET `/health`
Status da API
```json
{
  "status": "healthy",
  "service": "finaflow-backend",
  "version": "1.0.0"
}
```

### Documentação Interativa

#### GET `/docs`
Swagger UI (FastAPI)

#### GET `/redoc`
ReDoc (documentação alternativa)

---

## 🚀 PROCESSO DE DEPLOY

### Deploy Backend (Google Cloud Run)

#### Via Cloud Build (Recomendado)

```bash
# Configurar projeto
gcloud config set project trivihair

# Deploy via Cloud Build
gcloud builds submit --config=backend/cloudbuild.yaml --project=trivihair .
```

O `cloudbuild.yaml` executa:
1. Build da imagem Docker
2. Push para Google Container Registry
3. Deploy no Cloud Run com configurações

#### Deploy Manual

```bash
# Build da imagem
docker build -t gcr.io/trivihair/finaflow-backend .

# Push para GCR
docker push gcr.io/trivihair/finaflow-backend

# Deploy no Cloud Run
gcloud run deploy finaflow-backend \
  --image gcr.io/trivihair/finaflow-backend \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --add-cloudsql-instances trivihair:us-central1:finaflow-db \
  --set-env-vars DATABASE_URL=...,JWT_SECRET=... \
  --port 8080 \
  --memory 2Gi \
  --cpu 2
```

### Deploy Frontend (Vercel)

#### Via CLI

```bash
cd frontend
vercel --prod
```

#### Via Git (Automático)

- Push para branch `main` no GitHub
- Vercel detecta e faz deploy automático

### Verificação de Deploy

#### Backend
```bash
# Verificar logs
gcloud logging tail "resource.type=cloud_run_revision" --project=trivihair

# Verificar status
curl https://finaflow-backend-642830139828.us-central1.run.app/health
```

#### Frontend
- Acessar https://finaflow.vercel.app
- Verificar console do navegador

---

## 🔐 ESTRUTURA DE AUTENTICAÇÃO E AUTORIZAÇÃO

### Fluxo de Autenticação

1. **Login**
   - Usuário envia username/password
   - Backend valida credenciais
   - Backend retorna JWT access_token e refresh_token
   - Frontend armazena tokens no localStorage

2. **Seleção de Business Unit**
   - Após login, usuário seleciona business unit
   - Backend gera novo token com business_unit_id no payload
   - Frontend atualiza token no localStorage

3. **Requisições Autenticadas**
   - Frontend envia token no header: `Authorization: Bearer {token}`
   - Backend valida token via middleware
   - Backend extrai tenant_id e business_unit_id do token
   - Backend filtra dados por tenant/business unit

### Roles e Permissões

#### Roles Disponíveis

1. **admin**
   - Acesso total ao sistema
   - Pode gerenciar todos os tenants

2. **tenant_admin**
   - Administrador de um tenant específico
   - Pode gerenciar usuários, business units do tenant
   - Acesso completo aos dados do tenant

3. **tenant_user**
   - Usuário comum do tenant
   - Acesso limitado conforme permissões

### Middleware de Autenticação

```python
# backend/app/middleware/auth.py
- Valida JWT token
- Extrai informações do usuário
- Verifica permissões
- Filtra dados por tenant/business unit
```

### Proteção de Rotas (Frontend)

```typescript
// frontend/components/ProtectedRoute.tsx
- Verifica token no localStorage
- Redireciona para login se não autenticado
- Verifica seleção de business unit
```

---

## ⚠️ PROBLEMAS CONHECIDOS E HISTÓRICO

### Problemas Resolvidos

1. ✅ **Erro 404 ao selecionar Business Unit**
   - **Causa**: Endpoint incorreto, código mock
   - **Solução**: Corrigido endpoint, implementado com banco real
   - **Status**: Resolvido

2. ✅ **Problema de conexão DB (Cloud SQL)**
   - **Causa**: Configuração incorreta de conexão
   - **Solução**: Configurado Unix Socket para Cloud Run
   - **Status**: Resolvido

3. ✅ **Timeout no login**
   - **Causa**: Conexão DB lenta
   - **Solução**: Otimizado pool de conexões, Unix Socket
   - **Status**: Resolvido

4. ✅ **CORS errors**
   - **Causa**: Configuração CORS incompleta
   - **Solução**: Configurado CORS para aceitar Vercel
   - **Status**: Resolvido

### Observações Importantes

1. **Projeto GCP**: Backend está no projeto `trivihair` (não `finaflow-prod`)
2. **Cloud SQL**: Banco PostgreSQL conectado via Unix Socket em produção
3. **Autenticação**: JWT tokens com expiração de 60 minutos
4. **CORS**: Configurado para aceitar requests do Vercel
5. **URL Backend**: Pode variar após deploy (Cloud Run gera nova URL)
   - Verificar URL atual no Cloud Run Console
   - Atualizar `NEXT_PUBLIC_API_URL` no Vercel

### Arquivos Duplicados (Observação)

- Existe `hybrid_app.py` na raiz e `backend/app/main.py`
- Dockerfile usa `hybrid_app_working.py` (raiz)
- Manter consistência entre arquivos

---

## 🗺️ PRÓXIMOS PASSOS E ROADMAP

### Melhorias de Código

- [ ] Refatorar estrutura duplicada (`app/` vs `backend/app/`)
- [ ] Adicionar testes automatizados (unitários e E2E)
- [ ] Melhorar tratamento de erros
- [ ] Adicionar logging estruturado
- [ ] Implementar rate limiting
- [ ] Adicionar cache (Redis)

### Funcionalidades

- [ ] Integrações bancárias (Open Banking)
- [ ] Relatórios avançados (PDF export)
- [ ] Dashboard mais completo (KPIs)
- [ ] Mobile app (PWA já configurado)
- [ ] Notificações (email, push)
- [ ] Auditoria completa (audit logs)

### Infraestrutura

- [ ] Configurar CI/CD completo (GitHub Actions)
- [ ] Adicionar monitoramento (Sentry, Cloud Monitoring)
- [ ] Configurar backups automáticos
- [ ] Melhorar escalabilidade (auto-scaling)
- [ ] Implementar CDN para assets
- [ ] Configurar SSL/TLS adequadamente

### Documentação

- [ ] Documentar API completa (OpenAPI/Swagger)
- [ ] Guias de usuário
- [ ] Documentação de deploy detalhada
- [ ] Documentação de desenvolvimento
- [ ] Guias de troubleshooting

### Segurança

- [ ] Implementar 2FA (Two-Factor Authentication)
- [ ] Adicionar rate limiting
- [ ] Implementar WAF (Web Application Firewall)
- [ ] Auditoria de segurança
- [ ] Compliance (LGPD, GDPR)

---

## 🛠️ COMANDOS ÚTEIS

### Logs

```bash
# Logs do Cloud Run
gcloud logging tail "resource.type=cloud_run_revision" --project=trivihair

# Logs apenas erros
gcloud logging tail "resource.type=cloud_run_revision AND severity>=ERROR" --project=trivihair

# Logs do Cloud SQL
gcloud logging tail "resource.type=cloudsql_database" --project=trivihair
```

### Banco de Dados

```bash
# Conectar ao Cloud SQL
gcloud sql connect finaflow-db --user=finaflow_user --project=trivihair

# Backup do banco
gcloud sql export sql finaflow-db gs://bucket/backup.sql --project=trivihair

# Restaurar backup
gcloud sql import sql finaflow-db gs://bucket/backup.sql --project=trivihair
```

### Deploy

```bash
# Deploy backend
cd backend
gcloud builds submit --config=cloudbuild.yaml --project=trivihair .

# Deploy frontend
cd frontend
vercel --prod

# Verificar status do Cloud Run
gcloud run services describe finaflow-backend --region=us-central1 --project=trivihair
```

### Desenvolvimento Local

```bash
# Iniciar backend
cd backend
uvicorn app.main:app --reload --port 8000

# Iniciar frontend
cd frontend
npm run dev

# Criar tabelas
python backend/create_tables.py

# Testar API
curl http://localhost:8000/health
```

### Docker

```bash
# Build local
docker build -t finaflow-backend .

# Run local
docker run -p 8000:8080 finaflow-backend

# Testar container
docker exec -it <container-id> /bin/bash
```

---

## 📞 CONTATOS E RECURSOS

### URLs Importantes

- **Frontend Produção**: https://finaflow.vercel.app
- **Backend Produção**: https://finaflow-backend-642830139828.us-central1.run.app
- **API Docs**: https://finaflow-backend-642830139828.us-central1.run.app/docs
- **Health Check**: https://finaflow-backend-642830139828.us-central1.run.app/health

### GCP Console

- **Cloud Run**: https://console.cloud.google.com/run?project=trivihair
- **Cloud SQL**: https://console.cloud.google.com/sql?project=trivihair
- **Cloud Build**: https://console.cloud.google.com/cloud-build?project=trivihair
- **Logs**: https://console.cloud.google.com/logs?project=trivihair

### Documentação Adicional

- `README.md` - Visão geral e quick start
- `OVERVIEW_PROJETO.md` - Overview detalhado
- `API_DOCUMENTATION.md` - Documentação da API
- `STATUS_ATUAL.md` - Status de problemas conhecidos

---

## 📝 NOTAS FINAIS

### Para o Product Manager

Este documento fornece uma visão completa do sistema FinaFlow, incluindo:

1. **Arquitetura**: Entendimento completo da estrutura
2. **Tecnologias**: Stack utilizada
3. **Funcionalidades**: O que está implementado
4. **Estado Atual**: O que está em produção
5. **APIs**: Endpoints disponíveis
6. **Deploy**: Como fazer deploy
7. **Problemas**: Histórico e resoluções
8. **Roadmap**: Próximos passos

### Pontos de Atenção

1. **Projeto GCP**: Backend está no projeto `trivihair` (não `finaflow-prod`)
2. **URL Backend**: Pode mudar após deploy (verificar no Cloud Run)
3. **Banco de Dados**: PostgreSQL no Cloud SQL, conexão via Unix Socket
4. **Autenticação**: JWT com expiração de 60 minutos
5. **Multi-tenant**: Isolamento completo de dados por tenant

### Próximas Ações Recomendadas

1. Revisar este documento com a equipe
2. Priorizar itens do roadmap
3. Definir sprints e milestones
4. Configurar monitoramento e alertas
5. Implementar testes automatizados

---

**Documento criado em**: Janeiro 2025  
**Última atualização**: Janeiro 2025  
**Versão**: 1.0.0  
**Mantido por**: Equipe FinaFlow

---

**FinaFlow** - Sistema de Gestão Financeira Empresarial SaaS 🚀


