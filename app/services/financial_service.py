from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from decimal import Decimal
from app.models.financial_transactions import (
    FinancialTransaction, 
    TransactionType, 
    TransactionStatus,
    TransactionCategory
)
from app.models.chart_of_accounts import ChartAccount, ChartAccountSubgroup, ChartAccountGroup

class FinancialService:
    """Serviço para gerenciar transações financeiras"""
    
    @staticmethod
    def create_transaction(
        db: Session,
        data: dict,
        tenant_id: str,
        business_unit_id: str,
        created_by: str
    ) -> FinancialTransaction:
        """Cria uma nova transação financeira"""
        
        # Validar se a conta contábil existe e está ativa
        chart_account = db.query(ChartAccount).filter(
            ChartAccount.id == data['chart_account_id'],
            ChartAccount.is_active == True
        ).first()
        
        if not chart_account:
            raise ValueError("Conta contábil não encontrada ou inativa")
        
        # Gerar referência única se não fornecida
        if not data.get('reference'):
            data['reference'] = FinancialService._generate_reference(db, tenant_id, business_unit_id)
        
        # Criar transação
        transaction = FinancialTransaction(
            reference=data['reference'],
            description=data['description'],
            amount=Decimal(str(data['amount'])),
            transaction_date=datetime.fromisoformat(data['transaction_date']),
            transaction_type=data['transaction_type'],
            chart_account_id=data['chart_account_id'],
            notes=data.get('notes'),
            tenant_id=tenant_id,
            business_unit_id=business_unit_id,
            created_by=created_by
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        return transaction
    
    @staticmethod
    def _generate_reference(db: Session, tenant_id: str, business_unit_id: str) -> str:
        """Gera uma referência única para a transação"""
        # Formato: TX-YYYYMMDD-XXXX (onde XXXX é um número sequencial)
        today = datetime.now().strftime("%Y%m%d")
        
        # Buscar última transação do dia
        last_transaction = db.query(FinancialTransaction).filter(
            FinancialTransaction.tenant_id == tenant_id,
            FinancialTransaction.business_unit_id == business_unit_id,
            func.date(FinancialTransaction.created_at) == func.date(func.now())
        ).order_by(FinancialTransaction.created_at.desc()).first()
        
        if last_transaction and last_transaction.reference:
            # Extrair número sequencial
            try:
                last_number = int(last_transaction.reference.split('-')[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1
        
        return f"TX-{today}-{new_number:04d}"
    
    @staticmethod
    def get_transactions(
        db: Session,
        tenant_id: str,
        business_unit_id: str,
        filters: Optional[Dict] = None,
        page: int = 1,
        limit: int = 50
    ) -> Tuple[List[FinancialTransaction], int]:
        """Busca transações com filtros e paginação"""
        
        query = db.query(FinancialTransaction).filter(
            FinancialTransaction.tenant_id == tenant_id,
            FinancialTransaction.business_unit_id == business_unit_id,
            FinancialTransaction.is_active == True
        )
        
        # Aplicar filtros
        if filters:
            if filters.get('transaction_type'):
                query = query.filter(FinancialTransaction.transaction_type == filters['transaction_type'])
            
            if filters.get('status'):
                query = query.filter(FinancialTransaction.status == filters['status'])
            
            if filters.get('chart_account_id'):
                query = query.filter(FinancialTransaction.chart_account_id == filters['chart_account_id'])
            
            if filters.get('start_date'):
                start_date = datetime.fromisoformat(filters['start_date'])
                query = query.filter(FinancialTransaction.transaction_date >= start_date)
            
            if filters.get('end_date'):
                end_date = datetime.fromisoformat(filters['end_date'])
                query = query.filter(FinancialTransaction.transaction_date <= end_date)
            
            if filters.get('amount_min'):
                amount_min = Decimal(str(filters['amount_min']))
                query = query.filter(FinancialTransaction.amount >= amount_min)
            
            if filters.get('amount_max'):
                amount_max = Decimal(str(filters['amount_max']))
                query = query.filter(FinancialTransaction.amount <= amount_max)
            
            if filters.get('search'):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        FinancialTransaction.description.ilike(search_term),
                        FinancialTransaction.reference.ilike(search_term)
                    )
                )
        
        # Contar total
        total = query.count()
        
        # Aplicar paginação
        query = query.order_by(FinancialTransaction.transaction_date.desc())
        query = query.offset((page - 1) * limit).limit(limit)
        
        transactions = query.all()
        
        return transactions, total
    
    @staticmethod
    def get_transaction_by_id(
        db: Session,
        transaction_id: str,
        tenant_id: str,
        business_unit_id: str
    ) -> Optional[FinancialTransaction]:
        """Busca uma transação específica por ID"""
        return db.query(FinancialTransaction).filter(
            FinancialTransaction.id == transaction_id,
            FinancialTransaction.tenant_id == tenant_id,
            FinancialTransaction.business_unit_id == business_unit_id,
            FinancialTransaction.is_active == True
        ).first()
    
    @staticmethod
    def update_transaction(
        db: Session,
        transaction_id: str,
        data: dict,
        tenant_id: str,
        business_unit_id: str
    ) -> Optional[FinancialTransaction]:
        """Atualiza uma transação existente"""
        
        transaction = FinancialService.get_transaction_by_id(
            db, transaction_id, tenant_id, business_unit_id
        )
        
        if not transaction:
            return None
        
        # Atualizar campos
        for field, value in data.items():
            if hasattr(transaction, field) and value is not None:
                if field == 'amount':
                    setattr(transaction, field, Decimal(str(value)))
                elif field == 'transaction_date':
                    setattr(transaction, field, datetime.fromisoformat(value))
                else:
                    setattr(transaction, field, value)
        
        transaction.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(transaction)
        
        return transaction
    
    @staticmethod
    def delete_transaction(
        db: Session,
        transaction_id: str,
        tenant_id: str,
        business_unit_id: str
    ) -> bool:
        """Remove uma transação (soft delete)"""
        
        transaction = FinancialService.get_transaction_by_id(
            db, transaction_id, tenant_id, business_unit_id
        )
        
        if not transaction:
            return False
        
        transaction.is_active = False
        transaction.updated_at = datetime.utcnow()
        db.commit()
        
        return True
    
    @staticmethod
    def approve_transaction(
        db: Session,
        transaction_id: str,
        tenant_id: str,
        business_unit_id: str,
        approved_by: str
    ) -> Optional[FinancialTransaction]:
        """Aprova uma transação"""
        
        transaction = FinancialService.get_transaction_by_id(
            db, transaction_id, tenant_id, business_unit_id
        )
        
        if not transaction:
            return None
        
        if transaction.status != TransactionStatus.PENDENTE:
            raise ValueError("Apenas transações pendentes podem ser aprovadas")
        
        transaction.status = TransactionStatus.APROVADA
        transaction.approved_by = approved_by
        transaction.approved_at = datetime.utcnow()
        transaction.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(transaction)
        
        return transaction
    
    @staticmethod
    def reject_transaction(
        db: Session,
        transaction_id: str,
        tenant_id: str,
        business_unit_id: str,
        rejected_by: str
    ) -> Optional[FinancialTransaction]:
        """Rejeita uma transação"""
        
        transaction = FinancialService.get_transaction_by_id(
            db, transaction_id, tenant_id, business_unit_id
        )
        
        if not transaction:
            return None
        
        if transaction.status != TransactionStatus.PENDENTE:
            raise ValueError("Apenas transações pendentes podem ser rejeitadas")
        
        transaction.status = TransactionStatus.REJEITADA
        transaction.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(transaction)
        
        return transaction
    
    @staticmethod
    def get_financial_summary(
        db: Session,
        tenant_id: str,
        business_unit_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """Obtém resumo financeiro com receitas, despesas e saldo"""
        
        query = db.query(FinancialTransaction).filter(
            FinancialTransaction.tenant_id == tenant_id,
            FinancialTransaction.business_unit_id == business_unit_id,
            FinancialTransaction.is_active == True,
            FinancialTransaction.status == TransactionStatus.APROVADA
        )
        
        if start_date:
            query = query.filter(FinancialTransaction.transaction_date >= start_date)
        
        if end_date:
            query = query.filter(FinancialTransaction.transaction_date <= end_date)
        
        # Calcular receitas
        receitas = query.filter(
            FinancialTransaction.transaction_type == TransactionType.RECEITA
        ).with_entities(func.sum(FinancialTransaction.amount)).scalar() or Decimal('0')
        
        # Calcular despesas
        despesas = query.filter(
            FinancialTransaction.transaction_type == TransactionType.DESPESA
        ).with_entities(func.sum(FinancialTransaction.amount)).scalar() or Decimal('0')
        
        # Calcular saldo
        saldo = receitas - despesas
        
        # Contar transações por status
        status_counts = db.query(
            FinancialTransaction.status,
            func.count(FinancialTransaction.id)
        ).filter(
            FinancialTransaction.tenant_id == tenant_id,
            FinancialTransaction.business_unit_id == business_unit_id,
            FinancialTransaction.is_active == True
        ).group_by(FinancialTransaction.status).all()
        
        status_summary = {status: count for status, count in status_counts}
        
        return {
            "receitas": float(receitas),
            "despesas": float(despesas),
            "saldo": float(saldo),
            "total_transacoes": sum(status_summary.values()),
            "status_summary": status_summary,
            "periodo": {
                "inicio": start_date.isoformat() if start_date else None,
                "fim": end_date.isoformat() if end_date else None
            }
        }
    
    @staticmethod
    def get_chart_account_summary(
        db: Session,
        tenant_id: str,
        business_unit_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Obtém resumo por conta contábil"""
        
        query = db.query(
            ChartAccount.id,
            ChartAccount.name,
            ChartAccount.code,
            ChartAccount.account_type,
            func.sum(FinancialTransaction.amount).label('total_amount'),
            func.count(FinancialTransaction.id).label('transaction_count')
        ).join(
            FinancialTransaction,
            FinancialTransaction.chart_account_id == ChartAccount.id
        ).filter(
            FinancialTransaction.tenant_id == tenant_id,
            FinancialTransaction.business_unit_id == business_unit_id,
            FinancialTransaction.is_active == True,
            FinancialTransaction.status == TransactionStatus.APROVADA,
            ChartAccount.is_active == True
        )
        
        if start_date:
            query = query.filter(FinancialTransaction.transaction_date >= start_date)
        
        if end_date:
            query = query.filter(FinancialTransaction.transaction_date <= end_date)
        
        results = query.group_by(
            ChartAccount.id,
            ChartAccount.name,
            ChartAccount.code,
            ChartAccount.account_type
        ).all()
        
        return [
            {
                "account_id": result.id,
                "account_name": result.name,
                "account_code": result.code,
                "account_type": result.account_type,
                "total_amount": float(result.total_amount or 0),
                "transaction_count": result.transaction_count
            }
            for result in results
        ]
