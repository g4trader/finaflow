"""
Endpoints do sistema (status, validação, etc.)
"""
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import User
from app.models.validation_status import DashboardValidationStatus, ValidationStatus
from app.services.dependencies import get_current_active_user

router = APIRouter(tags=["system"])


def _require_business_unit(user: User) -> Optional[str]:
    """Obtém o business_unit_id do usuário"""
    business_unit_id = getattr(user, "business_unit_id", None)
    if not business_unit_id:
        if user.role != "super_admin":
            raise HTTPException(
                status_code=400,
                detail="Usuário precisa selecionar uma unidade de negócio."
            )
        return None
    return str(business_unit_id)


@router.get("/system/validation-status")
def get_validation_status(
    year: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Retorna o status da última validação do dashboard contra a planilha do cliente.
    
    Retorna:
    - status: SUCCESS | FAILED | PENDING
    - last_validation_at: data/hora da última validação
    - year: ano validado
    - validation_details: detalhes da validação (se houver)
    """
    target_year = year or datetime.utcnow().year
    tenant_id = str(current_user.tenant_id)
    business_unit_id = _require_business_unit(current_user)
    
    if not business_unit_id:
        # Para super_admin sem BU, retornar status genérico
        return {
            "status": ValidationStatus.PENDING.value,
            "last_validation_at": None,
            "year": target_year,
            "message": "Selecione uma unidade de negócio para ver o status de validação"
        }
    
    validation_record = db.query(DashboardValidationStatus).filter(
        DashboardValidationStatus.tenant_id == tenant_id,
        DashboardValidationStatus.business_unit_id == business_unit_id,
        DashboardValidationStatus.year == str(target_year)
    ).first()
    
    if not validation_record:
        return {
            "status": ValidationStatus.PENDING.value,
            "last_validation_at": None,
            "year": target_year,
            "message": "Nenhuma validação realizada ainda para este ano"
        }
    
    import json
    validation_details = None
    if validation_record.validation_details:
        try:
            validation_details = json.loads(validation_record.validation_details)
        except:
            pass
    
    return {
        "status": validation_record.status.value,
        "last_validation_at": validation_record.last_validation_at.isoformat() if validation_record.last_validation_at else None,
        "year": int(validation_record.year),
        "validation_details": validation_details
    }

