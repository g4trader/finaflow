from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.auth import User
from app.services.security import SecurityService

router = APIRouter(prefix="/test", tags=["test"])

@router.post("/simple-login")
async def simple_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Endpoint de teste simples para login."""
    try:
        print(f"🔐 Tentativa de login: {form_data.username}")
        
        # Buscar usuário
        user = db.query(User).filter(User.username == form_data.username).first()
        
        if not user:
            print("❌ Usuário não encontrado")
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        
        print(f"✅ Usuário encontrado: {user.username}")
        
        # Verificar senha
        if not SecurityService.verify_password(form_data.password, user.hashed_password):
            print("❌ Senha inválida")
            raise HTTPException(status_code=401, detail="Senha inválida")
        
        print("✅ Senha válida")
        
        # Criar token
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "tenant_id": str(user.tenant_id)
        }
        
        access_token = SecurityService.create_access_token(token_data)
        print("✅ Token criado")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erro interno: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")







