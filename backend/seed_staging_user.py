#!/usr/bin/env python3
"""
Script para criar usuário de QA no ambiente staging
"""

import sys
import os
from pathlib import Path
from uuid import uuid4
from datetime import datetime

# Adicionar backend ao path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import Session
from app.database import SessionLocal, create_tables
from app.models.auth import User, Tenant, BusinessUnit, UserRole, UserStatus
from app.services.security import SecurityService

def create_qa_user():
    """Cria usuário de QA no banco staging."""
    print("🔧 Inicializando banco de dados...")
    
    try:
        # Criar tabelas se não existirem
        create_tables()
        print("✅ Tabelas verificadas")
        
        db = SessionLocal()
        
        # Verificar se já existe tenant padrão
        print("🏢 Verificando tenant padrão...")
        tenant = db.query(Tenant).first()
        
        if not tenant:
            print("📝 Criando tenant padrão...")
            tenant = Tenant(
                id=str(uuid4()),
                name="FinaFlow Staging",
                domain="finaflow-staging.com",
                status="active"
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
            print(f"✅ Tenant criado: {tenant.name} (ID: {tenant.id})")
        else:
            print(f"✅ Tenant encontrado: {tenant.name} (ID: {tenant.id})")
        
        # Verificar se já existe Business Unit padrão
        print("🏢 Verificando Business Unit padrão...")
        business_unit = db.query(BusinessUnit).filter(
            BusinessUnit.tenant_id == tenant.id
        ).first()
        
        if not business_unit:
            print("📝 Criando Business Unit padrão...")
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
            print(f"✅ Business Unit criada: {business_unit.name} (ID: {business_unit.id})")
        else:
            print(f"✅ Business Unit encontrada: {business_unit.name} (ID: {business_unit.id})")
        
        # Verificar se usuário QA já existe
        print("👤 Verificando usuário QA...")
        qa_user = db.query(User).filter(
            User.email == "qa@finaflow.test"
        ).first()
        
        if qa_user:
            print(f"⚠️  Usuário QA já existe: {qa_user.email}")
            print(f"   ID: {qa_user.id}")
            print(f"   Status: {qa_user.status}")
            print(f"   Role: {qa_user.role}")
            
            # Atualizar senha e status para garantir que está ativo
            qa_user.hashed_password = SecurityService.hash_password("QaFinaflow123!")
            qa_user.status = UserStatus.ACTIVE
            qa_user.tenant_id = tenant.id
            qa_user.business_unit_id = business_unit.id
            qa_user.role = UserRole.SUPER_ADMIN
            qa_user.failed_login_attempts = 0
            qa_user.locked_until = None
            db.commit()
            print("✅ Usuário QA atualizado com sucesso!")
        else:
            print("📝 Criando usuário QA...")
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
            db.commit()
            db.refresh(qa_user)
            print("✅ Usuário QA criado com sucesso!")
        
        print("\n" + "="*60)
        print("✅ USUÁRIO QA CONFIGURADO")
        print("="*60)
        print(f"Email: qa@finaflow.test")
        print(f"Senha: QaFinaflow123!")
        print(f"Username: qa")
        print(f"Role: {qa_user.role}")
        print(f"Status: {qa_user.status}")
        print(f"Tenant: {tenant.name}")
        print(f"Business Unit: {business_unit.name}")
        print("="*60)
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar usuário QA: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_qa_user()
    sys.exit(0 if success else 1)

