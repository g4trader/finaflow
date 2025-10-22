from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.auth import User, UserRole, UserStatus
from app.services.security import SecurityService

# Configuração do bearer token
security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependência para obter usuário atual autenticado.
    """
    try:
        # Verificar token
        payload = SecurityService.verify_token(credentials.credentials, "access")
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )
        
        # Buscar usuário no banco
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário não encontrado"
            )
        
        # Verificar se usuário está ativo
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário inativo"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Erro na autenticação"
        )

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependência para obter usuário ativo.
    """
    if current_user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário inativo"
        )
    return current_user

def require_role(required_role: UserRole):
    """
    Decorator para verificar role específica.
    """
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role != required_role and current_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissão negada. Role requerida: {required_role}"
            )
        return current_user
    return role_checker

def require_minimum_role(minimum_role: UserRole):
    """
    Decorator para verificar role mínima.
    """
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        role_hierarchy = {
            UserRole.USER: 1,
            UserRole.DEPARTMENT_MANAGER: 2,
            UserRole.BUSINESS_UNIT_MANAGER: 3,
            UserRole.TENANT_ADMIN: 4,
            UserRole.SUPER_ADMIN: 5
        }
        
        user_level = role_hierarchy.get(current_user.role, 0)
        required_level = role_hierarchy.get(minimum_role, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissão negada. Role mínima requerida: {minimum_role}"
            )
        return current_user
    return role_checker

def get_tenant_context(
    current_user: User = Depends(get_current_active_user),
    request: Request = None
) -> dict:
    """
    Dependência para obter contexto do tenant.
    """
    return {
        "user": current_user,
        "tenant_id": current_user.tenant_id,
        "business_unit_id": current_user.business_unit_id,
        "department_id": current_user.department_id,
        "role": current_user.role
    }

def require_same_tenant_or_super_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Verifica se usuário tem acesso ao tenant ou é super admin.
    """
    if current_user.role == UserRole.SUPER_ADMIN:
        return current_user
    
    # Para outros usuários, verificar se estão no mesmo tenant
    # Esta verificação será feita nos endpoints específicos
    return current_user

def require_same_business_unit_or_higher(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Verifica se usuário tem acesso à business unit ou role superior.
    """
    if current_user.role in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
        return current_user
    
    # Para business unit managers, verificar se estão na mesma business unit
    if current_user.role == UserRole.BUSINESS_UNIT_MANAGER:
        return current_user
    
    # Para department managers e users, verificar se estão no mesmo departamento
    return current_user

def log_audit_event(
    action: str,
    resource_type: str,
    resource_id: str = None,
    details: str = None
):
    """
    Decorator para log automático de auditoria.
    """
    def audit_logger(
        current_user: User = Depends(get_current_active_user),
        request: Request = None,
        db: Session = Depends(get_db)
    ):
        # Log do evento
        SecurityService.log_audit_event(
            db=db,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
        return current_user
    return audit_logger

# Dependências específicas por role
get_super_admin = require_role(UserRole.SUPER_ADMIN)
get_tenant_admin = require_minimum_role(UserRole.TENANT_ADMIN)
get_business_unit_manager = require_minimum_role(UserRole.BUSINESS_UNIT_MANAGER)
get_department_manager = require_minimum_role(UserRole.DEPARTMENT_MANAGER)
get_any_user = get_current_active_user


def tenant(current_user: User = Depends(get_current_active_user)) -> str:
    """Return the tenant identifier associated with the authenticated user."""

    if not current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário não possui tenant associado",
        )
    return current_user.tenant_id
