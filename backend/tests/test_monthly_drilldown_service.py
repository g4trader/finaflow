"""
Testes unitários para MonthlyDrilldownService

Cobre:
- Agregação diária com lançamentos
- Agregação diária sem lançamentos
- Totais mensais consistentes
- Lançamentos detalhados com filtros
- Paginação
"""

import pytest
import os
import sys
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from unittest.mock import Mock, MagicMock

# Mock do database antes de importar qualquer módulo que use app.database
mock_database = MagicMock()
mock_database.SessionLocal = MagicMock()
sys.modules['app.database'] = mock_database

os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost/test'

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


def test_aggregate_daily_summary_with_transactions(mock_db, sample_transactions_january):
    """Testa agregação diária com lançamentos"""
    # Configurar mock
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = sample_transactions_january
    mock_db.query.return_value = query_mock
    
    # Executar
    result = MonthlyDrilldownService.aggregate_daily_summary(
        db=mock_db,
        tenant_id="test-tenant",
        business_unit_id="test-bu",
        year=2025,
        month=1,
    )
    
    # Verificações
    assert result["year"] == 2025
    assert result["month"] == 1
    assert result["currency"] == "BRL"
    assert len(result["days"]) == 31  # Janeiro tem 31 dias
    
    # Dia 1: 1000 receita - 500 despesa = 500
    day1 = result["days"][0]
    assert day1["day"] == 1
    assert day1["revenue"] == "1000.00"
    assert day1["expense"] == "500.00"
    assert day1["cost"] == "0"
    assert day1["balance"] == "500.00"
    
    # Dia 5: 2000 receita - 0 despesa - 300 custo = 1700
    day5 = result["days"][4]
    assert day5["day"] == 5
    assert day5["revenue"] == "2000.00"
    assert day5["expense"] == "0"
    assert day5["cost"] == "300.00"
    assert day5["balance"] == "1700.00"
    
    # Totais mensais
    assert result["metadata"]["month_total_revenue"] == "3000.00"
    assert result["metadata"]["month_total_expense"] == "500.00"
    assert result["metadata"]["month_total_cost"] == "300.00"
    assert result["metadata"]["month_total_balance"] == "2200.00"


def test_aggregate_daily_summary_empty_month(mock_db):
    """Testa agregação diária para mês sem lançamentos"""
    # Configurar mock
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = []
    mock_db.query.return_value = query_mock
    
    # Executar
    result = MonthlyDrilldownService.aggregate_daily_summary(
        db=mock_db,
        tenant_id="test-tenant",
        business_unit_id="test-bu",
        year=2025,
        month=2,  # Fevereiro (28 dias em 2025)
    )
    
    # Verificações
    assert result["year"] == 2025
    assert result["month"] == 2
    assert len(result["days"]) == 28  # Fevereiro tem 28 dias em 2025
    
    # Todos os dias devem ter valores zero
    for day_data in result["days"]:
        assert day_data["revenue"] == "0"
        assert day_data["expense"] == "0"
        assert day_data["cost"] == "0"
        assert day_data["balance"] == "0"
    
    # Totais mensais devem ser zero
    assert result["metadata"]["month_total_revenue"] == "0"
    assert result["metadata"]["month_total_expense"] == "0"
    assert result["metadata"]["month_total_cost"] == "0"
    assert result["metadata"]["month_total_balance"] == "0"


def test_aggregate_daily_summary_invalid_month(mock_db):
    """Testa validação de mês inválido"""
    query_mock = Mock()
    mock_db.query.return_value = query_mock
    
    # Mês inválido: 0
    with pytest.raises(ValueError, match="Mês inválido"):
        MonthlyDrilldownService.aggregate_daily_summary(
            db=mock_db,
            tenant_id="test-tenant",
            business_unit_id="test-bu",
            year=2025,
            month=0,
        )
    
    # Mês inválido: 13
    with pytest.raises(ValueError, match="Mês inválido"):
        MonthlyDrilldownService.aggregate_daily_summary(
            db=mock_db,
            tenant_id="test-tenant",
            business_unit_id="test-bu",
            year=2025,
            month=13,
        )


