from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.database import get_db
from app.models.auth import User, UserRole
from app.models.financial import (
    AccountGroup, AccountSubgroup, Account, Transaction, CashFlow, BankAccount,
    AccountGroupCreate, AccountGroupUpdate, AccountGroupResponse,
    AccountSubgroupCreate, AccountSubgroupUpdate, AccountSubgroupResponse,
    AccountCreate, AccountUpdate, AccountResponse,
    TransactionCreate, TransactionUpdate, TransactionResponse,
    CashFlowResponse, BankAccountCreate, BankAccountUpdate, BankAccountResponse
)
from app.services.dependencies import get_current_active_user, get_tenant_admin, log_audit_event
from app.services.security import SecurityService

router = APIRouter(prefix="/financial", tags=["financial"])


def _serialize_forecast(transaction: Transaction) -> dict:
    return {
        "id": transaction.id,
        "tenant_id": transaction.tenant_id,
        "account_id": transaction.account_id,
        "business_unit_id": transaction.business_unit_id,
        "department_id": transaction.department_id,
        "transaction_date": transaction.transaction_date,
        "amount": float(transaction.amount),
        "description": transaction.description,
        "transaction_type": transaction.transaction_type,
        "created_at": transaction.created_at,
        "updated_at": transaction.updated_at,
    }


