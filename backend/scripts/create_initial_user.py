#!/usr/bin/env python3
"""
Script para criar usuário inicial qa@finaflow.test
"""
import os
import sys
from pathlib import Path
from datetime import datetime
from uuid import uuid4

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.database import SessionLocal, create_tables
from app.models.auth import User, UserStatus
from app.services.security import SecurityService

def create_initial_user():
    """Cria usuário inicial se não existir"""
    print("🔄 Criando tabelas...")
    try:
        create_tables()
        print("✅ Tabelas criadas")
    except Exception as e:
        print(f"⚠️  Aviso ao criar tabelas: {e}")
    
    db = SessionLocal()
    try:
        # Verificar se usuário já existe
        existing_user = db.query(User).filter(User.email == "qa@finaflow.test").first()
        if existing_user:
            print(f"✅ Usuário qa@finaflow.test já existe (ID: {existing_user.id})")
            return existing_user
        
        # Criar usuário
        print("👤 Criando usuário qa@finaflow.test...")
        security_service = SecurityService()
        hashed_password = security_service.hash_password("QaFinaflow123!")
        
        user = User(
            id=str(uuid4()),
            email="qa@finaflow.test",
            hashed_password=hashed_password,
            full_name="QA User",
            status=UserStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print(f"✅ Usuário criado com sucesso (ID: {user.id})")
        return user
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao criar usuário: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_initial_user()



