from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database import get_db
from app.models.auth import (
    User, UserTenantAccess, UserBusinessUnitAccess, Tenant, BusinessUnit,
    UserTenantAccessCreate, UserTenantAccessUpdate, UserTenantAccessResponse,
    UserBusinessUnitAccessCreate, UserBusinessUnitAccessUpdate, UserBusinessUnitAccessResponse,
    UserRole
)
from app.middleware.auth import get_current_user, get_access_control, AccessControl, Permission
from app.models.permissions import UserPermission

router = APIRouter(prefix="/api/v1/permissions", tags=["permissions"])

PERMISSION_DEFINITIONS = [
    {
        "id": "can_read",
        "permission_id": "can_read",
        "permission_code": "can_read",
        "code": "can_read",
        "name": "Visualizar",
        "description": "Permite visualizar dados da unidade de negócio",
        "category": "acesso",
    },
    {
        "id": "can_write",
        "permission_id": "can_write",
        "permission_code": "can_write",
        "code": "can_write",
        "name": "Editar",
        "description": "Permite criar e editar dados da unidade de negócio",
        "category": "acesso",
    },
    {
        "id": "can_delete",
        "permission_id": "can_delete",
        "permission_code": "can_delete",
        "code": "can_delete",
        "name": "Excluir",
        "description": "Permite excluir dados da unidade de negócio",
        "category": "acesso",
    },
    {
        "id": "can_manage_users",
        "permission_id": "can_manage_users",
        "permission_code": "can_manage_users",
        "code": "can_manage_users",
        "name": "Gerenciar Usuários",
        "description": "Permite conceder e remover acessos de usuários",
        "category": "administração",
    },
]


def _permission_flags_from_payload(permissions: list) -> dict:
    flags = {
        "can_read": False,
        "can_write": False,
        "can_delete": False,
        "can_manage_users": False,
    }
    for permission in permissions or []:
        code = (
            permission.get("permission_code")
            or permission.get("permission_id")
            or permission.get("code")
            or permission.get("id")
        )
        if code in flags:
            flags[code] = bool(permission.get("is_granted", False))
    return flags


def _serialize_granular_permissions(user_id: str, business_unit_id: str, access: UserBusinessUnitAccess | None):
    flags = {
        "can_read": bool(access.can_read) if access else False,
        "can_write": bool(access.can_write) if access else False,
        "can_delete": bool(access.can_delete) if access else False,
        "can_manage_users": bool(access.can_manage_users) if access else False,
    }
    return [
        {
            **definition,
            "user_id": user_id,
            "business_unit_id": business_unit_id,
            "is_granted": flags[definition["code"]],
        }
        for definition in PERMISSION_DEFINITIONS
    ]

# ============================================================================
# PERMISSÕES DE EMPRESA (TENANT)
# ============================================================================

@router.get("/tenants/{user_id}", response_model=List[UserTenantAccessResponse])
async def get_user_tenant_permissions(
    user_id: str,
    current_user: User = Depends(get_current_user),
    access_control: AccessControl = Depends(get_access_control),
    db: Session = Depends(get_db)
):
    """Lista permissões de um usuário em empresas"""
    # Verificar se o usuário atual pode gerenciar o usuário alvo
    if current_user.role != UserRole.SUPER_ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para visualizar permissões de outros usuários"
        )
    
    # Buscar permissões do usuário
    permissions = db.query(UserTenantAccess).filter(
        UserTenantAccess.user_id == user_id
    ).all()
    
    # Formatar resposta
    result = []
    for perm in permissions:
        tenant = db.query(Tenant).filter(Tenant.id == perm.tenant_id).first()
        result.append(UserTenantAccessResponse(
            id=perm.id,
            user_id=perm.user_id,
            tenant_id=perm.tenant_id,
            tenant_name=tenant.name if tenant else "Empresa não encontrada",
            can_read=perm.can_read,
            can_write=perm.can_write,
            can_delete=perm.can_delete,
            can_manage_users=perm.can_manage_users,
            created_at=perm.created_at,
            updated_at=perm.updated_at
        ))
    
    return result

