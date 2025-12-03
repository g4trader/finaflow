from contextlib import suppress
from datetime import timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.auth import (
    User,
    UserCreate,
    UserResponse,
    UserLogin,
    TokenResponse,
    RefreshTokenRequest,
    TenantCreate,
    TenantResponse,
    UserRole,
    UserStatus,
    BusinessUnit,
    UserBusinessUnitAccess,
    Tenant,
)
from app.services.security import SecurityService
from app.services.dependencies import get_current_active_user, get_super_admin, log_audit_event
from app.models.auth import UserSession
from datetime import datetime
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["authentication"])

class BusinessUnitSelectionRequest(BaseModel):
    business_unit_id: str


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Autenticação de usuário com proteção contra brute force.
    """
    try:
        payload: Optional[dict] = None
        content_type = request.headers.get("content-type", "")

        if "application/json" in content_type:
            payload = await request.json()
        elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            form = await request.form()
            payload = dict(form.items())
        else:
            # tentar interpretar como JSON por padrão
            with suppress(Exception):
                payload = await request.json()

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Campos username e password são obrigatórios."
            )

        username = payload.get("username")
        password = payload.get("password")
        if not username or not password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Campos username e password são obrigatórios."
            )

        credentials = UserLogin(username=username, password=password)

        # Autenticar usuário
        user = SecurityService.authenticate_user(
            db=db,
            username=credentials.username,
            password=credentials.password,
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
        import traceback
        print(f"❌ [auth.login] Erro inesperado: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.get("/needs-business-unit-selection")
async def needs_business_unit_selection(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Verifica se o usuário precisa selecionar uma unidade de negócio.
    """
    try:
        if current_user.role == UserRole.SUPER_ADMIN:
            total_bus = db.query(BusinessUnit).count()
            needs_selection = total_bus > 1 and current_user.business_unit_id is None
        else:
            accesses = db.query(UserBusinessUnitAccess).filter(
                UserBusinessUnitAccess.user_id == current_user.id
            ).all()

            if not accesses:
                needs_selection = current_user.business_unit_id is None
            else:
                needs_selection = (
                    current_user.business_unit_id is None and len(accesses) > 1
                )

        return {
            "needs_selection": bool(needs_selection),
            "business_unit_id": current_user.business_unit_id,
            "role": current_user.role,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao verificar necessidade de seleção de BU: {exc}",
        ) from exc


@router.get("/user-business-units")
async def list_user_business_units(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Lista as unidades de negócio disponíveis para o usuário atual.
    """
    try:
        result = []

        if current_user.role == UserRole.SUPER_ADMIN:
            business_units = db.query(BusinessUnit).all()
            for bu in business_units:
                tenant = db.query(Tenant).filter(Tenant.id == bu.tenant_id).first()
                result.append(
                    {
                        "id": bu.id,
                        "name": bu.name,
                        "code": bu.code,
                        "tenant_id": bu.tenant_id,
                        "tenant_name": tenant.name if tenant else None,
                        "permissions": {
                            "can_read": True,
                            "can_write": True,
                            "can_delete": True,
                            "can_manage_users": True,
                        },
                    }
                )
        else:
            accesses = (
                db.query(UserBusinessUnitAccess, BusinessUnit, Tenant)
                .join(BusinessUnit, BusinessUnit.id == UserBusinessUnitAccess.business_unit_id)
                .join(Tenant, Tenant.id == BusinessUnit.tenant_id)
                .filter(UserBusinessUnitAccess.user_id == current_user.id)
                .all()
            )

            for access, bu, tenant in accesses:
                result.append(
                    {
                        "id": bu.id,
                        "name": bu.name,
                        "code": bu.code,
                        "tenant_id": bu.tenant_id,
                        "tenant_name": tenant.name if tenant else None,
                        "permissions": {
                            "can_read": bool(access.can_read),
                            "can_write": bool(access.can_write),
                            "can_delete": bool(access.can_delete),
                            "can_manage_users": bool(access.can_manage_users),
                        },
                    }
                )

        return result
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao carregar unidades de negócio: {exc}",
        ) from exc


@router.post("/select-business-unit", response_model=TokenResponse)
async def select_business_unit(
    payload: BusinessUnitSelectionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Seleciona a unidade de negócio ativa do usuário e retorna novo access token.
    """
    try:
        target_bu = (
            db.query(BusinessUnit)
            .filter(BusinessUnit.id == payload.business_unit_id)
            .first()
        )

        if not target_bu:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business unit não encontrada",
            )

        if current_user.role != UserRole.SUPER_ADMIN:
            has_access = (
                db.query(UserBusinessUnitAccess)
                .filter(
                    UserBusinessUnitAccess.user_id == current_user.id,
                    UserBusinessUnitAccess.business_unit_id == payload.business_unit_id,
                )
                .first()
            )
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Usuário não possui acesso a esta unidade de negócio",
                )

        current_user.business_unit_id = payload.business_unit_id
        db.commit()
        db.refresh(current_user)

        token_payload = {
            "sub": str(current_user.id),
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role,
            "tenant_id": str(current_user.tenant_id),
            "business_unit_id": str(current_user.business_unit_id) if current_user.business_unit_id else None,
            "department_id": str(current_user.department_id) if current_user.department_id else None,
        }

        access_token = SecurityService.create_access_token(data=token_payload)
        refresh_token = SecurityService.create_refresh_token(
            data={"sub": str(current_user.id), "session_id": SecurityService.generate_secure_token(24)}
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=30 * 60,
        )
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao selecionar unidade de negócio: {exc}",
        ) from exc


