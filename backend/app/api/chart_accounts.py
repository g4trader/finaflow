from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.auth import User
from app.models.chart_of_accounts import (
    ChartAccount,
    ChartAccountGroup,
    ChartAccountSubgroup,
)
from app.services.dependencies import get_current_active_user

router = APIRouter(tags=["chart-accounts"])


def _tenant_id(user: User) -> str:
    tenant_id = getattr(user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Usuário não possui tenant associado.")
    return str(tenant_id)


def _tenant_filter(tenant_id: str):
    """Return a SQLAlchemy filter to include tenant-specific and shared records."""
    return (ChartAccountGroup.tenant_id == tenant_id) | (ChartAccountGroup.tenant_id.is_(None))


@router.get("/api/v1/chart-accounts/groups")
def list_chart_account_groups(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[Dict[str, object]]:
    tenant_id = _tenant_id(current_user)

    groups = (
        db.query(ChartAccountGroup)
        .filter(ChartAccountGroup.is_active.is_(True))
        .filter((ChartAccountGroup.tenant_id == tenant_id) | (ChartAccountGroup.tenant_id.is_(None)))
        .order_by(ChartAccountGroup.code)
        .all()
    )

    return [
        {
            "id": group.id,
            "code": group.code,
            "name": group.name,
            "description": group.description,
            "tenant_id": group.tenant_id,
            "is_active": group.is_active,
            "created_at": group.created_at.isoformat() if group.created_at else None,
            "updated_at": group.updated_at.isoformat() if group.updated_at else None,
        }
        for group in groups
    ]


@router.get("/api/v1/chart-accounts/subgroups")
def list_chart_account_subgroups(
    group_id: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[Dict[str, object]]:
    tenant_id = _tenant_id(current_user)

    query = (
        db.query(ChartAccountSubgroup)
        .options(joinedload(ChartAccountSubgroup.group))
        .filter(ChartAccountSubgroup.is_active.is_(True))
        .filter((ChartAccountSubgroup.tenant_id == tenant_id) | (ChartAccountSubgroup.tenant_id.is_(None)))
    )

    if group_id:
        query = query.filter(ChartAccountSubgroup.group_id == group_id)

    subgroups = query.order_by(ChartAccountSubgroup.code).all()

    return [
        {
            "id": subgroup.id,
            "code": subgroup.code,
            "name": subgroup.name,
            "description": subgroup.description,
            "group_id": subgroup.group_id,
            "group_name": subgroup.group.name if subgroup.group else None,
            "tenant_id": subgroup.tenant_id,
            "is_active": subgroup.is_active,
            "created_at": subgroup.created_at.isoformat() if subgroup.created_at else None,
            "updated_at": subgroup.updated_at.isoformat() if subgroup.updated_at else None,
        }
        for subgroup in subgroups
    ]


@router.get("/api/v1/chart-accounts/accounts")
def list_chart_accounts(
    group_id: Optional[str] = Query(default=None),
    subgroup_id: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[Dict[str, object]]:
    tenant_id = _tenant_id(current_user)

    query = (
        db.query(ChartAccount)
        .options(joinedload(ChartAccount.subgroup).joinedload(ChartAccountSubgroup.group))
        .filter(ChartAccount.is_active.is_(True))
        .filter((ChartAccount.tenant_id == tenant_id) | (ChartAccount.tenant_id.is_(None)))
    )

    if subgroup_id:
        query = query.filter(ChartAccount.subgroup_id == subgroup_id)
    if group_id:
        query = query.join(ChartAccountSubgroup).filter(ChartAccountSubgroup.group_id == group_id)

    accounts = query.order_by(ChartAccount.code).all()

    return [
        {
            "id": account.id,
            "code": account.code,
            "name": account.name,
            "description": account.description,
            "subgroup_id": account.subgroup_id,
            "subgroup_name": account.subgroup.name if account.subgroup else None,
            "group_id": account.subgroup.group_id if account.subgroup else None,
            "group_name": account.subgroup.group.name if account.subgroup and account.subgroup.group else None,
            "account_type": account.account_type,
            "tenant_id": account.tenant_id,
            "is_active": account.is_active,
            "created_at": account.created_at.isoformat() if account.created_at else None,
            "updated_at": account.updated_at.isoformat() if account.updated_at else None,
        }
        for account in accounts
    ]


@router.get("/api/v1/chart-accounts/hierarchy")
def get_chart_accounts_hierarchy(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, List[Dict[str, object]]]:
    tenant_id = _tenant_id(current_user)

    groups = (
        db.query(ChartAccountGroup)
        .filter(ChartAccountGroup.is_active.is_(True))
        .filter((ChartAccountGroup.tenant_id == tenant_id) | (ChartAccountGroup.tenant_id.is_(None)))
        .order_by(ChartAccountGroup.code)
        .all()
    )

    subgroups = (
        db.query(ChartAccountSubgroup)
        .options(joinedload(ChartAccountSubgroup.group))
        .filter(ChartAccountSubgroup.is_active.is_(True))
        .filter((ChartAccountSubgroup.tenant_id == tenant_id) | (ChartAccountSubgroup.tenant_id.is_(None)))
        .order_by(ChartAccountSubgroup.code)
        .all()
    )

    accounts = (
        db.query(ChartAccount)
        .options(joinedload(ChartAccount.subgroup).joinedload(ChartAccountSubgroup.group))
        .filter(ChartAccount.is_active.is_(True))
        .filter((ChartAccount.tenant_id == tenant_id) | (ChartAccount.tenant_id.is_(None)))
        .order_by(ChartAccount.code)
        .all()
    )

    # Ordenar e estruturar hierarquia: grupo → subgrupo → conta
    # Filtrar subgrupos e contas para garantir que todos estejam incluídos
    from collections import defaultdict
    subgroup_by_group = defaultdict(list)
    account_by_subgroup = defaultdict(list)
    
    # Organizar subgrupos por grupo
    for subgroup in subgroups:
        if subgroup.group_id:
            subgroup_by_group[str(subgroup.group_id)].append(subgroup)
    
    # Organizar contas por subgrupo
    for account in accounts:
        if account.subgroup_id:
            account_by_subgroup[str(account.subgroup_id)].append(account)
    
    # Garantir que todos os grupos tenham seus subgrupos e contas
    groups_list = []
    subgroups_list = []
    accounts_list = []
    
    for group in sorted(groups, key=lambda g: g.code or ""):
        groups_list.append({
            "id": str(group.id),
            "code": group.code,
            "name": group.name,
            "description": group.description,
            "tenant_id": str(group.tenant_id) if group.tenant_id else None,
            "is_active": group.is_active,
            "created_at": group.created_at.isoformat() if group.created_at else None,
            "updated_at": group.updated_at.isoformat() if group.updated_at else None,
        })
        
        # Adicionar subgrupos deste grupo
        for subgroup in sorted(subgroup_by_group.get(str(group.id), []), key=lambda s: s.code or ""):
            subgroups_list.append({
                "id": str(subgroup.id),
                "code": subgroup.code,
                "name": subgroup.name,
                "description": subgroup.description,
                "group_id": str(subgroup.group_id) if subgroup.group_id else None,
                "group_name": subgroup.group.name if subgroup.group else None,
                "tenant_id": str(subgroup.tenant_id) if subgroup.tenant_id else None,
                "is_active": subgroup.is_active,
                "created_at": subgroup.created_at.isoformat() if subgroup.created_at else None,
                "updated_at": subgroup.updated_at.isoformat() if subgroup.updated_at else None,
            })
            
            # Adicionar contas deste subgrupo
            for account in sorted(account_by_subgroup.get(str(subgroup.id), []), key=lambda a: a.code or ""):
                accounts_list.append({
                    "id": str(account.id),
                    "code": account.code,
                    "name": account.name,
                    "description": account.description,
                    "subgroup_id": str(account.subgroup_id) if account.subgroup_id else None,
                    "subgroup_name": account.subgroup.name if account.subgroup else None,
                    "group_id": str(account.subgroup.group_id) if account.subgroup and account.subgroup.group else None,
                    "group_name": account.subgroup.group.name if account.subgroup and account.subgroup.group else None,
                    "account_type": account.account_type,
                    "tenant_id": str(account.tenant_id) if account.tenant_id else None,
                    "is_active": account.is_active,
                    "created_at": account.created_at.isoformat() if account.created_at else None,
                    "updated_at": account.updated_at.isoformat() if account.updated_at else None,
                })
    
    # Incluir subgrupos e contas órfãos (sem grupo/subgrupo pai)
    for subgroup in subgroups:
        if str(subgroup.id) not in [s["id"] for s in subgroups_list]:
            subgroups_list.append({
                "id": str(subgroup.id),
                "code": subgroup.code,
                "name": subgroup.name,
                "description": subgroup.description,
                "group_id": str(subgroup.group_id) if subgroup.group_id else None,
                "group_name": subgroup.group.name if subgroup.group else None,
                "tenant_id": str(subgroup.tenant_id) if subgroup.tenant_id else None,
                "is_active": subgroup.is_active,
                "created_at": subgroup.created_at.isoformat() if subgroup.created_at else None,
                "updated_at": subgroup.updated_at.isoformat() if subgroup.updated_at else None,
            })
    
    for account in accounts:
        if str(account.id) not in [a["id"] for a in accounts_list]:
            accounts_list.append({
                "id": str(account.id),
                "code": account.code,
                "name": account.name,
                "description": account.description,
                "subgroup_id": str(account.subgroup_id) if account.subgroup_id else None,
                "subgroup_name": account.subgroup.name if account.subgroup else None,
                "group_id": str(account.subgroup.group_id) if account.subgroup and account.subgroup.group else None,
                "group_name": account.subgroup.group.name if account.subgroup and account.subgroup.group else None,
                "account_type": account.account_type,
                "tenant_id": str(account.tenant_id) if account.tenant_id else None,
                "is_active": account.is_active,
                "created_at": account.created_at.isoformat() if account.created_at else None,
                "updated_at": account.updated_at.isoformat() if account.updated_at else None,
            })
    
    return {
        "groups": groups_list,
        "subgroups": subgroups_list,
        "accounts": accounts_list,
    }
