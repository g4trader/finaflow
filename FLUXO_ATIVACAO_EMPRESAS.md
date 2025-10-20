# 🏢 FLUXO DE ATIVAÇÃO DE NOVAS EMPRESAS - FINAFLOW SaaS

**Data**: 19 de Outubro de 2025  
**Sistema**: FinaFlow - Sistema de Gestão Financeira SaaS  
**Status**: ✅ IMPLEMENTADO

---

## 🎯 OBJETIVO

Processo completo e automatizado para **ativar novas empresas** no sistema SaaS, incluindo:
- Criação de Tenant (Empresa)
- Criação de Business Unit default (Matriz/Sede)
- Criação de usuário administrador
- Importação de dados iniciais via planilha Excel/Google Sheets
- Envio de credenciais de acesso

---

## 👥 PERSONAS DO FLUXO

### 1. Super Admin (Você)
- **Quem é**: Administrador do sistema FinaFlow
- **Responsabilidade**: Ativar novas empresas no SaaS
- **Acesso**: Todas as funcionalidades admin

### 2. Admin da Empresa (Cliente)
- **Quem é**: Administrador criado para a empresa cliente
- **Responsabilidade**: Gerenciar dados financeiros da empresa
- **Acesso**: Apenas dados da própria empresa

### 3. Usuários da Empresa
- **Quem é**: Colaboradores criados pelo admin da empresa
- **Responsabilidade**: Lançamentos financeiros diários
- **Acesso**: Conforme permissões definidas

---

## 🔄 FLUXO COMPLETO DE ATIVAÇÃO

```
┌─────────────────────────────────────────────────────────────────┐
│                    SUPER ADMIN (Você)                           │
│                                                                 │
│  1. Recebe solicitação de nova empresa                         │
│  2. Recebe planilha Excel/Google Sheets do cliente            │
│  3. Acessa: /admin/onboard-company                            │
│  4. Preenche formulário de ativação                           │
│  5. Clica em "Ativar Empresa"                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  PROCESSO AUTOMATIZADO                          │
│                                                                 │
│  ✅ Criar Tenant (Empresa)                                      │
│  ✅ Criar Business Unit (Filial default)                        │
│  ✅ Criar Usuário Admin da empresa                              │
│  ✅ Gerar senha temporária                                      │
│  ✅ Importar planilha (plano de contas + transações)           │
│  ✅ Criar vínculos Tenant-BU-Contas                            │
│  ✅ Configurar permissões do admin                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RESULTADO                                    │
│                                                                 │
│  Credenciais geradas:                                          │
│  - Username: admin.empresa                                     │
│  - Password: XyZ123AbC456 (gerada automaticamente)             │
│  - URL: https://finaflow.vercel.app/login                     │
│                                                                 │
│  Próximos passos exibidos                                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  SUPER ADMIN (Você)                             │
│                                                                 │
│  6. Copiar credenciais                                         │
│  7. Enviar para cliente via email/WhatsApp                     │
│  8. Orientar sobre primeiro acesso                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              ADMIN DA EMPRESA (Cliente)                         │
│                                                                 │
│  1. Recebe credenciais                                         │
│  2. Acessa: https://finaflow.vercel.app/login                 │
│  3. Faz login com credenciais temporárias                      │
│  4. Troca senha no primeiro acesso                             │
│  5. Revisa plano de contas importado                           │
│  6. Cria usuários adicionais da empresa                        │
│  7. Configura permissões                                       │
│  8. Começa a usar o sistema                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 DADOS NECESSÁRIOS PARA ATIVAÇÃO

### Obrigatórios:
1. **Nome da Empresa**: Ex: "Acme Corporation"
2. **Domínio**: Ex: "acme.com" (único no sistema)
3. **Email do Admin**: Ex: "admin@acme.com"

### Opcionais:
4. **Nome da Filial**: Default: "Matriz"
5. **Código da Filial**: Default: "MAT"
6. **Nome do Admin**: Default: "Administrador"
7. **Sobrenome do Admin**: Default: nome da empresa
8. **Telefone do Admin**: Opcional
9. **ID da Planilha Google Sheets**: Para importação de dados
10. **Importar Dados**: Checkbox (sim/não)

---

## 🚀 COMO USAR (Passo a Passo)

### PASSO 1: Acessar Interface de Onboarding

```
URL: https://finaflow.vercel.app/admin/onboard-company
Login: admin / admin123 (super_admin)
```

---

### PASSO 2: Preencher Formulário

#### Seção 1: Informações da Empresa
```
Nome da Empresa: Acme Corporation
Domínio: acme.com
```

#### Seção 2: Filial Inicial
```
Nome da Filial: Matriz
Código: MAT
```

#### Seção 3: Administrador
```
Email: admin@acme.com
Nome: João
Sobrenome: Silva
Telefone: (11) 99999-9999
```

#### Seção 4: Importação de Dados
```
☑ Importar dados da planilha Google Sheets
ID da Planilha: 1yyHuP6qjnK2Rd26yPPzaOqi_OJVeRjAJnewRIOJvFVY
```

---

### PASSO 3: Clicar em "Ativar Empresa"

O sistema irá:
1. ✅ Validar dados
2. ✅ Criar empresa
3. ✅ Criar filial
4. ✅ Criar admin
5. ✅ Importar planilha (se marcado)
6. ✅ Exibir credenciais

---

### PASSO 4: Copiar e Enviar Credenciais

Resultado exibido:
```
✅ EMPRESA ATIVADA COM SUCESSO!

