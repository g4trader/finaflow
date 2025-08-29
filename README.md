# 🚀 FinaFlow - Sistema de Gestão Financeira SaaS

> **Sistema SaaS de gestão financeira empresarial com suporte multi-empresa, multi-filial e controle granular de acesso.**

## 🏗️ Arquitetura

### **Frontend (Vercel)**
- **Next.js 14** com App Router
- **TypeScript** para type safety
- **Tailwind CSS** para UI/UX
- **PWA** para acesso mobile

### **Backend (GCP)**
- **FastAPI** para APIs REST
- **PostgreSQL** para banco de dados
- **Cloud Run** para deployment
- **Cloud SQL** para banco gerenciado

### **Segurança**
- **OAuth 2.0 + JWT** para autenticação
- **RBAC** para controle de acesso
- **Multi-tenant** com isolamento de dados
- **Audit logs** para compliance

## 🚀 Quick Start

### **Desenvolvimento Local**

```bash
# Clone o repositório
git clone https://github.com/g4trader/finaflow.git
cd finaflow

# Frontend (Vercel)
cd frontend
npm install
npm run dev

# Backend (Local)
cd ../backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### **Produção**

```bash
# Frontend (Vercel)
vercel --prod

# Backend (GCP)
gcloud run deploy finaflow-backend
```

## 📊 Funcionalidades

### **Gestão Organizacional**
- ✅ Multi-empresa (Tenants)
- ✅ Multi-filial (Business Units)
- ✅ Departamentos e centros de custo
- ✅ Hierarquia de usuários

### **Gestão Financeira**
- ✅ Plano de contas hierárquico
- ✅ Contas bancárias
- ✅ Transações categorizadas
- ✅ Fluxo de caixa

### **Relatórios**
- ✅ Dashboard executivo
- ✅ Relatórios financeiros
- ✅ Analytics e previsões
- ✅ Exportação de dados

## 🔧 Tecnologias

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Backend**: FastAPI, PostgreSQL, SQLAlchemy
- **Cloud**: Vercel (Frontend), GCP (Backend)
- **CI/CD**: GitHub Actions, Cloud Build
- **Monitoramento**: Cloud Monitoring, Sentry

## 📁 Estrutura do Projeto

```
finaflow/
├── frontend/          # Next.js (Vercel)
├── backend/           # FastAPI (GCP)
├── infrastructure/    # Terraform, Cloud Build
├── docs/             # Documentação
├── scripts/          # Utilitários
└── csv/              # Dados de exemplo
```

## 🔐 Segurança

- **Autenticação**: OAuth 2.0 + JWT
- **Autorização**: Role-Based Access Control
- **Dados**: Criptografia em repouso e trânsito
- **Compliance**: GDPR, LGPD, SOX

## 📈 Roadmap

- [x] Arquitetura base
- [x] Sistema de autenticação
- [ ] Multi-tenant completo
- [ ] Gestão financeira
- [ ] Relatórios avançados
- [ ] Integrações bancárias
- [ ] Mobile app

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 📞 Suporte

- **Email**: suporte@finaflow.com
- **Documentação**: [docs.finaflow.com](https://docs.finaflow.com)
- **Issues**: [GitHub Issues](https://github.com/g4trader/finaflow/issues)

---

**FinaFlow** - Transformando a gestão financeira empresarial 🚀