@router.get("/user-info")
async def get_user_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retorna informações detalhadas do usuário autenticado.
    """
    try:
        tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
        business_unit = None
        if current_user.business_unit_id:
            business_unit = (
                db.query(BusinessUnit)
                .filter(BusinessUnit.id == current_user.business_unit_id)
                .first()
            )

        return {
            "user_id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "role": current_user.role,
            "tenant_id": current_user.tenant_id,
            "tenant_name": tenant.name if tenant else None,
            "business_unit_id": current_user.business_unit_id,
            "business_unit_name": business_unit.name if business_unit else None,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao carregar informações do usuário: {exc}",
        ) from exc

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

@router.post("/create-qa-user")
async def create_qa_user_endpoint(
    db: Session = Depends(get_db)
):
    """
    Endpoint temporário para criar usuário de QA no staging.
    Remove após criar o usuário.
    """
    try:
        from uuid import uuid4
        
        # Verificar ou criar tenant
        tenant = db.query(Tenant).filter(Tenant.domain == "finaflow-staging.com").first()
        if not tenant:
            tenant = Tenant(
                id=str(uuid4()),
                name="FinaFlow Staging",
                domain="finaflow-staging.com",
                status="active"
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
        
        # Verificar ou criar Business Unit
        business_unit = db.query(BusinessUnit).filter(
            BusinessUnit.tenant_id == tenant.id,
            BusinessUnit.code == "MAT"
        ).first()
        if not business_unit:
            business_unit = BusinessUnit(
                id=str(uuid4()),
                tenant_id=tenant.id,
                name="Matriz",
                code="MAT",
                status="active"
            )
            db.add(business_unit)
            db.commit()
            db.refresh(business_unit)
        
        # Verificar ou criar usuário QA
        qa_user = db.query(User).filter(User.email == "qa@finaflow.test").first()
        if qa_user:
            qa_user.hashed_password = SecurityService.hash_password("QaFinaflow123!")
            qa_user.status = UserStatus.ACTIVE
            qa_user.tenant_id = tenant.id
            qa_user.business_unit_id = business_unit.id
            qa_user.role = UserRole.SUPER_ADMIN
            qa_user.failed_login_attempts = 0
            qa_user.locked_until = None
            action = "atualizado"
        else:
            qa_user = User(
                id=str(uuid4()),
                tenant_id=tenant.id,
                business_unit_id=business_unit.id,
                username="qa",
                email="qa@finaflow.test",
                hashed_password=SecurityService.hash_password("QaFinaflow123!"),
                first_name="QA",
                last_name="FinaFlow",
                role=UserRole.SUPER_ADMIN,
                status=UserStatus.ACTIVE,
                failed_login_attempts=0,
                locked_until=None
            )
            db.add(qa_user)
            action = "criado"
        
        db.commit()
        db.refresh(qa_user)
        
        return {
            "success": True,
            "action": action,
            "user": {
                "id": qa_user.id,
                "email": qa_user.email,
                "username": qa_user.username,
                "role": qa_user.role,
                "status": qa_user.status,
                "tenant": tenant.name,
                "business_unit": business_unit.name
            },
            "credentials": {
                "email": "qa@finaflow.test",
                "password": "QaFinaflow123!"
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar usuário QA: {str(e)}"
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
