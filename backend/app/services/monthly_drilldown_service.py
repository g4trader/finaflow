"""
Serviço de Drill Down Mensal

Fornece agregação diária e listagem detalhada de lançamentos para um mês específico.
Garante consistência com FinancialAggregationService.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from calendar import monthrange

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.lancamento_diario import LancamentoDiario, TransactionType


class MonthlyDrilldownService:
    """Serviço para drill down mensal (diário e detalhado)"""

    @staticmethod
    def aggregate_daily_summary(
        db: Session,
        tenant_id: str,
        business_unit_id: str,
        year: int,
        month: int,
    ) -> Dict[str, any]:
        """
        Agrega receitas, despesas e custos por dia para o mês informado.
        
        Retorna:
        {
            "year": int,
            "month": int,
            "currency": "BRL",
            "days": [
                {
                    "date": "2025-01-01",
                    "day": 1,
                    "revenue": "1234.56",
                    "expense": "789.10",
                    "cost": "500.00",
                    "balance": "-54.54"
                },
                ...
            ],
            "metadata": {
                "saldo_formula": "receita - despesa - custo",
                "month_total_revenue": "...",
                "month_total_expense": "...",
                "month_total_cost": "...",
                "month_total_balance": "..."
            }
        }
        """
        # Validar mês
        if month < 1 or month > 12:
            raise ValueError(f"Mês inválido: {month}. Deve estar entre 1 e 12.")
        
        # Calcular range de datas do mês
        start_dt = datetime(year, month, 1)
        last_day = monthrange(year, month)[1]
        end_dt = datetime(year, month, last_day, 23, 59, 59)
        
        # Query para buscar lançamentos do mês
        from app.models.chart_of_accounts import ChartAccountGroup
        
        query = (
            db.query(LancamentoDiario)
            .join(ChartAccountGroup, LancamentoDiario.grupo_id == ChartAccountGroup.id)
            .filter(
                LancamentoDiario.tenant_id == tenant_id,
                LancamentoDiario.business_unit_id == business_unit_id,
                LancamentoDiario.is_active.is_(True),
                LancamentoDiario.data_movimentacao >= start_dt,
                LancamentoDiario.data_movimentacao <= end_dt,
            )
        )
        
        # APLICAR FILTRO DIRETAMENTE NA QUERY para excluir Deduções e Movimentações Não Operacionais
        query = query.filter(
            ~ChartAccountGroup.name.ilike('%dedução%'),
            ~ChartAccountGroup.name.ilike('%deducao%'),
            ~ChartAccountGroup.name.ilike('%deduções%'),
            ~ChartAccountGroup.name.ilike('%deducoes%'),
            ~ChartAccountGroup.name.ilike('%movimentações não operacionais%'),
            ~ChartAccountGroup.name.ilike('%movimentacoes nao operacionais%'),
            ~ChartAccountGroup.name.ilike('%movimentações nao operacionais%'),
            ~ChartAccountGroup.name.ilike('%movimentacoes não operacionais%'),
        )
        
        # Buscar todos os lançamentos
        transactions = query.all()
        
        # Inicializar estrutura diária (todos os dias do mês)
        daily_data: Dict[int, Dict[str, Decimal]] = {
            day: {
                "revenue": Decimal("0"),
                "expense": Decimal("0"),
                "cost": Decimal("0"),
                "balance": Decimal("0"),
            }
            for day in range(1, last_day + 1)
        }
        
        # Agregar transações por dia
        # FILTRO JÁ APLICADO NA QUERY - não precisa verificar novamente
        for tx in transactions:
            # Ignorar transações sem tipo
            if tx.transaction_type is None:
                continue
            
            day = tx.data_movimentacao.day
            valor = tx.valor if tx.valor is not None else Decimal("0")
            
            if tx.transaction_type == TransactionType.RECEITA:
                daily_data[day]["revenue"] += valor
            elif tx.transaction_type == TransactionType.DESPESA:
                daily_data[day]["expense"] += valor
            elif tx.transaction_type == TransactionType.CUSTO:
                daily_data[day]["cost"] += valor
        
        # Calcular saldo diário (receita - despesa - custo)
        for day in range(1, last_day + 1):
            daily_data[day]["balance"] = (
                daily_data[day]["revenue"]
                - daily_data[day]["expense"]
                - daily_data[day]["cost"]
            )
        
        # Calcular totais mensais
        month_totals = {
            "revenue": Decimal("0"),
            "expense": Decimal("0"),
            "cost": Decimal("0"),
            "balance": Decimal("0"),
        }
        
        for day in range(1, last_day + 1):
            month_totals["revenue"] += daily_data[day]["revenue"]
            month_totals["expense"] += daily_data[day]["expense"]
            month_totals["cost"] += daily_data[day]["cost"]
            month_totals["balance"] += daily_data[day]["balance"]
        
        # Construir lista de dias
        days_list: List[Dict[str, any]] = []
        for day in range(1, last_day + 1):
            day_date = date(year, month, day)
            days_list.append({
                "date": day_date.isoformat(),
                "day": day,
                "revenue": str(daily_data[day]["revenue"]),
                "expense": str(daily_data[day]["expense"]),
                "cost": str(daily_data[day]["cost"]),
                "balance": str(daily_data[day]["balance"]),
            })
        
        return {
            "year": year,
            "month": month,
            "currency": "BRL",
            "days": days_list,
            "metadata": {
                "saldo_formula": "receita - despesa - custo",
                "month_total_revenue": str(month_totals["revenue"]),
                "month_total_expense": str(month_totals["expense"]),
                "month_total_cost": str(month_totals["cost"]),
                "month_total_balance": str(month_totals["balance"]),
            }
        }
    
    @staticmethod
    def get_monthly_transactions(
        db: Session,
        tenant_id: str,
        business_unit_id: str,
        year: int,
        month: int,
        transaction_type: Optional[TransactionType] = None,
        group_id: Optional[str] = None,
        subgroup_id: Optional[str] = None,
        account_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, any]:
        """
        Retorna lançamentos detalhados do mês com filtros e paginação.
        
        Retorna:
        {
            "year": int,
            "month": int,
            "page": int,
            "page_size": int,
            "total_items": int,
            "total_pages": int,
            "summary": {
                "revenue": "...",
                "expense": "...",
                "cost": "...",
                "balance": "..."
            },
            "items": [...]
        }
        """
        # Validar mês
        if month < 1 or month > 12:
            raise ValueError(f"Mês inválido: {month}. Deve estar entre 1 e 12.")
        
        # Validar paginação
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 50
        if page_size > 200:
            page_size = 200
        
        # Calcular range de datas do mês
        start_dt = datetime(year, month, 1)
        last_day = monthrange(year, month)[1]
        end_dt = datetime(year, month, last_day, 23, 59, 59)
        
        # Query base com joinedload para performance
        from sqlalchemy.orm import joinedload
        from app.models.chart_of_accounts import ChartAccountGroup
        
        query = (
            db.query(LancamentoDiario)
            .join(ChartAccountGroup, LancamentoDiario.grupo_id == ChartAccountGroup.id)
            .options(
                joinedload(LancamentoDiario.grupo),
                joinedload(LancamentoDiario.subgrupo),
                joinedload(LancamentoDiario.conta),
            )
            .filter(
                LancamentoDiario.tenant_id == tenant_id,
                LancamentoDiario.business_unit_id == business_unit_id,
                LancamentoDiario.is_active.is_(True),
                LancamentoDiario.data_movimentacao >= start_dt,
                LancamentoDiario.data_movimentacao <= end_dt,
            )
        )
        
        # APLICAR FILTRO DIRETAMENTE NA QUERY para excluir Deduções e Movimentações Não Operacionais
        # Isso é mais eficiente que filtrar depois
        query = query.filter(
            ~ChartAccountGroup.name.ilike('%dedução%'),
            ~ChartAccountGroup.name.ilike('%deducao%'),
            ~ChartAccountGroup.name.ilike('%deduções%'),
            ~ChartAccountGroup.name.ilike('%deducoes%'),
            ~ChartAccountGroup.name.ilike('%movimentações não operacionais%'),
            ~ChartAccountGroup.name.ilike('%movimentacoes nao operacionais%'),
            ~ChartAccountGroup.name.ilike('%movimentações nao operacionais%'),
            ~ChartAccountGroup.name.ilike('%movimentacoes não operacionais%'),
        )
        
        # Aplicar filtros
        if transaction_type:
            query = query.filter(LancamentoDiario.transaction_type == transaction_type)
        if group_id:
            query = query.filter(LancamentoDiario.grupo_id == group_id)
        if subgroup_id:
            query = query.filter(LancamentoDiario.subgrupo_id == subgroup_id)
        if account_id:
            query = query.filter(LancamentoDiario.conta_id == account_id)
        
        # Contar total (para summary e paginação)
        total_items = query.count()
        total_pages = (total_items + page_size - 1) // page_size  # Ceiling division
        
        # Calcular summary (totais do mês considerando filtros)
        # Buscar todos os lançamentos que passam pelos filtros
        all_filtered_transactions = query.all()
        
        summary = {
            "revenue": Decimal("0"),
            "expense": Decimal("0"),
            "cost": Decimal("0"),
            "balance": Decimal("0"),
        }
        
        for tx in all_filtered_transactions:
            if tx.transaction_type is None:
                continue
            
            # FILTRO JÁ APLICADO NA QUERY - não precisa verificar novamente
            # Mas manter verificação como segurança adicional
            grupo_nome = tx.grupo.name.lower() if tx.grupo else ""
            
            # Excluir Deduções (verificação adicional)
            if "dedução" in grupo_nome or "deducao" in grupo_nome or "deduções" in grupo_nome or "deducoes" in grupo_nome:
                continue  # Não contar como despesa
            
            # Excluir Movimentações Não Operacionais (verificação adicional)
            if "movimentações não operacionais" in grupo_nome or "movimentacoes nao operacionais" in grupo_nome or \
               "movimentações nao operacionais" in grupo_nome or "movimentacoes não operacionais" in grupo_nome:
                continue  # Não contar como despesa operacional
            
            valor = tx.valor if tx.valor is not None else Decimal("0")
            
            if tx.transaction_type == TransactionType.RECEITA:
                summary["revenue"] += valor
            elif tx.transaction_type == TransactionType.DESPESA:
                summary["expense"] += valor
            elif tx.transaction_type == TransactionType.CUSTO:
                summary["cost"] += valor
        
        summary["balance"] = summary["revenue"] - summary["expense"] - summary["cost"]
        
        # Aplicar paginação
        offset = (page - 1) * page_size
        paginated_transactions = query.order_by(
            LancamentoDiario.data_movimentacao.desc(),
            LancamentoDiario.created_at.desc()
        ).offset(offset).limit(page_size).all()
        
        # Formatar items
        items: List[Dict[str, any]] = []
        for tx in paginated_transactions:
            items.append({
                "id": tx.id,
                "date": tx.data_movimentacao.date().isoformat(),
                "description": tx.observacoes or "Lançamento",
                "type": tx.transaction_type.value if tx.transaction_type else None,
                "group": tx.grupo.name if tx.grupo else None,
                "subgroup": tx.subgrupo.name if tx.subgrupo else None,
                "account": tx.conta.name if tx.conta else None,
                "amount": str(tx.valor) if tx.valor else "0",
            })
        
        return {
            "year": year,
            "month": month,
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": total_pages,
            "summary": {
                "revenue": str(summary["revenue"]),
                "expense": str(summary["expense"]),
                "cost": str(summary["cost"]),
                "balance": str(summary["balance"]),
            },
            "items": items,
        }