@router.post("/tenants", response_model=UserTenantAccessResponse)
async def create_user_tenant_permission(
    permission_data: UserTenantAccessCreate,
    current_user: User = Depends(get_current_user),
    access_control: AccessControl = Depends(get_access_control),
    db: Session = Depends(get_db)
):
    """Cria permissão de usuário em uma empresa"""
    # Verificar se o usuário atual tem permissão para gerenciar usuários na empresa
    if current_user.role != UserRole.SUPER_ADMIN:
        if not access_control.has_tenant_access(permission_data.tenant_id, Permission.MANAGE_USERS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para gerenciar usuários nesta empresa"
            )
    
    # Verificar se a empresa existe
    tenant = db.query(Tenant).filter(Tenant.id == permission_data.tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada"
        )
    
    # Verificar se o usuário existe
    user = db.query(User).filter(User.id == permission_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Verificar se já existe permissão
    existing = db.query(UserTenantAccess).filter(
        UserTenantAccess.user_id == permission_data.user_id,
        UserTenantAccess.tenant_id == permission_data.tenant_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permissão já existe para este usuário nesta empresa"
        )
    
    # Criar nova permissão
    permission = UserTenantAccess(
        user_id=permission_data.user_id,
        tenant_id=permission_data.tenant_id,
        can_read=permission_data.can_read,
        can_write=permission_data.can_write,
        can_delete=permission_data.can_delete,
        can_manage_users=permission_data.can_manage_users
    )
    
    db.add(permission)
    db.commit()
    db.refresh(permission)
    
    return UserTenantAccessResponse(
        id=permission.id,
        user_id=permission.user_id,
        tenant_id=permission.tenant_id,
        tenant_name=tenant.name,
        can_read=permission.can_read,
        can_write=permission.can_write,
        can_delete=permission.can_delete,
        can_manage_users=permission.can_manage_users,
        created_at=permission.created_at,
        updated_at=permission.updated_at
    )

@router.put("/tenants/{permission_id}", response_model=UserTenantAccessResponse)
async def update_user_tenant_permission(
    permission_id: str,
    permission_data: UserTenantAccessUpdate,
    current_user: User = Depends(get_current_user),
    access_control: AccessControl = Depends(get_access_control),
    db: Session = Depends(get_db)
):
    """Atualiza permissão de usuário em uma empresa"""
    # Buscar permissão
    permission = db.query(UserTenantAccess).filter(UserTenantAccess.id == permission_id).first()
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permissão não encontrada"
        )
    
    # Verificar se o usuário atual tem permissão para gerenciar usuários na empresa
    if current_user.role != UserRole.SUPER_ADMIN:
        if not access_control.has_tenant_access(permission.tenant_id, Permission.MANAGE_USERS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para gerenciar usuários nesta empresa"
            )
    
    # Atualizar permissões
    if permission_data.can_read is not None:
        permission.can_read = permission_data.can_read
    if permission_data.can_write is not None:
        permission.can_write = permission_data.can_write
    if permission_data.can_delete is not None:
        permission.can_delete = permission_data.can_delete
    if permission_data.can_manage_users is not None:
        permission.can_manage_users = permission_data.can_manage_users
    
    permission.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(permission)
    
    # Buscar nome da empresa
    tenant = db.query(Tenant).filter(Tenant.id == permission.tenant_id).first()
    
    return UserTenantAccessResponse(
        id=permission.id,
        user_id=permission.user_id,
        tenant_id=permission.tenant_id,
        tenant_name=tenant.name if tenant else "Empresa não encontrada",
        can_read=permission.can_read,
        can_write=permission.can_write,
        can_delete=permission.can_delete,
        can_manage_users=permission.can_manage_users,
        created_at=permission.created_at,
        updated_at=permission.updated_at
    )

@router.delete("/tenants/{permission_id}")
async def delete_user_tenant_permission(
    permission_id: str,
    current_user: User = Depends(get_current_user),
    access_control: AccessControl = Depends(get_access_control),
    db: Session = Depends(get_db)
):
    """Remove permissão de usuário em uma empresa"""
    # Buscar permissão
    permission = db.query(UserTenantAccess).filter(UserTenantAccess.id == permission_id).first()
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permissão não encontrada"
        )
    
    # Verificar se o usuário atual tem permissão para gerenciar usuários na empresa
    if current_user.role != UserRole.SUPER_ADMIN:
        if not access_control.has_tenant_access(permission.tenant_id, Permission.MANAGE_USERS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para gerenciar usuários nesta empresa"
            )
    
    db.delete(permission)
    db.commit()
    
    return {"message": "Permissão removida com sucesso"}

# ============================================================================
# PERMISSÕES DE BUSINESS UNIT
# ============================================================================

@router.get("/business-units/{user_id}", response_model=List[UserBusinessUnitAccessResponse])
async def get_user_business_unit_permissions(
    user_id: str,
    current_user: User = Depends(get_current_user),
    access_control: AccessControl = Depends(get_access_control),
    db: Session = Depends(get_db)
):
    """Lista permissões de um usuário em BUs"""
    # Verificar se o usuário atual pode gerenciar o usuário alvo
    if current_user.role != UserRole.SUPER_ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para visualizar permissões de outros usuários"
        )
    
    # Buscar permissões do usuário
    permissions = db.query(UserBusinessUnitAccess).filter(
        UserBusinessUnitAccess.user_id == user_id
    ).all()
    
    # Formatar resposta
    result = []
    for perm in permissions:
        bu = db.query(BusinessUnit).filter(BusinessUnit.id == perm.business_unit_id).first()
        tenant = db.query(Tenant).filter(Tenant.id == bu.tenant_id).first() if bu else None
        
        result.append(UserBusinessUnitAccessResponse(
            id=perm.id,
            user_id=perm.user_id,
            business_unit_id=perm.business_unit_id,
            business_unit_name=bu.name if bu else "BU não encontrada",
            tenant_name=tenant.name if tenant else "Empresa não encontrada",
            can_read=perm.can_read,
            can_write=perm.can_write,
            can_delete=perm.can_delete,
            can_manage_users=perm.can_manage_users,
            created_at=perm.created_at,
            updated_at=perm.updated_at
        ))
    
    return result

