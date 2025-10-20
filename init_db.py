#!/usr/bin/env python3
"""
Script para inicializar o banco de dados PostgreSQL
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from uuid import uuid4

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Forçar uso do PostgreSQL
os.environ["DATABASE_URL"] = "postgresql://finaflow_user:finaflow_password@34.70.102.98:5432/finaflow_db"

from app.database import get_db, engine
from app.models.auth import Base, User, Tenant, BusinessUnit, UserRole, UserStatus

def init_database():
    """Inicializa o banco de dados com tabelas e dados básicos"""
    print("🔄 Inicializando banco de dados...")
    
    # Criar todas as tabelas
    print("📋 Criando tabelas...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tabelas criadas com sucesso")
    
    # Criar sessão
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    # Forçar criação de dados (removendo verificação)
    print("🔄 Criando dados iniciais...")
    
    try:
        print("🏢 Criando empresa padrão...")
        # Criar empresa padrão
        default_tenant = Tenant(
            id=str(uuid4()),
            name="FinaFlow",
            domain="finaflow.com",
            status="active"
        )
        db.add(default_tenant)
        db.commit()
        db.refresh(default_tenant)
        print(f"✅ Empresa criada: {default_tenant.name}")
        
        print("🏢 Criando Business Unit padrão...")
        # Criar BU padrão
        default_bu = BusinessUnit(
            id=str(uuid4()),
            tenant_id=default_tenant.id,
            name="Matriz",
            code="MAT",
            status="active"
        )
        db.add(default_bu)
        db.commit()
        db.refresh(default_bu)
        print(f"✅ Business Unit criada: {default_bu.name}")
        
        print("👤 Criando usuário administrador...")
        # Criar usuário administrador
        admin_user = User(
            id=str(uuid4()),
            tenant_id=default_tenant.id,
            business_unit_id=default_bu.id,
            username="admin",
            email="admin@finaflow.com",
            first_name="Admin",
            last_name="User",
            hashed_password="hashed_password_placeholder",
            phone="(11) 99999-9999",
            role=UserRole.SUPER_ADMIN,
            status=UserStatus.ACTIVE
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print(f"✅ Usuário administrador criado: {admin_user.email}")
        
        print("👤 Criando usuário de teste...")
        # Criar usuário de teste
        test_user = User(
            id=str(uuid4()),
            tenant_id=default_tenant.id,
            business_unit_id=default_bu.id,
            username="test",
            email="test@finaflow.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed_password_placeholder",
            phone="(11) 88888-8888",
            role=UserRole.USER,
            status=UserStatus.ACTIVE
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"✅ Usuário de teste criado: {test_user.email}")
        
        print("🎉 Banco de dados inicializado com sucesso!")
        print(f"📊 Resumo:")
        print(f"   - Empresas: {db.query(Tenant).count()}")
        print(f"   - Business Units: {db.query(BusinessUnit).count()}")
        print(f"   - Usuários: {db.query(User).count()}")
        
    except Exception as e:
        print(f"❌ Erro ao inicializar banco de dados: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    # Forçar uso do PostgreSQL
    os.environ["DATABASE_URL"] = "postgresql://finaflow_user:finaflow_password@34.70.102.98:5432/finaflow_db"
    
    init_database()