🔑 Credenciais de Acesso:
   Empresa: Acme Corporation
   Filial: Matriz
   Username: admin.acme
   Email: admin@acme.com
   Senha: XyZ123AbC456
   URL: https://finaflow.vercel.app/login
```

**Ações**:
1. Copiar credenciais
2. Enviar para admin@acme.com
3. Orientar sobre troca de senha

---

## 📊 O QUE É CRIADO AUTOMATICAMENTE

### 1. Tenant (Empresa)
```sql
INSERT INTO tenants (id, name, domain, status)
VALUES (uuid, 'Acme Corporation', 'acme.com', 'active');
```

### 2. Business Unit (Filial)
```sql
INSERT INTO business_units (id, tenant_id, name, code, status)
VALUES (uuid, tenant_id, 'Matriz', 'MAT', 'active');
```

### 3. User (Admin da Empresa)
```sql
INSERT INTO users (
  id, tenant_id, business_unit_id, username, email, 
  hashed_password, first_name, last_name, phone, 
  role, status
)
VALUES (
  uuid, tenant_id, bu_id, 'admin.acme', 'admin@acme.com',
  hash('XyZ123AbC456'), 'João', 'Silva', '(11) 99999-9999',
  'admin', 'active'
);
```

### 4. UserBusinessUnitAccess (Permissões)
```sql
INSERT INTO user_business_unit_access (
  id, user_id, business_unit_id, 
  can_read, can_write, can_delete, can_manage_users
)
VALUES (
  uuid, user_id, bu_id,
  true, true, true, true
);
```

### 5. Plano de Contas (Se importar planilha)
- **7 Grupos** com tenant_id
- **~25 Subgrupos** com tenant_id
- **~120 Contas** com tenant_id
- **120 Vínculos** BU-Conta

### 6. Transações (Se importar planilha)
- **~800 Transações** com tenant_id e bu_id
- **~600 Previsões** com tenant_id e bu_id

---

## 🔐 SEGURANÇA E ISOLAMENTO

### Garantias Automáticas:

1. ✅ **Tenant Único**: Domínio não pode ser duplicado
2. ✅ **Email Único**: Admin email único no sistema
3. ✅ **Username Único**: Auto-incrementado se necessário
4. ✅ **Senha Segura**: 12 caracteres aleatórios
5. ✅ **Isolamento**: Todos os dados vinculados ao tenant
6. ✅ **Permissões**: Admin tem acesso total à própria empresa
7. ✅ **Auditoria**: Registros de criação mantidos

---

## 📱 INTERFACE DO USUÁRIO

### Página: `/admin/onboard-company`

```
┌─────────────────────────────────────────────────────────────┐
│  🏢 Ativar Nova Empresa                                     │
│  Processo completo de onboarding                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📋 DADOS DA NOVA EMPRESA                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ INFORMAÇÕES DA EMPRESA                              │   │
│  │ Nome da Empresa *: [Acme Corporation        ]       │   │
│  │ Domínio *:        [acme.com                ]       │   │
│  │                                                     │   │
│  │ FILIAL/UNIDADE INICIAL                              │   │
│  │ Nome: [Matriz    ]  Código: [MAT  ]                │   │
│  │                                                     │   │
│  │ ADMINISTRADOR DA EMPRESA                            │   │
│  │ Email *:      [admin@acme.com              ]       │   │
│  │ Nome:         [João        ] Sobrenome: [Silva   ] │   │
│  │ Telefone:     [(11) 99999-9999             ]       │   │
│  │                                                     │   │
│  │ IMPORTAÇÃO DE DADOS INICIAIS                        │   │
│  │ ☑ Importar planilha Google Sheets                  │   │
│  │ ID: [1yyHuP6qjnK2Rd26yPPzaOqi_OJVeRjAJnewRIOJvFVY] │   │
│  │                                                     │   │
│  │                 [Limpar]  [Ativar Empresa]          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ✅ EMPRESA ATIVADA COM SUCESSO!                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 🔑 Credenciais de Acesso     [Mostrar/Ocultar]     │   │
│  │                                                     │   │
│  │ Empresa: Acme Corporation                           │   │
│  │ Username: admin.acme              📋 Copiar         │   │
│  │ Senha: XyZ123AbC456              📋 Copiar         │   │
│  │ URL: https://finaflow.vercel.app/login             │   │
│  │                                                     │   │
│  │ ⚠️ Salve essas credenciais e envie para o cliente  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ API ENDPOINT