def test_get_monthly_transactions_without_filters(mock_db, sample_transactions_january):
    """Testa busca de lançamentos sem filtros"""
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
    
    # Executar
    result = MonthlyDrilldownService.get_monthly_transactions(
        db=mock_db,
        tenant_id="test-tenant",
        business_unit_id="test-bu",
        year=2025,
        month=1,
        page=1,
        page_size=50,
    )
    
    # Verificações
    assert result["year"] == 2025
    assert result["month"] == 1
    assert result["page"] == 1
    assert result["page_size"] == 50
    assert result["total_items"] == 4
    assert result["total_pages"] == 1
    
    # Summary deve bater com os totais
    assert result["summary"]["revenue"] == "3000.00"
    assert result["summary"]["expense"] == "500.00"
    assert result["summary"]["cost"] == "300.00"
    assert result["summary"]["balance"] == "2200.00"
    
    # Items
    assert len(result["items"]) == 4


def test_get_monthly_transactions_with_type_filter(mock_db, sample_transactions_january):
    """Testa busca de lançamentos com filtro por tipo"""
    # Filtrar apenas receitas
    receitas = [tx for tx in sample_transactions_january if tx.transaction_type == TransactionType.RECEITA]
    
    for tx in receitas:
        tx.id = f"tx-{tx.data_movimentacao.day}"
        tx.observacoes = f"Receita dia {tx.data_movimentacao.day}"
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
    query_mock.count.return_value = len(receitas)
    query_mock.all.return_value = receitas
    mock_db.query.return_value = query_mock
    
    # Executar
    result = MonthlyDrilldownService.get_monthly_transactions(
        db=mock_db,
        tenant_id="test-tenant",
        business_unit_id="test-bu",
        year=2025,
        month=1,
        transaction_type=TransactionType.RECEITA,
        page=1,
        page_size=50,
    )
    
    # Verificações
    assert result["total_items"] == 2  # Apenas receitas
    assert result["summary"]["revenue"] == "3000.00"
    assert result["summary"]["expense"] == "0"
    assert result["summary"]["cost"] == "0"
    assert result["summary"]["balance"] == "3000.00"


def test_get_monthly_transactions_pagination(mock_db):
    """Testa paginação de lançamentos"""
    # Criar 100 transações mock
    transactions = []
    for i in range(100):
        tx = Mock()
        tx.data_movimentacao = datetime(2025, 1, 1 + (i % 31), 10, 0)
        tx.valor = Decimal("100.00")
        tx.transaction_type = TransactionType.RECEITA
        tx.is_active = True
        tx.id = f"tx-{i}"
        tx.observacoes = f"Lançamento {i}"
        tx.grupo = Mock()
        tx.grupo.name = "Grupo"
        tx.subgrupo = Mock()
        tx.subgrupo.name = "Subgrupo"
        tx.conta = Mock()
        tx.conta.name = "Conta"
        transactions.append(tx)
    
    # Configurar mock
    query_mock = Mock()
    query_mock.options.return_value = query_mock
    query_mock.filter.return_value = query_mock
    query_mock.order_by.return_value = query_mock
    query_mock.offset.return_value = query_mock
    query_mock.limit.return_value = query_mock
    query_mock.count.return_value = 100
    query_mock.all.return_value = transactions[:50]  # Primeira página
    mock_db.query.return_value = query_mock
    
    # Executar página 1
    result = MonthlyDrilldownService.get_monthly_transactions(
        db=mock_db,
        tenant_id="test-tenant",
        business_unit_id="test-bu",
        year=2025,
        month=1,
        page=1,
        page_size=50,
    )
    
    # Verificações
    assert result["total_items"] == 100
    assert result["total_pages"] == 2  # 100 / 50 = 2 páginas
    assert result["page"] == 1
    assert result["page_size"] == 50
    assert len(result["items"]) == 50

