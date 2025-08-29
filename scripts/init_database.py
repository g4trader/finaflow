#!/usr/bin/env python3
"""
Script para inicializar banco de dados e criar super admin
"""

import sys
import os
from pathlib import Path

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_path))

from sqlalchemy.orm import Session
from app.database import SessionLocal, create_tables
from app.models.auth import User, Tenant, UserRole, UserStatus
from app.services.security import SecurityService
from uuid import uuid4

def init_database():
    """Inicializa o banco de dados."""
    print("🗄️ Inicializando banco de dados...")
    
    try:
        # Criar tabelas
        create_tables()
        print("✅ Tabelas criadas com sucesso")
        
        # Criar sessão
        db = SessionLocal()
        
        # Criar tenant padrão
        print("🏢 Criando tenant padrão...")
        default_tenant = Tenant(
            id=uuid4(),
            name="FinaFlow Default",
            domain="finaflow.com",
            status="active"
        )
        db.add(default_tenant)
        db.commit()
        db.refresh(default_tenant)
        print(f"✅ Tenant criado: {default_tenant.name}")
        
        # Criar super admin
        print("👑 Criando super admin...")
        super_admin_password = "Admin@123"
        hashed_password = SecurityService.hash_password(super_admin_password)
        
        super_admin = User(
            id=uuid4(),
            tenant_id=default_tenant.id,
            username="admin",
            email="admin@finaflow.com",
            hashed_password=hashed_password,
            first_name="Super",
            last_name="Admin",
            role=UserRole.SUPER_ADMIN,
            status=UserStatus.ACTIVE
        )
        db.add(super_admin)
        db.commit()
        db.refresh(super_admin)
        
        print("✅ Super admin criado com sucesso!")
        print(f"   Username: {super_admin.username}")
        print(f"   Email: {super_admin.email}")
        print(f"   Password: {super_admin_password}")
        print(f"   Role: {super_admin.role}")
        
        # Criar tenant admin de exemplo
        print("👤 Criando tenant admin de exemplo...")
        tenant_admin_password = "Tenant@123"
        hashed_password = SecurityService.hash_password(tenant_admin_password)
        
        tenant_admin = User(
            id=uuid4(),
            tenant_id=default_tenant.id,
            username="tenant_admin",
            email="tenant@finaflow.com",
            hashed_password=hashed_password,
            first_name="Tenant",
            last_name="Admin",
            role=UserRole.TENANT_ADMIN,
            status=UserStatus.ACTIVE
        )
        db.add(tenant_admin)
        db.commit()
        db.refresh(tenant_admin)
        
        print("✅ Tenant admin criado com sucesso!")
        print(f"   Username: {tenant_admin.username}")
        print(f"   Email: {tenant_admin.email}")
        print(f"   Password: {tenant_admin_password}")
        print(f"   Role: {tenant_admin.role}")
        
        # Criar usuário de exemplo
        print("👤 Criando usuário de exemplo...")
        user_password = "User@123"
        hashed_password = SecurityService.hash_password(user_password)
        
        example_user = User(
            id=uuid4(),
            tenant_id=default_tenant.id,
            username="user",
            email="user@finaflow.com",
            hashed_password=hashed_password,
            first_name="Example",
            last_name="User",
            role=UserRole.USER,
            status=UserStatus.ACTIVE
        )
        db.add(example_user)
        db.commit()
        db.refresh(example_user)
        
        print("✅ Usuário de exemplo criado com sucesso!")
        print(f"   Username: {example_user.username}")
        print(f"   Email: {example_user.email}")
        print(f"   Password: {user_password}")
        print(f"   Role: {example_user.role}")
        
        db.close()
        
        print("\n🎉 Banco de dados inicializado com sucesso!")
        print("\n📋 RESUMO DOS USUÁRIOS CRIADOS:")
        print("=" * 50)
        print("👑 SUPER ADMIN:")
        print(f"   Username: admin")
        print(f"   Password: {super_admin_password}")
        print(f"   Email: admin@finaflow.com")
        print()
        print("👤 TENANT ADMIN:")
        print(f"   Username: tenant_admin")
        print(f"   Password: {tenant_admin_password}")
        print(f"   Email: tenant@finaflow.com")
        print()
        print("👤 USUÁRIO EXEMPLO:")
        print(f"   Username: user")
        print(f"   Password: {user_password}")
        print(f"   Email: user@finaflow.com")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Erro ao inicializar banco: {e}")
        db.rollback()
        db.close()
        sys.exit(1)

if __name__ == "__main__":
    init_database()
