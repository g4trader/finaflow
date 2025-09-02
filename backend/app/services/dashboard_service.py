from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, extract
from datetime import datetime, timedelta
from decimal import Decimal
from app.models.financial_transactions import FinancialTransaction, TransactionType, TransactionStatus
from app.models.chart_of_accounts import ChartAccount, ChartAccountSubgroup, ChartAccountGroup

class DashboardService:
    """Serviço para o dashboard financeiro integrado"""
    
    @staticmethod
    def get_dashboard_data(
        db: Session,
        tenant_id: str,
        business_unit_id: str,
        period: str = "month"  # day, week, month, quarter, year
    ) -> Dict:
        """Obtém dados completos do dashboard"""
        
        # Calcular período
        end_date = datetime.now()
        if period == "day":
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start_date = end_date - timedelta(days=7)
        elif period == "month":
            start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == "quarter":
            quarter = (end_date.month - 1) // 3
            start_date = end_date.replace(month=quarter * 3 + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == "year":
            start_date = end_date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start_date = end_date - timedelta(days=30)
        
        # Buscar dados financeiros
        financial_summary = DashboardService._get_financial_summary(
            db, tenant_id, business_unit_id, start_date, end_date
        )
        
        # Buscar dados do plano de contas
        chart_accounts_summary = DashboardService._get_chart_accounts_summary(
            db, tenant_id, business_unit_id, start_date, end_date
        )
        
        # Buscar dados de tendências
        trends = DashboardService._get_financial_trends(
            db, tenant_id, business_unit_id, start_date, end_date
        )
        
        # Buscar dados de status
        status_summary = DashboardService._get_status_summary(
            db, tenant_id, business_unit_id
        )
        
        # Buscar dados de performance
        performance = DashboardService._get_performance_metrics(
            db, tenant_id, business_unit_id, start_date, end_date
        )
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "type": period
            },
            "financial_summary": financial_summary,
            "chart_accounts_summary": chart_accounts_summary,
            "trends": trends,
            "status_summary": status_summary,
            "performance": performance
        }
    
    @staticmethod
    def _get_financial_summary(
        db: Session,
        tenant_id: str,
        business_unit_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """Obtém resumo financeiro básico"""
        
        query = db.query(FinancialTransaction).filter(
            FinancialTransaction.tenant_id == tenant_id,
            FinancialTransaction.business_unit_id == business_unit_id,
            FinancialTransaction.is_active == True,
            FinancialTransaction.status == TransactionStatus.APROVADA,
            FinancialTransaction.transaction_date >= start_date,
            FinancialTransaction.transaction_date <= end_date
        )
        
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
        
        # Calcular margem
        margem = (receitas - despesas) / receitas * 100 if receitas > 0 else 0
        
        return {
            "receitas": float(receitas),
            "despesas": float(despesas),
            "saldo": float(saldo),
            "margem": float(margem),
            "total_transacoes": query.count()
        }
    
    @staticmethod
    def _get_chart_accounts_summary(
        db: Session,
        tenant_id: str,
        business_unit_id: str,
        start_date: datetime,
        end_date: datetime
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
            FinancialTransaction.transaction_date >= start_date,
            FinancialTransaction.transaction_date <= end_date,
            ChartAccount.is_active == True
        )
        
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
    
    @staticmethod
    def _get_financial_trends(
        db: Session,
        tenant_id: str,
        business_unit_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """Obtém tendências financeiras por período"""
        
        # Agrupar por dia
        daily_data = db.query(
            func.date(FinancialTransaction.transaction_date).label('date'),
            FinancialTransaction.transaction_type,
            func.sum(FinancialTransaction.amount).label('amount')
        ).filter(
            FinancialTransaction.tenant_id == tenant_id,
            FinancialTransaction.business_unit_id == business_unit_id,
            FinancialTransaction.is_active == True,
            FinancialTransaction.status == TransactionStatus.APROVADA,
            FinancialTransaction.transaction_date >= start_date,
            FinancialTransaction.transaction_date <= end_date
        ).group_by(
            func.date(FinancialTransaction.transaction_date),
            FinancialTransaction.transaction_type
        ).all()
        
        # Organizar dados por data
        trends = {}
        for data in daily_data:
            date_str = data.date.isoformat()
            if date_str not in trends:
                trends[date_str] = {"receitas": 0, "despesas": 0}
            
            if data.transaction_type == TransactionType.RECEITA:
                trends[date_str]["receitas"] += float(data.amount)
            elif data.transaction_type == TransactionType.DESPESA:
                trends[date_str]["despesas"] += float(data.amount)
        
        # Converter para arrays ordenados
        dates = sorted(trends.keys())
        receitas_trend = [trends[date]["receitas"] for date in dates]
        despesas_trend = [trends[date]["despesas"] for date in dates]
        
        return {
            "dates": dates,
            "receitas": receitas_trend,
            "despesas": despesas_trend
        }
    
    @staticmethod
    def _get_status_summary(
        db: Session,
        tenant_id: str,
        business_unit_id: str
    ) -> Dict:
        """Obtém resumo por status das transações"""
        
        status_counts = db.query(
            FinancialTransaction.status,
            func.count(FinancialTransaction.id)
        ).filter(
            FinancialTransaction.tenant_id == tenant_id,
            FinancialTransaction.business_unit_id == business_unit_id,
            FinancialTransaction.is_active == True
        ).group_by(FinancialTransaction.status).all()
        
        return {status.value: count for status, count in status_counts}
    
    @staticmethod
    def _get_performance_metrics(
        db: Session,
        tenant_id: str,
        business_unit_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """Obtém métricas de performance"""
        
        # Total de transações aprovadas
        total_approved = db.query(FinancialTransaction).filter(
            FinancialTransaction.tenant_id == tenant_id,
            FinancialTransaction.business_unit_id == business_unit_id,
            FinancialTransaction.is_active == True,
            FinancialTransaction.status == TransactionStatus.APROVADA,
            FinancialTransaction.transaction_date >= start_date,
            FinancialTransaction.transaction_date <= end_date
        ).count()
        
        # Total de transações pendentes
        total_pending = db.query(FinancialTransaction).filter(
            FinancialTransaction.tenant_id == tenant_id,
            FinancialTransaction.business_unit_id == business_unit_id,
            FinancialTransaction.is_active == True,
            FinancialTransaction.status == TransactionStatus.PENDENTE,
            FinancialTransaction.transaction_date >= start_date,
            FinancialTransaction.transaction_date <= end_date
        ).count()
        
        # Total de transações rejeitadas
        total_rejected = db.query(FinancialTransaction).filter(
            FinancialTransaction.tenant_id == tenant_id,
            FinancialTransaction.business_unit_id == business_unit_id,
            FinancialTransaction.is_active == True,
            FinancialTransaction.status == TransactionStatus.REJEITADA,
            FinancialTransaction.transaction_date >= start_date,
            FinancialTransaction.transaction_date <= end_date
        ).count()
        
        # Calcular taxa de aprovação
        total_transactions = total_approved + total_pending + total_rejected
        approval_rate = (total_approved / total_transactions * 100) if total_transactions > 0 else 0
        
        # Calcular valor médio por transação
        avg_transaction_value = db.query(
            func.avg(FinancialTransaction.amount)
        ).filter(
            FinancialTransaction.tenant_id == tenant_id,
            FinancialTransaction.business_unit_id == business_unit_id,
            FinancialTransaction.is_active == True,
            FinancialTransaction.status == TransactionStatus.APROVADA,
            FinancialTransaction.transaction_date >= start_date,
            FinancialTransaction.transaction_date <= end_date
        ).scalar() or 0
        
        return {
            "total_transactions": total_transactions,
            "approved_transactions": total_approved,
            "pending_transactions": total_pending,
            "rejected_transactions": total_rejected,
            "approval_rate": float(approval_rate),
            "avg_transaction_value": float(avg_transaction_value)
        }
    
    @staticmethod
    def get_chart_accounts_tree(
        db: Session,
        tenant_id: str,
        business_unit_id: str
    ) -> Dict:
        """Obtém árvore completa do plano de contas com resumos"""
        
        # Buscar grupos
        groups = db.query(ChartAccountGroup).filter(
            ChartAccountGroup.is_active == True
        ).all()
        
        # Buscar subgrupos
        subgroups = db.query(ChartAccountSubgroup).filter(
            ChartAccountSubgroup.is_active == True
        ).all()
        
        # Buscar contas
        accounts = db.query(ChartAccount).filter(
            ChartAccount.is_active == True
        ).all()
        
        # Buscar resumos financeiros por conta
        account_summaries = db.query(
            FinancialTransaction.chart_account_id,
            func.sum(FinancialTransaction.amount).label('total_amount'),
            func.count(FinancialTransaction.id).label('transaction_count')
        ).filter(
            FinancialTransaction.tenant_id == tenant_id,
            FinancialTransaction.business_unit_id == business_unit_id,
            FinancialTransaction.is_active == True,
            FinancialTransaction.status == TransactionStatus.APROVADA
        ).group_by(FinancialTransaction.chart_account_id).all()
        
        # Criar dicionário de resumos
        summaries_dict = {
            summary.chart_account_id: {
                "total_amount": float(summary.total_amount or 0),
                "transaction_count": summary.transaction_count
            }
            for summary in account_summaries
        }
        
        # Construir árvore
        tree = {
            "groups": [],
            "subgroups": [],
            "accounts": []
        }
        
        # Processar grupos
        for group in groups:
            group_data = {
                "id": group.id,
                "code": group.code,
                "name": group.name,
                "description": group.description,
                "is_active": group.is_active,
                "created_at": group.created_at.isoformat(),
                "updated_at": group.updated_at.isoformat()
            }
            tree["groups"].append(group_data)
        
        # Processar subgrupos
        for subgroup in subgroups:
            subgroup_data = {
                "id": subgroup.id,
                "code": subgroup.code,
                "name": subgroup.name,
                "description": subgroup.description,
                "group_id": subgroup.group_id,
                "group_name": subgroup.group.name,
                "is_active": subgroup.is_active,
                "created_at": subgroup.created_at.isoformat(),
                "updated_at": subgroup.updated_at.isoformat()
            }
            tree["subgroups"].append(subgroup_data)
        
        # Processar contas
        for account in accounts:
            account_data = {
                "id": account.id,
                "code": account.code,
                "name": account.name,
                "description": account.description,
                "subgroup_id": account.subgroup_id,
                "subgroup_name": account.subgroup.name,
                "group_id": account.subgroup.group.id,
                "group_name": account.subgroup.group.name,
                "account_type": account.account_type,
                "is_active": account.is_active,
                "created_at": account.created_at.isoformat(),
                "updated_at": account.updated_at.isoformat()
            }
            
            # Adicionar resumo financeiro se existir
            if account.id in summaries_dict:
                account_data.update(summaries_dict[account.id])
            else:
                account_data.update({
                    "total_amount": 0,
                    "transaction_count": 0
                })
            
            tree["accounts"].append(account_data)
        
        return tree