@router.post("/business-units", response_model=UserBusinessUnitAccessResponse)
async def create_user_business_unit_permission(
    permission_data: UserBusinessUnitAccessCreate,
    current_user: User = Depends(get_current_user),
    access_control: AccessControl = Depends(get_access_control),
    db: Session = Depends(get_db)
):
    """Cria permissão de usuário em uma BU"""
    # Verificar se o usuário atual tem permissão para gerenciar usuários na BU
    if current_user.role != UserRole.SUPER_ADMIN:
        if not access_control.has_business_unit_access(permission_data.business_unit_id, Permission.MANAGE_USERS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para gerenciar usuários nesta BU"
            )
    
    # Verificar se a BU existe
    bu = db.query(BusinessUnit).filter(BusinessUnit.id == permission_data.business_unit_id).first()
    if not bu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business Unit não encontrada"
        )
    
    # Verificar se o usuário existe
    user = db.query(User).filter(User.id == permission_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Verificar se já existe permissão
    existing = db.query(UserBusinessUnitAccess).filter(
        UserBusinessUnitAccess.user_id == permission_data.user_id,
        UserBusinessUnitAccess.business_unit_id == permission_data.business_unit_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permissão já existe para este usuário nesta BU"
        )
    
    # Criar nova permissão
    permission = UserBusinessUnitAccess(
        user_id=permission_data.user_id,
        business_unit_id=permission_data.business_unit_id,
        can_read=permission_data.can_read,
        can_write=permission_data.can_write,
        can_delete=permission_data.can_delete,
        can_manage_users=permission_data.can_manage_users
    )
    
    db.add(permission)
    db.commit()
    db.refresh(permission)
    
    # Buscar dados da BU e empresa
    tenant = db.query(Tenant).filter(Tenant.id == bu.tenant_id).first()
    
    return UserBusinessUnitAccessResponse(
        id=permission.id,
        user_id=permission.user_id,
        business_unit_id=permission.business_unit_id,
        business_unit_name=bu.name,
        tenant_name=tenant.name if tenant else "Empresa não encontrada",
        can_read=permission.can_read,
        can_write=permission.can_write,
        can_delete=permission.can_delete,
        can_manage_users=permission.can_manage_users,
        created_at=permission.created_at,
        updated_at=permission.updated_at
    )

@router.put("/business-units/{permission_id}", response_model=UserBusinessUnitAccessResponse)
async def update_user_business_unit_permission(
    permission_id: str,
    permission_data: UserBusinessUnitAccessUpdate,
    current_user: User = Depends(get_current_user),
    access_control: AccessControl = Depends(get_access_control),
    db: Session = Depends(get_db)
):
    """Atualiza permissão de usuário em uma BU"""
    # Buscar permissão
    permission = db.query(UserBusinessUnitAccess).filter(UserBusinessUnitAccess.id == permission_id).first()
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permissão não encontrada"
        )
    
    # Verificar se o usuário atual tem permissão para gerenciar usuários na BU
    if current_user.role != UserRole.SUPER_ADMIN:
        if not access_control.has_business_unit_access(permission.business_unit_id, Permission.MANAGE_USERS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para gerenciar usuários nesta BU"
            )
    
    # Atualizar permissões
    if permission_data.can_read is not None:
        permission.can_read = permission_data.can_read
    if permission_data.can_write is not None:
        permission.can_write = permission_data.can_write
    if permission_data.can_delete is not None:
        permission.can_delete = permission_data.can_delete
    if permission_data.can_manage_users is not None:
        permission.can_manage_users = permission_data.can_manage_users
    
    permission.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(permission)
    
    # Buscar dados da BU e empresa
    bu = db.query(BusinessUnit).filter(BusinessUnit.id == permission.business_unit_id).first()
    tenant = db.query(Tenant).filter(Tenant.id == bu.tenant_id).first() if bu else None
    
    return UserBusinessUnitAccessResponse(
        id=permission.id,
        user_id=permission.user_id,
        business_unit_id=permission.business_unit_id,
        business_unit_name=bu.name if bu else "BU não encontrada",
        tenant_name=tenant.name if tenant else "Empresa não encontrada",
        can_read=permission.can_read,
        can_write=permission.can_write,
        can_delete=permission.can_delete,
        can_manage_users=permission.can_manage_users,
        created_at=permission.created_at,
        updated_at=permission.updated_at
    )

@router.delete("/business-units/{permission_id}")
async def delete_user_business_unit_permission(
    permission_id: str,
    current_user: User = Depends(get_current_user),
    access_control: AccessControl = Depends(get_access_control),
    db: Session = Depends(get_db)
):
    """Remove permissão de usuário em uma BU"""
    # Buscar permissão
    permission = db.query(UserBusinessUnitAccess).filter(UserBusinessUnitAccess.id == permission_id).first()
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permissão não encontrada"
        )
    
    # Verificar se o usuário atual tem permissão para gerenciar usuários na BU
    if current_user.role != UserRole.SUPER_ADMIN:
        if not access_control.has_business_unit_access(permission.business_unit_id, Permission.MANAGE_USERS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para gerenciar usuários nesta BU"
            )
    
    db.delete(permission)
    db.commit()
    
    return {"message": "Permissão removida com sucesso"}

# ============================================================================
# ENDPOINTS DE CONSULTA
# ============================================================================

