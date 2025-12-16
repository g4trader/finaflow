"""
Testes unitários para FinancialAggregationService

Cobre:
- Mês com lançamentos
- Mês sem lançamentos
- Saldo acumulado
- Soma de receita/despesa/custo
- Totais anuais
"""

import pytest
import os
import sys
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from unittest.mock import Mock, MagicMock, patch

# Mock do database antes de importar qualquer módulo que use app.database
# Isso evita tentar criar conexão real durante os testes
mock_database = MagicMock()
mock_database.SessionLocal = MagicMock()
sys.modules['app.database'] = mock_database

# Configurar DATABASE_URL para evitar erro de conexão
os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost/test'

from app.services.financial_aggregation_service import FinancialAggregationService
from app.models.lancamento_diario import LancamentoDiario, TransactionType


@pytest.fixture
def mock_db():
    """Mock do banco de dados"""
    db = Mock(spec=Session)
    return db


@pytest.fixture
def sample_transactions():
    """Transações de exemplo para testes"""
    transactions = []
    
    # Janeiro - Receitas e Despesas
    for i in range(3):
        tx = Mock()
        tx.data_movimentacao = datetime(2025, 1, 15 + i)
        tx.valor = Decimal("1000.00")
        tx.transaction_type = TransactionType.RECEITA
        tx.is_active = True
        transactions.append(tx)
    
    for i in range(2):
        tx = Mock()
        tx.data_movimentacao = datetime(2025, 1, 20 + i)
        tx.valor = Decimal("500.00")
        tx.transaction_type = TransactionType.DESPESA
        tx.is_active = True
        transactions.append(tx)
    
    # Fevereiro - Apenas Custos
    for i in range(2):
        tx = Mock()
        tx.data_movimentacao = datetime(2025, 2, 10 + i)
        tx.valor = Decimal("200.00")
        tx.transaction_type = TransactionType.CUSTO
        tx.is_active = True
        transactions.append(tx)
    
    # Março - Vazio (sem lançamentos)
    
    # Abril - Mix completo
    tx = Mock()
    tx.data_movimentacao = datetime(2025, 4, 5)
    tx.valor = Decimal("5000.00")
    tx.transaction_type = TransactionType.RECEITA
    tx.is_active = True
    transactions.append(tx)
    
    tx = Mock()
    tx.data_movimentacao = datetime(2025, 4, 10)
    tx.valor = Decimal("2000.00")
    tx.transaction_type = TransactionType.DESPESA
    tx.is_active = True
    transactions.append(tx)
    
    tx = Mock()
    tx.data_movimentacao = datetime(2025, 4, 15)
    tx.valor = Decimal("1000.00")
    tx.transaction_type = TransactionType.CUSTO
    tx.is_active = True
    transactions.append(tx)
    
    return transactions


def test_aggregate_monthly_summary_with_transactions(mock_db, sample_transactions):
    """Testa agregação mensal com lançamentos"""
    # Configurar mock
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = sample_transactions
    mock_db.query.return_value = query_mock
    
    # Adicionar tenant_id e business_unit_id aos mocks das transações
    for tx in sample_transactions:
        tx.tenant_id = "test-tenant"
        tx.business_unit_id = "test-bu"
    
    # Executar
    result = FinancialAggregationService.aggregate_monthly_summary(
        db=mock_db,
        tenant_id="test-tenant",
        business_unit_id="test-bu",
        year=2025,
    )
    
    # Verificações
    assert result["year"] == 2025
    assert len(result["monthly"]) == 12
    
    # Janeiro: 3 receitas (3000) - 2 despesas (1000) = 2000
    jan = result["monthly"][0]
    assert jan["month"] == 1
    assert jan["revenue"] == 3000.0
    assert jan["expense"] == 1000.0
    assert jan["cost"] == 0.0
    assert jan["balance"] == 2000.0
    assert jan["accumulated_balance"] == 2000.0
    
    # Fevereiro: 0 receitas - 0 despesas - 2 custos (400) = -400
    feb = result["monthly"][1]
    assert feb["month"] == 2
    assert feb["revenue"] == 0.0
    assert feb["expense"] == 0.0
    assert feb["cost"] == 400.0
    assert feb["balance"] == -400.0
    assert feb["accumulated_balance"] == 1600.0  # 2000 - 400
    
    # Março: Vazio
    mar = result["monthly"][2]
    assert mar["month"] == 3
    assert mar["revenue"] == 0.0
    assert mar["expense"] == 0.0
    assert mar["cost"] == 0.0
    assert mar["balance"] == 0.0
    assert mar["accumulated_balance"] == 1600.0  # Mantém acumulado
    
    # Abril: 5000 receita - 2000 despesa - 1000 custo = 2000
    apr = result["monthly"][3]
    assert apr["month"] == 4
    assert apr["revenue"] == 5000.0
    assert apr["expense"] == 2000.0
    assert apr["cost"] == 1000.0
    assert apr["balance"] == 2000.0
    assert apr["accumulated_balance"] == 3600.0  # 1600 + 2000