### POST `/api/v1/admin/onboard-new-company`

**Autenticação**: Apenas `super_admin`

**Request Body**:
```json
{
  "tenant_name": "Acme Corporation",
  "tenant_domain": "acme.com",
  "bu_name": "Matriz",
  "bu_code": "MAT",
  "admin_email": "admin@acme.com",
  "admin_first_name": "João",
  "admin_last_name": "Silva",
  "admin_phone": "(11) 99999-9999",
  "spreadsheet_id": "1yyHuP...",
  "import_data": true
}
```

**Response (Sucesso)**:
```json
{
  "success": true,
  "steps": [
    "1️⃣ Criando empresa (tenant)...",
    "   ✅ Empresa criada: Acme Corporation",
    "2️⃣ Criando unidade de negócio...",
    "   ✅ Business Unit criada: Matriz (MAT)",
    "3️⃣ Criando usuário administrador...",
    "   ✅ Admin criado: admin.acme",
    "   🔑 Senha gerada: XyZ123AbC456",
    "   ✅ Permissões configuradas",
    "4️⃣ Importando dados da planilha...",
    "   ✅ 120 contas importadas",
    "   ✅ 800 transações importadas",
    "✅ ONBOARDING CONCLUÍDO!"
  ],
  "tenant_id": "abc123...",
  "business_unit_id": "def456...",
  "admin_user_id": "ghi789...",
  "company_info": {
    "tenant_name": "Acme Corporation",
    "tenant_domain": "acme.com",
    "business_unit_name": "Matriz",
    "admin_username": "admin.acme",
    "admin_email": "admin@acme.com",
    "admin_password": "XyZ123AbC456",
    "login_url": "https://finaflow.vercel.app/login"
  },
  "next_steps": [
    "1. Enviar credenciais para admin@acme.com",
    "2. Admin deve fazer login e trocar senha",
    "3. Admin pode criar usuários adicionais",
    ...
  ]
}
```

---

## 📝 CHECKLIST DE ATIVAÇÃO

### Antes de Ativar:
- [ ] Recebeu solicitação do cliente
- [ ] Cliente enviou planilha Excel/Google Sheets
- [ ] Planilha está no formato correto (metodologia Ana Paula)
- [ ] Planilha compartilhada com service account (se Google Sheets)
- [ ] Tem email do administrador

