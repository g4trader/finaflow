from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
import jwt
from app.config import Settings
from app.models.user import UserInDB, Role

settings = Settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        
        # Mapear campos do JWT para UserInDB
        user_data = {
            "id": payload.get("sub"),
            "username": payload.get("sub"),  # Usar sub como username temporariamente
            "email": f"{payload.get('sub')}@finaflow.com",  # Email temporário
            "hashed_password": "",  # Não precisamos da senha aqui
            "role": payload.get("role"),
            "tenant_id": payload.get("tenant_id"),
            "created_at": None  # Não temos essa informação no JWT
        }
        
        return UserInDB(**user_data)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_active_user(current: UserInDB = Depends(get_current_user)) -> UserInDB:
    return current

def require_super_admin(current: UserInDB = Depends(get_current_active_user)) -> UserInDB:
    if current.role != Role.super_admin:
        raise HTTPException(status_code=403, detail="Super admin privileges required")
    return current

def require_tenant_access(tenant_id: str, current: UserInDB = Depends(get_current_active_user)) -> UserInDB:
    if current.role == Role.tenant_user and current.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this tenant")
    return current


def tenant(tenant_id: str | None = None, current: UserInDB = Depends(get_current_user)) -> str:
    """Validate and return the tenant identifier for the request.

    If ``tenant_id`` is not provided, the current user's tenant is used. Tenant
    users are restricted to their own tenant and will receive a 403 error when
    trying to access others.
    """

    if tenant_id is None:
        if current.tenant_id is None:
            raise HTTPException(status_code=400, detail="tenant_id required")
        tenant_id = current.tenant_id

    if current.role == Role.tenant_user and current.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this tenant")

    return tenant_id
