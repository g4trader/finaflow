# 🚀 Setup Local Dev Environment - Finaflow

## Objetivo
Montar um ambiente de desenvolvimento local (Docker Compose) com:
- PostgreSQL 15 (banco de dados local)
- FastAPI Backend (Python, uvicorn com hot-reload)
- Next.js Frontend (React)
- Acesso direto sem depender de Cloud Run

## Pré-requisitos
- Docker Desktop instalado e rodando
- Docker Compose (incluído no Docker Desktop)
- Opcional: Git para clonar/sincronizar código

## ⚡ Início Rápido

### 1️⃣ Parar qualquer serviço anterior (se rodando)
```bash
# Se houver containers rodando, parar
docker-compose down

# Opcionalmente, limpar volumes (para DB 100% novo)
docker-compose down -v
```

### 2️⃣ Iniciar o ambiente local
```bash
cd /Users/lucianoterres/Documents/GitHub/finaflow

# Construir imagens e rodar (em background)
docker-compose up --build -d

# OU ver logs em tempo real (deixe em outro terminal)
docker-compose up --build
```

### 3️⃣ Verificar status dos serviços
```bash
# Ver se todos os containers estão rodando
docker-compose ps

# Ver logs de um serviço específico
docker-compose logs -f backend      # FastAPI backend
docker-compose logs -f postgres     # PostgreSQL
docker-compose logs -f frontend     # Next.js
```

### 4️⃣ Acessar o ambiente
- **Frontend (Next.js)**: http://localhost:3000
- **Backend API Docs (Swagger)**: http://localhost:8000/docs
- **Backend Redoc**: http://localhost:8000/redoc
- **Database (Postgres)**: localhost:5432
  - User: `finaflow_user`
  - Password: `Finaflow123!`
  - Database: `finaflow`

## 🔌 Conectar ao Banco de Dados Local

### Option 1: Terminal (psql)
```bash
# Conectar ao banco local
psql -h localhost -U finaflow_user -d finaflow

# Quando pedir password: Finaflow123!
```

### Option 2: DBeaver / pgAdmin
- Host: `localhost`
- Port: `5432`
- User: `finaflow_user`
- Password: `Finaflow123!`
- Database: `finaflow`

### Option 3: Docker Exec
```bash
# Conectar via container
docker-compose exec postgres psql -U finaflow_user -d finaflow
```

## 📝 Estrutura de Containers

```
finaflow-postgres-local  → PostgreSQL 15 (port 5432)
     ↓
finaflow-backend-local   → FastAPI uvicorn (port 8000)
     ↓
finaflow-frontend-local  → Next.js dev (port 3000)
```

## 🛠️ Tarefas Comuns

### Inicializar Banco com Migrações (Alembic)
```bash
# Rodar migrations automaticamente (já faz no startup)
docker-compose exec backend alembic upgrade head

# Ver status das migrations
docker-compose exec backend alembic current

# Revert última migration
docker-compose exec backend alembic downgrade -1
```

### Seedar Dados de Teste
```bash
# Copiar script seed para container e rodar
docker-compose exec backend python scripts/seed_test_data.py
```

### Limpar Banco Completamente
```bash
# Parar e remover volume de dados
docker-compose down -v

# Recriar (novo banco vazio)
docker-compose up --build -d
```

### Ver Logs em Tempo Real
```bash
# Todos os serviços
docker-compose logs -f

# Apenas backend
docker-compose logs -f backend

# Últimas 50 linhas + follow
docker-compose logs -f --tail=50 backend
```

### Executar Comando no Backend
```bash
# Ex: Listar arquivos
docker-compose exec backend ls -la

# Ex: Rodar script Python
docker-compose exec backend python scripts/some_script.py

# Ex: Instalar pacote Python
docker-compose exec backend pip install novo-pacote
```

### Parar e Desligar
```bash
# Parar containers (preserva dados)
docker-compose stop

# Parar e remover (limpa containers, preserva volumes)
docker-compose down

# Parar, remover containers E volumes (limpa TUDO)
docker-compose down -v
```

## 🔍 Troubleshooting

### ❌ "Cannot connect to Docker daemon"
- Verifique se Docker Desktop está rodando
- Mac: `open -a Docker`

### ❌ "Port 5432 already in use"
```bash
# Encontrar processo usando porta
lsof -i :5432

# Matar processo
kill -9 <PID>
```

### ❌ "Port 8000 already in use"
```bash
# Mesma abordagem
lsof -i :8000
kill -9 <PID>
```

### ❌ PostgreSQL não inicializa
```bash
# Verificar logs
docker-compose logs postgres

# Limpar volume de dados e reiniciar
docker-compose down -v
docker-compose up --build postgres
```

### ❌ Backend não consegue conectar ao DB
```bash
# Verificar se postgres está saudável
docker-compose ps

# Ver logs do backend
docker-compose logs backend

# Reiniciar backend após postgres estar ready
docker-compose restart backend
```

### ❌ Frontend não carrega
```bash
# Verificar logs
docker-compose logs frontend

# Se necessário, reinstalar node_modules
docker-compose exec frontend npm install
```

## 📚 Documentação Referência

- **Docker Compose**: https://docs.docker.com/compose/
- **FastAPI**: https://fastapi.tiangolo.com/
- **PostgreSQL**: https://www.postgresql.org/docs/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **Next.js**: https://nextjs.org/docs

## 🎯 Próximos Passos

1. ✅ Ambiente local rodando
2. ⏳ Implementar cursor-based pagination em `get_transactions_annual()`
3. ⏳ Fazer seed idempotente (FIX UniqueViolation)
4. ⏳ Testar onboarding flow localmente
5. ⏳ Validar funcionalidades antes de fazer push

---

**Última Atualização**: $(date)
**Status**: Ambiente pronto para desenvolvimento local
