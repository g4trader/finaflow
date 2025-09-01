from typing import List, Dict, Optional, Set
from sqlalchemy.orm import Session
from app.models.auth import User, BusinessUnit
from app.models.permissions import Permission, UserPermission, PermissionType
from datetime import datetime

class PermissionService:
    """Serviço para gerenciar permissões do sistema"""
    
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
        
        # Se é super_admin, adicionar todas as permissões
        if user.role == "super_admin":
            all_permissions = db.query(Permission).filter(Permission.is_active == True).all()
            for perm in all_permissions:
                permissions.add(perm.code)
            return permissions
        
        # Se é admin, adicionar permissões de admin
        if user.role == "admin":
            admin_permissions = [
                PermissionType.DASHBOARD_READ,
                PermissionType.DASHBOARD_WRITE,
                PermissionType.TRANSACTIONS_READ,
                PermissionType.TRANSACTIONS_WRITE,
                PermissionType.ACCOUNTS_READ,
                PermissionType.ACCOUNTS_WRITE,
                PermissionType.USERS_READ,
                PermissionType.USERS_WRITE
            ]
            permissions.update(admin_permissions)
        
        # Se é user, adicionar permissões básicas
        if user.role == "user":
            user_permissions = [
                PermissionType.DASHBOARD_READ,
                PermissionType.TRANSACTIONS_READ,
                PermissionType.ACCOUNTS_READ
            ]
            permissions.update(user_permissions)
        
        # Buscar permissões específicas do usuário
        query = db.query(UserPermission).filter(
            UserPermission.user_id == user_id,
            UserPermission.is_granted == True
        )
        
        if business_unit_id:
            query = query.filter(UserPermission.business_unit_id == business_unit_id)
        
        user_permissions = query.all()
        
        for user_perm in user_permissions:
            permissions.add(user_perm.permission_code)
        
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
        # Verificar se já existe
        existing = db.query(UserPermission).filter(
            UserPermission.user_id == user_id,
            UserPermission.business_unit_id == business_unit_id,
            UserPermission.permission_code == permission_code
        ).first()
        
        if existing:
            existing.is_granted = True
            existing.granted_by = granted_by
            existing.granted_at = datetime.utcnow()
        else:
            user_permission = UserPermission(
                user_id=user_id,
                business_unit_id=business_unit_id,
                permission_code=permission_code,
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
        user_permission = db.query(UserPermission).filter(
            UserPermission.user_id == user_id,
            UserPermission.business_unit_id == business_unit_id,
            UserPermission.permission_code == permission_code
        ).first()
        
        if user_permission:
            user_permission.is_granted = False
            db.commit()
            return True
        
        return False
    
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
                        description=f"Permissão para {permission_type.value.replace('_', ' ')}",
                        category="general"
                    )
                    db.add(permission)
            
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Erro ao inicializar permissões: {e}")
            return False
