"""
Serviço de Agregação Financeira Mensal

Centraliza a lógica de agregação de receitas, despesas e custos por mês,
garantindo consistência absoluta entre banco de dados e API.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, cast, Integer

from app.models.lancamento_diario import LancamentoDiario, TransactionType


class FinancialAggregationService:
    """Serviço para agregação financeira mensal"""

    @staticmethod
    def aggregate_monthly_summary(
        db: Session,
        tenant_id: str,
        business_unit_id: str,
        year: int,
    ) -> Dict[str, any]:
        """
        Agrega receitas, despesas e custos por mês para o ano informado.
        
        Retorna:
        {
            "year": int,
            "totals": {
                "revenue": float,
                "expense": float,
                "cost": float,
                "balance": float
            },
            "monthly": [
                {
                    "month": int,
                    "revenue": float,
                    "expense": float,
                    "cost": float,
                    "balance": float,
                    "accumulated_balance": float
                },
                ...
            ]
        }
        """
        start_dt = datetime(year, 1, 1)
        end_dt = datetime(year, 12, 31, 23, 59, 59)

        # Query para buscar lançamentos do ano
        query = (
            db.query(LancamentoDiario)
            .filter(
                LancamentoDiario.tenant_id == tenant_id,
                LancamentoDiario.business_unit_id == business_unit_id,
                LancamentoDiario.is_active.is_(True),
                LancamentoDiario.data_movimentacao >= start_dt,
                LancamentoDiario.data_movimentacao <= end_dt,
            )
        )

        # Buscar todos os lançamentos
        transactions = query.all()

        # Inicializar estrutura mensal (12 meses)
        monthly_data: Dict[int, Dict[str, Decimal]] = {
            month: {
                "revenue": Decimal("0"),
                "expense": Decimal("0"),
                "cost": Decimal("0"),
                "balance": Decimal("0"),
            }
            for month in range(1, 13)
        }

        # Agregar transações por mês
        for tx in transactions:
            # Ignorar transações sem tipo
            if tx.transaction_type is None:
                continue

            # FILTRO CRÍTICO: Excluir categorias que não devem entrar no cálculo
            # "Deduções" não são despesas - são reduções de receita
            # "Movimentações Não Operacionais" não são despesas operacionais
            grupo_nome = tx.grupo.name.lower() if tx.grupo else ""
            
            # Excluir Deduções
            if "dedução" in grupo_nome or "deducao" in grupo_nome or "deduções" in grupo_nome or "deducoes" in grupo_nome:
                continue  # Não contar como despesa
            
            # Excluir Movimentações Não Operacionais
            if "movimentações não operacionais" in grupo_nome or "movimentacoes nao operacionais" in grupo_nome or \
               "movimentações nao operacionais" in grupo_nome or "movimentacoes não operacionais" in grupo_nome:
                continue  # Não contar como despesa operacional

            month = tx.data_movimentacao.month
            valor = tx.valor if tx.valor is not None else Decimal("0")

            if tx.transaction_type == TransactionType.RECEITA:
                monthly_data[month]["revenue"] += valor
            elif tx.transaction_type == TransactionType.DESPESA:
                monthly_data[month]["expense"] += valor
            elif tx.transaction_type == TransactionType.CUSTO:
                monthly_data[month]["cost"] += valor

        # ============================================================
        # CÁLCULO DO SALDO MENSAL
        # ============================================================
        # Fórmula: saldo_mensal = receita - despesa - custo
        # Sempre calculado, mesmo para meses sem lançamentos (resulta em 0)
        for month in range(1, 13):
            monthly_data[month]["balance"] = (
                monthly_data[month]["revenue"]
                - monthly_data[month]["expense"]
                - monthly_data[month]["cost"]
            )

        # ============================================================
        # CÁLCULO DOS TOTAIS ANUAIS
        # ============================================================
        # Soma de todos os 12 meses para cada categoria
        annual_totals = {
            "revenue": Decimal("0"),
            "expense": Decimal("0"),
            "cost": Decimal("0"),
            "balance": Decimal("0"),
        }

        for month in range(1, 13):
            annual_totals["revenue"] += monthly_data[month]["revenue"]
            annual_totals["expense"] += monthly_data[month]["expense"]
            annual_totals["cost"] += monthly_data[month]["cost"]
            annual_totals["balance"] += monthly_data[month]["balance"]

        # ============================================================
        # CÁLCULO DO SALDO ACUMULADO
        # ============================================================
        # Fórmula: saldo_acumulado[mês] = saldo_acumulado[mês_anterior] + saldo_mensal[mês]
        # 
        # Regras:
        # - Janeiro: saldo_acumulado = saldo_mensal[jan] (sem mês anterior)
        # - Meses seguintes: saldo_acumulado = acumulado_anterior + saldo_mensal
        # - Meses sem lançamentos: saldo_acumulado se propaga (mantém valor anterior)
        # - Usa Decimal para precisão absoluta em todos os cálculos
        accumulated_balance = Decimal("0")
        monthly_list: List[Dict[str, any]] = []

        for month in range(1, 13):
            balance = monthly_data[month]["balance"]
            # Acumular: saldo_acumulado = saldo_acumulado_anterior + saldo_mensal
            accumulated_balance += balance

            monthly_list.append({
                "month": month,
                "revenue": float(monthly_data[month]["revenue"]),
                "expense": float(monthly_data[month]["expense"]),
                "cost": float(monthly_data[month]["cost"]),
                "balance": float(balance),  # saldo_mensal
                "accumulated_balance": float(accumulated_balance),  # saldo_acumulado
            })

        return {
            "year": year,
            "totals": {
                "revenue": float(annual_totals["revenue"]),
                "expense": float(annual_totals["expense"]),
                "cost": float(annual_totals["cost"]),
                "balance": float(annual_totals["balance"]),
            },
            "monthly": monthly_list,
        }

    @staticmethod
    def get_debug_summary(
        db: Session,
        tenant_id: str,
        business_unit_id: str,
        year: int,
    ) -> Dict[str, any]:
        """
        Retorna resumo detalhado para debug/QA, incluindo:
        - Totais brutos do banco (SQL agregado)
        - Totais por tipo de transação
        - Contagem de lançamentos
        - Valores por mês em formato Decimal (precisão)
        """
        start_dt = datetime(year, 1, 1)
        end_dt = datetime(year, 12, 31, 23, 59, 59)

        # Query base
        base_query = (
            db.query(LancamentoDiario)
            .filter(
                LancamentoDiario.tenant_id == tenant_id,
                LancamentoDiario.business_unit_id == business_unit_id,
                LancamentoDiario.is_active.is_(True),
                LancamentoDiario.data_movimentacao >= start_dt,
                LancamentoDiario.data_movimentacao <= end_dt,
            )
        )

        # Agregação SQL direta por tipo e mês
        # Usar func.extract para compatibilidade (PostgreSQL/SQLite)
        try:
            # Tentar PostgreSQL (date_part)
            sql_aggregation = (
                db.query(
                    cast(func.date_part("month", LancamentoDiario.data_movimentacao), Integer).label("month"),
                    LancamentoDiario.transaction_type,
                    func.sum(LancamentoDiario.valor).label("total"),
                    func.count(LancamentoDiario.id).label("count"),
                )
                .filter(
                    LancamentoDiario.tenant_id == tenant_id,
                    LancamentoDiario.business_unit_id == business_unit_id,
                    LancamentoDiario.is_active.is_(True),
                    LancamentoDiario.data_movimentacao >= start_dt,
                    LancamentoDiario.data_movimentacao <= end_dt,
                    LancamentoDiario.transaction_type.isnot(None),
                )
                .group_by(
                    cast(func.date_part("month", LancamentoDiario.data_movimentacao), Integer),
                    LancamentoDiario.transaction_type,
                )
                .all()
            )
        except Exception:
            # Fallback: usar agregação em memória apenas
            sql_aggregation = []

        # Estrutura para armazenar dados SQL
        sql_monthly: Dict[int, Dict[str, Dict[str, any]]] = {
            month: {
                "revenue": {"total": Decimal("0"), "count": 0},
                "expense": {"total": Decimal("0"), "count": 0},
                "cost": {"total": Decimal("0"), "count": 0},
            }
            for month in range(1, 13)
        }

        for row in sql_aggregation:
            month = int(row.month)
            tx_type = row.transaction_type.value if row.transaction_type else None
            total = Decimal(str(row.total)) if row.total else Decimal("0")
            count = row.count or 0

            if tx_type == "RECEITA":
                sql_monthly[month]["revenue"]["total"] = total
                sql_monthly[month]["revenue"]["count"] = count
            elif tx_type == "DESPESA":
                sql_monthly[month]["expense"]["total"] = total
                sql_monthly[month]["expense"]["count"] = count
            elif tx_type == "CUSTO":
                sql_monthly[month]["cost"]["total"] = total
                sql_monthly[month]["cost"]["count"] = count

        # Buscar todos os lançamentos para agregação em memória
        transactions = base_query.all()

        # Agregação em memória (método atual)
        memory_monthly: Dict[int, Dict[str, Decimal]] = {
            month: {
                "revenue": Decimal("0"),
                "expense": Decimal("0"),
                "cost": Decimal("0"),
            }
            for month in range(1, 13)
        }

        for tx in transactions:
            if tx.transaction_type is None:
                continue

            month = tx.data_movimentacao.month
            valor = tx.valor if tx.valor is not None else Decimal("0")

            if tx.transaction_type == TransactionType.RECEITA:
                memory_monthly[month]["revenue"] += valor
            elif tx.transaction_type == TransactionType.DESPESA:
                memory_monthly[month]["expense"] += valor
            elif tx.transaction_type == TransactionType.CUSTO:
                memory_monthly[month]["cost"] += valor

        # Comparar SQL vs Memória
        monthly_comparison = []
        for month in range(1, 13):
            sql_rev = sql_monthly[month]["revenue"]["total"]
            sql_exp = sql_monthly[month]["expense"]["total"]
            sql_cst = sql_monthly[month]["cost"]["total"]
            mem_rev = memory_monthly[month]["revenue"]
            mem_exp = memory_monthly[month]["expense"]
            mem_cst = memory_monthly[month]["cost"]

            monthly_comparison.append({
                "month": month,
                "sql": {
                    "revenue": str(sql_rev),
                    "expense": str(sql_exp),
                    "cost": str(sql_cst),
                    "revenue_count": sql_monthly[month]["revenue"]["count"],
                    "expense_count": sql_monthly[month]["expense"]["count"],
                    "cost_count": sql_monthly[month]["cost"]["count"],
                },
                "memory": {
                    "revenue": str(mem_rev),
                    "expense": str(mem_exp),
                    "cost": str(mem_cst),
                },
                "match": {
                    "revenue": sql_rev == mem_rev,
                    "expense": sql_exp == mem_exp,
                    "cost": sql_cst == mem_cst,
                },
            })

        # Totais anuais
        annual_sql = {
            "revenue": sum(sql_monthly[m]["revenue"]["total"] for m in range(1, 13)),
            "expense": sum(sql_monthly[m]["expense"]["total"] for m in range(1, 13)),
            "cost": sum(sql_monthly[m]["cost"]["total"] for m in range(1, 13)),
        }
        annual_memory = {
            "revenue": sum(memory_monthly[m]["revenue"] for m in range(1, 13)),
            "expense": sum(memory_monthly[m]["expense"] for m in range(1, 13)),
            "cost": sum(memory_monthly[m]["cost"] for m in range(1, 13)),
        }

        return {
            "year": year,
            "tenant_id": tenant_id,
            "business_unit_id": business_unit_id,
            "date_range": {
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
            },
            "total_transactions": base_query.count(),
            "transactions_with_type": base_query.filter(
                LancamentoDiario.transaction_type.isnot(None)
            ).count(),
            "annual_totals": {
                "sql": {
                    "revenue": str(annual_sql["revenue"]),
                    "expense": str(annual_sql["expense"]),
                    "cost": str(annual_sql["cost"]),
                },
                "memory": {
                    "revenue": str(annual_memory["revenue"]),
                    "expense": str(annual_memory["expense"]),
                    "cost": str(annual_memory["cost"]),
                },
            },
            "monthly_comparison": monthly_comparison,
        }

