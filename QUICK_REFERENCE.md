# ⚡ QUICK REFERENCE - FinaFlow

## 🎯 Info Rápida

**Tipo**: SaaS de Gestão Financeira  
**Status**: ✅ Em Produção  
**Versão**: 1.0.0

---

## 🌐 URLs

| Ambiente | URL |
|----------|-----|
| **Frontend** | https://finaflow.vercel.app |
| **Backend API** | https://finaflow-backend-6arhlm3mha-uc.a.run.app |
| **Health Check** | https://finaflow-backend-6arhlm3mha-uc.a.run.app/health |
| **API Docs** | https://finaflow-backend-6arhlm3mha-uc.a.run.app/docs |

---

## 🏗️ Stack

| Componente | Tecnologia |
|-----------|-----------|
| **Frontend** | Next.js 13 + TypeScript + Tailwind |
| **Backend** | FastAPI + Python |
| **DB** | PostgreSQL (Cloud SQL) |
| **Frontend Deploy** | Vercel |
| **Backend Deploy** | Google Cloud Run |
| **Projeto GCP** | `trivihair` |

---

## 🚀 Deploy Rápido

### Backend
```bash
gcloud builds submit --config=backend/cloudbuild.yaml --project=trivihair .
```

### Frontend
```bash
cd frontend && vercel --prod
```

---

## 💻 Dev Local

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 🔐 Variáveis Importantes

### Backend
```bash
DATABASE_URL=postgresql://...
JWT_SECRET=...
CORS_ORIGINS=https://finaflow.vercel.app,http://localhost:3000
```

### Frontend
```bash
NEXT_PUBLIC_API_URL=https://finaflow-backend-6arhlm3mha-uc.a.run.app
```

---

## 📂 Estrutura Chave

```
finaflow/
├── frontend/          # Next.js app
│   ├── pages/         # Rotas
│   ├── components/    # Componentes React
│   └── services/      # API client
├── backend/           # FastAPI app
│   ├── app/
│   │   ├── main.py    # Entry point
│   │   ├── api/       # Endpoints
│   │   ├── models/    # SQLAlchemy models
│   │   └── services/  # Business logic
└── infrastructure/    # IaC
```

---

## 🔍 Logs

```bash
# Logs em tempo real
gcloud logging tail "resource.type=cloud_run_revision" --project=trivihair

# Apenas erros
gcloud logging tail "resource.type=cloud_run_revision AND severity>=ERROR" --project=trivihair
```

---

## ✅ Funcionalidades Principais

- ✅ Login/Auth (JWT)
- ✅ Dashboard
- ✅ Transações (CRUD)
- ✅ Contas/Plano de Contas
- ✅ Importação CSV
- ✅ Multi-tenant
- ✅ Relatórios

---

## 🐛 Troubleshooting

### Login não funciona
- Verificar Cloud SQL Proxy configurado
- Verificar DATABASE_URL usa Unix Socket
- Ver logs: `gcloud logging tail ...`

### 404 em endpoints
- Verificar rotas em `backend/app/main.py`
- Verificar prefixo `/api/v1`

### CORS errors
- Verificar CORS_ORIGINS no backend
- Verificar NEXT_PUBLIC_API_URL no frontend

---

## 📚 Docs

- `OVERVIEW_PROJETO.md` - Overview completo
- `README.md` - Documentação principal
- `API_DOCUMENTATION.md` - API docs

---

**Última atualização**: Janeiro 2025


