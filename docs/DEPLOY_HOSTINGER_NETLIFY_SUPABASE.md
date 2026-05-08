# Deploy: Hostinger + Netlify + Supabase

Arquitetura confirmada:

```text
Hostinger VPS / EasyPanel -> backend FastAPI Docker
Netlify                   -> frontend Next.js
Supabase                  -> Postgres
```

## 1. Backend no Hostinger EasyPanel

No EasyPanel, crie um app para o backend:

```text
Source: GitHub
Repository: g4trader/finaflow
App directory: backend
Dockerfile: Dockerfile
Port: 8080
Health check path: /health
```

Variáveis de ambiente:

```env
DATABASE_URL=postgresql://postgres.ufipviljyskfsbhvtclk:<PASSWORD_URL_ENCODED>@aws-1-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require
SECRET_KEY=<strong-secret>
JWT_SECRET=<strong-jwt-secret>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
PROJECT_ID=finaflow
ENVIRONMENT=production
ALLOWED_HOSTS=*
CORS_ORIGINS=https://<netlify-site>.netlify.app
```

O backend usa `PORT` quando a plataforma injeta essa variável e cai para `8080` como padrão.

Depois do deploy, valide:

```bash
curl https://<backend-domain>/health
curl -X POST https://<backend-domain>/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"qa@finaflow.test","password":"QaFinaflow123!"}'
```

## 2. Frontend no Netlify

O arquivo `netlify.toml` na raiz configura:

```text
base: frontend
build: npm run build
publish: .next
plugin: @netlify/plugin-nextjs
```

No Netlify, configure estas variáveis:

```env
NEXT_PUBLIC_API_URL=https://<backend-domain>
BACKEND_URL=https://<backend-domain>
NEXT_PUBLIC_SUPABASE_URL=https://ufipviljyskfsbhvtclk.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=<publishable-key>
```

Depois que o domínio final do Netlify existir, volte no EasyPanel e ajuste:

```env
CORS_ORIGINS=https://<netlify-site>.netlify.app
```

Se também houver domínio customizado:

```env
CORS_ORIGINS=https://<netlify-site>.netlify.app,https://app.seudominio.com
```

## 3. Supabase

Use o Session Pooler IPv4 para o backend:

```text
host: aws-1-us-east-1.pooler.supabase.com
port: 5432
user: postgres.ufipviljyskfsbhvtclk
database: postgres
sslmode: require
```

Não use a connection string direta `db.ufipviljyskfsbhvtclk.supabase.co` em containers, porque ela pode resolver para IPv6 e falhar em alguns ambientes.

## 4. Smoke test final

Após backend e frontend publicados:

```bash
curl https://<backend-domain>/health
```

No browser:

```text
https://<netlify-site>.netlify.app/login

Usuário: qa@finaflow.test
Senha: QaFinaflow123!
```

O login deve redirecionar para `/dashboard`.

