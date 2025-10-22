"""Transaction endpoints backed by the relational database."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import User, UserRole
from app.models.financial import (
    Account,
    Transaction,
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)
from app.services.dependencies import get_current_active_user

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("/", response_model=List[TransactionResponse])
async def list_transactions(
    start_date: Optional[datetime] = Query(None, description="Data inicial para filtro"),
    end_date: Optional[datetime] = Query(None, description="Data final para filtro"),
    account_id: Optional[str] = Query(None, description="Filtrar por conta"),
    transaction_type: Optional[str] = Query(
        None, description="Filtrar por tipo (credit ou debit)"
    ),
    is_forecast: Optional[bool] = Query(
        None, description="Filtrar por lançamentos previstos"
    ),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[TransactionResponse]:
    """Listar transações armazenadas no banco relacional."""

    query = db.query(Transaction).filter(Transaction.tenant_id == current_user.tenant_id)

    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
        query = query.filter(
            Transaction.business_unit_id == current_user.business_unit_id
        )

    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    if is_forecast is not None:
        query = query.filter(Transaction.is_forecast == is_forecast)

    return query.order_by(Transaction.transaction_date.desc()).all()


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> TransactionResponse:
    """Criar uma nova transação no banco de dados PostgreSQL."""

    if transaction_data.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado para este tenant",
        )

    account = (
        db.query(Account)
        .filter(
            Account.id == transaction_data.account_id,
            Account.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conta não encontrada",
        )

    if (
        transaction_data.business_unit_id
        and current_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]
        and current_user.business_unit_id != transaction_data.business_unit_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para esta unidade de negócio",
        )

    transaction = Transaction(
        tenant_id=current_user.tenant_id,
        account_id=transaction_data.account_id,
        business_unit_id=
            transaction_data.business_unit_id or current_user.business_unit_id,
        department_id=transaction_data.department_id or current_user.department_id,
        transaction_date=transaction_data.transaction_date,
        description=transaction_data.description,
        amount=transaction_data.amount,
        transaction_type=transaction_data.transaction_type,
        category=transaction_data.category,
        is_recurring=transaction_data.is_recurring,
        is_forecast=transaction_data.is_forecast,
        created_by=current_user.id,
        is_approved=True,
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: str,
    transaction_data: TransactionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> TransactionResponse:
    """Atualizar os dados de uma transação existente."""

    transaction = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transação não encontrada",
        )

    updates = transaction_data.dict(exclude_unset=True)

    if "account_id" in updates:
        account = (
            db.query(Account)
            .filter(
                Account.id == updates["account_id"],
                Account.tenant_id == current_user.tenant_id,
            )
            .first()
        )
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conta não encontrada",
            )

    if "business_unit_id" in updates and updates["business_unit_id"] is not None:
        if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
            if current_user.business_unit_id != updates["business_unit_id"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Sem permissão para esta unidade de negócio",
                )

    for field, value in updates.items():
        setattr(transaction, field, value)

    transaction.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(transaction)

    return transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    """Remover uma transação pertencente ao tenant do usuário."""

    transaction = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transação não encontrada",
        )

    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
        if transaction.business_unit_id != current_user.business_unit_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para esta unidade de negócio",
            )

    db.delete(transaction)
    db.commit()
