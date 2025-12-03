# 🔐 Credenciais de QA - Ambiente Staging

## 📅 Data: Janeiro 2025

## 👤 Usuário de QA

**Email**: `qa@finaflow.test`  
**Username**: `qa`  
**Senha**: `QaFinaflow123!`  
**Role**: `super_admin`  
**Status**: `active`

## 🏢 Tenant e Business Unit

**Tenant**: FinaFlow Staging  
**Business Unit**: Matriz (MAT)

## 🔗 URLs de Acesso

**Frontend Staging**: https://finaflow-lcz5.vercel.app/  
**Backend Staging**: https://finaflow-backend-staging-642830139828.us-central1.run.app

## 📋 Como Criar o Usuário (se necessário)

### Via Endpoint (Recomendado)

```bash
curl -X POST https://finaflow-backend-staging-642830139828.us-central1.run.app/api/v1/auth/create-qa-user \
  -H "Content-Type: application/json"
```

### Via Banco de Dados

```sql
-- Conectar ao banco staging
gcloud sql connect finaflow-db-staging --user=finaflow_user --database=finaflow

-- Verificar se usuário existe
SELECT * FROM users WHERE email = 'qa@finaflow.test';

-- Se não existir, criar (hash precisa ser gerado via Python)
-- Ver script: backend/seed_staging_user.py
```

## ✅ Teste de Login

### Via API

```bash
curl -X POST https://finaflow-backend-staging-642830139828.us-central1.run.app/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=qa@finaflow.test&password=QaFinaflow123!"
```

**Resposta esperada**:
```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Via Frontend

1. Acessar: https://finaflow-lcz5.vercel.app/login
2. Preencher:
   - Email: `qa@finaflow.test`
   - Senha: `QaFinaflow123!`
3. Clicar em "Entrar"
4. Verificar redirecionamento para dashboard ou seleção de BU

## ⚠️ Notas Importantes

- Este usuário é **temporário** para testes de QA
- Após validar que login funciona, pode ser removido ou mantido
- Endpoint `/api/v1/auth/create-qa-user` deve ser **removido** após uso
- Credenciais são para **ambiente staging apenas**

## 🔒 Segurança

- Senha segue padrão: `QaFinaflow123!` (maiúscula, minúscula, número, caractere especial)
- Hash gerado com bcrypt (rounds=12)
- Usuário tem role `super_admin` para permitir testes completos