def test_aggregate_monthly_summary_empty_year(mock_db):
    """Testa agregação para ano sem lançamentos"""
    # Configurar mock
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = []
    mock_db.query.return_value = query_mock
    
    # Executar
    result = FinancialAggregationService.aggregate_monthly_summary(
        db=mock_db,
        tenant_id="test-tenant",
        business_unit_id="test-bu",
        year=2025,
    )
    
    # Verificações
    assert result["year"] == 2025
    assert len(result["monthly"]) == 12
    
    # Todos os meses devem ter valores zero
    for month_data in result["monthly"]:
        assert month_data["revenue"] == 0.0
        assert month_data["expense"] == 0.0
        assert month_data["cost"] == 0.0
        assert month_data["balance"] == 0.0
        assert month_data["accumulated_balance"] == 0.0
    
    # Totais anuais devem ser zero
    assert result["totals"]["revenue"] == 0.0
    assert result["totals"]["expense"] == 0.0
    assert result["totals"]["cost"] == 0.0
    assert result["totals"]["balance"] == 0.0


def test_aggregate_monthly_summary_ignores_null_transaction_type(mock_db):
    """Testa que transações sem tipo são ignoradas"""
    transactions = []
    
    # Transação com tipo
    tx1 = Mock()
    tx1.data_movimentacao = datetime(2025, 1, 15)
    tx1.valor = Decimal("1000.00")
    tx1.transaction_type = TransactionType.RECEITA
    tx1.is_active = True
    transactions.append(tx1)
    
    # Transação sem tipo (deve ser ignorada)
    tx2 = Mock()
    tx2.data_movimentacao = datetime(2025, 1, 20)
    tx2.valor = Decimal("500.00")
    tx2.transaction_type = None
    tx2.is_active = True
    transactions.append(tx2)
    
    # Configurar mock
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = transactions
    mock_db.query.return_value = query_mock
    
    # Executar
    result = FinancialAggregationService.aggregate_monthly_summary(
        db=mock_db,
        tenant_id="test-tenant",
        business_unit_id="test-bu",
        year=2025,
    )
    
    # Apenas a transação com tipo deve ser contabilizada
    jan = result["monthly"][0]
    assert jan["revenue"] == 1000.0
    assert jan["expense"] == 0.0
    assert jan["cost"] == 0.0


def test_aggregate_monthly_summary_accumulated_balance_calculation(mock_db):
    """Testa cálculo correto do saldo acumulado"""
    transactions = []
    
    # Janeiro: +1000
    tx1 = Mock()
    tx1.data_movimentacao = datetime(2025, 1, 15)
    tx1.valor = Decimal("1000.00")
    tx1.transaction_type = TransactionType.RECEITA
    tx1.is_active = True
    transactions.append(tx1)
    
    # Fevereiro: -500
    tx2 = Mock()
    tx2.data_movimentacao = datetime(2025, 2, 10)
    tx2.valor = Decimal("500.00")
    tx2.transaction_type = TransactionType.DESPESA
    tx2.is_active = True
    transactions.append(tx2)
    
    # Março: +2000
    tx3 = Mock()
    tx3.data_movimentacao = datetime(2025, 3, 5)
    tx3.valor = Decimal("2000.00")
    tx3.transaction_type = TransactionType.RECEITA
    tx3.is_active = True
    transactions.append(tx3)
    
    # Configurar mock
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = transactions
    mock_db.query.return_value = query_mock
    
    # Executar
    result = FinancialAggregationService.aggregate_monthly_summary(
        db=mock_db,
        tenant_id="test-tenant",
        business_unit_id="test-bu",
        year=2025,
    )
    
    # Verificar saldo acumulado
    jan = result["monthly"][0]
    assert jan["balance"] == 1000.0
    assert jan["accumulated_balance"] == 1000.0
    
    feb = result["monthly"][1]
    assert feb["balance"] == -500.0
    assert feb["accumulated_balance"] == 500.0  # 1000 - 500
    
    mar = result["monthly"][2]
    assert mar["balance"] == 2000.0
    assert mar["accumulated_balance"] == 2500.0  # 500 + 2000


