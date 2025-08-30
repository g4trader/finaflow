#!/usr/bin/env python3
"""
Script para debugar o endpoint de usuários
"""

import os
import sys

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Forçar uso do PostgreSQL
os.environ["DATABASE_URL"] = "postgresql://finaflow_user:finaflow_password@34.70.102.98:5432/finaflow_db"

from app.database import get_db, engine, SessionLocal
from app.models.auth import User
from pydantic import BaseModel
from typing import Optional

# Modelo UserResponse exato do hybrid_app.py
class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    role: str
    status: str
    created_at: str
    last_login: Optional[str] = None

    class Config:
        from_attributes = True

def debug_get_users():
    """Simula exatamente o endpoint get_users"""
    print("🔍 Debugando endpoint get_users...")
    
    try:
        # Criar sessão exatamente como no endpoint
        db = SessionLocal()
        
        print("📋 Fazendo query no banco...")
        users = db.query(User).all()
        print(f"✅ Query executada, encontrados {len(users)} usuários")
        
        print("📋 Criando responses...")
        result = []
        for user in users:
            print(f"   🔍 Processando usuário: {user.email}")
            try:
                user_response = UserResponse(
                    id=user.id,
                    name=f"{user.first_name} {user.last_name}",
                    email=user.email,
                    phone=user.phone or '(11) 99999-9999',
                    role=user.role,
                    status=user.status,
                    created_at=user.created_at.strftime("%Y-%m-%d") if user.created_at else "",
                    last_login=user.last_login.strftime("%Y-%m-%d") if user.last_login else None
                )
                result.append(user_response)
                print(f"   ✅ UserResponse criado para {user.email}")
            except Exception as e:
                print(f"   ❌ Erro ao criar UserResponse para {user.email}: {e}")
                print(f"      Valores: id={user.id}, role={user.role}, status={user.status}")
                print(f"      Phone: {user.phone}, Created: {user.created_at}")
                import traceback
                traceback.print_exc()
        
        print(f"\n🎉 Processamento concluído: {len(result)} UserResponses criados")
        
        # Testar serialização JSON
        print("📋 Testando serialização JSON...")
        for user_response in result:
            try:
                json_dict = user_response.dict()
                print(f"   ✅ JSON criado para {json_dict['email']}")
            except Exception as e:
                print(f"   ❌ Erro ao serializar {user_response.email}: {e}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_get_users()
