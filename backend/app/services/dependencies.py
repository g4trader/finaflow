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
        
        # Atualizar business_unit_id do usuário se presente no token
        # Isso garante que o business_unit_id selecionado seja usado
        token_business_unit_id = payload.get("business_unit_id")
        if token_business_unit_id:
            # Atualizar apenas se diferente do atual (evita queries desnecessárias)
            if str(user.business_unit_id) != str(token_business_unit_id):
                user.business_unit_id = token_business_unit_id
                db.commit()
                db.refresh(user)
        
        # Verificar se usuário está ativo
        user_status = getattr(user, "status", UserStatus.ACTIVE)
        if isinstance(user_status, str):
            try:
                user_status = UserStatus(user_status)
            except ValueError:
                pass

        if user_status != UserStatus.ACTIVE:
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
    user_status = getattr(current_user, "status", UserStatus.ACTIVE)
    if isinstance(user_status, str):
        try:
            user_status = UserStatus(user_status)
        except ValueError:
            pass

    if user_status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário inativo"
        )
    return current_user

def _role_hierarchy_map() -> dict[UserRole, int]:
    return {
        UserRole.USER: 1,
        UserRole.DEPARTMENT_MANAGER: 2,
        UserRole.BUSINESS_UNIT_MANAGER: 3,
        UserRole.TENANT_ADMIN: 4,
        UserRole.SUPER_ADMIN: 5,
    }


def require_role(required_role: UserRole):
    """
    Decorator para verificar role específica.
    """

    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role != required_role and current_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissão negada. Role requerida: {required_role}",
            )
        return current_user

    return role_checker


def require_minimum_role(minimum_role: UserRole):
    """
    Decorator para verificar role mínima.
    """

    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        hierarchy = _role_hierarchy_map()
        user_level = hierarchy.get(current_user.role, 0)
        required_level = hierarchy.get(minimum_role, 0)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissão negada. Role mínima requerida: {minimum_role}",
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
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Verifica se usuário tem acesso ao tenant ou é super admin.
    """
    if current_user.role == UserRole.SUPER_ADMIN:
        return current_user
    tenant_id = getattr(current_user, "tenant_id", None)
    if tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário não associado a um tenant",
        )
    return current_user


def require_same_business_unit_or_higher(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Verifica se usuário tem acesso à business unit ou role superior.
    """
    if current_user.role in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
        return current_user

    if current_user.role == UserRole.BUSINESS_UNIT_MANAGER:
        business_unit_id = getattr(current_user, "business_unit_id", None)
        if business_unit_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário não associado a uma unidade de negócio",
            )
        return current_user

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

def require_super_admin(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão negada. Necessário ser super admin.",
        )
    return current_user


def require_tenant_access(target_tenant_id: str, current_user: User) -> None:
    """
    Garante que o usuário possua acesso ao tenant alvo.
    """
    if current_user.role == UserRole.SUPER_ADMIN:
        return

    tenant_id = getattr(current_user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário não associado a um tenant",
        )

    if str(tenant_id) != str(target_tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado para este tenant",
        )


def tenant(
    request: Request,
    current_user: User = Depends(get_current_active_user),
) -> str:
    """
    Resolve o tenant alvo com base no usuário autenticado e parâmetros da requisição.
    """
    requested_tenant = request.query_params.get("tenant_id")
    if requested_tenant is None:
        current_tenant_id = getattr(current_user, "tenant_id", None)
        if current_tenant_id is None and current_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant não informado",
            )
        requested_tenant = str(current_tenant_id) if current_tenant_id else None

    if requested_tenant is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant não informado",
        )

    require_tenant_access(requested_tenant, current_user)
    return requested_tenant


# Dependências específicas por role
get_super_admin = require_role(UserRole.SUPER_ADMIN)
get_tenant_admin = require_minimum_role(UserRole.TENANT_ADMIN)
get_business_unit_manager = require_minimum_role(UserRole.BUSINESS_UNIT_MANAGER)
get_department_manager = require_minimum_role(UserRole.DEPARTMENT_MANAGER)
get_any_user = get_current_active_user