### Durante Ativação:
- [ ] Acessou `/admin/onboard-company`
- [ ] Preencheu nome da empresa (único)
- [ ] Preencheu domínio (único)
- [ ] Preencheu email do admin
- [ ] Marcou "Importar planilha" (se aplicável)
- [ ] Colou ID da planilha
- [ ] Clicou em "Ativar Empresa"

### Após Ativação:
- [ ] Copiou credenciais exibidas
- [ ] Salvou credenciais em local seguro
- [ ] Enviou credenciais para o cliente
- [ ] Orientou sobre troca de senha
- [ ] Verificou empresa na lista (/admin/companies)

---

## 📧 TEMPLATE DE EMAIL PARA CLIENTE

```
Assunto: ✅ Sua conta FinaFlow foi ativada!

Olá [Nome do Admin],

Sua empresa [Nome da Empresa] foi ativada com sucesso no FinaFlow!

🔑 Credenciais de Acesso:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
URL: https://finaflow.vercel.app/login
Username: [username]
Senha Temporária: [password]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ IMPORTANTE:
• Troque sua senha no primeiro acesso
• Salve suas credenciais em local seguro
• Não compartilhe sua senha

📊 Seus Dados:
• Empresa: [Nome da Empresa]
• Filial: [Nome da Filial]
• Plano de Contas: [X contas importadas] ✅
• Transações: [Y transações importadas] ✅

📝 Próximos Passos:
1. Fazer login no sistema
2. Trocar senha temporária
3. Revisar plano de contas importado
4. Criar usuários adicionais da empresa
5. Configurar permissões dos usuários
6. Começar lançamentos diários

📞 Suporte:
• Email: suporte@finaflow.com
• Documentação: docs.finaflow.com

Bem-vindo ao FinaFlow! 🚀
```

---

## 🎯 CASOS DE USO

### Caso 1: Nova Empresa SEM dados (vazia)

**Situação**: Cliente novo, sem histórico  
**Ação**: 
1. Ativar empresa (sem marcar "importar planilha")
2. Admin faz login
3. Admin importa planilha via `/google-sheets-import`
4. Ou admin cria contas manualmente

---

### Caso 2: Nova Empresa COM dados (migração)

**Situação**: Cliente migrando de outro sistema  
**Ação**:
1. Cliente exporta dados para formato Google Sheets
2. Super admin ativa empresa (marcando "importar planilha")
3. Sistema importa automaticamente tudo
4. Admin faz login e valida dados
5. **Cliente operacional em minutos!**

---

### Caso 3: Adicionar Filial a Empresa Existente

**Situação**: Empresa quer adicionar segunda filial  
**Ação**:
1. Admin da empresa acessa `/business-units`
2. Clica em "Nova Filial"
3. Preenche dados (Nome: "Filial SP", Código: "SP01")
4. Sistema cria BU vinculada ao tenant
5. Admin pode importar planilha específica da filial

---

## ⚠️ VALIDAÇÕES E REGRAS

### Validações Automáticas:
1. ✅ **Domínio único**: Não permite duplicar empresa.com
2. ✅ **Email único**: Não permite duplicar admin@empresa.com
3. ✅ **Username único**: Auto-incrementa se necessário (admin, admin1, admin2...)
4. ✅ **Tenant_id obrigatório**: Todos os dados vinculados
5. ✅ **Business_unit_id obrigatório**: Para transações
6. ✅ **Role correto**: Admin da empresa = "admin" (não "super_admin")

### Regras de Negócio:
1. ✅ Cada empresa tem pelo menos 1 filial
2. ✅ Cada empresa tem pelo menos 1 admin
3. ✅ Admin tem permissões totais na própria empresa
4. ✅ Admin NÃO vê dados de outras empresas
5. ✅ Super admin vê todas as empresas

---

## 🔒 SEGURANÇA

### O que o Admin da Empresa PODE fazer:
- ✅ Ver dados da própria empresa
- ✅ Criar filiais da própria empresa
- ✅ Criar usuários da própria empresa
- ✅ Importar dados da própria empresa
- ✅ Fazer lançamentos financeiros
- ✅ Gerar relatórios da própria empresa

