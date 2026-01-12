# ⚡ Quick Start - Local Dev Environment (Manual)

## Status: Docker não está rodando no momento

Para usar o ambiente local, você precisa:

### 1. Iniciar Docker Desktop
```bash
# Abra o Docker Desktop manualmente ou via terminal:
open -a Docker

# Aguarde ~1-2 minutos até ele estar completamente iniciado
# Verifique com:
docker info
```

### 2. Iniciar o Ambiente (automático)
```bash
cd /Users/lucianoterres/Documents/GitHub/finaflow

# Método 1: Script automático (recomendado)
./start_local_env.sh

# Método 2: Comandos manuais
docker-compose down -v              # Limpar anterior (opcional)
docker-compose up --build -d        # Iniciar em background
docker-compose ps                   # Ver status
```

### 3. Acessar o Ambiente
Aguarde ~30-60 segundos para os serviços inicializarem:

- **Frontend**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs
- **Database**: localhost:5432

### 4. Ver Logs
```bash
# Em outro terminal, veja os logs em tempo real:
docker-compose logs -f

# Ou apenas do backend:
docker-compose logs -f backend
```

---

## Se Ainda Estiver Com Dúvidas

Execute em ordem:

```bash
# Terminal 1: Iniciar Docker Desktop
open -a Docker

# Terminal 2: Aguarde Docker estar pronto (pode levar minutos)
# Quando estiver pronto:
cd /Users/lucianoterres/Documents/GitHub/finaflow

# Terminal 2: Iniciar ambiente
docker-compose up --build

# Terminal 3 (quando quiser): Ver status
docker-compose ps

# Terminal 3: Testar backend
curl http://localhost:8000/docs
```

---

## Estrutura de Arquivos Criados

✅ **docker-compose.yml** — Atualizado com PostgreSQL + volumes
✅ **.env.local** — Variáveis de ambiente locais
✅ **LOCAL_DEV_SETUP.md** — Documentação completa
✅ **start_local_env.sh** — Script de inicialização automática

## Próximos Passos

1. Iniciar Docker Desktop
2. Rodar `./start_local_env.sh` ou `docker-compose up --build`
3. Verificar http://localhost:8000/docs
4. Começar a desenvolver (backend hot-reload automático)

---

**Data**: 2024
**Status**: Pronto para inicialização manual
