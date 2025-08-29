from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.auth import (
    User, UserCreate, UserResponse, UserLogin, TokenResponse, 
    RefreshTokenRequest, TenantCreate, TenantResponse, UserRole, UserStatus
)
from app.services.security import SecurityService
from app.services.dependencies import get_current_active_user, get_super_admin, log_audit_event
from app.models.auth import UserSession
from datetime import datetime
from app.models.auth import Tenant

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Autenticação de usuário com proteção contra brute force.
    """
    try:
        # Autenticar usuário
        user = SecurityService.authenticate_user(
            db=db,
            username=form_data.username,
            password=form_data.password,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
        
        # Criar sessão
        session = SecurityService.create_user_session(
            db=db,
            user=user,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
        
        # Criar tokens
        access_token = SecurityService.create_access_token(
            data={
                "sub": str(user.id),
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "tenant_id": str(user.tenant_id),
                "business_unit_id": str(user.business_unit_id) if user.business_unit_id else None,
                "department_id": str(user.department_id) if user.department_id else None
            }
        )
        
        refresh_token = SecurityService.create_refresh_token(
            data={
                "sub": str(user.id),
                "session_id": str(session.id)
            }
        )
        
        # Log de auditoria
        SecurityService.log_audit_event(
            db=db,
            user_id=user.id,
            tenant_id=user.tenant_id,
            action="LOGIN_SUCCESS",
            resource_type="USER",
            resource_id=user.username,
            details="Login realizado com sucesso",
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=30 * 60  # 30 minutos
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Renovar token de acesso usando refresh token.
    """
    try:
        # Verificar refresh token
        payload = SecurityService.verify_token(refresh_request.refresh_token, "refresh")
        user_id = payload.get("sub")
        session_id = payload.get("session_id")
        
        if not user_id or not session_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido"
            )
        
        # Verificar se sessão ainda existe
        session = db.query(UserSession).filter(
            UserSession.id == session_id,
            UserSession.user_id == user_id,
            UserSession.expires_at > datetime.utcnow()
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sessão expirada"
            )
        
        # Buscar usuário
        user = db.query(User).filter(User.id == user_id).first()
        if not user or user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário não encontrado ou inativo"
            )
        
        # Criar novo access token
        access_token = SecurityService.create_access_token(
            data={
                "sub": str(user.id),
        "username": user.username,
        "email": user.email,
                "role": user.role,
                "tenant_id": str(user.tenant_id),
                "business_unit_id": str(user.business_unit_id) if user.business_unit_id else None,
                "department_id": str(user.department_id) if user.department_id else None
            }
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_request.refresh_token,
            token_type="bearer",
            expires_in=30 * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Logout do usuário (invalida sessão).
    """
    try:
        # Invalidar sessão atual
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            SecurityService.invalidate_user_session(db, token)
        
        # Log de auditoria
        SecurityService.log_audit_event(
            db=db,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            action="LOGOUT",
            resource_type="USER",
            resource_id=current_user.username,
            details="Logout realizado",
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
        
        return {"message": "Logout realizado com sucesso"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Obter informações do usuário atual.
    """
    return current_user

@router.post("/tenants", response_model=TenantResponse)
async def create_tenant(
    tenant_data: TenantCreate,
    current_user: User = Depends(get_super_admin),
    db: Session = Depends(get_db)
):
    """
    Criar novo tenant (apenas super admin).
    """
    try:
        # Verificar se domain já existe
        existing_tenant = db.query(Tenant).filter(Tenant.domain == tenant_data.domain).first()
        if existing_tenant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Domain já existe"
            )
        
        # Criar tenant
        tenant = Tenant(
            name=tenant_data.name,
            domain=tenant_data.domain
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        
        # Log de auditoria
        SecurityService.log_audit_event(
            db=db,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            action="TENANT_CREATED",
            resource_type="TENANT",
            resource_id=str(tenant.id),
            details=f"Tenant criado: {tenant.name}"
        )
        
        return tenant
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_super_admin),
    db: Session = Depends(get_db)
):
    """
    Criar novo usuário (apenas super admin).
    """
    try:
        # Verificar se username já existe
        existing_user = db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username já existe"
            )
        
        # Verificar se email já existe
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já existe"
            )
        
        # Hash da senha
        hashed_password = SecurityService.hash_password(user_data.password)
        
        # Criar usuário
        user = User(
            tenant_id=user_data.tenant_id,
            business_unit_id=user_data.business_unit_id,
            department_id=user_data.department_id,
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=user_data.role,
            status=UserStatus.ACTIVE
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Log de auditoria
        SecurityService.log_audit_event(
            db=db,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            action="USER_CREATED",
            resource_type="USER",
            resource_id=user.username,
            details=f"Usuário criado: {user.first_name} {user.last_name}"
        )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(get_super_admin),
    db: Session = Depends(get_db)
):
    """
    Listar usuários do tenant (apenas super admin).
    """
    try:
        # Super admin pode ver todos os usuários
        users = db.query(User).all()
        
        return users
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )
