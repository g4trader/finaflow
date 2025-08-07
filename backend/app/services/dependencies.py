from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
import jwt
from app.config import Settings
from app.models.user import UserInDB, Role

settings = Settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return UserInDB(**payload)
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