def test_aggregate_monthly_summary_annual_totals(mock_db, sample_transactions):
    """Testa cálculo correto dos totais anuais"""
    # Configurar mock
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = sample_transactions
    mock_db.query.return_value = query_mock
    
    # Executar
    result = FinancialAggregationService.aggregate_monthly_summary(
        db=mock_db,
        tenant_id="test-tenant",
        business_unit_id="test-bu",
        year=2025,
    )
    
    # Totais esperados:
    # Receita: 3000 (jan) + 0 (fev) + 0 (mar) + 5000 (abr) = 8000
    # Despesa: 1000 (jan) + 0 (fev) + 0 (mar) + 2000 (abr) = 3000
    # Custo: 0 (jan) + 400 (fev) + 0 (mar) + 1000 (abr) = 1400
    # Saldo: 8000 - 3000 - 1400 = 3600
    
    assert result["totals"]["revenue"] == 8000.0
    assert result["totals"]["expense"] == 3000.0
    assert result["totals"]["cost"] == 1400.0
    assert result["totals"]["balance"] == 3600.0


def test_get_debug_summary_structure(mock_db, sample_transactions):
    """Testa estrutura do endpoint de debug"""
    # Configurar mock
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = sample_transactions
    query_mock.count.return_value = len(sample_transactions)
    mock_db.query.return_value = query_mock
    
    # Mock para query SQL agregada
    sql_result_mock = Mock()
    sql_result_mock.month = 1
    sql_result_mock.transaction_type = TransactionType.RECEITA
    sql_result_mock.total = Decimal("3000.00")
    sql_result_mock.count = 3
    
    query_mock.group_by.return_value = query_mock
    query_mock.all.return_value = [sql_result_mock]
    
    # Executar
    result = FinancialAggregationService.get_debug_summary(
        db=mock_db,
        tenant_id="test-tenant",
        business_unit_id="test-bu",
        year=2025,
    )
    
    # Verificar estrutura
    assert "year" in result
    assert "tenant_id" in result
    assert "business_unit_id" in result
    assert "date_range" in result
    assert "total_transactions" in result
    assert "transactions_with_type" in result
    assert "annual_totals" in result
    assert "monthly_comparison" in result
    assert len(result["monthly_comparison"]) == 12


def test_accumulated_balance_with_empty_months(mock_db):
    """Testa que saldo acumulado se propaga em meses vazios"""
    transactions = []
    
    # Janeiro: +1000
    tx1 = Mock()
    tx1.data_movimentacao = datetime(2025, 1, 15)
    tx1.valor = Decimal("1000.00")
    tx1.transaction_type = TransactionType.RECEITA
    tx1.is_active = True
    transactions.append(tx1)
    
    # Fevereiro: vazio (sem lançamentos)
    # Março: vazio (sem lançamentos)
    
    # Abril: -500
    tx2 = Mock()
    tx2.data_movimentacao = datetime(2025, 4, 10)
    tx2.valor = Decimal("500.00")
    tx2.transaction_type = TransactionType.DESPESA
    tx2.is_active = True
    transactions.append(tx2)
    
    # Configurar mock
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = transactions
    mock_db.query.return_value = query_mock
    
    # Executar
    result = FinancialAggregationService.aggregate_monthly_summary(
        db=mock_db,
        tenant_id="test-tenant",
        business_unit_id="test-bu",
        year=2025,
    )
    
    # Janeiro: saldo = 1000, acumulado = 1000
    jan = result["monthly"][0]
    assert jan["balance"] == 1000.0
    assert jan["accumulated_balance"] == 1000.0
    
    # Fevereiro: saldo = 0, acumulado = 1000 (propaga)
    feb = result["monthly"][1]
    assert feb["balance"] == 0.0
    assert feb["accumulated_balance"] == 1000.0
    
    # Março: saldo = 0, acumulado = 1000 (propaga)
    mar = result["monthly"][2]
    assert mar["balance"] == 0.0
    assert mar["accumulated_balance"] == 1000.0
    
    # Abril: saldo = -500, acumulado = 500 (1000 - 500)
    apr = result["monthly"][3]
    assert apr["balance"] == -500.0
    assert apr["accumulated_balance"] == 500.0


