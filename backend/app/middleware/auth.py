from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, List
import jwt
from datetime import datetime, timedelta
import os

from app.database import get_db
from app.models.auth import User, UserTenantAccess, UserBusinessUnitAccess, UserRole

# Configuração JWT
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

class Permission:
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    MANAGE_USERS = "manage_users"

class AccessControl:
    def __init__(self, user: User, db: Session):
        self.user = user
        self.db = db
        self._tenant_access_cache = None
        self._business_unit_access_cache = None

    def has_tenant_access(self, tenant_id: str, permission: str) -> bool:
        """Verifica se o usuário tem acesso a uma empresa específica"""
        if self.user.role == UserRole.SUPER_ADMIN:
            return True
        
        # Buscar acesso específico do usuário à empresa
        access = self.db.query(UserTenantAccess).filter(
            UserTenantAccess.user_id == self.user.id,
            UserTenantAccess.tenant_id == tenant_id
        ).first()
        
        if not access:
            return False
        
        # Verificar permissão específica
        if permission == Permission.READ:
            return access.can_read
        elif permission == Permission.WRITE:
            return access.can_write
        elif permission == Permission.DELETE:
            return access.can_delete
        elif permission == Permission.MANAGE_USERS:
            return access.can_manage_users
        
        return False

    def has_business_unit_access(self, business_unit_id: str, permission: str) -> bool:
        """Verifica se o usuário tem acesso a uma BU específica"""
        if self.user.role == UserRole.SUPER_ADMIN:
            return True
        
        # Buscar acesso específico do usuário à BU
        access = self.db.query(UserBusinessUnitAccess).filter(
            UserBusinessUnitAccess.user_id == self.user.id,
            UserBusinessUnitAccess.business_unit_id == business_unit_id
        ).first()
        
        if not access:
            return False
        
        # Verificar permissão específica
        if permission == Permission.READ:
            return access.can_read
        elif permission == Permission.WRITE:
            return access.can_write
        elif permission == Permission.DELETE:
            return access.can_delete
        elif permission == Permission.MANAGE_USERS:
            return access.can_manage_users
        
        return False

    def get_accessible_tenants(self) -> List[str]:
        """Retorna lista de IDs de empresas que o usuário pode acessar"""
        if self.user.role == UserRole.SUPER_ADMIN:
            # Super admin pode acessar todas as empresas
            tenants = self.db.query(UserTenantAccess.tenant_id).distinct().all()
            return [t.tenant_id for t in tenants]
        
        # Buscar empresas específicas do usuário
        accesses = self.db.query(UserTenantAccess).filter(
            UserTenantAccess.user_id == self.user.id,
            UserTenantAccess.can_read == True
        ).all()
        
        return [access.tenant_id for access in accesses]

    def get_accessible_business_units(self, tenant_id: Optional[str] = None) -> List[str]:
        """Retorna lista de IDs de BUs que o usuário pode acessar"""
        if self.user.role == UserRole.SUPER_ADMIN:
            # Super admin pode acessar todas as BUs
            query = self.db.query(UserBusinessUnitAccess.business_unit_id).distinct()
            if tenant_id:
                # Filtrar por empresa se especificado
                query = query.join(UserBusinessUnitAccess.business_unit).filter(
                    UserBusinessUnitAccess.business_unit.has(tenant_id=tenant_id)
                )
            business_units = query.all()
            return [bu.business_unit_id for bu in business_units]
        
        # Buscar BUs específicas do usuário
        query = self.db.query(UserBusinessUnitAccess).filter(
            UserBusinessUnitAccess.user_id == self.user.id,
            UserBusinessUnitAccess.can_read == True
        )
        
        if tenant_id:
            # Filtrar por empresa se especificado
            query = query.join(UserBusinessUnitAccess.business_unit).filter(
                UserBusinessUnitAccess.business_unit.has(tenant_id=tenant_id)
            )
        
        accesses = query.all()
        return [access.business_unit_id for access in accesses]

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Obtém o usuário atual baseado no token JWT"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado"
        )
    
    return user

def get_access_control(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> AccessControl:
    """Obtém o controle de acesso do usuário atual"""
    return AccessControl(user, db)

def require_tenant_access(permission: str = Permission.READ):
    """Decorator para requerer acesso a uma empresa específica"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Esta função será implementada nos endpoints específicos
            pass
        return wrapper
    return decorator

def require_business_unit_access(permission: str = Permission.READ):
    """Decorator para requerer acesso a uma BU específica"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Esta função será implementada nos endpoints específicos
            pass
        return wrapper
    return decorator

def require_role(required_role: UserRole):
    """Decorator para requerer um papel específico"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Esta função será implementada nos endpoints específicos
            pass
        return wrapper
    return decorator
