# 🎯 Alterações Específicas na Vercel - Baseado na Imagem

## 📍 Localização Atual

Você está em: **Settings → Git** do projeto `finaflow-lcz5`

## ❌ O Que NÃO Precisa Ser Alterado (na página atual)

1. **Connected Git Repository**: ✅ Está correto (`g4trader/finaflow`)
2. **Git Large File Storage**: ✅ Pode deixar como está
3. **Deploy Hooks**: ⚠️ O campo "Branch" aqui mostra "main", mas isso é apenas para criar hooks, não afeta a branch de produção
4. **Ignored Build Step**: ✅ Pode deixar como está

## ✅ O Que PRECISA Ser Alterado

### Opção 1: Verificar em "General" (Mais Provável)

A configuração da **Production Branch** geralmente está em outra seção:

1. **No menu lateral esquerdo**, clique em **"General"** (primeira opção da lista)
2. Procure por uma seção chamada:
   - **"Production Branch"** OU
   - **"Git Branch"** OU
   - **"Branch"**
3. Se encontrar um campo mostrando `main`, altere para: **`staging`**
4. Clique em **"Save"**

### Opção 2: Verificar em "Build and Deployment"

1. **No menu lateral esquerdo**, clique em **"Build and Deployment"**
2. Procure por:
   - **"Production Branch"**
   - **"Git Branch"**
   - Ou uma seção sobre branches
3. Se encontrar `main`, altere para: **`staging`**
4. Clique em **"Save"**

## 🔍 Como Identificar a Seção Correta

Procure por qualquer campo ou dropdown que mostre:
- Valor atual: `main`
- Label: "Production Branch", "Git Branch", "Branch", ou similar

## 📋 Checklist de Alteração

- [ ] Navegar para Settings → General OU Build and Deployment
- [ ] Localizar campo "Production Branch" ou similar
- [ ] Alterar de `main` para `staging`
- [ ] Salvar alterações
- [ ] Verificar que aparece "Branch: staging" ou similar
- [ ] Disparar redeploy (ou aguardar automático)

## ⚠️ Importante

- O campo "Branch" em **Deploy Hooks** (que mostra "main" na imagem) **NÃO é** a configuração da branch de produção
- A branch de produção geralmente está em **General** ou **Build and Deployment**
- Após alterar, o próximo deploy deve usar a branch `staging`

## 🔗 Próximos Passos Após Alterar

1. Aguardar redeploy automático OU
2. Ir em **Deployments** e clicar em **"Redeploy"**
3. Verificar no log: "Cloning ... (Branch: staging)"
4. Testar login QA no frontend

