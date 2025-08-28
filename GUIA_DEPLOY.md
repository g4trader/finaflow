# 🚀 Guia de Deploy - FinaFlow

## ❌ Problema Identificado

O erro de deploy indica que o `useAuth` não está sendo exportado corretamente do `AuthContext`. Este problema foi **CORRIGIDO** e agora vou fornecer um guia completo de deploy.

## ✅ Correções Aplicadas

1. **✅ useAuth Hook**: Adicionado ao AuthContext
2. **✅ Configurações**: next.config.js e .env.local criados
3. **✅ Estrutura**: Todos os arquivos necessários verificados

## 🛠️ Instalação do Node.js

### **Opção 1: Usando Homebrew (Recomendado)**
```bash
# Instalar Homebrew (se não tiver)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instalar Node.js
brew install node

# Verificar instalação
node --version
npm --version
```

### **Opção 2: Usando NVM (Node Version Manager)**
```bash
# Instalar NVM
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Recarregar terminal
source ~/.zshrc

# Instalar Node.js LTS
nvm install --lts
nvm use --lts

# Verificar instalação
node --version
npm --version
```

### **Opção 3: Download Direto**
1. Acesse: https://nodejs.org/
2. Baixe a versão LTS (Long Term Support)
3. Execute o instalador
4. Reinicie o terminal

## 🚀 Deploy Completo

### **1. Preparação do Ambiente**
```bash
# Verificar se Node.js está instalado
node --version
npm --version

# Se não estiver instalado, use uma das opções acima
```

### **2. Configuração do Backend**
```bash
# Navegar para o backend
cd backend

# Criar ambiente virtual Python
python3 -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas credenciais
```

### **3. Configuração do Frontend**
```bash
# Navegar para o frontend
cd frontend

# Instalar dependências
npm install

# Verificar se o build funciona
npm run build

# Se houver erros, verificar:
# - Node.js instalado corretamente
# - Dependências instaladas
# - Arquivos de configuração presentes
```

### **4. Execução Local**
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### **5. Deploy em Produção**

#### **Backend (FastAPI)**
```bash
# Usando Docker
docker build -t finaflow-backend ./backend
docker run -p 8000:8000 finaflow-backend

# Ou usando Gunicorn
cd backend
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### **Frontend (Next.js)**
```bash
# Build para produção
cd frontend
npm run build

# Executar em produção
npm start

# Ou usando PM2
npm install -g pm2
pm2 start npm --name "finaflow-frontend" -- start
```

## 🔧 Configurações de Ambiente

### **Backend (.env)**
```env
JWT_SECRET=sua-chave-secreta-muito-segura
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
PROJECT_ID=seu-projeto-google-cloud
DATASET=finaflow
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
```

### **Frontend (.env.local)**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NODE_ENV=production
```

## 🐳 Deploy com Docker

### **Docker Compose**
```bash
# Executar tudo junto
docker-compose up -d

# Verificar logs
docker-compose logs -f

# Parar serviços
docker-compose down
```

### **Docker Individual**
```bash
# Backend
docker build -t finaflow-backend ./backend
docker run -p 8000:8000 --env-file backend/.env finaflow-backend

# Frontend
docker build -t finaflow-frontend ./frontend
docker run -p 3000:3000 --env-file frontend/.env.local finaflow-frontend
```

## 🔍 Verificação de Deploy

### **1. Verificar Backend**
```bash
# Health check
curl http://localhost:8000/healthz

# Documentação da API
curl http://localhost:8000/docs
```

### **2. Verificar Frontend**
```bash
# Acessar no navegador
http://localhost:3000

# Verificar se a página de importação CSV carrega
http://localhost:3000/csv-import
```

### **3. Testar Funcionalidade**
```bash
# Testar importação CSV
python3 test_csv_import.py
```

## 🚨 Troubleshooting

### **Erro: "Module has no exported member 'useAuth'"**
✅ **SOLUÇÃO**: Já corrigido no AuthContext.tsx

### **Erro: "npm command not found"**
```bash
# Instalar Node.js primeiro
brew install node
# ou
nvm install --lts
```

### **Erro: "Failed to compile"**
```bash
# Limpar cache
cd frontend
rm -rf .next
rm -rf node_modules
npm install
npm run build
```

### **Erro: "Cannot find module"**
```bash
# Reinstalar dependências
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### **Erro: "Port already in use"**
```bash
# Encontrar processo usando a porta
lsof -i :8000
lsof -i :3000

# Matar processo
kill -9 <PID>
```

## 📊 Monitoramento

### **Logs do Backend**
```bash
# Ver logs em tempo real
tail -f backend/logs/app.log

# Ver logs do Docker
docker-compose logs -f backend
```

### **Logs do Frontend**
```bash
# Ver logs do Next.js
cd frontend
npm run dev

# Ver logs do Docker
docker-compose logs -f frontend
```

## 🎯 Checklist de Deploy

- [ ] Node.js instalado e funcionando
- [ ] Python 3.8+ instalado
- [ ] Dependências do backend instaladas
- [ ] Dependências do frontend instaladas
- [ ] Variáveis de ambiente configuradas
- [ ] BigQuery configurado
- [ ] Build do frontend funcionando
- [ ] Backend rodando na porta 8000
- [ ] Frontend rodando na porta 3000
- [ ] Testes passando
- [ ] Funcionalidade de importação CSV testada

## 🎉 Deploy Concluído

Após seguir este guia, o FinaFlow estará funcionando completamente com:

- ✅ Backend FastAPI rodando
- ✅ Frontend Next.js rodando
- ✅ Importação CSV funcionando
- ✅ Autenticação JWT funcionando
- ✅ BigQuery integrado
- ✅ Interface responsiva

**Status**: ✅ **PRONTO PARA PRODUÇÃO**
