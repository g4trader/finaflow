# 🔐 Credenciais do Sistema FINAFlow

**⚠️ ARQUIVO CONFIDENCIAL - NÃO COMMITAR NO GIT**

---

## 🌐 URLs do Sistema

| Componente | URL |
|------------|-----|
| Frontend | https://finaflow.vercel.app |
| Backend API | https://finaflow-backend-642830139828.us-central1.run.app |
| API Docs | https://finaflow-backend-642830139828.us-central1.run.app/docs |
| GCP Console | https://console.cloud.google.com/?project=trivihair |

---

## 👤 Usuário Admin

**Username**: `admin`  
**Password**: `admin123`  
**Email**: admin@finaflow.com  
**Role**: super_admin  
**Tenant**: FINAFlow (ID: 995c964a-eb82-4b60-95d6-1860ed989fdf)

### Token de Acesso (Exemplo)
```
Endpoint: POST https://finaflow-backend-642830139828.us-central1.run.app/api/v1/auth/login
Content-Type: application/x-www-form-urlencoded
Body: username=admin&password=admin123

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

## 🗄️ Banco de Dados (Cloud SQL)

**Tipo**: PostgreSQL 14  
**Instância**: finaflow-db  
**IP Público**: 34.41.169.224  
**Connection Name**: trivihair:us-central1:finaflow-db  

**Banco**: finaflow_db  
**Usuário**: finaflow_user  
**Senha**: finaflow_password  

**Root Password**: FinaFlow2024Secure!

### Conexão via psql
```bash
PGPASSWORD=finaflow_password psql -h 34.41.169.224 -U finaflow_user -d finaflow_db
```

### Conexão via Cloud SQL Proxy
```bash
cloud_sql_proxy -instances=trivihair:us-central1:finaflow-db=tcp:5432
psql -h localhost -U finaflow_user -d finaflow_db
```

**⚠️ IMPORTANTE**: Acesso público está DESABILITADO por padrão. Para conectar:
1. Habilitar temporariamente: `gcloud sql instances patch finaflow-db --authorized-networks=SEU_IP`
2. Ou usar Cloud SQL Proxy (recomendado)

---

## ☁️ Google Cloud Platform

### Projeto
- **ID**: trivihair
- **Número**: 642830139828
- **Service Account**: dashboardluciano@trivihair.iam.gserviceaccount.com

### Credenciais da Service Account
**Arquivo**: `google_credentials.json` (na raiz do projeto)

**⚠️ NÃO COMMITAR** este arquivo no Git!

Key ID: 555eaf8d3914368bcbfd9a64cb446cbeea803251

---

## 🐳 Container Registry

**Imagem**: gcr.io/trivihair/finaflow-backend:latest

### Push de Nova Versão
```bash
docker build -t gcr.io/trivihair/finaflow-backend .
docker push gcr.io/trivihair/finaflow-backend
```

---

## 🔑 Secrets e Variáveis de Ambiente

### Backend (Cloud Run)
```bash
DATABASE_URL=postgresql://finaflow_user:finaflow_password@/finaflow_db?host=/cloudsql/trivihair:us-central1:finaflow-db
SECRET_KEY=finaflow-secret-key-2024
CORS_ORIGINS=https://finaflow.vercel.app;http://localhost:3000
PROJECT_ID=trivihair
```

### Frontend (Vercel)
```bash
NEXT_PUBLIC_API_URL=https://finaflow-backend-642830139828.us-central1.run.app
```

---

## 📝 Como Atualizar Senhas

### 1. Senha do Usuário Admin
```bash
# Gerar novo hash
python3 << 'EOF'
import bcrypt
password = "NOVA_SENHA"
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
print(hashed.decode())
EOF

# Atualizar no banco
PGPASSWORD=finaflow_password psql -h 34.41.169.224 -U finaflow_user -d finaflow_db -c \
"UPDATE users SET hashed_password = 'HASH_GERADO' WHERE username = 'admin';"
```

### 2. Senha do Banco de Dados
```bash
gcloud sql users set-password finaflow_user \
  --instance=finaflow-db \
  --password=NOVA_SENHA

# Depois atualizar em:
# - Cloud Run (DATABASE_URL)
# - Scripts locais
# - Este arquivo
```

### 3. Secret Key (JWT)
```bash
# Gerar nova secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Atualizar no Cloud Run
gcloud run services update finaflow-backend \
  --region us-central1 \
  --update-env-vars SECRET_KEY=NOVA_SECRET_KEY
```

---

## 🔒 Segurança

### Boas Práticas Implementadas
- ✅ Banco de dados sem acesso público direto
- ✅ CORS configurado apenas para domínios autorizados
- ✅ JWT com expiração (30 minutos)
- ✅ Senhas hasheadas com bcrypt
- ✅ HTTPS em todas as comunicações
- ✅ Service account com permissões mínimas

### Recomendações Futuras
- [ ] Migrar secrets para Google Secret Manager
- [ ] Implementar rotação de senhas
- [ ] Configurar 2FA para admin
- [ ] Adicionar rate limiting
- [ ] Implementar audit logs

---

## 📞 Comandos Úteis

### Ver Logs do Backend
```bash
gcloud run services logs tail finaflow-backend --region us-central1 --project trivihair
```

### Resetar Senha do Admin via SQL
```bash
# Hash para senha "admin123"
UPDATE users SET hashed_password = '$2b$12$LIIaFNFYW6Bmcv/X47ZX/eLVmdbirQO3a6fwEln/h.pCsynW15o9y' 
WHERE username = 'admin';
```

### Verificar Usuários
```bash
PGPASSWORD=finaflow_password psql -h 34.41.169.224 -U finaflow_user -d finaflow_db -c \
"SELECT username, email, role, status FROM users;"
```

---

**Última Atualização**: 15 de Outubro de 2025  
**Responsável**: Equipe de Desenvolvimento  

**⚠️ MANTENHA ESTE ARQUIVO SEGURO E CONFIDENCIAL**


