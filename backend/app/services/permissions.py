from typing import List, Dict, Optional, Set
from sqlalchemy.orm import Session
from app.models.auth import User, BusinessUnit, Tenant
from app.models.permissions import Permission, UserPermission, RolePermission, PermissionType
from app.config.permissions_config import DEFAULT_ROLE_PERMISSIONS, PERMISSION_DESCRIPTIONS
from datetime import datetime

class PermissionService:
    """Serviço para gerenciar permissões granulares do sistema"""
    
    @staticmethod
    def get_user_permissions(
        db: Session, 
        user_id: str, 
        business_unit_id: Optional[str] = None
    ) -> Set[str]:
        """
        Obtém todas as permissões de um usuário para uma BU específica
        """
        # Buscar usuário
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return set()
        
        permissions = set()
        
        # 1. Permissões baseadas no role (padrão)
        role_permissions = db.query(RolePermission).filter(
            RolePermission.role == user.role
        ).all()
        
        for role_perm in role_permissions:
            if role_perm.is_granted:
                permissions.add(role_perm.permission.code)
        
        # 2. Permissões específicas do usuário
        query = db.query(UserPermission).filter(
            UserPermission.user_id == user_id,
            UserPermission.is_granted == True
        )
        
        if business_unit_id:
            query = query.filter(UserPermission.business_unit_id == business_unit_id)
        
        user_permissions = query.all()
        
        for user_perm in user_permissions:
            permissions.add(user_perm.permission.code)
        
        # 3. Se é super_admin, adicionar todas as permissões
        if user.role == "super_admin":
            all_permissions = db.query(Permission).filter(Permission.is_active == True).all()
            for perm in all_permissions:
                permissions.add(perm.code)
        
        return permissions
    
    @staticmethod
    def check_permission(
        db: Session, 
        user_id: str, 
        permission_code: str, 
        business_unit_id: Optional[str] = None
    ) -> bool:
        """
        Verifica se um usuário tem uma permissão específica
        """
        user_permissions = PermissionService.get_user_permissions(db, user_id, business_unit_id)
        return permission_code in user_permissions
    
    @staticmethod
    def grant_permission(
        db: Session,
        user_id: str,
        business_unit_id: str,
        permission_code: str,
        granted_by: str
    ) -> bool:
        """
        Concede uma permissão específica a um usuário
        """
        # Verificar se a permissão existe
        permission = db.query(Permission).filter(
            Permission.code == permission_code,
            Permission.is_active == True
        ).first()
        
        if not permission:
            return False
        
        # Verificar se já existe
        existing = db.query(UserPermission).filter(
            UserPermission.user_id == user_id,
            UserPermission.business_unit_id == business_unit_id,
            UserPermission.permission_id == permission.id
        ).first()
        
        if existing:
            existing.is_granted = True
            existing.granted_by = granted_by
            existing.granted_at = datetime.utcnow()
        else:
            user_permission = UserPermission(
                user_id=user_id,
                business_unit_id=business_unit_id,
                permission_id=permission.id,
                is_granted=True,
                granted_by=granted_by
            )
            db.add(user_permission)
        
        db.commit()
        return True
    
    @staticmethod
    def revoke_permission(
        db: Session,
        user_id: str,
        business_unit_id: str,
        permission_code: str
    ) -> bool:
        """
        Revoga uma permissão específica de um usuário
        """
        permission = db.query(Permission).filter(
            Permission.code == permission_code
        ).first()
        
        if not permission:
            return False
        
        user_permission = db.query(UserPermission).filter(
            UserPermission.user_id == user_id,
            UserPermission.business_unit_id == business_unit_id,
            UserPermission.permission_id == permission.id
        ).first()
        
        if user_permission:
            user_permission.is_granted = False
            db.commit()
            return True
        
        return False
    
    @staticmethod
    def get_user_business_units_with_permissions(
        db: Session, 
        user_id: str
    ) -> List[Dict]:
        """
        Obtém todas as BUs que um usuário pode acessar com suas permissões
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        # Se é super_admin, retornar todas as BUs
        if user.role == "super_admin":
            business_units = db.query(BusinessUnit).all()
            result = []
            for bu in business_units:
                tenant = db.query(Tenant).filter(Tenant.id == bu.tenant_id).first()
                result.append({
                    "id": str(bu.id),
                    "name": bu.name,
                    "code": bu.code,
                    "tenant_id": str(bu.tenant_id),
                    "tenant_name": tenant.name if tenant else "Empresa não encontrada",
                    "permissions": PermissionService.get_user_permissions(db, user_id, str(bu.id))
                })
            return result
        
        # Buscar permissões específicas do usuário
        user_permissions = db.query(UserPermission).filter(
            UserPermission.user_id == user_id,
            UserPermission.is_granted == True
        ).all()
        
        # Agrupar por BU
        bu_permissions = {}
        for up in user_permissions:
            bu_id = up.business_unit_id
            if bu_id not in bu_permissions:
                bu_permissions[bu_id] = set()
            bu_permissions[bu_id].add(up.permission.code)
        
        # Buscar informações das BUs
        result = []
        for bu_id, permissions in bu_permissions.items():
            bu = db.query(BusinessUnit).filter(BusinessUnit.id == bu_id).first()
            if bu:
                tenant = db.query(Tenant).filter(Tenant.id == bu.tenant_id).first()
                result.append({
                    "id": str(bu.id),
                    "name": bu.name,
                    "code": bu.code,
                    "tenant_id": str(bu.tenant_id),
                    "tenant_name": tenant.name if tenant else "Empresa não encontrada",
                    "permissions": list(permissions)
                })
        
        return result
    
    @staticmethod
    def initialize_permissions(db: Session) -> bool:
        """
        Inicializa as permissões padrão do sistema
        """
        try:
            # Criar permissões se não existirem
            for permission_type in PermissionType:
                existing = db.query(Permission).filter(Permission.code == permission_type.value).first()
                if not existing:
                    permission = Permission(
                        name=permission_type.value.replace('_', ' ').title(),
                        code=permission_type.value,
                        description=PERMISSION_DESCRIPTIONS.get(permission_type, ""),
                        category="general"
                    )
                    db.add(permission)
            
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Erro ao inicializar permissões: {e}")
            return False
    
    @staticmethod
    def get_permissions_by_category(db: Session) -> Dict[str, List[Dict]]:
        """
        Obtém todas as permissões organizadas por categoria
        """
        permissions = db.query(Permission).filter(Permission.is_active == True).all()
        
        categories = {}
        for perm in permissions:
            category = perm.category
            if category not in categories:
                categories[category] = []
            
            categories[category].append({
                "id": perm.id,
                "name": perm.name,
                "code": perm.code,
                "description": perm.description
            })
        
        return categories
