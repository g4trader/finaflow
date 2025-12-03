#!/usr/bin/env python3
"""
Endpoint temporário para criar usuário de QA no staging
Execute via Cloud Run ou localmente com DATABASE_URL configurada
"""

import sys
import os
from pathlib import Path
from uuid import uuid4
from datetime import datetime

# Adicionar backend ao path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal, create_tables
from app.models.auth import User, Tenant, BusinessUnit, UserRole, UserStatus
from app.services.security import SecurityService

app = FastAPI()

@app.post("/create-qa-user")
def create_qa_user_endpoint():
    """Endpoint temporário para criar usuário de QA."""
    try:
        db = SessionLocal()
        
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
        db.close()
        
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
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

