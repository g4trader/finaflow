import bcrypt
import jwt
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID
import os
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.auth import User, UserSession, AuditLog, UserStatus
from app.database import get_db

# Configurações de segurança
JWT_SECRET = os.getenv("JWT_SECRET", "finaflow-super-secret-jwt-key-2024")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30

class SecurityService:
    """Serviço de segurança para autenticação e autorização."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash de senha usando bcrypt."""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verifica se a senha está correta."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Gera token seguro aleatório."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Cria token de acesso JWT."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """Cria token de refresh JWT."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verifica e decodifica token JWT."""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Tipo de token inválido"
                )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str, ip_address: str = None, user_agent: str = None) -> User:
        """Autentica usuário com proteção contra brute force."""
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            SecurityService._log_failed_login(db, username, ip_address, user_agent, "Usuário não encontrado")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas"
            )
        
        # Verificar se usuário está bloqueado
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Conta bloqueada até {user.locked_until.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        
        # Verificar se usuário está ativo
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Conta inativa ou suspensa"
            )
        
        # Verificar senha
        if not SecurityService.verify_password(password, user.hashed_password):
            SecurityService._handle_failed_login(db, user, ip_address, user_agent)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas"
            )
        
        # Reset de tentativas falhadas
        if user.failed_login_attempts > 0:
            user.failed_login_attempts = 0
            user.locked_until = None
            db.commit()
        
        # Atualizar último login
        user.last_login = datetime.utcnow()
        db.commit()
        
        return user
    
    @staticmethod
    def _handle_failed_login(db: Session, user: User, ip_address: str = None, user_agent: str = None):
        """Gerencia tentativas falhadas de login."""
        user.failed_login_attempts += 1
        
        # Bloquear conta após muitas tentativas
        if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
            user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            user.status = UserStatus.SUSPENDED
        
        db.commit()
        
        # Log da tentativa falhada
        SecurityService._log_failed_login(db, user.username, ip_address, user_agent, f"Tentativa {user.failed_login_attempts}")
    
    @staticmethod
    def _log_failed_login(db: Session, username: str, ip_address: str = None, user_agent: str = None, reason: str = None):
        """Registra tentativa falhada de login."""
        # Criar log de auditoria
        audit_log = AuditLog(
            user_id=None,  # Usuário não autenticado
            tenant_id=None,  # Será preenchido quando encontrar o usuário
            action="LOGIN_FAILED",
            resource_type="USER",
            resource_id=username,
            details=f"Tentativa de login falhada: {reason}",
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(audit_log)
        db.commit()
    
    @staticmethod
    def create_user_session(db: Session, user: User, ip_address: str = None, user_agent: str = None) -> UserSession:
        """Cria sessão de usuário."""
        # Gerar tokens
        session_token = SecurityService.generate_secure_token(64)
        refresh_token = SecurityService.generate_secure_token(64)
        
        # Criar sessão
        session = UserSession(
            user_id=user.id,
            session_token=session_token,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return session
    
    @staticmethod
    def invalidate_user_session(db: Session, session_token: str) -> bool:
        """Invalida sessão de usuário."""
        session = db.query(UserSession).filter(UserSession.session_token == session_token).first()
        if session:
            db.delete(session)
            db.commit()
            return True
        return False
    
    @staticmethod
    def log_audit_event(db: Session, user_id: UUID, tenant_id: UUID, action: str, 
                       resource_type: str, resource_id: str = None, details: str = None,
                       ip_address: str = None, user_agent: str = None):
        """Registra evento de auditoria."""
        audit_log = AuditLog(
            user_id=user_id,
            tenant_id=tenant_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(audit_log)
        db.commit()
    
    @staticmethod
    def generate_secure_password(length: int = 12) -> str:
        """Gera senha segura aleatória."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        while True:
            password = ''.join(secrets.choice(alphabet) for _ in range(length))
            if (any(c.islower() for c in password)
                    and any(c.isupper() for c in password)
                    and any(c.isdigit() for c in password)
                    and any(c in "!@#$%^&*" for c in password)):
                return password