@router.get("/forecasts")
async def list_forecasts(
    account_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Listar previsões financeiras armazenadas no Postgres."""
    query = db.query(Transaction).filter(
        Transaction.tenant_id == current_user.tenant_id,
        Transaction.is_forecast == True,
    )
    if account_id:
        query = query.filter(Transaction.account_id == account_id)

    return [_serialize_forecast(item) for item in query.order_by(Transaction.transaction_date.desc()).all()]


@router.post("/forecasts", status_code=status.HTTP_201_CREATED)
async def create_forecast(
    forecast_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Criar previsão financeira no mesmo storage das transações."""
    account_id = forecast_data.get("account_id")
    if not account_id:
        raise HTTPException(status_code=422, detail="account_id é obrigatório")

    account = db.query(Account).filter(
        Account.id == account_id,
        Account.tenant_id == current_user.tenant_id,
        Account.status == "active",
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Conta não encontrada")

    amount = float(forecast_data.get("amount") or 0)
    if amount <= 0:
        raise HTTPException(status_code=422, detail="amount deve ser maior que zero")

    transaction_date = forecast_data.get("transaction_date")
    if isinstance(transaction_date, str):
        transaction_date = datetime.fromisoformat(transaction_date.replace("Z", "+00:00"))
    if not transaction_date:
        transaction_date = datetime.utcnow()

    transaction = Transaction(
        tenant_id=current_user.tenant_id,
        account_id=account_id,
        business_unit_id=forecast_data.get("business_unit_id") or current_user.business_unit_id,
        department_id=forecast_data.get("department_id"),
        transaction_date=transaction_date,
        description=forecast_data.get("description") or "Previsão",
        amount=amount,
        transaction_type=forecast_data.get("transaction_type")
        or ("credit" if account.account_type == "revenue" else "debit"),
        category=forecast_data.get("category") or "forecast",
        is_recurring=bool(forecast_data.get("is_recurring", False)),
        is_forecast=True,
        is_approved=False,
        created_by=current_user.id,
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return _serialize_forecast(transaction)


@router.put("/forecasts/{forecast_id}")
async def update_forecast(
    forecast_id: str,
    forecast_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    transaction = db.query(Transaction).filter(
        Transaction.id == forecast_id,
        Transaction.tenant_id == current_user.tenant_id,
        Transaction.is_forecast == True,
    ).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Previsão não encontrada")

    if forecast_data.get("account_id") and forecast_data["account_id"] != transaction.account_id:
        account = db.query(Account).filter(
            Account.id == forecast_data["account_id"],
            Account.tenant_id == current_user.tenant_id,
            Account.status == "active",
        ).first()
        if not account:
            raise HTTPException(status_code=404, detail="Conta não encontrada")
        transaction.account_id = forecast_data["account_id"]

    if "amount" in forecast_data:
        amount = float(forecast_data.get("amount") or 0)
        if amount <= 0:
            raise HTTPException(status_code=422, detail="amount deve ser maior que zero")
        transaction.amount = amount
    if "description" in forecast_data:
        transaction.description = forecast_data.get("description") or "Previsão"
    if "business_unit_id" in forecast_data:
        transaction.business_unit_id = forecast_data.get("business_unit_id")
    if "department_id" in forecast_data:
        transaction.department_id = forecast_data.get("department_id")
    if "transaction_type" in forecast_data:
        transaction.transaction_type = forecast_data["transaction_type"]
    if "transaction_date" in forecast_data and forecast_data["transaction_date"]:
        transaction_date = forecast_data["transaction_date"]
        if isinstance(transaction_date, str):
            transaction_date = datetime.fromisoformat(transaction_date.replace("Z", "+00:00"))
        transaction.transaction_date = transaction_date

    db.commit()
    db.refresh(transaction)
    return _serialize_forecast(transaction)


@router.delete("/forecasts/{forecast_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_forecast(
    forecast_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    transaction = db.query(Transaction).filter(
        Transaction.id == forecast_id,
        Transaction.tenant_id == current_user.tenant_id,
        Transaction.is_forecast == True,
    ).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Previsão não encontrada")

    db.delete(transaction)
    db.commit()
    return None

# Account Groups
@router.post("/account-groups", response_model=AccountGroupResponse)
async def create_account_group(
    group_data: AccountGroupCreate,
    current_user: User = Depends(get_tenant_admin),
    db: Session = Depends(get_db)
):
    """Criar grupo de contas."""
    try:
        # Verificar se código já existe no tenant
        existing_group = db.query(AccountGroup).filter(
            AccountGroup.tenant_id == current_user.tenant_id,
            AccountGroup.code == group_data.code,
            AccountGroup.status != "deleted",
        ).first()
        
        if existing_group:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código já existe no tenant"
            )
        
        group = AccountGroup(
            tenant_id=current_user.tenant_id,
            name=group_data.name,
            code=group_data.code,
            description=group_data.description
        )
        db.add(group)
        db.commit()
        db.refresh(group)
        
        # Log de auditoria
        SecurityService.log_audit_event(
            db=db,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            action="ACCOUNT_GROUP_CREATED",
            resource_type="ACCOUNT_GROUP",
            resource_id=str(group.id),
            details=f"Grupo criado: {group.name}"
        )
        
        return group
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.get("/account-groups", response_model=List[AccountGroupResponse])
async def list_account_groups(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Listar grupos de contas do tenant."""
    try:
        groups = db.query(AccountGroup).filter(
            AccountGroup.tenant_id == current_user.tenant_id,
            AccountGroup.status == "active"
        ).all()
        return groups
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.put("/account-groups/{group_id}", response_model=AccountGroupResponse)
async def update_account_group(
    group_id: str,
    group_data: AccountGroupUpdate,
    current_user: User = Depends(get_tenant_admin),
    db: Session = Depends(get_db),
):
    group = db.query(AccountGroup).filter(
        AccountGroup.id == group_id,
        AccountGroup.tenant_id == current_user.tenant_id,
    ).first()
    if not group or group.status == "deleted":
        raise HTTPException(status_code=404, detail="Grupo não encontrado")

    if group_data.code and group_data.code != group.code:
        existing_group = db.query(AccountGroup).filter(
            AccountGroup.tenant_id == current_user.tenant_id,
            AccountGroup.code == group_data.code,
            AccountGroup.id != group_id,
            AccountGroup.status != "deleted",
        ).first()
        if existing_group:
            raise HTTPException(status_code=400, detail="Código já existe no tenant")
        group.code = group_data.code
    if group_data.name is not None:
        group.name = group_data.name
    if group_data.description is not None:
        group.description = group_data.description
    if group_data.status is not None:
        group.status = group_data.status

    db.commit()
    db.refresh(group)
    return group

@router.delete("/account-groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account_group(
    group_id: str,
    current_user: User = Depends(get_tenant_admin),
    db: Session = Depends(get_db),
):
    group = db.query(AccountGroup).filter(
        AccountGroup.id == group_id,
        AccountGroup.tenant_id == current_user.tenant_id,
    ).first()
    if not group or group.status == "deleted":
        raise HTTPException(status_code=404, detail="Grupo não encontrado")

    subgroup_ids = [
        row[0]
        for row in db.query(AccountSubgroup.id).filter(
            AccountSubgroup.group_id == group_id,
            AccountSubgroup.tenant_id == current_user.tenant_id,
        ).all()
    ]
    if subgroup_ids:
        db.query(Account).filter(
            Account.subgroup_id.in_(subgroup_ids),
            Account.tenant_id == current_user.tenant_id,
        ).update({Account.status: "deleted"}, synchronize_session=False)
        db.query(AccountSubgroup).filter(
            AccountSubgroup.id.in_(subgroup_ids),
            AccountSubgroup.tenant_id == current_user.tenant_id,
        ).update({AccountSubgroup.status: "deleted"}, synchronize_session=False)
    group.status = "deleted"
    db.commit()
    return None

# Account Subgroups
@router.post("/account-subgroups", response_model=AccountSubgroupResponse)
async def create_account_subgroup(
    subgroup_data: AccountSubgroupCreate,
    current_user: User = Depends(get_tenant_admin),
    db: Session = Depends(get_db)
):
    """Criar subgrupo de contas."""
    try:
        # Verificar se grupo existe
        group = db.query(AccountGroup).filter(
            AccountGroup.id == subgroup_data.group_id,
            AccountGroup.tenant_id == current_user.tenant_id,
            AccountGroup.status == "active",
        ).first()
        
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grupo não encontrado"
            )
        
        # Verificar se código já existe no tenant
        existing_subgroup = db.query(AccountSubgroup).filter(
            AccountSubgroup.tenant_id == current_user.tenant_id,
            AccountSubgroup.code == subgroup_data.code,
            AccountSubgroup.status != "deleted",
        ).first()
        
        if existing_subgroup:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código já existe no tenant"
            )
        
        subgroup = AccountSubgroup(
            tenant_id=current_user.tenant_id,
            group_id=subgroup_data.group_id,
            name=subgroup_data.name,
            code=subgroup_data.code,
            description=subgroup_data.description
        )
        db.add(subgroup)
        db.commit()
        db.refresh(subgroup)
        
        # Log de auditoria
        SecurityService.log_audit_event(
            db=db,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            action="ACCOUNT_SUBGROUP_CREATED",
            resource_type="ACCOUNT_SUBGROUP",
            resource_id=str(subgroup.id),
            details=f"Subgrupo criado: {subgroup.name}"
        )
        
        return subgroup
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.get("/account-subgroups", response_model=List[AccountSubgroupResponse])
async def list_account_subgroups(
    group_id: Optional[str] = Query(None, description="ID do grupo para filtrar"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Listar subgrupos de contas do tenant."""
    try:
        query = db.query(AccountSubgroup).filter(
            AccountSubgroup.tenant_id == current_user.tenant_id,
            AccountSubgroup.status == "active"
        )
        
        if group_id:
            query = query.filter(AccountSubgroup.group_id == group_id)
        
        subgroups = query.all()
        return subgroups
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.put("/account-subgroups/{subgroup_id}", response_model=AccountSubgroupResponse)
async def update_account_subgroup(
    subgroup_id: str,
    subgroup_data: AccountSubgroupUpdate,
    current_user: User = Depends(get_tenant_admin),
    db: Session = Depends(get_db),
):
    subgroup = db.query(AccountSubgroup).filter(
        AccountSubgroup.id == subgroup_id,
        AccountSubgroup.tenant_id == current_user.tenant_id,
    ).first()
    if not subgroup or subgroup.status == "deleted":
        raise HTTPException(status_code=404, detail="Subgrupo não encontrado")

    if subgroup_data.group_id is not None:
        group = db.query(AccountGroup).filter(
            AccountGroup.id == subgroup_data.group_id,
            AccountGroup.tenant_id == current_user.tenant_id,
            AccountGroup.status == "active",
        ).first()
        if not group:
            raise HTTPException(status_code=404, detail="Grupo não encontrado")
        subgroup.group_id = subgroup_data.group_id
    if subgroup_data.code and subgroup_data.code != subgroup.code:
        existing_subgroup = db.query(AccountSubgroup).filter(
            AccountSubgroup.tenant_id == current_user.tenant_id,
            AccountSubgroup.code == subgroup_data.code,
            AccountSubgroup.id != subgroup_id,
            AccountSubgroup.status != "deleted",
        ).first()
        if existing_subgroup:
            raise HTTPException(status_code=400, detail="Código já existe no tenant")
        subgroup.code = subgroup_data.code
    if subgroup_data.name is not None:
        subgroup.name = subgroup_data.name
    if subgroup_data.description is not None:
        subgroup.description = subgroup_data.description
    if subgroup_data.status is not None:
        subgroup.status = subgroup_data.status

    db.commit()
    db.refresh(subgroup)
    return subgroup

@router.delete("/account-subgroups/{subgroup_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account_subgroup(
    subgroup_id: str,
    current_user: User = Depends(get_tenant_admin),
    db: Session = Depends(get_db),
):
    subgroup = db.query(AccountSubgroup).filter(
        AccountSubgroup.id == subgroup_id,
        AccountSubgroup.tenant_id == current_user.tenant_id,
    ).first()
    if not subgroup or subgroup.status == "deleted":
        raise HTTPException(status_code=404, detail="Subgrupo não encontrado")

    db.query(Account).filter(
        Account.subgroup_id == subgroup_id,
        Account.tenant_id == current_user.tenant_id,
    ).update({Account.status: "deleted"}, synchronize_session=False)
    subgroup.status = "deleted"
    db.commit()
    return None

# Accounts
@router.post("/accounts", response_model=AccountResponse)
async def create_account(
    account_data: AccountCreate,
    current_user: User = Depends(get_tenant_admin),
    db: Session = Depends(get_db)
):
    """Criar conta específica."""
    try:
        # Verificar se subgrupo existe
        subgroup = db.query(AccountSubgroup).filter(
            AccountSubgroup.id == account_data.subgroup_id,
            AccountSubgroup.tenant_id == current_user.tenant_id,
            AccountSubgroup.status == "active",
        ).first()
        
        if not subgroup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subgrupo não encontrado"
            )
        
        # Verificar se código já existe no tenant
        existing_account = db.query(Account).filter(
            Account.tenant_id == current_user.tenant_id,
            Account.code == account_data.code,
            Account.status != "deleted",
        ).first()
        
        if existing_account:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código já existe no tenant"
            )
        
        account = Account(
            tenant_id=current_user.tenant_id,
            subgroup_id=account_data.subgroup_id,
            name=account_data.name,
            code=account_data.code,
            description=account_data.description,
            account_type=account_data.account_type
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        
        # Log de auditoria
        SecurityService.log_audit_event(
            db=db,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            action="ACCOUNT_CREATED",
            resource_type="ACCOUNT",
            resource_id=str(account.id),
            details=f"Conta criada: {account.name}"
        )
        
        return account
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.get("/accounts", response_model=List[AccountResponse])
async def list_accounts(
    subgroup_id: Optional[str] = Query(None, description="ID do subgrupo para filtrar"),
    account_type: Optional[str] = Query(None, description="Tipo de conta para filtrar"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Listar contas do tenant."""
    try:
        query = db.query(Account).filter(
            Account.tenant_id == current_user.tenant_id,
            Account.status == "active"
        )
        
        if subgroup_id:
            query = query.filter(Account.subgroup_id == subgroup_id)
        
        if account_type:
            query = query.filter(Account.account_type == account_type)
        
        accounts = query.all()
        return accounts
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.put("/accounts/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: str,
    account_data: AccountUpdate,
    current_user: User = Depends(get_tenant_admin),
    db: Session = Depends(get_db),
):
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.tenant_id == current_user.tenant_id,
    ).first()
    if not account or account.status == "deleted":
        raise HTTPException(status_code=404, detail="Conta não encontrada")

    if account_data.subgroup_id is not None:
        subgroup = db.query(AccountSubgroup).filter(
            AccountSubgroup.id == account_data.subgroup_id,
            AccountSubgroup.tenant_id == current_user.tenant_id,
            AccountSubgroup.status == "active",
        ).first()
        if not subgroup:
            raise HTTPException(status_code=404, detail="Subgrupo não encontrado")
        account.subgroup_id = account_data.subgroup_id
    if account_data.code and account_data.code != account.code:
        existing_account = db.query(Account).filter(
            Account.tenant_id == current_user.tenant_id,
            Account.code == account_data.code,
            Account.id != account_id,
            Account.status != "deleted",
        ).first()
        if existing_account:
            raise HTTPException(status_code=400, detail="Código já existe no tenant")
        account.code = account_data.code
    if account_data.name is not None:
        account.name = account_data.name
    if account_data.description is not None:
        account.description = account_data.description
    if account_data.account_type is not None:
        account.account_type = account_data.account_type
    if account_data.status is not None:
        account.status = account_data.status

    db.commit()
    db.refresh(account)
    return account

@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: str,
    current_user: User = Depends(get_tenant_admin),
    db: Session = Depends(get_db),
):
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.tenant_id == current_user.tenant_id,
    ).first()
    if not account or account.status == "deleted":
        raise HTTPException(status_code=404, detail="Conta não encontrada")

    account.status = "deleted"
    db.commit()
    return None

# Transactions
@router.post("/transactions", response_model=TransactionResponse)
async def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Criar transação financeira."""
    try:
        # Verificar se conta existe
        account = db.query(Account).filter(
            Account.id == transaction_data.account_id,
            Account.tenant_id == current_user.tenant_id
        ).first()
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conta não encontrada"
            )
        
        # Verificar permissões de business unit
        if transaction_data.business_unit_id and current_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
            if current_user.business_unit_id != transaction_data.business_unit_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Sem permissão para esta business unit"
                )
        
        transaction = Transaction(
            tenant_id=current_user.tenant_id,
            account_id=transaction_data.account_id,
            business_unit_id=transaction_data.business_unit_id or current_user.business_unit_id,
            department_id=transaction_data.department_id or current_user.department_id,
            transaction_date=transaction_data.transaction_date,
            description=transaction_data.description,
            amount=transaction_data.amount,
            transaction_type=transaction_data.transaction_type,
            category=transaction_data.category,
            is_recurring=transaction_data.is_recurring,
            is_forecast=transaction_data.is_forecast,
            created_by=current_user.id
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        # Log de auditoria
        SecurityService.log_audit_event(
            db=db,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            action="TRANSACTION_CREATED",
            resource_type="TRANSACTION",
            resource_id=str(transaction.id),
            details=f"Transação criada: {transaction.description} - R$ {transaction.amount}"
        )
        
        return transaction
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.get("/transactions", response_model=List[TransactionResponse])
async def list_transactions(
    start_date: Optional[datetime] = Query(None, description="Data inicial"),
    end_date: Optional[datetime] = Query(None, description="Data final"),
    account_id: Optional[str] = Query(None, description="ID da conta"),
    transaction_type: Optional[str] = Query(None, description="Tipo de transação"),
    is_forecast: Optional[bool] = Query(None, description="Se é previsão"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Listar transações do tenant."""
    try:
        query = db.query(Transaction).filter(
            Transaction.tenant_id == current_user.tenant_id
        )
        
        # Filtrar por business unit se não for admin
        if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
            query = query.filter(Transaction.business_unit_id == current_user.business_unit_id)
        
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
        
        transactions = query.order_by(Transaction.transaction_date.desc()).all()
        return transactions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.put("/transactions/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: str,
    transaction_data: TransactionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.tenant_id == current_user.tenant_id,
    ).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
        if transaction.business_unit_id != current_user.business_unit_id:
            raise HTTPException(status_code=403, detail="Sem permissão para esta transação")

    if transaction_data.account_id is not None:
        account = db.query(Account).filter(
            Account.id == transaction_data.account_id,
            Account.tenant_id == current_user.tenant_id,
            Account.status == "active",
        ).first()
        if not account:
            raise HTTPException(status_code=404, detail="Conta não encontrada")
        transaction.account_id = transaction_data.account_id
    for field in [
        "business_unit_id",
        "department_id",
        "transaction_date",
        "description",
        "amount",
        "transaction_type",
        "category",
        "is_recurring",
        "is_forecast",
        "is_approved",
    ]:
        value = getattr(transaction_data, field)
        if value is not None:
            setattr(transaction, field, value)

    db.commit()
    db.refresh(transaction)
    return transaction

@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.tenant_id == current_user.tenant_id,
    ).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
        if transaction.business_unit_id != current_user.business_unit_id:
            raise HTTPException(status_code=403, detail="Sem permissão para esta transação")

    db.delete(transaction)
    db.commit()
    return None

# Cash Flow
@router.get("/cash-flow", response_model=List[CashFlowResponse])
async def get_cash_flow(
    start_date: datetime = Query(..., description="Data inicial"),
    end_date: datetime = Query(..., description="Data final"),
    period_type: str = Query("daily", description="Tipo de período (daily, monthly, yearly)"),
    business_unit_id: Optional[str] = Query(None, description="ID da business unit"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obter fluxo de caixa consolidado."""
    try:
        # Verificar permissões
        if business_unit_id and current_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
            if current_user.business_unit_id != business_unit_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Sem permissão para esta business unit"
                )
        
        # Buscar transações no período
        query = db.query(Transaction).filter(
            Transaction.tenant_id == current_user.tenant_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
            Transaction.is_forecast == False
        )
        
        if business_unit_id:
            query = query.filter(Transaction.business_unit_id == business_unit_id)
        elif current_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
            query = query.filter(Transaction.business_unit_id == current_user.business_unit_id)
        
        transactions = query.all()
        
        # Calcular fluxo de caixa
        cash_flows = []
        current_balance = 0.0
        
        # Agrupar por período
        if period_type == "daily":
            # Agrupar por dia
            from collections import defaultdict
            daily_data = defaultdict(lambda: {"revenue": 0, "expenses": 0, "costs": 0})
            
            for transaction in transactions:
                date_key = transaction.transaction_date.date()
                if transaction.transaction_type == "credit":
                    daily_data[date_key]["revenue"] += float(transaction.amount)
                else:
                    # Verificar tipo de conta
                    account = db.query(Account).filter(Account.id == transaction.account_id).first()
                    if account and account.account_type == "cost":
                        daily_data[date_key]["costs"] += float(transaction.amount)
                    else:
                        daily_data[date_key]["expenses"] += float(transaction.amount)
            
            # Criar registros de fluxo de caixa
            for date, data in sorted(daily_data.items()):
                opening_balance = current_balance
                net_flow = data["revenue"] - data["expenses"] - data["costs"]
                current_balance += net_flow
                
                cash_flow = CashFlow(
                    tenant_id=current_user.tenant_id,
                    business_unit_id=business_unit_id or current_user.business_unit_id,
                    date=datetime.combine(date, datetime.min.time()),
                    opening_balance=opening_balance,
                    total_revenue=data["revenue"],
                    total_expenses=data["expenses"],
                    total_costs=data["costs"],
                    net_flow=net_flow,
                    closing_balance=current_balance,
                    period_type="daily"
                )
                cash_flows.append(cash_flow)
        
        return cash_flows
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

# Bank Accounts
@router.post("/bank-accounts", response_model=BankAccountResponse)
async def create_bank_account(
    account_data: BankAccountCreate,
    current_user: User = Depends(get_tenant_admin),
    db: Session = Depends(get_db)
):
    """Criar conta bancária."""
    try:
        # Verificar se número de conta já existe no tenant
        existing_account = db.query(BankAccount).filter(
            BankAccount.tenant_id == current_user.tenant_id,
            BankAccount.account_number == account_data.account_number
        ).first()
        
        if existing_account:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Número de conta já existe no tenant"
            )
        
        bank_account = BankAccount(
            tenant_id=current_user.tenant_id,
            business_unit_id=account_data.business_unit_id,
            bank_name=account_data.bank_name,
            account_number=account_data.account_number,
            account_type=account_data.account_type,
            balance=account_data.balance,
            currency=account_data.currency
        )
        db.add(bank_account)
        db.commit()
        db.refresh(bank_account)
        
        # Log de auditoria
        SecurityService.log_audit_event(
            db=db,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            action="BANK_ACCOUNT_CREATED",
            resource_type="BANK_ACCOUNT",
            resource_id=str(bank_account.id),
            details=f"Conta bancária criada: {bank_account.bank_name} - {bank_account.account_number}"
        )
        
        return bank_account
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.get("/bank-accounts", response_model=List[BankAccountResponse])
async def list_bank_accounts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Listar contas bancárias do tenant."""
    try:
        query = db.query(BankAccount).filter(
            BankAccount.tenant_id == current_user.tenant_id,
            BankAccount.status == "active"
        )
        
        # Filtrar por business unit se não for admin
        if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
            query = query.filter(BankAccount.business_unit_id == current_user.business_unit_id)
        
        accounts = query.all()
        return accounts
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )
