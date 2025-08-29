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
            AccountGroup.code == group_data.code
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
            AccountGroup.tenant_id == current_user.tenant_id
        ).first()
        
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grupo não encontrado"
            )
        
        # Verificar se código já existe no tenant
        existing_subgroup = db.query(AccountSubgroup).filter(
            AccountSubgroup.tenant_id == current_user.tenant_id,
            AccountSubgroup.code == subgroup_data.code
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
            AccountSubgroup.tenant_id == current_user.tenant_id
        ).first()
        
        if not subgroup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subgrupo não encontrado"
            )
        
        # Verificar se código já existe no tenant
        existing_account = db.query(Account).filter(
            Account.tenant_id == current_user.tenant_id,
            Account.code == account_data.code
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
