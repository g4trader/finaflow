# Supabase + Netlify setup

Guia rápido para usar Supabase como DB/Auth/Storage e publicar o frontend Next.js.

## 1. Criar projeto Supabase

- Acesse `https://app.supabase.com` e crie um projeto.
- Em `Settings > Database`, copie a connection string Postgres e use como `DATABASE_URL`.
- Em `Project Settings > API`, copie a URL do projeto e as chaves públicas/privadas.

## 2. Backend

Configure estas variáveis no ambiente do backend:

```env
DATABASE_URL=postgresql://...
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=public-anon-or-publishable-key
SUPABASE_SERVICE_ROLE_KEY=service-role-key
SECRET_KEY=replace-with-secret
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ORIGINS=http://localhost:3000
```

`SUPABASE_SERVICE_ROLE_KEY` deve ficar apenas no servidor. Não use essa chave em código que roda no browser.

## 3. Frontend Next.js

O pacote `@supabase/supabase-js` já está listado em `frontend/package.json`.

Variáveis públicas para `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=your-publishable-key
```

Também há suporte a `NEXT_PUBLIC_SUPABASE_ANON_KEY` no helper público, mas prefira `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` para ficar alinhado com o template.

Arquivos adicionados:

- `frontend/utils/supabase/client.ts`: cliente público para browser.
- `frontend/utils/supabase/server.ts`: helper server-side para API routes.

Exemplo no browser:

```ts
import supabase from '../utils/supabase/client'

if (!supabase) {
  throw new Error('Supabase env vars are not configured')
}

const { data, error } = await supabase.from('users').select('*')
```

Exemplo em API route:

```ts
import { createSupabaseServer } from '../../utils/supabase/server'

export default async function handler(req, res) {
  const supabase = createSupabaseServer()
  const { data, error } = await supabase.from('sensitive_table').select('*')
  return res.json({ data, error })
}
```

## 4. Desenvolvimento local

Instale/valide dependências:

```bash
cd frontend
npm install
npm ls @supabase/supabase-js
```

Verifique as variáveis do YAML no root:

```bash
python3 -c "from env_loader import load_env; import os; load_env(); print(os.environ.get('NEXT_PUBLIC_SUPABASE_URL'))"
```

Rode o frontend:

```bash
cd frontend
npm run dev
```

Teste no console do browser, trocando os placeholders pelos valores públicos:

```js
await fetch('https://your-project.supabase.co/auth/v1/settings', {
  headers: { apikey: 'your-publishable-key' }
}).then((res) => res.status)
```

Para testar o helper em uma página ou componente, importe `frontend/utils/supabase/client.ts` e execute uma consulta em uma tabela com RLS permitindo leitura.

## 5. Deploy

No Netlify/Vercel, configure apenas as variáveis públicas no ambiente do frontend:

```env
NEXT_PUBLIC_API_URL=https://your-backend.example.com
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=your-publishable-key
```

Configure `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL` e demais secrets somente no backend/API.
