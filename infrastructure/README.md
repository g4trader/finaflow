# 🏗️ Infraestrutura FinaFlow

> **Configuração de infraestrutura híbrida: Vercel (Frontend) + GCP (Backend)**

## 🎯 Arquitetura de Infraestrutura

### **Frontend (Vercel)**
```
Vercel
├── Next.js 14 (SSR/SSG)
├── Edge Functions (APIs simples)
├── CDN Global (Performance)
└── Analytics (Métricas)
```

### **Backend (GCP)**
```
Google Cloud Platform
├── Cloud Run (APIs principais)
├── Cloud SQL (PostgreSQL)
├── Cloud Storage (Arquivos)
├── Cloud Functions (Processamento)
├── Cloud Build (CI/CD)
└── Cloud Monitoring (Observabilidade)
```

## 🚀 Deploy

### **Frontend (Vercel)**
```bash
cd frontend
vercel --prod
```

### **Backend (GCP)**
```bash
# Configurar projeto
gcloud config set project finaflow-prod

# Deploy Cloud Run
gcloud run deploy finaflow-backend \
  --source backend/ \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

# Configurar banco
gcloud sql instances create finaflow-db \
  --database-version=POSTGRES_14 \
  --tier=db-f1-micro \
  --region=us-central1
```

## 🔐 Segurança

### **IAM Roles**
- `finaflow-backend@finaflow-prod.iam.gserviceaccount.com`
- `finaflow-frontend@finaflow-prod.iam.gserviceaccount.com`

### **VPC Network**
- Rede privada para recursos internos
- Cloud NAT para acesso à internet
- Firewall rules restritivas

### **Encryption**
- Dados em repouso: Cloud KMS
- Dados em trânsito: TLS 1.3
- Secrets: Secret Manager

## 📊 Monitoramento

### **Cloud Monitoring**
- Métricas de performance
- Logs estruturados
- Alertas automáticos

### **Sentry**
- Error tracking
- Performance monitoring
- Release tracking

## 💰 Custos Estimados

### **Desenvolvimento (100 usuários)**
- **Vercel**: $20/mês
- **GCP**: $50/mês
- **Total**: $70/mês

### **Produção (1.000 usuários)**
- **Vercel**: $100/mês
- **GCP**: $300/mês
- **Total**: $400/mês

### **Escala (10.000 usuários)**
- **Vercel**: $500/mês
- **GCP**: $1.500/mês
- **Total**: $2.000/mês

## 🔧 Configuração

### **Variáveis de Ambiente**

#### **Frontend (.env.local)**
```env
NEXT_PUBLIC_API_URL=https://finaflow-backend-xxxxx-uc.a.run.app
NEXT_PUBLIC_APP_URL=https://finaflow.vercel.app
```

#### **Backend (.env)**
```env
DATABASE_URL=postgresql://user:pass@host:5432/finaflow
JWT_SECRET=your-super-secret-key
CORS_ORIGINS=https://finaflow.vercel.app
```

## 📈 Escalabilidade

### **Auto-scaling**
- Cloud Run: 0-1000 instâncias
- Cloud SQL: Connection pooling
- Cloud Storage: CDN global

### **Performance**
- Response time: <200ms
- Uptime: 99.9%
- Throughput: 10k req/s

## 🛠️ Manutenção

### **Backup**
- Database: Diário automático
- Storage: Versioning habilitado
- Configuração: Git versionado

### **Updates**
- Frontend: Vercel auto-deploy
- Backend: Cloud Build pipeline
- Database: Maintenance windows

---

**Infraestrutura FinaFlow** - Escalável, segura e confiável 🚀
