# Problema: Erro 404 ao Selecionar Business Unit

## 🔴 Problema Reportado

O usuário relata erro 404 ao tentar selecionar uma empresa para acessar o dashboard:

```
Failed to load resource: the server responded with a status of 404 ()
Erro ao selecionar BU: AxiosError
```

## 🔍 Investigação Realizada

### 1. Testes da API
- ✅ Endpoint de login: **FUNCIONANDO** (200)
- ✅ Endpoint de business units: **FUNCIONANDO** (200)
- ❌ Endpoint select-business-unit: **ERRO 404**

### 2. Verificações
- ✅ Business Unit existe no banco (ID: `cdaf430c-9f1d-4652-aff5-de20909d9d14`)
- ✅ Usuário admin tem permissão (super_admin)
- ✅ Endpoint direto `/api/v1/business-units/{id}`: **FUNCIONANDO**
- ❌ Endpoint POST `/api/v1/auth/select-business-unit`: **ERRO 404**

### 3. Descoberta do Problema
O problema foi identificado após vários deploys:
- Endpoints básicos (`/`, `/health`) funcionam
- Endpoints de autenticação (`/api/v1/auth/*`) retornam 404
- O arquivo `hybrid_app.py` tem duplicados na raiz e em `backend/`
- O Dockerfile usa `hybrid_app.py` da **raiz**

## 📝 Análise

O arquivo `hybrid_app.py` na raiz do projeto estava **desatualizado** e não continha as correções implementadas. O Cloud Build estava fazendo deploy deste arquivo antigo, por isso os novos endpoints não funcionavam.

## ✅ Correções Implementadas

### 1. Atualizado `hybrid_app.py` da raiz
- Corrigido endpoint `select-business-unit` para usar banco de dados real
- Removido código mock/duplicado
- Corrigida função `create_access_token` para usar `jwt.encode`
- Adicionados logs de debug

### 2. Adicionados Endpoints de Teste
```python
@app.get("/")
async def root():
    return {"message": "FinaFlow API funcionando", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/v1/auth/test")
async def test_auth():
    return {"message": "Auth endpoint funcionando"}
```

### 3. Código Corrigido do Endpoint
```python
@app.post("/api/v1/auth/select-business-unit")
async def select_business_unit(
    business_unit_data: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Seleciona uma Business Unit para o usuário atual e retorna novo token"""
    try:
        user_id = current_user.get("sub")
        business_unit_id = business_unit_data.get("business_unit_id")
        
        if not business_unit_id:
            raise HTTPException(status_code=400, detail="business_unit_id é obrigatório")
        
        # Verificar se a BU existe
        business_unit = db.query(BusinessUnit).filter(BusinessUnit.id == business_unit_id).first()
        if not business_unit:
            raise HTTPException(status_code=404, detail="Business Unit não encontrada")
        
        # Verificar se o usuário tem acesso à BU
        user_role = current_user.get("role")
        has_access = False
        
        if user_role == "super_admin":
            has_access = True
        else:
            user_permission = db.query(UserBusinessUnitAccess).filter(
                UserBusinessUnitAccess.user_id == user_id,
                UserBusinessUnitAccess.business_unit_id == business_unit_id
            ).first()
            has_access = user_permission is not None
        
        if not has_access:
            raise HTTPException(status_code=403, detail="Usuário não tem acesso a esta Business Unit")
        
        # Buscar dados completos do usuário
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        # Buscar dados da empresa
        tenant = db.query(Tenant).filter(Tenant.id == business_unit.tenant_id).first()
        
        # Criar novo token com a BU selecionada
        token_data = {
            "sub": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "tenant_id": str(business_unit.tenant_id),
            "business_unit_id": str(business_unit_id),
            "tenant_name": tenant.name if tenant else "Empresa não encontrada",
            "business_unit_name": business_unit.name
        }
        
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": 3600,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "tenant_id": str(business_unit.tenant_id),
                "business_unit_id": str(business_unit_id),
                "tenant_name": tenant.name if tenant else "Empresa não encontrada",
                "business_unit_name": business_unit.name
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao selecionar Business Unit: {str(e)}")
```

## 🔄 Próximos Passos

1. **Aguardar conclusão do último deploy** (em andamento)
2. **Testar endpoint** `/api/v1/auth/test`
3. **Testar seleção de empresa** com usuário admin
4. **Verificar se dashboard carrega** após seleção

## 🎯 Status Atual

- ⏳ Deploy em andamento (Build ID: 320c1df6-9e02-47ed-ac83-a0c22df863f8)
- 🔄 Aguardando teste do endpoint corrigido
- 📋 Próximo teste: verificar se `/api/v1/auth/test` retorna 200

## 📌 Observações

- O arquivo `hybrid_app.py` está duplicado (raiz e backend/)
- Considerar consolidar em um único arquivo
- Adicionar testes automatizados para evitar regressões
- Implementar CI/CD com validação de endpoints

## 🌐 URLs

- **Frontend**: https://finaflow.vercel.app
- **Backend**: https://finaflow-backend-6arhlm3mha-uc.a.run.app
- **Login**: admin / admin123



