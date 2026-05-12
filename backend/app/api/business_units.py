from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import (
    BusinessUnit,
    BusinessUnitCreate,
    BusinessUnitUpdate,
    BusinessUnitResponse,
    UserBusinessUnitAccess,
    User,
    UserRole,
)
from app.models.permissions import UserPermission
from app.services.dependencies import get_current_active_user, get_super_admin


router = APIRouter(prefix="/business-units", tags=["business-units"])


@router.get("", response_model=List[BusinessUnitResponse])
@router.get("/", response_model=List[BusinessUnitResponse])
async def list_business_units(
    tenant_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.SUPER_ADMIN:
        tenant_id = str(current_user.tenant_id)

    query = db.query(BusinessUnit).filter(BusinessUnit.status == "active")
    if tenant_id:
        query = query.filter(BusinessUnit.tenant_id == tenant_id)

    return query.order_by(BusinessUnit.created_at.asc()).all()


@router.post("", response_model=BusinessUnitResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=BusinessUnitResponse, status_code=status.HTTP_201_CREATED)
async def create_business_unit(
    payload: BusinessUnitCreate,
    current_user: User = Depends(get_super_admin),
    db: Session = Depends(get_db),
):
    business_unit = BusinessUnit(
        tenant_id=payload.tenant_id,
        name=payload.name,
        code=payload.code,
        status="active",
    )
    db.add(business_unit)
    db.commit()
    db.refresh(business_unit)
    return business_unit


@router.put("/{business_unit_id}", response_model=BusinessUnitResponse)
async def update_business_unit(
    business_unit_id: str,
    payload: BusinessUnitUpdate,
    current_user: User = Depends(get_super_admin),
    db: Session = Depends(get_db),
):
    business_unit = db.query(BusinessUnit).filter(BusinessUnit.id == business_unit_id).first()
    if not business_unit or business_unit.status == "deleted":
        raise HTTPException(status_code=404, detail="Business unit não encontrada")

    if payload.name is not None:
        business_unit.name = payload.name
    if payload.code is not None:
        business_unit.code = payload.code
    if payload.status is not None:
        business_unit.status = payload.status

    db.commit()
    db.refresh(business_unit)
    return business_unit


@router.delete("/{business_unit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business_unit(
    business_unit_id: str,
    current_user: User = Depends(get_super_admin),
    db: Session = Depends(get_db),
):
    business_unit = db.query(BusinessUnit).filter(BusinessUnit.id == business_unit_id).first()
    if not business_unit or business_unit.status == "deleted":
        raise HTTPException(status_code=404, detail="Business unit não encontrada")

    if current_user.business_unit_id == business_unit.id:
        raise HTTPException(
            status_code=400,
            detail="Não é permitido excluir a unidade de negócio atualmente selecionada pelo usuário.",
        )

    business_unit.status = "deleted"
    business_unit.updated_at = datetime.utcnow()
    db.query(User).filter(User.business_unit_id == business_unit_id).update(
        {User.business_unit_id: None, User.department_id: None},
        synchronize_session=False,
    )
    db.query(UserBusinessUnitAccess).filter(
        UserBusinessUnitAccess.business_unit_id == business_unit_id
    ).delete(synchronize_session=False)
    db.query(UserPermission).filter(
        UserPermission.business_unit_id == business_unit_id
    ).delete(synchronize_session=False)
    db.commit()
