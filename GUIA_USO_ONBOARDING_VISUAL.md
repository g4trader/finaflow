# 📱 GUIA VISUAL - COMO USAR O ONBOARDING

**URL**: https://finaflow.vercel.app/admin/onboard-company  
**Status**: ✅ DEPLOYADO E FUNCIONAL

---

## 🎯 PASSO A PASSO (COM PRINT DA TELA)

### PASSO 1: Acessar a Página

1. Abrir navegador
2. Acessar: **https://finaflow.vercel.app/login**
3. Fazer login como super admin:
   - Username: `admin`
   - Password: `admin123`
4. Após login, acessar: **https://finaflow.vercel.app/admin/onboard-company**

---

### PASSO 2: O Que Você Verá

```
┌─────────────────────────────────────────────────────────┐
│  🏢 Ativar Nova Empresa                                 │
│  Processo completo de onboarding para SaaS              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Nome da Empresa *                                      │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Ex: Acme Corporation                              │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  Domínio *                                              │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Ex: acme.com                                      │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  Email do Administrador *                               │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Ex: admin@acme.com                                │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │           [ Ativar Empresa ]                      │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

### PASSO 3: Preencher os Campos

**EXEMPLO REAL**:

```
Nome da Empresa: Empresa Teste 123
Domínio: teste123.com
Email do Administrador: admin@teste123.com
```

**Clique em**: `Ativar Empresa`

---

### PASSO 4: Resultado Aparece Automaticamente

Após ~5 segundos, você verá:

```
┌─────────────────────────────────────────────────────────┐
│  ✅ Empresa Ativada com Sucesso!                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Processo Executado:                                    │
│  • 1️⃣ Criando empresa (tenant)...                       │
│    ✅ Empresa criada: Empresa Teste 123                 │
│  • 2️⃣ Criando unidade de negócio...                     │
│    ✅ Business Unit criada: Matriz (MAT)                │
│  • 3️⃣ Criando usuário administrador...                  │
│    ✅ Admin criado: admin                               │
│    🔑 Senha gerada: XyZ123AbC456                        │
│    ✅ Permissões configuradas                           │
│  • ✅ ONBOARDING CONCLUÍDO!                             │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  🔑 Credenciais de Acesso                               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Empresa: Empresa Teste 123                             │
│  Username: admin                                        │
│  Senha Temporária: XyZ123AbC456 ◄─── COPIAR ISSO!      │
│  Email: admin@teste123.com                              │
│  URL: https://finaflow.vercel.app/login                │
│                                                         │
│  ⚠️ IMPORTANTE: Salve e envie para o cliente            │
│                                                         │
│  [ Ativar Outra Empresa ]  [ Ver Todas as Empresas ]   │
└─────────────────────────────────────────────────────────┘
```

---

### PASSO 5: Copiar e Enviar Credenciais

**O QUE COPIAR**:
```
Username: admin
Senha: XyZ123AbC456
URL: https://finaflow.vercel.app/login
```

**COMO ENVIAR**:

#### Opção 1: WhatsApp
```
Olá! Sua empresa foi ativada no FinaFlow 🎉

Acesse: https://finaflow.vercel.app/login
Username: admin
Senha: XyZ123AbC456

⚠️ Troque sua senha no primeiro acesso!
```

#### Opção 2: Email
Ver template completo em `FLUXO_ATIVACAO_EMPRESAS.md`

---

## ✅ VALIDAÇÃO

### Como Saber que Funcionou?

1. **Credenciais aparecem** na tela ✅
2. **Cliente consegue fazer login** ✅  
3. **Cliente vê apenas dados da própria empresa** ✅
4. **Cliente pode criar usuários** ✅

---

## 🎯 TESTE RÁPIDO

### Testar Agora (2 minutos):

1. Acessar: https://finaflow.vercel.app/admin/onboard-company
2. Preencher:
   - Nome: `Teste Demo`
   - Domínio: `testedemo.com`
   - Email: `admin@testedemo.com`
3. Clicar "Ativar Empresa"
4. Copiar credenciais geradas
5. Abrir aba anônima
6. Fazer login com credenciais copiadas
7. ✅ **Funciona!**

---

## 🆘 SE NÃO FUNCIONAR

### Problema: Página mostra "Carregando..." infinito

**Causa**: Usuário não é super_admin ou não está logado  
**Solução**:
1. Fazer logout
2. Login como: `admin` / `admin123`
3. Acessar novamente a página

---

### Problema: Erro "Apenas super_admin..."

**Causa**: Usuário logado não tem role de super_admin  
**Solução**:
1. Logout
2. Login com: `admin` / `admin123`
3. Tentar novamente

---

### Problema: Deploy não aparece

**Causa**: Cache do Vercel ou navegador  
**Solução**:
1. Aguardar 1-2 minutos
2. CTRL + F5 (limpar cache)
3. Abrir aba anônima
4. Tentar novamente

---

## 📊 O QUE A PÁGINA FAZ

### Input (O que você fornece):
```
✏️ Nome da empresa
✏️ Domínio único
✏️ Email do admin
```

### Processo Automático (5 segundos):
```
⚙️ Criar empresa no banco
⚙️ Criar filial (Matriz)
⚙️ Criar admin com senha
⚙️ Configurar permissões
⚙️ Gerar credenciais
```

### Output (O que você recebe):
```
✅ Username gerado
✅ Senha gerada (12 caracteres aleatórios)
✅ URL de login
✅ Lista de próximos passos
```

---

## 🎯 FLUXO VISUAL COMPLETO

```
VOCÊ (Super Admin)
       │
       ├─ 1. Acessa página onboarding
       ├─ 2. Preenche 3 campos
       ├─ 3. Clica "Ativar"
       │
       ▼
   SISTEMA
   (5 segundos)
       │
       ├─ Criar empresa
       ├─ Criar filial
       ├─ Criar admin
       ├─ Gerar senha
       │
       ▼
RESULTADO
(na tela)
       │
       ├─ Credenciais geradas
       ├─ Próximos passos
       │
       ▼
VOCÊ
       │
       ├─ Copiar credenciais
       ├─ Enviar para cliente
       │
       ▼
CLIENTE
       │
       ├─ Fazer login
       ├─ Trocar senha
       ├─ Usar sistema
```

---

## ✅ TUDO PRONTO!

**Agora você pode**:

1. ✅ Acessar: https://finaflow.vercel.app/admin/onboard-company
2. ✅ Ver formulário de ativação
3. ✅ Criar empresas em 5 segundos
4. ✅ Copiar credenciais automaticamente
5. ✅ Escalar para centenas de clientes

---

## 📞 PÁGINAS RELACIONADAS

- **Listar Empresas**: https://finaflow.vercel.app/admin/companies
- **Dashboard**: https://finaflow.vercel.app/dashboard
- **Login**: https://finaflow.vercel.app/login

---

**🚀 SISTEMA TOTALMENTE FUNCIONAL!**

**Acesse agora e teste**: https://finaflow.vercel.app/admin/onboard-company

---

**Criado por**: FinaFlow SaaS Team  
**Data**: 2025-10-20  
**Status**: ✅ Em Produção

