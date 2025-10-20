from fastapi import FastAPI, HTTPException, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
from typing import List, Optional
import os

app = FastAPI(title="FinaFlow API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Security
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, "your-secret-key", algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

# Endpoints básicos
@app.get("/")
async def root():
    return {"message": "FinaFlow API v1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/test-db")
async def test_db():
    try:
        from app.database import get_db
        from sqlalchemy import text
        
        db = next(get_db())
        result = db.execute(text("SELECT 1"))
        db.close()
        return {"message": "Database connection successful"}
    except Exception as e:
        return {"message": "Database connection failed", "error": str(e)}

@app.post("/create-tables")
async def create_tables():
    try:
        from app.database import engine
        from app.models import auth, chart_of_accounts
        
        auth.Base.metadata.create_all(bind=engine)
        chart_of_accounts.Base.metadata.create_all(bind=engine)
        
        return {"message": "Tables created successfully"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/test-models")
async def test_models():
    try:
        from app.models import auth, chart_of_accounts
        return {"message": "Models imported successfully"}
    except Exception as e:
        return {"error": str(e)}

# Endpoint de login
@app.post("/api/v1/auth/login")
async def login(username: str = Form(...), password: str = Form(...)):
    try:
        from app.database import get_db
        from app.models.auth import User
        
        db = next(get_db())
        user = db.query(User).filter(User.username == username).first()
        db.close()
        
        if user and user.check_password(password):
            payload = {
                "sub": str(user.id),
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "tenant_id": str(user.tenant_id),
                "exp": datetime.utcnow() + timedelta(days=30)
            }
            token = jwt.encode(payload, "your-secret-key", algorithm="HS256")
            return {"access_token": token, "token_type": "bearer"}
        else:
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
    except Exception as e:
        return {"error": str(e)}

# Endpoints de Tenants
@app.get("/api/v1/tenants")
async def get_tenants(token: dict = Depends(verify_token)):
    try:
        from app.database import get_db
        from app.models.auth import Tenant
        
        db = next(get_db())
        tenants = db.query(Tenant).all()
        db.close()
        
        return [
            {
                "id": str(tenant.id),
                "name": tenant.name,
                "code": tenant.code,
                "status": tenant.status
            }
            for tenant in tenants
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints de Business Units
@app.get("/api/v1/business-units")
async def get_business_units(token: dict = Depends(verify_token)):
    try:
        from app.database import get_db
        from app.models.auth import BusinessUnit
        
        db = next(get_db())
        business_units = db.query(BusinessUnit).all()
        db.close()
        
        return [
            {
                "id": str(bu.id),
                "name": bu.name,
                "code": bu.code,
                "tenant_id": str(bu.tenant_id),
                "status": bu.status
            }
            for bu in business_units
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints do Chart of Accounts
@app.get("/api/v1/financial/account-groups")
async def get_account_groups(token: dict = Depends(verify_token)):
    try:
        from app.database import get_db
        from app.models.chart_of_accounts import AccountGroup
        from app.models.auth import Tenant, BusinessUnit
        
        db = next(get_db())
        groups = db.query(AccountGroup).all()
        
        result = []
        for group in groups:
            tenant = db.query(Tenant).filter(Tenant.id == group.tenant_id).first()
            bu = db.query(BusinessUnit).filter(BusinessUnit.id == group.business_unit_id).first()
            
            result.append({
                "id": str(group.id),
                "name": group.name,
                "code": group.code,
                "description": group.description,
                "tenant_id": str(group.tenant_id),
                "business_unit_id": str(group.business_unit_id),
                "tenant_name": tenant.name if tenant else None,
                "business_unit_name": bu.name if bu else None,
                "status": group.status
            })
        
        db.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/financial/account-groups")
async def create_account_group(
    name: str,
    code: str,
    description: Optional[str] = None,
    tenant_id: str = None,
    business_unit_id: str = None,
    token: dict = Depends(verify_token)
):
    try:
        from app.database import get_db
        from app.models.chart_of_accounts import AccountGroup
        from uuid import uuid4
        
        db = next(get_db())
        
        if not tenant_id:
            tenant_id = token.get("tenant_id")
        
        if not business_unit_id:
            from app.models.auth import BusinessUnit
            bu = db.query(BusinessUnit).filter(BusinessUnit.tenant_id == tenant_id).first()
            if bu:
                business_unit_id = str(bu.id)
            else:
                raise HTTPException(status_code=400, detail="Business Unit não encontrada")
        
        group = AccountGroup(
            id=str(uuid4()),
            name=name,
            code=code,
            description=description,
            tenant_id=tenant_id,
            business_unit_id=business_unit_id
        )
        
        db.add(group)
        db.commit()
        db.refresh(group)
        db.close()
        
        return {"id": str(group.id), "message": "Grupo criado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/financial/account-subgroups")
async def get_account_subgroups(token: dict = Depends(verify_token)):
    try:
        from app.database import get_db
        from app.models.chart_of_accounts import AccountSubgroup
        from app.models.auth import Tenant, BusinessUnit
        
        db = next(get_db())
        subgroups = db.query(AccountSubgroup).all()
        
        result = []
        for subgroup in subgroups:
            tenant = db.query(Tenant).filter(Tenant.id == subgroup.tenant_id).first()
            bu = db.query(BusinessUnit).filter(BusinessUnit.id == subgroup.business_unit_id).first()
            group = db.query(AccountGroup).filter(AccountGroup.id == subgroup.group_id).first()
            
            result.append({
                "id": str(subgroup.id),
                "name": subgroup.name,
                "code": subgroup.code,
                "description": subgroup.description,
                "group_id": str(subgroup.group_id),
                "group_name": group.name if group else None,
                "tenant_id": str(subgroup.tenant_id),
                "business_unit_id": str(subgroup.business_unit_id),
                "tenant_name": tenant.name if tenant else None,
                "business_unit_name": bu.name if bu else None,
                "status": subgroup.status
            })
        
        db.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/financial/account-subgroups")
async def create_account_subgroup(
    name: str,
    code: str,
    group_id: str,
    description: Optional[str] = None,
    tenant_id: str = None,
    business_unit_id: str = None,
    token: dict = Depends(verify_token)
):
    try:
        from app.database import get_db
        from app.models.chart_of_accounts import AccountSubgroup
        from uuid import uuid4
        
        db = next(get_db())
        
        if not tenant_id:
            tenant_id = token.get("tenant_id")
        
        if not business_unit_id:
            from app.models.auth import BusinessUnit
            bu = db.query(BusinessUnit).filter(BusinessUnit.tenant_id == tenant_id).first()
            if bu:
                business_unit_id = str(bu.id)
            else:
                raise HTTPException(status_code=400, detail="Business Unit não encontrada")
        
        subgroup = AccountSubgroup(
            id=str(uuid4()),
            name=name,
            code=code,
            description=description,
            group_id=group_id,
            tenant_id=tenant_id,
            business_unit_id=business_unit_id
        )
        
        db.add(subgroup)
        db.commit()
        db.refresh(subgroup)
        db.close()
        
        return {"id": str(subgroup.id), "message": "Subgrupo criado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/financial/accounts")
async def get_accounts(token: dict = Depends(verify_token)):
    try:
        from app.database import get_db
        from app.models.chart_of_accounts import Account
        from app.models.auth import Tenant, BusinessUnit
        
        db = next(get_db())
        accounts = db.query(Account).all()
        
        result = []
        for account in accounts:
            tenant = db.query(Tenant).filter(Tenant.id == account.tenant_id).first()
            bu = db.query(BusinessUnit).filter(BusinessUnit.id == account.business_unit_id).first()
            
            result.append({
                "id": str(account.id),
                "name": account.name,
                "code": account.code,
                "description": account.description,
                "group_id": str(account.group_id),
                "subgroup_id": str(account.subgroup_id),
                "tenant_id": str(account.tenant_id),
                "business_unit_id": str(account.business_unit_id),
                "tenant_name": tenant.name if tenant else None,
                "business_unit_name": bu.name if bu else None,
                "is_active": account.is_active,
                "status": account.status
            })
        
        db.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/financial/accounts")
async def create_account(
    name: str,
    code: str,
    subgroup_id: str,
    description: Optional[str] = None,
    tenant_id: str = None,
    business_unit_id: str = None,
    is_active: bool = True,
    token: dict = Depends(verify_token)
):
    try:
        from app.database import get_db
        from app.models.chart_of_accounts import Account
        from uuid import uuid4
        
        db = next(get_db())
        
        if not tenant_id:
            tenant_id = token.get("tenant_id")
        
        if not business_unit_id:
            from app.models.auth import BusinessUnit
            bu = db.query(BusinessUnit).filter(BusinessUnit.tenant_id == tenant_id).first()
            if bu:
                business_unit_id = str(bu.id)
            else:
                raise HTTPException(status_code=400, detail="Business Unit não encontrada")
        
        account = Account(
            id=str(uuid4()),
            name=name,
            code=code,
            description=description,
            subgroup_id=subgroup_id,
            tenant_id=tenant_id,
            business_unit_id=business_unit_id,
            is_active=is_active
        )
        
        db.add(account)
        db.commit()
        db.refresh(account)
        db.close()
        
        return {"id": str(account.id), "message": "Conta criada com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
from typing import List, Optional
import os

app = FastAPI(title="FinaFlow API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Security
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, "your-secret-key", algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

# Endpoints básicos
@app.get("/")
async def root():
    return {"message": "FinaFlow API v1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/test-db")
async def test_db():
    try:
        from app.database import get_db
        from sqlalchemy import text
        
        db = next(get_db())
        result = db.execute(text("SELECT 1"))
        db.close()
        return {"message": "Database connection successful"}
    except Exception as e:
        return {"message": "Database connection failed", "error": str(e)}

@app.post("/create-tables")
async def create_tables():
    try:
        from app.database import engine
        from app.models import auth, chart_of_accounts
        
        auth.Base.metadata.create_all(bind=engine)
        chart_of_accounts.Base.metadata.create_all(bind=engine)
        
        return {"message": "Tables created successfully"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/test-models")
async def test_models():
    try:
        from app.models import auth, chart_of_accounts
        return {"message": "Models imported successfully"}
    except Exception as e:
        return {"error": str(e)}

# Endpoint de login
@app.post("/api/v1/auth/login")
async def login(username: str = Form(...), password: str = Form(...)):
    try:
        from app.database import get_db
        from app.models.auth import User
        
        db = next(get_db())
        user = db.query(User).filter(User.username == username).first()
        db.close()
        
        if user and user.check_password(password):
            payload = {
                "sub": str(user.id),
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "tenant_id": str(user.tenant_id),
                "exp": datetime.utcnow() + timedelta(days=30)
            }
            token = jwt.encode(payload, "your-secret-key", algorithm="HS256")
            return {"access_token": token, "token_type": "bearer"}
        else:
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
    except Exception as e:
        return {"error": str(e)}

# Endpoints de Tenants
@app.get("/api/v1/tenants")
async def get_tenants(token: dict = Depends(verify_token)):
    try:
        from app.database import get_db
        from app.models.auth import Tenant
        
        db = next(get_db())
        tenants = db.query(Tenant).all()
        db.close()
        
        return [
            {
                "id": str(tenant.id),
                "name": tenant.name,
                "code": tenant.code,
                "status": tenant.status
            }
            for tenant in tenants
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints de Business Units
@app.get("/api/v1/business-units")
async def get_business_units(token: dict = Depends(verify_token)):
    try:
        from app.database import get_db
        from app.models.auth import BusinessUnit
        
        db = next(get_db())
        business_units = db.query(BusinessUnit).all()
        db.close()
        
        return [
            {
                "id": str(bu.id),
                "name": bu.name,
                "code": bu.code,
                "tenant_id": str(bu.tenant_id),
                "status": bu.status
            }
            for bu in business_units
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints do Chart of Accounts
@app.get("/api/v1/financial/account-groups")
async def get_account_groups(token: dict = Depends(verify_token)):
    try:
        from app.database import get_db
        from app.models.chart_of_accounts import AccountGroup
        from app.models.auth import Tenant, BusinessUnit
        
        db = next(get_db())
        groups = db.query(AccountGroup).all()
        
        result = []
        for group in groups:
            tenant = db.query(Tenant).filter(Tenant.id == group.tenant_id).first()
            bu = db.query(BusinessUnit).filter(BusinessUnit.id == group.business_unit_id).first()
            
            result.append({
                "id": str(group.id),
                "name": group.name,
                "code": group.code,
                "description": group.description,
                "tenant_id": str(group.tenant_id),
                "business_unit_id": str(group.business_unit_id),
                "tenant_name": tenant.name if tenant else None,
                "business_unit_name": bu.name if bu else None,
                "status": group.status
            })
        
        db.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/financial/account-groups")
async def create_account_group(
    name: str,
    code: str,
    description: Optional[str] = None,
    tenant_id: str = None,
    business_unit_id: str = None,
    token: dict = Depends(verify_token)
):
    try:
        from app.database import get_db
        from app.models.chart_of_accounts import AccountGroup
        from uuid import uuid4
        
        db = next(get_db())
        
        if not tenant_id:
            tenant_id = token.get("tenant_id")
        
        if not business_unit_id:
            from app.models.auth import BusinessUnit
            bu = db.query(BusinessUnit).filter(BusinessUnit.tenant_id == tenant_id).first()
            if bu:
                business_unit_id = str(bu.id)
            else:
                raise HTTPException(status_code=400, detail="Business Unit não encontrada")
        
        group = AccountGroup(
            id=str(uuid4()),
            name=name,
            code=code,
            description=description,
            tenant_id=tenant_id,
            business_unit_id=business_unit_id
        )
        
        db.add(group)
        db.commit()
        db.refresh(group)
        db.close()
        
        return {"id": str(group.id), "message": "Grupo criado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/financial/account-subgroups")
async def get_account_subgroups(token: dict = Depends(verify_token)):
    try:
        from app.database import get_db
        from app.models.chart_of_accounts import AccountSubgroup
        from app.models.auth import Tenant, BusinessUnit
        
        db = next(get_db())
        subgroups = db.query(AccountSubgroup).all()
        
        result = []
        for subgroup in subgroups:
            tenant = db.query(Tenant).filter(Tenant.id == subgroup.tenant_id).first()
            bu = db.query(BusinessUnit).filter(BusinessUnit.id == subgroup.business_unit_id).first()
            group = db.query(AccountGroup).filter(AccountGroup.id == subgroup.group_id).first()
            
            result.append({
                "id": str(subgroup.id),
                "name": subgroup.name,
                "code": subgroup.code,
                "description": subgroup.description,
                "group_id": str(subgroup.group_id),
                "group_name": group.name if group else None,
                "tenant_id": str(subgroup.tenant_id),
                "business_unit_id": str(subgroup.business_unit_id),
                "tenant_name": tenant.name if tenant else None,
                "business_unit_name": bu.name if bu else None,
                "status": subgroup.status
            })
        
        db.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/financial/account-subgroups")
async def create_account_subgroup(
    name: str,
    code: str,
    group_id: str,
    description: Optional[str] = None,
    tenant_id: str = None,
    business_unit_id: str = None,
    token: dict = Depends(verify_token)
):
    try:
        from app.database import get_db
        from app.models.chart_of_accounts import AccountSubgroup
        from uuid import uuid4
        
        db = next(get_db())
        
        if not tenant_id:
            tenant_id = token.get("tenant_id")
        
        if not business_unit_id:
            from app.models.auth import BusinessUnit
            bu = db.query(BusinessUnit).filter(BusinessUnit.tenant_id == tenant_id).first()
            if bu:
                business_unit_id = str(bu.id)
            else:
                raise HTTPException(status_code=400, detail="Business Unit não encontrada")
        
        subgroup = AccountSubgroup(
            id=str(uuid4()),
            name=name,
            code=code,
            description=description,
            group_id=group_id,
            tenant_id=tenant_id,
            business_unit_id=business_unit_id
        )
        
        db.add(subgroup)
        db.commit()
        db.refresh(subgroup)
        db.close()
        
        return {"id": str(subgroup.id), "message": "Subgrupo criado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/financial/accounts")
async def get_accounts(token: dict = Depends(verify_token)):
    try:
        from app.database import get_db
        from app.models.chart_of_accounts import Account
        from app.models.auth import Tenant, BusinessUnit
        
        db = next(get_db())
        accounts = db.query(Account).all()
        
        result = []
        for account in accounts:
            tenant = db.query(Tenant).filter(Tenant.id == account.tenant_id).first()
            bu = db.query(BusinessUnit).filter(BusinessUnit.id == account.business_unit_id).first()
            
            result.append({
                "id": str(account.id),
                "name": account.name,
                "code": account.code,
                "description": account.description,
                "group_id": str(account.group_id),
                "subgroup_id": str(account.subgroup_id),
                "tenant_id": str(account.tenant_id),
                "business_unit_id": str(account.business_unit_id),
                "tenant_name": tenant.name if tenant else None,
                "business_unit_name": bu.name if bu else None,
                "is_active": account.is_active,
                "status": account.status
            })
        
        db.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/financial/accounts")
async def create_account(
    name: str,
    code: str,
    subgroup_id: str,
    description: Optional[str] = None,
    tenant_id: str = None,
    business_unit_id: str = None,
    is_active: bool = True,
    token: dict = Depends(verify_token)
):
    try:
        from app.database import get_db
        from app.models.chart_of_accounts import Account
        from uuid import uuid4
        
        db = next(get_db())
        
        if not tenant_id:
            tenant_id = token.get("tenant_id")
        
        if not business_unit_id:
            from app.models.auth import BusinessUnit
            bu = db.query(BusinessUnit).filter(BusinessUnit.tenant_id == tenant_id).first()
            if bu:
                business_unit_id = str(bu.id)
            else:
                raise HTTPException(status_code=400, detail="Business Unit não encontrada")
        
        account = Account(
            id=str(uuid4()),
            name=name,
            code=code,
            description=description,
            subgroup_id=subgroup_id,
            tenant_id=tenant_id,
            business_unit_id=business_unit_id,
            is_active=is_active
        )
        
        db.add(account)
        db.commit()
        db.refresh(account)
        db.close()
        
        return {"id": str(account.id), "message": "Conta criada com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
from typing import List, Optional
import os

app = FastAPI(title="FinaFlow API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Security
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, "your-secret-key", algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

# Endpoints básicos
@app.get("/")
async def root():
    return {"message": "FinaFlow API v1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/test-db")
async def test_db():
    try:
        from app.database import get_db
        from sqlalchemy import text
        
        db = next(get_db())
        result = db.execute(text("SELECT 1"))
        db.close()
        return {"message": "Database connection successful"}
    except Exception as e:
        return {"message": "Database connection failed", "error": str(e)}

@app.post("/create-tables")
async def create_tables():
    try:
        from app.database import engine
        from app.models import auth, chart_of_accounts
        
        auth.Base.metadata.create_all(bind=engine)
        chart_of_accounts.Base.metadata.create_all(bind=engine)
        
        return {"message": "Tables created successfully"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/test-models")
async def test_models():
    try:
        from app.models import auth, chart_of_accounts
        return {"message": "Models imported successfully"}
    except Exception as e:
        return {"error": str(e)}

# Endpoint de login
@app.post("/api/v1/auth/login")
async def login(username: str = Form(...), password: str = Form(...)):
    try:
        from app.database import get_db
        from app.models.auth import User
        
        db = next(get_db())
        user = db.query(User).filter(User.username == username).first()
        db.close()
        
        if user and user.check_password(password):
            payload = {
                "sub": str(user.id),
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "tenant_id": str(user.tenant_id),
                "exp": datetime.utcnow() + timedelta(days=30)
            }
            token = jwt.encode(payload, "your-secret-key", algorithm="HS256")
            return {"access_token": token, "token_type": "bearer"}
        else:
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
    except Exception as e:
        return {"error": str(e)}

# Endpoints de Tenants
@app.get("/api/v1/tenants")
async def get_tenants(token: dict = Depends(verify_token)):
    try:
        from app.database import get_db
        from app.models.auth import Tenant
        
        db = next(get_db())
        tenants = db.query(Tenant).all()
        db.close()
        
        return [
            {
                "id": str(tenant.id),
                "name": tenant.name,
                "code": tenant.code,
                "status": tenant.status
            }
            for tenant in tenants
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints de Business Units
@app.get("/api/v1/business-units")
async def get_business_units(token: dict = Depends(verify_token)):
    try:
        from app.database import get_db
        from app.models.auth import BusinessUnit
        
        db = next(get_db())
        business_units = db.query(BusinessUnit).all()
        db.close()
        
        return [
            {
                "id": str(bu.id),
                "name": bu.name,
                "code": bu.code,
                "tenant_id": str(bu.tenant_id),
                "status": bu.status
            }
            for bu in business_units
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints do Chart of Accounts
@app.get("/api/v1/financial/account-groups")
async def get_account_groups(token: dict = Depends(verify_token)):
    try:
        from app.database import get_db
        from app.models.chart_of_accounts import AccountGroup
        from app.models.auth import Tenant, BusinessUnit
        
        db = next(get_db())
        groups = db.query(AccountGroup).all()
        
        result = []
        for group in groups:
            tenant = db.query(Tenant).filter(Tenant.id == group.tenant_id).first()
            bu = db.query(BusinessUnit).filter(BusinessUnit.id == group.business_unit_id).first()
            
            result.append({
                "id": str(group.id),
                "name": group.name,
                "code": group.code,
                "description": group.description,
                "tenant_id": str(group.tenant_id),
                "business_unit_id": str(group.business_unit_id),
                "tenant_name": tenant.name if tenant else None,
                "business_unit_name": bu.name if bu else None,
                "status": group.status
            })
        
        db.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/financial/account-groups")
async def create_account_group(
    name: str,
    code: str,
    description: Optional[str] = None,
    tenant_id: str = None,
    business_unit_id: str = None,
    token: dict = Depends(verify_token)
):
    try:
        from app.database import get_db
        from app.models.chart_of_accounts import AccountGroup
        from uuid import uuid4
        
        db = next(get_db())
        
        if not tenant_id:
            tenant_id = token.get("tenant_id")
        
        if not business_unit_id:
            from app.models.auth import BusinessUnit
            bu = db.query(BusinessUnit).filter(BusinessUnit.tenant_id == tenant_id).first()
            if bu:
                business_unit_id = str(bu.id)
            else:
                raise HTTPException(status_code=400, detail="Business Unit não encontrada")
        
        group = AccountGroup(
            id=str(uuid4()),
            name=name,
            code=code,
            description=description,
            tenant_id=tenant_id,
            business_unit_id=business_unit_id
        )
        
        db.add(group)
        db.commit()
        db.refresh(group)
        db.close()
        
        return {"id": str(group.id), "message": "Grupo criado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/financial/account-subgroups")
async def get_account_subgroups(token: dict = Depends(verify_token)):
    try:
        from app.database import get_db
        from app.models.chart_of_accounts import AccountSubgroup
        from app.models.auth import Tenant, BusinessUnit
        
        db = next(get_db())
        subgroups = db.query(AccountSubgroup).all()
        
        result = []
        for subgroup in subgroups:
            tenant = db.query(Tenant).filter(Tenant.id == subgroup.tenant_id).first()
            bu = db.query(BusinessUnit).filter(BusinessUnit.id == subgroup.business_unit_id).first()
            group = db.query(AccountGroup).filter(AccountGroup.id == subgroup.group_id).first()
            
            result.append({
                "id": str(subgroup.id),
                "name": subgroup.name,
                "code": subgroup.code,
                "description": subgroup.description,
                "group_id": str(subgroup.group_id),
                "group_name": group.name if group else None,
                "tenant_id": str(subgroup.tenant_id),
                "business_unit_id": str(subgroup.business_unit_id),
                "tenant_name": tenant.name if tenant else None,
                "business_unit_name": bu.name if bu else None,
                "status": subgroup.status
            })
        
        db.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/financial/account-subgroups")
async def create_account_subgroup(
    name: str,
    code: str,
    group_id: str,
    description: Optional[str] = None,
    tenant_id: str = None,
    business_unit_id: str = None,
    token: dict = Depends(verify_token)
):
    try:
        from app.database import get_db
        from app.models.chart_of_accounts import AccountSubgroup
        from uuid import uuid4
        
        db = next(get_db())
        
        if not tenant_id:
            tenant_id = token.get("tenant_id")
        
        if not business_unit_id:
            from app.models.auth import BusinessUnit
            bu = db.query(BusinessUnit).filter(BusinessUnit.tenant_id == tenant_id).first()
            if bu:
                business_unit_id = str(bu.id)
            else:
                raise HTTPException(status_code=400, detail="Business Unit não encontrada")
        
        subgroup = AccountSubgroup(
            id=str(uuid4()),
            name=name,
            code=code,
            description=description,
            group_id=group_id,
            tenant_id=tenant_id,
            business_unit_id=business_unit_id
        )
        
        db.add(subgroup)
        db.commit()
        db.refresh(subgroup)
        db.close()
        
        return {"id": str(subgroup.id), "message": "Subgrupo criado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/financial/accounts")
async def get_accounts(token: dict = Depends(verify_token)):
    try:
        from app.database import get_db
        from app.models.chart_of_accounts import Account
        from app.models.auth import Tenant, BusinessUnit
        
        db = next(get_db())
        accounts = db.query(Account).all()
        
        result = []
        for account in accounts:
            tenant = db.query(Tenant).filter(Tenant.id == account.tenant_id).first()
            bu = db.query(BusinessUnit).filter(BusinessUnit.id == account.business_unit_id).first()
            
            result.append({
                "id": str(account.id),
                "name": account.name,
                "code": account.code,
                "description": account.description,
                "group_id": str(account.group_id),
                "subgroup_id": str(account.subgroup_id),
                "tenant_id": str(account.tenant_id),
                "business_unit_id": str(account.business_unit_id),
                "tenant_name": tenant.name if tenant else None,
                "business_unit_name": bu.name if bu else None,
                "is_active": account.is_active,
                "status": account.status
            })
        
        db.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/financial/accounts")
async def create_account(
    name: str,
    code: str,
    subgroup_id: str,
    description: Optional[str] = None,
    tenant_id: str = None,
    business_unit_id: str = None,
    is_active: bool = True,
    token: dict = Depends(verify_token)
):
    try:
        from app.database import get_db
        from app.models.chart_of_accounts import Account
        from uuid import uuid4
        
        db = next(get_db())
        
        if not tenant_id:
            tenant_id = token.get("tenant_id")
        
        if not business_unit_id:
            from app.models.auth import BusinessUnit
            bu = db.query(BusinessUnit).filter(BusinessUnit.tenant_id == tenant_id).first()
            if bu:
                business_unit_id = str(bu.id)
            else:
                raise HTTPException(status_code=400, detail="Business Unit não encontrada")
        
        account = Account(
            id=str(uuid4()),
            name=name,
            code=code,
            description=description,
            subgroup_id=subgroup_id,
            tenant_id=tenant_id,
            business_unit_id=business_unit_id,
            is_active=is_active
        )
        
        db.add(account)
        db.commit()
        db.refresh(account)
        db.close()
        
        return {"id": str(account.id), "message": "Conta criada com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
from typing import List, Optional
import os

app = FastAPI(title="FinaFlow API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Security
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, "your-secret-key", algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

# Endpoints básicos
@app.get("/")
async def root():
    return {"message": "FinaFlow API v1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/test-db")
async def test_db():
    try:
        from app.database import get_db
        from sqlalchemy import text
        
        db = next(get_db())
        result = db.execute(text("SELECT 1"))
        db.close()
        return {"message": "Database connection successful"}
    except Exception as e:
        return {"message": "Database connection failed", "error": str(e)}

@app.post("/create-tables")
async def create_tables():
    try:
        from app.database import engine
        from app.models import auth, chart_of_accounts
        
        auth.Base.metadata.create_all(bind=engine)
        chart_of_accounts.Base.metadata.create_all(bind=engine)
        
        return {"message": "Tables created successfully"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/test-models")
async def test_models():
    try:
        from app.models import auth, chart_of_accounts
        return {"message": "Models imported successfully"}
    except Exception as e:
        return {"error": str(e)}

# Endpoint de login
@app.post("/api/v1/auth/login")
async def login(username: str = Form(...), password: str = Form(...)):
    try:
        from app.database import get_db
        from app.models.auth import User
        
        db = next(get_db())
        user = db.query(User).filter(User.username == username).first()
        db.close()
        
        if user and user.check_password(password):
            payload = {
                "sub": str(user.id),
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "tenant_id": str(user.tenant_id),
                "exp": datetime.utcnow() + timedelta(days=30)
            }
            token = jwt.encode(payload, "your-secret-key", algorithm="HS256")
            return {"access_token": token, "token_type": "bearer"}
        else:
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
    except Exception as e:
        return {"error": str(e)}

# Endpoints de Tenants
@app.get("/api/v1/tenants")
async def get_tenants(token: dict = Depends(verify_token)):
    try:
        from app.database import get_db
        from app.models.auth import Tenant
        
        db = next(get_db())
        tenants = db.query(Tenant).all()
        db.close()
        
        return [
            {
                "id": str(tenant.id),
                "name": tenant.name,
                "code": tenant.code,
                "status": tenant.status
            }
            for tenant in tenants
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints de Business Units
@app.get("/api/v1/business-units")
async def get_business_units(token: dict = Depends(verify_token)):
    try:
        from app.database import get_db
        from app.models.auth import BusinessUnit
        
        db = next(get_db())
        business_units = db.query(BusinessUnit).all()
        db.close()
        
        return [
            {
                "id": str(bu.id),
                "name": bu.name,
                "code": bu.code,
                "tenant_id": str(bu.tenant_id),
                "status": bu.status
            }
            for bu in business_units
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints do Chart of Accounts
@app.get("/api/v1/financial/account-groups")
async def get_account_groups(token: dict = Depends(verify_token)):
    try:
        from app.database import get_db
        from app.models.chart_of_accounts import AccountGroup
        from app.models.auth import Tenant, BusinessUnit
        
        db = next(get_db())
        groups = db.query(AccountGroup).all()
        
        result = []
        for group in groups:
            tenant = db.query(Tenant).filter(Tenant.id == group.tenant_id).first()
            bu = db.query(BusinessUnit).filter(BusinessUnit.id == group.business_unit_id).first()
            
            result.append({
                "id": str(group.id),
                "name": group.name,
                "code": group.code,
                "description": group.description,
                "tenant_id": str(group.tenant_id),
                "business_unit_id": str(group.business_unit_id),
                "tenant_name": tenant.name if tenant else None,
                "business_unit_name": bu.name if bu else None,
                "status": group.status
            })
        
        db.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/financial/account-groups")
async def create_account_group(
    name: str,
    code: str,
    description: Optional[str] = None,
    tenant_id: str = None,
    business_unit_id: str = None,
    token: dict = Depends(verify_token)
):
    try:
        from app.database import get_db
        from app.models.chart_of_accounts import AccountGroup
        from uuid import uuid4
        
        db = next(get_db())
        
        if not tenant_id:
            tenant_id = token.get("tenant_id")
        
        if not business_unit_id:
            from app.models.auth import BusinessUnit
            bu = db.query(BusinessUnit).filter(BusinessUnit.tenant_id == tenant_id).first()
            if bu:
                business_unit_id = str(bu.id)
            else:
                raise HTTPException(status_code=400, detail="Business Unit não encontrada")
        
        group = AccountGroup(
            id=str(uuid4()),
            name=name,
            code=code,
            description=description,
            tenant_id=tenant_id,
            business_unit_id=business_unit_id
        )
        
        db.add(group)
        db.commit()
        db.refresh(group)
        db.close()
        
        return {"id": str(group.id), "message": "Grupo criado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/financial/account-subgroups")
async def get_account_subgroups(token: dict = Depends(verify_token)):
    try:
        from app.database import get_db
        from app.models.chart_of_accounts import AccountSubgroup
        from app.models.auth import Tenant, BusinessUnit
        
        db = next(get_db())
        subgroups = db.query(AccountSubgroup).all()
        
        result = []
        for subgroup in subgroups:
            tenant = db.query(Tenant).filter(Tenant.id == subgroup.tenant_id).first()
            bu = db.query(BusinessUnit).filter(BusinessUnit.id == subgroup.business_unit_id).first()
            group = db.query(AccountGroup).filter(AccountGroup.id == subgroup.group_id).first()
            
            result.append({
                "id": str(subgroup.id),
                "name": subgroup.name,
                "code": subgroup.code,
                "description": subgroup.description,
                "group_id": str(subgroup.group_id),
                "group_name": group.name if group else None,
                "tenant_id": str(subgroup.tenant_id),
                "business_unit_id": str(subgroup.business_unit_id),
                "tenant_name": tenant.name if tenant else None,
                "business_unit_name": bu.name if bu else None,
                "status": subgroup.status
            })
        
        db.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/financial/account-subgroups")
async def create_account_subgroup(
    name: str,
    code: str,
    group_id: str,
    description: Optional[str] = None,
    tenant_id: str = None,
    business_unit_id: str = None,
    token: dict = Depends(verify_token)
):
    try:
        from app.database import get_db
        from app.models.chart_of_accounts import AccountSubgroup
        from uuid import uuid4
        
        db = next(get_db())
        
        if not tenant_id:
            tenant_id = token.get("tenant_id")
        
        if not business_unit_id:
            from app.models.auth import BusinessUnit
            bu = db.query(BusinessUnit).filter(BusinessUnit.tenant_id == tenant_id).first()
            if bu:
                business_unit_id = str(bu.id)
            else:
                raise HTTPException(status_code=400, detail="Business Unit não encontrada")
        
        subgroup = AccountSubgroup(
            id=str(uuid4()),
            name=name,
            code=code,
            description=description,
            group_id=group_id,
            tenant_id=tenant_id,
            business_unit_id=business_unit_id
        )
        
        db.add(subgroup)
        db.commit()
        db.refresh(subgroup)
        db.close()
        
        return {"id": str(subgroup.id), "message": "Subgrupo criado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/financial/accounts")
async def get_accounts(token: dict = Depends(verify_token)):
    try:
        from app.database import get_db
        from app.models.chart_of_accounts import Account
        from app.models.auth import Tenant, BusinessUnit
        
        db = next(get_db())
        accounts = db.query(Account).all()
        
        result = []
        for account in accounts:
            tenant = db.query(Tenant).filter(Tenant.id == account.tenant_id).first()
            bu = db.query(BusinessUnit).filter(BusinessUnit.id == account.business_unit_id).first()
            
            result.append({
                "id": str(account.id),
                "name": account.name,
                "code": account.code,
                "description": account.description,
                "group_id": str(account.group_id),
                "subgroup_id": str(account.subgroup_id),
                "tenant_id": str(account.tenant_id),
                "business_unit_id": str(account.business_unit_id),
                "tenant_name": tenant.name if tenant else None,
                "business_unit_name": bu.name if bu else None,
                "is_active": account.is_active,
                "status": account.status
            })
        
        db.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/financial/accounts")
async def create_account(
    name: str,
    code: str,
    subgroup_id: str,
    description: Optional[str] = None,
    tenant_id: str = None,
    business_unit_id: str = None,
    is_active: bool = True,
    token: dict = Depends(verify_token)
):
    try:
        from app.database import get_db
        from app.models.chart_of_accounts import Account
        from uuid import uuid4
        
        db = next(get_db())
        
        if not tenant_id:
            tenant_id = token.get("tenant_id")
        
        if not business_unit_id:
            from app.models.auth import BusinessUnit
            bu = db.query(BusinessUnit).filter(BusinessUnit.tenant_id == tenant_id).first()
            if bu:
                business_unit_id = str(bu.id)
            else:
                raise HTTPException(status_code=400, detail="Business Unit não encontrada")
        
        account = Account(
            id=str(uuid4()),
            name=name,
            code=code,
            description=description,
            subgroup_id=subgroup_id,
            tenant_id=tenant_id,
            business_unit_id=business_unit_id,
            is_active=is_active
        )
        
        db.add(account)
        db.commit()
        db.refresh(account)
        db.close()
        
        return {"id": str(account.id), "message": "Conta criada com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
from typing import List, Optional
import os

app = FastAPI(title="FinaFlow API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Security
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, "your-secret-key", algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

# Endpoints básicos
@app.get("/")
async def root():
    return {"message": "FinaFlow API v1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/test-db")
async def test_db():
    try:
        from app.database import get_db
        from sqlalchemy import text
        
        db = next(get_db())
        result = db.execute(text("SELECT 1"))
        db.close()
        return {"message": "Database connection successful"}
    except Exception as e:
        return {"message": "Database connection failed", "error": str(e)}

@app.post("/create-tables")
async def create_tables():
    try:
        from app.database import engine
        from app.models import auth, chart_of_accounts
        
        auth.Base.metadata.create_all(bind=engine)
        chart_of_accounts.Base.metadata.create_all(bind=engine)
        
        return {"message": "Tables created successfully"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/test-models")
async def test_models():
    try:
        from app.models import auth, chart_of_accounts
        return {"message": "Models imported successfully"}
    except Exception as e:
        return {"error": str(e)}

# Endpoint de login
@app.post("/api/v1/auth/login")
async def login(username: str = Form(...), password: str = Form(...)):
    try:
        from app.database import get_db
        from app.models.auth import User
        
        db = next(get_db())
        user = db.query(User).filter(User.username == username).first()
        db.close()
        
        if user and user.check_password(password):
            payload = {
                "sub": str(user.id),
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "tenant_id": str(user.tenant_id),
                "exp": datetime.utcnow() + timedelta(days=30)
            }
            token = jwt.encode(payload, "your-secret-key", algorithm="HS256")
            return {"access_token": token, "token_type": "bearer"}
        else:
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
    except Exception as e:
        return {"error": str(e)}

# Endpoints de Tenants
@app.get("/api/v1/tenants")
async def get_tenants(token: dict = Depends(verify_token)):
    try:
        from app.database import get_db
        from app.models.auth import Tenant
        
        db = next(get_db())
        tenants = db.query(Tenant).all()
        db.close()
        
        return [
            {
                "id": str(tenant.id),
                "name": tenant.name,
                "code": tenant.code,
                "status": tenant.status
            }
            for tenant in tenants
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints de Business Units
@app.get("/api/v1/business-units")
async def get_business_units(token: dict = Depends(verify_token)):
    try:
        from app.database import get_db
        from app.models.auth import BusinessUnit
        
        db = next(get_db())
        business_units = db.query(BusinessUnit).all()
        db.close()
        
        return [
            {
                "id": str(bu.id),
                "name": bu.name,
                "code": bu.code,
                "tenant_id": str(bu.tenant_id),
                "status": bu.status
            }
            for bu in business_units
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints do Chart of Accounts
@app.get("/api/v1/financial/account-groups")
async def get_account_groups(token: dict = Depends(verify_token)):
    try:
        from app.database import get_db
        from app.models.chart_of_accounts import AccountGroup
        from app.models.auth import Tenant, BusinessUnit
        
        db = next(get_db())
        groups = db.query(AccountGroup).all()
        
        result = []
        for group in groups:
            tenant = db.query(Tenant).filter(Tenant.id == group.tenant_id).first()
            bu = db.query(BusinessUnit).filter(BusinessUnit.id == group.business_unit_id).first()
            
            result.append({
                "id": str(group.id),
                "name": group.name,
                "code": group.code,
                "description": group.description,
                "tenant_id": str(group.tenant_id),
                "business_unit_id": str(group.business_unit_id),
                "tenant_name": tenant.name if tenant else None,
                "business_unit_name": bu.name if bu else None,
                "status": group.status
            })
        
        db.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/financial/account-groups")
async def create_account_group(
    name: str,
    code: str,
    description: Optional[str] = None,
    tenant_id: str = None,
    business_unit_id: str = None,
    token: dict = Depends(verify_token)
):
    try:
        from app.database import get_db
        from app.models.chart_of_accounts import AccountGroup
        from uuid import uuid4
        
        db = next(get_db())
        
        if not tenant_id:
            tenant_id = token.get("tenant_id")
        
        if not business_unit_id:
            from app.models.auth import BusinessUnit
            bu = db.query(BusinessUnit).filter(BusinessUnit.tenant_id == tenant_id).first()
            if bu:
                business_unit_id = str(bu.id)
            else:
                raise HTTPException(status_code=400, detail="Business Unit não encontrada")
        
        group = AccountGroup(
            id=str(uuid4()),
            name=name,
            code=code,
            description=description,
            tenant_id=tenant_id,
            business_unit_id=business_unit_id
        )
        
        db.add(group)
        db.commit()
        db.refresh(group)
        db.close()
        
        return {"id": str(group.id), "message": "Grupo criado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/financial/account-subgroups")
async def get_account_subgroups(token: dict = Depends(verify_token)):
    try:
        from app.database import get_db
        from app.models.chart_of_accounts import AccountSubgroup
        from app.models.auth import Tenant, BusinessUnit
        
        db = next(get_db())
        subgroups = db.query(AccountSubgroup).all()
        
        result = []
        for subgroup in subgroups:
            tenant = db.query(Tenant).filter(Tenant.id == subgroup.tenant_id).first()
            bu = db.query(BusinessUnit).filter(BusinessUnit.id == subgroup.business_unit_id).first()
            group = db.query(AccountGroup).filter(AccountGroup.id == subgroup.group_id).first()
            
            result.append({
                "id": str(subgroup.id),
                "name": subgroup.name,
                "code": subgroup.code,
                "description": subgroup.description,
                "group_id": str(subgroup.group_id),
                "group_name": group.name if group else None,
                "tenant_id": str(subgroup.tenant_id),
                "business_unit_id": str(subgroup.business_unit_id),
                "tenant_name": tenant.name if tenant else None,
                "business_unit_name": bu.name if bu else None,
                "status": subgroup.status
            })
        
        db.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/financial/account-subgroups")
async def create_account_subgroup(
    name: str,
    code: str,
    group_id: str,
    description: Optional[str] = None,
    tenant_id: str = None,
    business_unit_id: str = None,
    token: dict = Depends(verify_token)
):
    try:
        from app.database import get_db
        from app.models.chart_of_accounts import AccountSubgroup
        from uuid import uuid4
        
        db = next(get_db())
        
        if not tenant_id:
            tenant_id = token.get("tenant_id")
        
        if not business_unit_id:
            from app.models.auth import BusinessUnit
            bu = db.query(BusinessUnit).filter(BusinessUnit.tenant_id == tenant_id).first()
            if bu:
                business_unit_id = str(bu.id)
            else:
                raise HTTPException(status_code=400, detail="Business Unit não encontrada")
        
        subgroup = AccountSubgroup(
            id=str(uuid4()),
            name=name,
            code=code,
            description=description,
            group_id=group_id,
            tenant_id=tenant_id,
            business_unit_id=business_unit_id
        )
        
        db.add(subgroup)
        db.commit()
        db.refresh(subgroup)
        db.close()
        
        return {"id": str(subgroup.id), "message": "Subgrupo criado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/financial/accounts")
async def get_accounts(token: dict = Depends(verify_token)):
    try:
        from app.database import get_db
        from app.models.chart_of_accounts import Account
        from app.models.auth import Tenant, BusinessUnit
        
        db = next(get_db())
        accounts = db.query(Account).all()
        
        result = []
        for account in accounts:
            tenant = db.query(Tenant).filter(Tenant.id == account.tenant_id).first()
            bu = db.query(BusinessUnit).filter(BusinessUnit.id == account.business_unit_id).first()
            
            result.append({
                "id": str(account.id),
                "name": account.name,
                "code": account.code,
                "description": account.description,
                "group_id": str(account.group_id),
                "subgroup_id": str(account.subgroup_id),
                "tenant_id": str(account.tenant_id),
                "business_unit_id": str(account.business_unit_id),
                "tenant_name": tenant.name if tenant else None,
                "business_unit_name": bu.name if bu else None,
                "is_active": account.is_active,
                "status": account.status
            })
        
        db.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/financial/accounts")
async def create_account(
    name: str,
    code: str,
    subgroup_id: str,
    description: Optional[str] = None,
    tenant_id: str = None,
    business_unit_id: str = None,
    is_active: bool = True,
    token: dict = Depends(verify_token)
):
    try:
        from app.database import get_db
        from app.models.chart_of_accounts import Account
        from uuid import uuid4
        
        db = next(get_db())
        
        if not tenant_id:
            tenant_id = token.get("tenant_id")
        
        if not business_unit_id:
            from app.models.auth import BusinessUnit
            bu = db.query(BusinessUnit).filter(BusinessUnit.tenant_id == tenant_id).first()
            if bu:
                business_unit_id = str(bu.id)
            else:
                raise HTTPException(status_code=400, detail="Business Unit não encontrada")
        
        account = Account(
            id=str(uuid4()),
            name=name,
            code=code,
            description=description,
            subgroup_id=subgroup_id,
            tenant_id=tenant_id,
            business_unit_id=business_unit_id,
            is_active=is_active
        )
        
        db.add(account)
        db.commit()
        db.refresh(account)
        db.close()
        
        return {"id": str(account.id), "message": "Conta criada com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