def test_accumulated_balance_with_negative_values(mock_db):
    """Testa saldo acumulado com valores negativos"""
    transactions = []
    
    # Janeiro: -2000 (despesa maior que receita)
    tx1 = Mock()
    tx1.data_movimentacao = datetime(2025, 1, 5)
    tx1.valor = Decimal("1000.00")
    tx1.transaction_type = TransactionType.RECEITA
    tx1.is_active = True
    transactions.append(tx1)
    
    tx2 = Mock()
    tx2.data_movimentacao = datetime(2025, 1, 10)
    tx2.valor = Decimal("3000.00")
    tx2.transaction_type = TransactionType.DESPESA
    tx2.is_active = True
    transactions.append(tx2)
    
    # Fevereiro: +500
    tx3 = Mock()
    tx3.data_movimentacao = datetime(2025, 2, 5)
    tx3.valor = Decimal("500.00")
    tx3.transaction_type = TransactionType.RECEITA
    tx3.is_active = True
    transactions.append(tx3)
    
    # Configurar mock
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = transactions
    mock_db.query.return_value = query_mock
    
    # Executar
    result = FinancialAggregationService.aggregate_monthly_summary(
        db=mock_db,
        tenant_id="test-tenant",
        business_unit_id="test-bu",
        year=2025,
    )
    
    # Janeiro: 1000 - 3000 = -2000
    jan = result["monthly"][0]
    assert jan["balance"] == -2000.0
    assert jan["accumulated_balance"] == -2000.0
    
    # Fevereiro: +500, acumulado = -2000 + 500 = -1500
    feb = result["monthly"][1]
    assert feb["balance"] == 500.0
    assert feb["accumulated_balance"] == -1500.0


def test_accumulated_balance_sign_change(mock_db):
    """Testa virada de saldo (positivo → negativo e vice-versa)"""
    transactions = []
    
    # Janeiro: +1000 (positivo)
    tx1 = Mock()
    tx1.data_movimentacao = datetime(2025, 1, 5)
    tx1.valor = Decimal("1000.00")
    tx1.transaction_type = TransactionType.RECEITA
    tx1.is_active = True
    transactions.append(tx1)
    
    # Fevereiro: -1500 (vira negativo)
    tx2 = Mock()
    tx2.data_movimentacao = datetime(2025, 2, 5)
    tx2.valor = Decimal("1500.00")
    tx2.transaction_type = TransactionType.DESPESA
    tx2.is_active = True
    transactions.append(tx2)
    
    # Março: +2000 (volta a positivo)
    tx3 = Mock()
    tx3.data_movimentacao = datetime(2025, 3, 5)
    tx3.valor = Decimal("2000.00")
    tx3.transaction_type = TransactionType.RECEITA
    tx3.is_active = True
    transactions.append(tx3)
    
    # Configurar mock
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = transactions
    mock_db.query.return_value = query_mock
    
    # Executar
    result = FinancialAggregationService.aggregate_monthly_summary(
        db=mock_db,
        tenant_id="test-tenant",
        business_unit_id="test-bu",
        year=2025,
    )
    
    # Janeiro: +1000
    jan = result["monthly"][0]
    assert jan["balance"] == 1000.0
    assert jan["accumulated_balance"] == 1000.0
    
    # Fevereiro: -1500, acumulado = 1000 - 1500 = -500 (virada para negativo)
    feb = result["monthly"][1]
    assert feb["balance"] == -1500.0
    assert feb["accumulated_balance"] == -500.0
    
    # Março: +2000, acumulado = -500 + 2000 = 1500 (volta a positivo)
    mar = result["monthly"][2]
    assert mar["balance"] == 2000.0
    assert mar["accumulated_balance"] == 1500.0