### O que o Admin da Empresa NÃO PODE fazer:
- ❌ Ver dados de outras empresas
- ❌ Criar outras empresas
- ❌ Acessar filiais de outras empresas
- ❌ Ver usuários de outras empresas
- ❌ Executar migrations
- ❌ Acessar endpoints de super_admin

---

## 📊 PLANILHA DE ATIVAÇÃO (Template)

### Estrutura Esperada:

**Aba 1: Plano de Contas**
```
Conta,Subgrupo,Grupo,Escolha
Vendas Cursos,Receita,Receita,Usar
Salários,Custos com Mão de Obra,Custos,Usar
...
```

**Aba 2: Lançamento Diário**
```
Data,Descrição,Conta,Valor,Tipo
2025-01-15,Venda Curso,Vendas Cursos,1000.00,Receita
2025-01-16,Salário,Salários,5000.00,Despesa
...
```

**Aba 3: Lançamentos Previstos**
```
Data,Descrição,Conta,Valor,Tipo
2025-12-01,Venda Prevista,Vendas Cursos,2000.00,Receita
...
```

---

## 🎯 MÉTRICAS DE SUCESSO

### Tempo de Ativação:
- **Sem importação**: ~5 segundos
- **Com importação**: ~30-60 segundos

### Taxa de Sucesso:
- **Objetivo**: >99%
- **Erros comuns**: Email duplicado, domínio duplicado

### Satisfação:
- **Cliente operacional** em minutos (não dias!)
- **Zero digitação manual** (tudo importado)
- **Dados validados** automaticamente

---

## 🆘 TROUBLESHOOTING

### Erro: "Empresa com domínio já existe"
**Causa**: Domínio duplicado  
**Solução**: Usar domínio diferente ou sufixo (acme.com.br, acme-corp.com)

### Erro: "Email já está em uso"
**Causa**: Email duplicado  
**Solução**: Usar email diferente ou adicionar sufixo (+1, +2)

### Erro: "Planilha não encontrada"
**Causa**: ID errado ou sem permissão  
**Solução**: 
1. Verificar ID copiado corretamente
2. Compartilhar planilha com service account
3. Tentar importar manualmente após ativação

### Importação falha mas empresa criada
**Causa**: Erro na planilha  
**Solução**:
1. Empresa já está criada ✅
2. Admin pode fazer login
3. Importar planilha manualmente via interface
4. Ou corrigir planilha e reimportar

---

## 📚 ARQUIVOS RELACIONADOS

### Backend:
- `backend/hybrid_app.py` - Endpoint `/api/v1/admin/onboard-new-company`
- `backend/app/services/chart_accounts_importer.py` - Importação com vínculos
- `backend/app/models/chart_of_accounts.py` - Modelos com tenant_id

### Frontend:
- `frontend/pages/admin/onboard-company.tsx` - Interface de ativação
- `frontend/pages/admin/companies.tsx` - Listagem de empresas
- `frontend/services/api.ts` - Cliente API

### Migrations:
- `migrations/add_tenant_id_to_chart_accounts.sql` - Migration SQL

---

## ✅ RESUMO EXECUTIVO

### O que foi implementado:

1. ✅ **Endpoint API** completo de onboarding
2. ✅ **Interface visual** para super admin
3. ✅ **Geração automática** de credenciais
4. ✅ **Importação integrada** de planilhas
5. ✅ **Vínculos automáticos** Tenant-BU-Contas
6. ✅ **Validações** de segurança
7. ✅ **Isolamento** multi-tenant completo
8. ✅ **Documentação** do processo

### Benefícios:

- ⚡ **Rápido**: Ativação em segundos
- 🎯 **Preciso**: Dados vinculados corretamente
- 🔒 **Seguro**: Isolamento garantido
- 😊 **Fácil**: Interface intuitiva
- 📊 **Completo**: Importa tudo automaticamente

### Status:

✅ **PRONTO PARA PRODUÇÃO**

Processo de onboarding profissional, escalável e seguro para SaaS financeiro!

---

**Preparado por**: Sistema FinaFlow  
**Data**: 2025-10-19  
**Versão**: 1.0  
**Status**: ✅ Implementado e Documentado

