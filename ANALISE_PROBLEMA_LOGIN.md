# 🐛 Análise do Problema de Login

## 🔍 Problema Identificado

O login não funciona devido a uma **inconsistência** entre o que o frontend envia e o que o backend espera.

---

## 📊 Fluxo Atual (Com Erro)

### 1. **login.tsx** (Linha 94-98)
```tsx
<Input
  type="text"
  name="username"     // ✅ Nome correto no HTML
  label="Username ou Email"
  placeholder="admin ou seu@email.com"
  value={email}       // ❌ PROBLEMA: Usa variável "email"
  onChange={(e) => setEmail(e.target.value)}  // ❌ State "email"
  ...
/>
```

### 2. **login.tsx - handleSubmit** (Linha 26)
```tsx
await login(email, password);  // ❌ Passa "email" (deveria ser username)
```

### 3. **AuthContext.tsx** (Linha 113)
```tsx
const data = await apiLogin(username, password);  
// ✅ Recebe como "username", mas o valor vem da variável "email"
```

### 4. **api.ts** (Linha 57-60)
```tsx
export const login = async (username: string, password: string) => {
  const formData = new FormData();
  formData.append('username', username);  // ✅ Correto
  formData.append('password', password);
  
  const response = await api.post('/api/v1/auth/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
  ...
}
```

### 5. **Backend API** (Endpoint esperado)
```
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123  // ✅ Formato correto
```

---

## 💥 Por Que Falha?

**O formulário funciona corretamente**, mas há uma confusão de nomenclatura:

1. O usuário digita "admin" no campo
2. O valor vai para a variável `email` (nome enganoso)
3. Essa variável é passada como parâmetro `username` para a API
4. A API formata corretamente e envia para o backend
5. **O backend deve estar recebendo e funcionando!**

**O problema real pode ser**:
- O `await checkNeedsBusinessUnitSelection()` está falhando (linha 134 do AuthContext)
- Erro ao decodificar o JWT
- Exceção silenciosa no try/catch

---

## 🔧 Soluções

### Solução 1: Renomear Variável (Melhor Prática)

**Arquivo**: `frontend/pages/login.tsx`

```tsx
// Linha 14 - ANTES:
const [email, setEmail] = useState('');

// Linha 14 - DEPOIS:
const [username, setUsername] = useState('');

// Linha 26 - ANTES:
await login(email, password);

// Linha 26 - DEPOIS:
await login(username, password);

// Linha 97 - ANTES:
value={email}
onChange={(e) => setEmail(e.target.value)}

// Linha 97 - DEPOIS:
value={username}
onChange={(e) => setUsername(e.target.value)}
```

### Solução 2: Adicionar Logs para Debug

**Arquivo**: `frontend/context/AuthContext.tsx`

Adicionar logs na linha 107-145:

```tsx
const login = async (username: string, password: string) => {
  try {
    console.log('🔐 Tentando login...', { username });  // ✅ ADD
    
    localStorage.removeItem('token');
    removeCookie('auth-token');
    
    const data = await apiLogin(username, password);
    console.log('✅ Login API bem-sucedido', data);  // ✅ ADD
    
    setToken(data.access_token);
    localStorage.setItem('token', data.access_token);
    setCookie('auth-token', data.access_token, 7);
    
    const decoded: any = jwtDecode(data.access_token);
    console.log('🔓 Token decodificado:', decoded);  // ✅ ADD
    
    const userData = { ... };
    setUser(userData);
    
    // Verificar se o usuário precisa selecionar uma BU
    try {
      console.log('🔍 Verificando necessidade de BU...');  // ✅ ADD
      const needsSelection = await checkNeedsBusinessUnitSelection();
      console.log('📋 Precisa BU?', needsSelection);  // ✅ ADD
      setNeedsBusinessUnitSelection(needsSelection.needs_selection);
    } catch (error) {
      console.error('❌ Erro ao verificar BU:', error);  // ✅ ADD
      setNeedsBusinessUnitSelection(!decoded.business_unit_id);
    }
    
    console.log('✅ Login completo!');  // ✅ ADD
  } catch (error) {
    console.error('❌ Erro no login:', error);  // JÁ EXISTE
    throw error;
  }
};
```

### Solução 3: Melhorar Tratamento de Erro

**Arquivo**: `frontend/pages/login.tsx`

```tsx
// Linha 34 - ANTES:
} catch {
  setError('Email ou senha incorretos. Tente novamente.');
}

// Linha 34 - DEPOIS:
} catch (err: any) {
  console.error('Erro no formulário de login:', err);
  const message = err?.response?.data?.detail || err?.message || 'Email ou senha incorretos. Tente novamente.';
  setError(message);
}
```

---

## 🎯 Causa Mais Provável

Baseado no código, a **causa mais provável** é:

### ❌ Erro no `checkNeedsBusinessUnitSelection()`

**Linha 134 do AuthContext**:
```tsx
const needsSelection = await checkNeedsBusinessUnitSelection();
```

Este endpoint está sendo chamado **logo após o login bem-sucedido**, e pode estar:
1. Falhando (404 Not Found)
2. Retornando erro
3. Causando exceção

**Como o erro é capturado**, ele não interrompe o processo, mas pode estar causando algum problema no redirecionamento.

---

## 🔬 Como Confirmar

### Teste Manual no Console do Browser

1. Abrir DevTools (F12)
2. Ir para aba Console
3. Fazer login
4. Observar mensagens

**Esperado**:
```
🔐 Tentando login... {username: "admin"}
✅ Login API bem-sucedido {access_token: "eyJ...", ...}
🔓 Token decodificado: {sub: "...", username: "admin", ...}
🔍 Verificando necessidade de BU...
❌ Erro ao verificar BU: {...}  // PODE ESTAR APARECENDO
✅ Login completo!
```

### Teste da API Diretamente

```bash
# Testar login
curl -X POST "https://finaflow-backend-642830139828.us-central1.run.app/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# Pegar o token da resposta e testar o endpoint de BU
curl -X GET "https://finaflow-backend-642830139828.us-central1.run.app/api/v1/auth/needs-business-unit-selection" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

---

## ✅ Solução Imediata

### Arquivo: `frontend/pages/login.tsx`

**Mudanças necessárias**:

1. Renomear variável `email` para `username` (linhas 14, 26, 97, 98)
2. Melhorar tratamento de erro (linha 34)

### Arquivo: `frontend/context/AuthContext.tsx`

**Mudanças opcionais (para debug)**:

1. Adicionar console.logs
2. Tornar a verificação de BU não-bloqueante

---

## 📋 Checklist de Correção

- [ ] Renomear variável `email` para `username` em login.tsx
- [ ] Adicionar logs de debug no AuthContext
- [ ] Melhorar mensagem de erro
- [ ] Testar endpoint `/api/v1/auth/needs-business-unit-selection`
- [ ] Verificar no console do browser o erro exato
- [ ] Considerar tornar a verificação de BU opcional

---

## 🚀 Correção Aplicada

Vou aplicar as correções agora!

**Data**: 15 de Outubro de 2025  
**Problema**: Login não redireciona  
**Causa**: Nomenclatura confusa + possível erro no endpoint de BU  
**Solução**: Renomear variável + adicionar logs + melhorar error handling