@router.get("/available")
async def list_available_permissions(
    current_user: User = Depends(get_current_user),
):
    """Lista permissões disponíveis para as telas de administração."""
    return PERMISSION_DEFINITIONS


@router.get("/users/{user_id}/business-units/{business_unit_id}")
async def get_user_business_unit_granular_permissions(
    user_id: str,
    business_unit_id: str,
    current_user: User = Depends(get_current_user),
    access_control: AccessControl = Depends(get_access_control),
    db: Session = Depends(get_db),
):
    """Retorna as permissões editáveis de um usuário em uma BU."""
    if current_user.role != UserRole.SUPER_ADMIN and current_user.id != user_id:
        if not access_control.has_business_unit_access(business_unit_id, Permission.MANAGE_USERS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para visualizar permissões desta BU",
            )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    business_unit = db.query(BusinessUnit).filter(
        BusinessUnit.id == business_unit_id,
        BusinessUnit.status == "active",
    ).first()
    if not business_unit:
        raise HTTPException(status_code=404, detail="Business Unit não encontrada")

    access = db.query(UserBusinessUnitAccess).filter(
        UserBusinessUnitAccess.user_id == user_id,
        UserBusinessUnitAccess.business_unit_id == business_unit_id,
    ).first()

    return _serialize_granular_permissions(user_id, business_unit_id, access)


@router.put("/users/{user_id}/business-units/{business_unit_id}")
async def update_user_business_unit_granular_permissions(
    user_id: str,
    business_unit_id: str,
    payload: dict,
    current_user: User = Depends(get_current_user),
    access_control: AccessControl = Depends(get_access_control),
    db: Session = Depends(get_db),
):
    """Atualiza permissões de um usuário em uma BU a partir do formato usado no frontend."""
    if current_user.role != UserRole.SUPER_ADMIN:
        if not access_control.has_business_unit_access(business_unit_id, Permission.MANAGE_USERS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para gerenciar usuários nesta BU",
            )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    business_unit = db.query(BusinessUnit).filter(
        BusinessUnit.id == business_unit_id,
        BusinessUnit.status == "active",
    ).first()
    if not business_unit:
        raise HTTPException(status_code=404, detail="Business Unit não encontrada")

    flags = _permission_flags_from_payload(payload.get("permissions", []))

    access = db.query(UserBusinessUnitAccess).filter(
        UserBusinessUnitAccess.user_id == user_id,
        UserBusinessUnitAccess.business_unit_id == business_unit_id,
    ).first()
    if not access:
        access = UserBusinessUnitAccess(
            user_id=user_id,
            business_unit_id=business_unit_id,
        )
        db.add(access)

    access.can_read = flags["can_read"]
    access.can_write = flags["can_write"]
    access.can_delete = flags["can_delete"]
    access.can_manage_users = flags["can_manage_users"]
    access.updated_at = datetime.utcnow()

    for code, granted in flags.items():
        user_permission = db.query(UserPermission).filter(
            UserPermission.user_id == user_id,
            UserPermission.business_unit_id == business_unit_id,
            UserPermission.permission_code == code,
        ).first()
        if not user_permission:
            user_permission = UserPermission(
                user_id=user_id,
                business_unit_id=business_unit_id,
                permission_code=code,
                granted_by=current_user.id,
            )
            db.add(user_permission)

        user_permission.is_granted = granted
        user_permission.granted_by = current_user.id
        user_permission.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(access)

    return _serialize_granular_permissions(user_id, business_unit_id, access)

@router.get("/my-access")
async def get_my_access(
    current_user: User = Depends(get_current_user),
    access_control: AccessControl = Depends(get_access_control)
):
    """Retorna as permissões do usuário atual"""
    accessible_tenants = access_control.get_accessible_tenants()
    accessible_business_units = access_control.get_accessible_business_units()
    
    return {
        "user_id": current_user.id,
        "role": current_user.role,
        "accessible_tenants": accessible_tenants,
        "accessible_business_units": accessible_business_units
    }
