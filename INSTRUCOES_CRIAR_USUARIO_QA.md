# 📋 Instruções para Criar Usuário QA no Staging

## 🎯 Objetivo

Criar usuário de QA no banco staging para permitir login e testes.

## 🔧 Método 1: Via Endpoint (Após Deploy)

### Passo 1: Aguardar Deploy
O endpoint `/api/v1/auth/create-qa-user` foi adicionado ao código e será disponibilizado após o próximo deploy do backend staging.

### Passo 2: Criar Usuário
```bash
curl -X POST https://finaflow-backend-staging-642830139828.us-central1.run.app/api/v1/auth/create-qa-user \
  -H "Content-Type: application/json"
```

### Passo 3: Verificar Resposta
Resposta esperada:
```json
{
  "success": true,
  "action": "criado",
  "user": {
    "email": "qa@finaflow.test",
    "username": "qa",
    "role": "super_admin"
  },
  "credentials": {
    "email": "qa@finaflow.test",
    "password": "QaFinaflow123!"
  }
}
```

## 🔧 Método 2: Via SQL Direto (Alternativo)

### Passo 1: Conectar ao Banco
```bash
gcloud sql connect finaflow-db-staging \
  --user=finaflow_user \
  --database=finaflow \
  --project=trivihair
```

### Passo 2: Executar SQL
```sql
-- Verificar se tenant existe
SELECT * FROM tenants WHERE domain = 'finaflow-staging.com';

-- Se não existir, criar tenant
INSERT INTO tenants (id, name, domain, status, created_at, updated_at)
VALUES (
  gen_random_uuid()::VARCHAR,
  'FinaFlow Staging',
  'finaflow-staging.com',
  'active',
  NOW(),
  NOW()
);

-- Verificar tenant criado
SELECT id FROM tenants WHERE domain = 'finaflow-staging.com';
-- Anotar o ID do tenant

-- Criar Business Unit (usar tenant_id do passo anterior)
INSERT INTO business_units (id, tenant_id, name, code, status, created_at, updated_at)
VALUES (
  gen_random_uuid()::VARCHAR,
  '<TENANT_ID_AQUI>',
  'Matriz',
  'MAT',
  'active',
  NOW(),
  NOW()
);

-- Verificar BU criada
SELECT id FROM business_units WHERE code = 'MAT' AND tenant_id = '<TENANT_ID_AQUI>';
-- Anotar o ID da BU

-- IMPORTANTE: Hash da senha precisa ser gerado via Python
-- Usar o script backend/seed_staging_user.py ou endpoint create-qa-user
```

**⚠️ ATENÇÃO**: O hash da senha precisa ser gerado via bcrypt. Não é possível criar usuário diretamente via SQL sem o hash correto.

## 🔧 Método 3: Usar Endpoint Existente (Temporário)

Se o endpoint `/api/v1/auth/create-superadmin` existir:

```bash
curl -X POST https://finaflow-backend-staging-642830139828.us-central1.run.app/api/v1/auth/create-superadmin \
  -H "Content-Type: application/json"
```

Isso criará usuário `admin` com senha `Admin@123`.

## ✅ Após Criar Usuário

### Testar Login via API
```bash
curl -X POST https://finaflow-backend-staging-642830139828.us-central1.run.app/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=qa@finaflow.test&password=QaFinaflow123!"
```

### Testar Login via Frontend
1. Acessar: https://finaflow-lcz5.vercel.app/login
2. Email: `qa@finaflow.test`
3. Senha: `QaFinaflow123!`
4. Clicar em "Entrar"

## 📝 Credenciais de QA

- **Email**: `qa@finaflow.test`
- **Senha**: `QaFinaflow123!`
- **Role**: `super_admin`
- **Status**: `active`

