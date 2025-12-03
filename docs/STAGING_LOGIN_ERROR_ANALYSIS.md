# 🔍 Análise do Erro 500 no Login - Staging

## 📅 Data: Janeiro 2025

## 🔴 Problema Identificado

**Erro**: `500 Internal Server Error` no endpoint `/api/v1/auth/login`

**Credenciais testadas**: 
- `admin` / `admin123` → ❌ Erro 500
- `qa@finaflow.test` / `QaFinaflow123!` → ❌ Erro 500 (após criar usuário)

## 🔍 Diagnóstico

### 1. Health Check
- ✅ **Status**: Funcional
- ✅ **Resposta**: `{"status":"healthy","service":"finaflow-backend","version":"1.0.0"}`

### 2. Endpoint de Login
- ❌ **Status**: Erro 500
- ❌ **Resposta**: `{"detail":"Erro interno do servidor"}`

### 3. Possíveis Causas

#### A. Usuário não existe no banco
- **Probabilidade**: Alta
- **Evidência**: Banco staging pode não ter sido inicializado com usuários
- **Solução**: Criar usuário via endpoint `/api/v1/auth/create-qa-user`

#### B. Problema de conexão com banco
- **Probabilidade**: Média
- **Evidência**: Health check funciona, mas queries podem falhar
- **Solução**: Verificar logs do Cloud Run para erros de conexão

#### C. Problema de hash de senha
- **Probabilidade**: Baixa
- **Evidência**: Código de hash está correto
- **Solução**: Verificar se hash está sendo gerado corretamente

#### D. Variável de ambiente ausente
- **Probabilidade**: Baixa
- **Evidência**: Health check funciona
- **Solução**: Verificar `JWT_SECRET` e outras variáveis

## 🔧 Solução Implementada

### Endpoint Temporário Criado

**Endpoint**: `POST /api/v1/auth/create-qa-user`

**Funcionalidade**:
- Cria tenant "FinaFlow Staging" se não existir
- Cria Business Unit "Matriz" se não existir
- Cria ou atualiza usuário QA com credenciais:
  - Email: `qa@finaflow.test`
  - Senha: `QaFinaflow123!`
  - Role: `super_admin`
  - Status: `active`

**Como usar**:
```bash
curl -X POST https://finaflow-backend-staging-642830139828.us-central1.run.app/api/v1/auth/create-qa-user \
  -H "Content-Type: application/json"
```

**Resposta esperada**:
```json
{
  "success": true,
  "action": "criado",
  "user": {
    "id": "...",
    "email": "qa@finaflow.test",
    "username": "qa",
    "role": "super_admin",
    "status": "active"
  },
  "credentials": {
    "email": "qa@finaflow.test",
    "password": "QaFinaflow123!"
  }
}
```

## 📋 Próximos Passos

1. ⏳ **Aguardar deploy do backend** (Cloud Build automático após push)
2. ✅ **Criar usuário QA** via endpoint `/api/v1/auth/create-qa-user`
3. ✅ **Testar login** com credenciais `qa@finaflow.test` / `QaFinaflow123!`
4. ✅ **Testar no frontend** https://finaflow-lcz5.vercel.app/login
5. ✅ **Remover endpoint temporário** após confirmar que funciona

## 🔗 URLs

- **Backend Staging**: https://finaflow-backend-staging-642830139828.us-central1.run.app
- **Health Check**: https://finaflow-backend-staging-642830139828.us-central1.run.app/health
- **Create QA User**: https://finaflow-backend-staging-642830139828.us-central1.run.app/api/v1/auth/create-qa-user
- **Login**: https://finaflow-backend-staging-642830139828.us-central1.run.app/api/v1/auth/login

