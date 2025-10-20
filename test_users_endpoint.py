#!/usr/bin/env python3
"""
Script para testar o endpoint de usuários localmente
"""

import os
import sys

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Forçar uso do PostgreSQL
os.environ["DATABASE_URL"] = "postgresql://finaflow_user:finaflow_password@34.70.102.98:5432/finaflow_db"

from app.database import get_db, engine, SessionLocal
from app.models.auth import User, Tenant, BusinessUnit, UserRole, UserStatus

def test_users_endpoint():
    """Testa a lógica do endpoint de usuários"""
    print("🔌 Testando endpoint de usuários...")
    
    try:
        # Criar sessão
        db = SessionLocal()
        
        # Testar busca de usuários
        print("📋 Buscando usuários...")
        users = db.query(User).all()
        print(f"✅ Encontrados {len(users)} usuários")
        
        for user in users:
            print(f"   - {user.first_name} {user.last_name} ({user.email}) - {user.role}")
        
        # Testar criação de UserResponse
        print("\n📋 Testando criação de UserResponse...")
        for user in users:
            try:
                response = {
                    "id": user.id,
                    "name": f"{user.first_name} {user.last_name}",
                    "email": user.email,
                    "phone": user.phone or '(11) 99999-9999',
                    "role": user.role,
                    "status": user.status,
                    "created_at": user.created_at.strftime("%Y-%m-%d") if user.created_at else "",
                    "last_login": user.last_login.strftime("%Y-%m-%d") if user.last_login else None
                }
                print(f"✅ UserResponse criado para {user.email}")
            except Exception as e:
                print(f"❌ Erro ao criar UserResponse para {user.email}: {e}")
        
        db.close()
        print("\n🎉 Teste concluído com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_users_endpoint()
