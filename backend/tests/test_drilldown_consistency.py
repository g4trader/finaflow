"""
Teste de consistência entre annual-summary e monthly-drilldown

Garante que:
- Soma dos dias = total mensal
- Total mensal = valor de /annual-summary
- Summary dos lançamentos sem filtro = total do mês
"""

import pytest
import os
import sys
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from unittest.mock import Mock, MagicMock

# Mock do database
mock_database = MagicMock()
mock_database.SessionLocal = MagicMock()
sys.modules['app.database'] = mock_database

os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost/test'

from app.services.financial_aggregation_service import FinancialAggregationService
from app.services.monthly_drilldown_service import MonthlyDrilldownService
from app.models.lancamento_diario import LancamentoDiario, TransactionType


@pytest.fixture
def mock_db():
    """Mock do banco de dados"""
    db = Mock(spec=Session)
    return db


@pytest.fixture
def sample_transactions_january():
    """Transações de exemplo para janeiro"""
    transactions = []
    
    # Dia 1: Receita
    tx1 = Mock()
    tx1.data_movimentacao = datetime(2025, 1, 1, 10, 0)
    tx1.valor = Decimal("1000.00")
    tx1.transaction_type = TransactionType.RECEITA
    tx1.is_active = True
    transactions.append(tx1)
    
    # Dia 1: Despesa
    tx2 = Mock()
    tx2.data_movimentacao = datetime(2025, 1, 1, 14, 0)
    tx2.valor = Decimal("500.00")
    tx2.transaction_type = TransactionType.DESPESA
    tx2.is_active = True
    transactions.append(tx2)
    
    # Dia 5: Receita
    tx3 = Mock()
    tx3.data_movimentacao = datetime(2025, 1, 5, 9, 0)
    tx3.valor = Decimal("2000.00")
    tx3.transaction_type = TransactionType.RECEITA
    tx3.is_active = True
    transactions.append(tx3)
    
    # Dia 5: Custo
    tx4 = Mock()
    tx4.data_movimentacao = datetime(2025, 1, 5, 15, 0)
    tx4.valor = Decimal("300.00")
    tx4.transaction_type = TransactionType.CUSTO
    tx4.is_active = True
    transactions.append(tx4)
    
    return transactions


def test_consistency_daily_summary_vs_annual_summary(mock_db, sample_transactions_january):
    """
    Testa que os totais mensais do daily-summary batem com annual-summary
    """
    # Configurar mock para ambas as queries
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = sample_transactions_january
    mock_db.query.return_value = query_mock
    
    # 1. Buscar annual summary
    annual_result = FinancialAggregationService.aggregate_monthly_summary(
        db=mock_db,
        tenant_id="test-tenant",
        business_unit_id="test-bu",
        year=2025,
    )
    
    # 2. Buscar daily summary de janeiro
    daily_result = MonthlyDrilldownService.aggregate_daily_summary(
        db=mock_db,
        tenant_id="test-tenant",
        business_unit_id="test-bu",
        year=2025,
        month=1,
    )
    
    # 3. Comparar totais
    jan_annual = annual_result["monthly"][0]  # Janeiro é índice 0
    
    assert Decimal(daily_result["metadata"]["month_total_revenue"]) == Decimal(str(jan_annual["revenue"]))
    assert Decimal(daily_result["metadata"]["month_total_expense"]) == Decimal(str(jan_annual["expense"]))
    assert Decimal(daily_result["metadata"]["month_total_cost"]) == Decimal(str(jan_annual["cost"]))
    assert Decimal(daily_result["metadata"]["month_total_balance"]) == Decimal(str(jan_annual["balance"]))


def test_consistency_sum_of_days_equals_month_total(mock_db, sample_transactions_january):
    """
    Testa que a soma dos dias = total mensal
    """
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = sample_transactions_january
    mock_db.query.return_value = query_mock
    
    daily_result = MonthlyDrilldownService.aggregate_daily_summary(
        db=mock_db,
        tenant_id="test-tenant",
        business_unit_id="test-bu",
        year=2025,
        month=1,
    )
    
    # Somar todos os dias
    sum_revenue = sum(Decimal(day["revenue"]) for day in daily_result["days"])
    sum_expense = sum(Decimal(day["expense"]) for day in daily_result["days"])
    sum_cost = sum(Decimal(day["cost"]) for day in daily_result["days"])
    sum_balance = sum(Decimal(day["balance"]) for day in daily_result["days"])
    
    # Comparar com totais
    assert sum_revenue == Decimal(daily_result["metadata"]["month_total_revenue"])
    assert sum_expense == Decimal(daily_result["metadata"]["month_total_expense"])
    assert sum_cost == Decimal(daily_result["metadata"]["month_total_cost"])
    assert sum_balance == Decimal(daily_result["metadata"]["month_total_balance"])


def test_consistency_transactions_summary_vs_month_total(mock_db, sample_transactions_january):
    """
    Testa que o summary dos lançamentos (sem filtro) = total do mês
    """
    # Mock dos relacionamentos
    for tx in sample_transactions_january:
        tx.id = f"tx-{tx.data_movimentacao.day}"
        tx.observacoes = f"Lançamento dia {tx.data_movimentacao.day}"
        tx.grupo = Mock()
        tx.grupo.name = "Grupo Teste"
        tx.subgrupo = Mock()
        tx.subgrupo.name = "Subgrupo Teste"
        tx.conta = Mock()
        tx.conta.name = "Conta Teste"
    
    # Configurar mock
    query_mock = Mock()
    query_mock.options.return_value = query_mock
    query_mock.filter.return_value = query_mock
    query_mock.order_by.return_value = query_mock
    query_mock.offset.return_value = query_mock
    query_mock.limit.return_value = query_mock
    query_mock.count.return_value = len(sample_transactions_january)
    query_mock.all.return_value = sample_transactions_january
    mock_db.query.return_value = query_mock
    
    # 1. Buscar daily summary
    daily_result = MonthlyDrilldownService.aggregate_daily_summary(
        db=mock_db,
        tenant_id="test-tenant",
        business_unit_id="test-bu",
        year=2025,
        month=1,
    )
    
    # 2. Buscar transactions (sem filtro)
    transactions_result = MonthlyDrilldownService.get_monthly_transactions(
        db=mock_db,
        tenant_id="test-tenant",
        business_unit_id="test-bu",
        year=2025,
        month=1,
        page=1,
        page_size=50,
    )
    
    # 3. Comparar summary com totais mensais
    assert Decimal(transactions_result["summary"]["revenue"]) == Decimal(daily_result["metadata"]["month_total_revenue"])
    assert Decimal(transactions_result["summary"]["expense"]) == Decimal(daily_result["metadata"]["month_total_expense"])
    assert Decimal(transactions_result["summary"]["cost"]) == Decimal(daily_result["metadata"]["month_total_cost"])
    assert Decimal(transactions_result["summary"]["balance"]) == Decimal(daily_result["metadata"]["month_total_balance"])

