from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
import calendar
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import User, UserRole, UserRole
from app.models.caixa import Caixa
from app.models.conta_bancaria import ContaBancaria
from app.models.investimento import Investimento
from app.models.chart_of_accounts import (
    ChartAccount,
    ChartAccountGroup,
    ChartAccountSubgroup,
)
from app.models.lancamento_diario import LancamentoDiario, TransactionType
from app.models.lancamento_previsto import LancamentoPrevisto
from app.services.dependencies import get_current_active_user
from app.services.financial_aggregation_service import FinancialAggregationService
from app.services.monthly_drilldown_service import MonthlyDrilldownService
from app.services.cash_flow_service import CashFlowService

router = APIRouter(tags=["dashboard"])


def _require_business_unit(user: User) -> Optional[str]:
    """
    Obtém o business_unit_id do usuário.
    Primeiro tenta obter do token (atualizado em get_current_user),
    depois do objeto user, e por último retorna None (permitindo acesso sem BU para super_admin).
    """
    # Primeiro, tentar obter do token (já atualizado em get_current_user)
    business_unit_id = getattr(user, "business_unit_id", None)
    
    # Se não tiver business_unit_id e não for super_admin, retornar erro
    if not business_unit_id:
        if user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=400,
                detail="Usuário precisa selecionar uma unidade de negócio para acessar o dashboard.",
            )
        # Para super_admin sem BU, usar None (permitir acesso sem filtro de BU)
        return None
    
    return str(business_unit_id)


def _decimal_to_float(value: Optional[Decimal]) -> float:
    if value is None:
        return 0.0
    return float(value)


MONTH_LABELS = [
    "JANEIRO",
    "FEVEREIRO",
    "MARÇO",
    "ABRIL",
    "MAIO",
    "JUNHO",
    "JULHO",
    "AGOSTO",
    "SETEMBRO",
    "OUTUBRO",
    "NOVEMBRO",
    "DEZEMBRO",
]


@router.get("/financial/transactions")
def list_transactions(
    year: Optional[int] = Query(default=None, ge=1900),
    limit: int = Query(default=10, ge=1, le=100),
    cursor: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Retorna as transações recentes do ano especificado.
    """
    target_year = year or datetime.utcnow().year
    tenant_id = str(current_user.tenant_id)
    business_unit_id = _require_business_unit(current_user)

    query = (
        db.query(LancamentoDiario)
        .filter(
            LancamentoDiario.tenant_id == tenant_id,
            LancamentoDiario.is_active.is_(True),
        )
    )
    
    # Filtrar por business_unit_id apenas se fornecido
    if business_unit_id:
        query = query.filter(LancamentoDiario.business_unit_id == business_unit_id)

    start_dt = datetime(target_year, 1, 1)
    end_dt = datetime(target_year, 12, 31, 23, 59, 59)
    query = query.filter(
        LancamentoDiario.data_movimentacao >= start_dt,
        LancamentoDiario.data_movimentacao <= end_dt,
    )

    if cursor:
        try:
            cursor_dt = datetime.fromisoformat(cursor.replace("Z", "+00:00"))
            query = query.filter(LancamentoDiario.data_movimentacao < cursor_dt)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Cursor inválido.") from exc

    query = query.order_by(
        LancamentoDiario.data_movimentacao.desc(), LancamentoDiario.created_at.desc()
    )
    items = query.limit(limit).all()

    def map_type(tx_type: Optional[TransactionType]) -> str:
        if tx_type == TransactionType.RECEITA:
            return "revenue"
        if tx_type == TransactionType.DESPESA:
            return "expense"
        if tx_type == TransactionType.CUSTO:
            return "cost"
        return "expense"

    formatted = [
        {
            "id": item.id,
            "date": item.data_movimentacao.isoformat(),
            "description": item.observacoes or "Lançamento",
            "type": map_type(item.transaction_type),
            "amount": _decimal_to_float(item.valor),
            "account": item.conta.name if getattr(item, "conta", None) else "Conta",
        }
        for item in items
    ]

    next_cursor: Optional[str] = None
    if items and len(items) == limit:
        next_cursor = items[-1].data_movimentacao.isoformat()

    return {
        "year": target_year,
        "items": formatted,
        "nextCursor": next_cursor,
    }


@router.get("/financial/annual-summary")
def annual_summary(
    year: Optional[int] = Query(default=None, ge=1900),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Consolida receitas, despesas e custos por mês para o ano informado.
    
    Retorna:
    - 12 meses completos (mesmo sem lançamentos)
    - Totais anuais de receita, despesa, custo e saldo
    - Saldo mensal e saldo acumulado por mês
    - Metadata explicativa das fórmulas de cálculo
    
    FÓRMULAS DE CÁLCULO:
    - receita = soma(lancamentos.tipo == RECEITA)
    - despesa = soma(lancamentos.tipo == DESPESA)
    - custo = soma(lancamentos.tipo == CUSTO)
    - saldo_mensal = receita - despesa - custo
    - saldo_acumulado[jan] = saldo_mensal[jan]
    - saldo_acumulado[fev] = saldo_acumulado[jan] + saldo_mensal[fev]
    - saldo_acumulado[mar] = saldo_acumulado[fev] + saldo_mensal[mar]
    - ... (soma progressiva)
    
    REGRAS IMPORTANTES:
    - Saldo acumulado sempre começa no primeiro mês do ano (janeiro)
    - Meses sem lançamentos: saldo_mensal = 0, saldo_acumulado se propaga
    - Todos os cálculos usam Decimal para precisão absoluta
    """
    target_year = year or datetime.utcnow().year
    tenant_id = str(current_user.tenant_id)
    business_unit_id = _require_business_unit(current_user)

    result = FinancialAggregationService.aggregate_monthly_summary(
        db=db,
        tenant_id=tenant_id,
        business_unit_id=business_unit_id,
        year=target_year,
    )
    
    # Adicionar metadata explicativa (BLOCO 2)
    result["metadata"] = {
        "saldo_formula": "receita - despesa - custo",
        "saldo_acumulado_formula": "soma progressiva dos saldos mensais",
        "saldo_acumulado_explanation": "O saldo acumulado de cada mês é a soma do saldo acumulado do mês anterior com o saldo mensal do mês atual. Janeiro não tem mês anterior, então o saldo acumulado é igual ao saldo mensal.",
        "calculation_precision": "Decimal (precisão absoluta)",
        "empty_months_behavior": "Meses sem lançamentos têm saldo_mensal = 0, mas o saldo_acumulado se propaga (mantém o valor do mês anterior)"
    }
    
    return result


@router.get("/financial/annual-summary/debug")
def annual_summary_debug(
    year: Optional[int] = Query(default=None, ge=1900),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Endpoint auxiliar para QA/Debug.
    
    Retorna comparação entre:
    - Agregação SQL direta (GROUP BY)
    - Agregação em memória (método atual)
    
    Útil para identificar discrepâncias entre métodos de cálculo.
    """
    target_year = year or datetime.utcnow().year
    tenant_id = str(current_user.tenant_id)
    business_unit_id = _require_business_unit(current_user)

    return FinancialAggregationService.get_debug_summary(
        db=db,
        tenant_id=tenant_id,
        business_unit_id=business_unit_id,
        year=target_year,
    )


@router.get("/financial/monthly-daily-summary")
def monthly_daily_summary(
    year: int = Query(..., ge=1900, description="Ano (ex: 2025)"),
    month: int = Query(..., ge=1, le=12, description="Mês (1-12)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Retorna resumo diário de um mês específico.
    
    Agrega receitas, despesas e custos por dia do mês informado.
    Os totais mensais DEVEM bater com o mês correspondente de /annual-summary.
    
    Retorna:
    - Lista de dias do mês (mesmo sem lançamentos)
    - Totais mensais de receita, despesa, custo e saldo
    - Metadata explicativa das fórmulas
    
    FÓRMULAS:
    - saldo_diário = receita - despesa - custo
    - month_total_* = soma dos dias do mês
    
    CONSISTÊNCIA:
    - month_total_* deve bater com monthly[month-1] de /annual-summary
    """
    tenant_id = str(current_user.tenant_id)
    business_unit_id = _require_business_unit(current_user)
    
    try:
        result = MonthlyDrilldownService.aggregate_daily_summary(
            db=db,
            tenant_id=tenant_id,
            business_unit_id=business_unit_id,
            year=year,
            month=month,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular resumo diário: {str(e)}")


@router.get("/financial/monthly-transactions")
def monthly_transactions(
    year: int = Query(..., ge=1900, description="Ano (ex: 2025)"),
    month: int = Query(..., ge=1, le=12, description="Mês (1-12)"),
    type: Optional[str] = Query(None, description="Tipo: RECEITA, DESPESA ou CUSTO"),
    group_id: Optional[str] = Query(None, description="ID do grupo"),
    subgroup_id: Optional[str] = Query(None, description="ID do subgrupo"),
    account_id: Optional[str] = Query(None, description="ID da conta"),
    page: int = Query(1, ge=1, description="Página (começa em 1)"),
    page_size: int = Query(50, ge=1, le=200, description="Itens por página (máx 200)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Retorna lançamentos detalhados de um mês específico com filtros e paginação.
    
    Parâmetros:
    - year, month: obrigatórios
    - type: opcional (RECEITA, DESPESA, CUSTO)
    - group_id, subgroup_id, account_id: filtros opcionais
    - page, page_size: paginação
    
    Retorna:
    - Lista paginada de lançamentos
    - Summary com totais do mês (considerando filtros)
    - Metadados de paginação
    
    CONSISTÊNCIA:
    - Se nenhum filtro for aplicado, summary.* deve bater com monthly[month-1] de /annual-summary
    - A soma dos items retornados (dentro da página) é parcial
    - O summary.* é o total do mês considerando os filtros aplicados
    """
    tenant_id = str(current_user.tenant_id)
    business_unit_id = _require_business_unit(current_user)
    
    # Converter type string para enum
    transaction_type = None
    if type:
        try:
            transaction_type = TransactionType(type.upper())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo inválido: {type}. Use RECEITA, DESPESA ou CUSTO."
            )
    
    try:
        result = MonthlyDrilldownService.get_monthly_transactions(
            db=db,
            tenant_id=tenant_id,
            business_unit_id=business_unit_id,
            year=year,
            month=month,
            transaction_type=transaction_type,
            group_id=group_id,
            subgroup_id=subgroup_id,
            account_id=account_id,
            page=page,
            page_size=page_size,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar lançamentos: {str(e)}")


@router.get("/financial/wallet")
def wallet_overview(
    year: Optional[int] = Query(default=None, ge=1900),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Retorna os saldos consolidados de contas bancárias, caixas e investimentos.
    O parâmetro `year` é aceito apenas para compatibilidade com o frontend.
    """
    _ = year  # Mantido para compatibilidade; dados não são segmentados por ano.

    tenant_id = str(current_user.tenant_id)
    business_unit_id = _require_business_unit(current_user)

    bank_query = (
        db.query(ContaBancaria)
        .filter(
            ContaBancaria.tenant_id == tenant_id,
            ContaBancaria.is_active.is_(True),
        )
    )
    if business_unit_id:
        bank_query = bank_query.filter(ContaBancaria.business_unit_id == business_unit_id)
    bank_accounts = bank_query.all()
    
    cash_query = (
        db.query(Caixa)
        .filter(
            Caixa.tenant_id == tenant_id,
            Caixa.is_active.is_(True),
        )
    )
    if business_unit_id:
        cash_query = cash_query.filter(Caixa.business_unit_id == business_unit_id)
    cash_accounts = cash_query.all()
    
    investment_query = (
        db.query(Investimento)
        .filter(
            Investimento.tenant_id == tenant_id,
            Investimento.is_active.is_(True),
        )
    )
    if business_unit_id:
        investment_query = investment_query.filter(Investimento.business_unit_id == business_unit_id)
    investments = investment_query.all()

    bank_payload = [
        {"label": account.banco, "amount": _decimal_to_float(account.saldo_atual)}
        for account in bank_accounts
    ]
    cash_payload = [
        {"label": cash.nome, "amount": _decimal_to_float(cash.saldo_atual)}
        for cash in cash_accounts
    ]
    investment_payload = [
        {"label": investment.tipo, "amount": _decimal_to_float(investment.valor_atual)}
        for investment in investments
    ]

    total_available = (
        sum(item["amount"] for item in bank_payload)
        + sum(item["amount"] for item in cash_payload)
        + sum(item["amount"] for item in investment_payload)
    )

    return {
        "year": year or datetime.utcnow().year,
        "bankAccounts": bank_payload,
        "cash": cash_payload,
        "investments": investment_payload,
        "totalAvailable": total_available,
    }


@router.get("/financial/cash-flow")
def cash_flow(
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    group_id: Optional[str] = Query(default=None, description="ID do grupo"),
    subgroup_id: Optional[str] = Query(default=None, description="ID do subgrupo"),
    account_id: Optional[str] = Query(default=None, description="ID da conta"),
    transaction_type: Optional[str] = Query(default=None, description="Tipo de transação"),
    status: Optional[str] = Query(default=None, description="Status (previsto/realizado)"),
    cost_center_id: Optional[str] = Query(default=None, description="ID do centro de custo"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """
    Retorna o fluxo de caixa diário dentro do intervalo informado.
    Se não informado, considera os últimos 30 dias.
    """
    now = datetime.utcnow()
    end_dt = (
        datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        if end_date
        else now
    )
    start_dt = (
        datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        if start_date
        else end_dt - timedelta(days=30)
    )

    tenant_id = str(current_user.tenant_id)
    business_unit_id = _require_business_unit(current_user)

    query = (
        db.query(LancamentoDiario)
        .filter(
            LancamentoDiario.tenant_id == tenant_id,
            LancamentoDiario.is_active.is_(True),
            LancamentoDiario.data_movimentacao >= start_dt,
            LancamentoDiario.data_movimentacao <= end_dt,
        )
    )
    
    # Filtrar por business_unit_id apenas se fornecido
    if business_unit_id:
        query = query.filter(LancamentoDiario.business_unit_id == business_unit_id)
    
    # Aplicar filtros adicionais
    if group_id:
        query = query.filter(LancamentoDiario.grupo_id == group_id)
    if subgroup_id:
        query = query.filter(LancamentoDiario.subgrupo_id == subgroup_id)
    if account_id:
        query = query.filter(LancamentoDiario.conta_id == account_id)
    if transaction_type:
        from app.models.lancamento_diario import TransactionType
        try:
            tipo_enum = TransactionType(transaction_type)
            query = query.filter(LancamentoDiario.transaction_type == tipo_enum)
        except ValueError:
            query = query.filter(LancamentoDiario.transaction_type == transaction_type)
    if status:
        from app.models.lancamento_diario import TransactionStatus
        try:
            status_enum = TransactionStatus(status)
            query = query.filter(LancamentoDiario.status == status_enum)
        except ValueError:
            query = query.filter(LancamentoDiario.status == status)
    # cost_center_id - preparar campo mesmo se não implementado ainda
    # if cost_center_id:
    #     query = query.filter(LancamentoDiario.cost_center_id == cost_center_id)
    
    transactions = query.all()

    daily_totals: Dict[str, Dict[str, float]] = defaultdict(
        lambda: {
            "total_revenue": 0.0,
            "total_expenses": 0.0,
            "total_costs": 0.0,
        }
    )

    for tx in transactions:
        date_key = tx.data_movimentacao.date().isoformat()
        amount = _decimal_to_float(tx.valor)
        if tx.transaction_type == TransactionType.RECEITA:
            daily_totals[date_key]["total_revenue"] += amount
        elif tx.transaction_type == TransactionType.DESPESA:
            daily_totals[date_key]["total_expenses"] += amount
        elif tx.transaction_type == TransactionType.CUSTO:
            daily_totals[date_key]["total_costs"] += amount

    payload: List[Dict[str, Any]] = []
    for day in sorted(daily_totals.keys()):
        totals = daily_totals[day]
        payload.append(
            {
                "date": day,
                "total_revenue": totals["total_revenue"],
                "total_expenses": totals["total_expenses"],
                "total_costs": totals["total_costs"],
                "net_flow": totals["total_revenue"]
                - totals["total_expenses"]
                - totals["total_costs"],
            }
        )

    return payload


def _load_plan_structure(
    db: Session, tenant_id: str
) -> tuple[
    List[ChartAccountGroup],
    List[ChartAccountSubgroup],
    List[ChartAccount],
    Dict[str, List[ChartAccountSubgroup]],
    Dict[str, List[ChartAccount]],
]:
    def _load(model):
        tenant_items = (
            db.query(model)
            .filter(
                model.tenant_id == tenant_id,
                model.is_active.is_(True),
            )
            .order_by(model.code)
            .all()
        )
        if tenant_items:
            return tenant_items
        return (
            db.query(model)
            .filter(
                model.tenant_id.is_(None),
                model.is_active.is_(True),
            )
            .order_by(model.code)
            .all()
        )

    groups = _load(ChartAccountGroup)
    subgroups = _load(ChartAccountSubgroup)
    accounts = _load(ChartAccount)

    subgroup_by_group: Dict[str, List[ChartAccountSubgroup]] = defaultdict(list)
    for sub in subgroups:
        subgroup_by_group[str(sub.group_id)].append(sub)

    account_by_subgroup: Dict[str, List[ChartAccount]] = defaultdict(list)
    for account in accounts:
        account_by_subgroup[str(account.subgroup_id)].append(account)

    return groups, subgroups, accounts, subgroup_by_group, account_by_subgroup


def _empty_months() -> Dict[str, Dict[str, float]]:
    return {
        label: {"previsto": 0.0, "realizado": 0.0, "ah": 0.0, "av": 0.0}
        for label in MONTH_LABELS
    }


def _empty_days(last_day: int) -> Dict[int, float]:
    return {day: 0.0 for day in range(1, last_day + 1)}


@router.get("/cash-flow/previsto-realizado")
def cash_flow_previsto_realizado(
    year: Optional[int] = Query(default=None, ge=1900),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Compara valores previstos (planilha de previsões) e realizados (lançamentos diários)
    agrupando por plano de contas (grupo → subgrupo → conta) por mês.
    """
    target_year = year or datetime.utcnow().year
    tenant_id = str(current_user.tenant_id)
    business_unit_id = _require_business_unit(current_user)

    start_dt = datetime(target_year, 1, 1)
    end_dt = datetime(target_year, 12, 31, 23, 59, 59)

    (
        groups,
        subgroups,
        accounts,
        subgroup_by_group,
        account_by_subgroup,
    ) = _load_plan_structure(db, tenant_id)

    rows: List[Dict[str, Any]] = []
    group_rows: Dict[str, Dict[str, Any]] = {}
    subgroup_rows: Dict[str, Dict[str, Any]] = {}
    account_rows: Dict[str, Dict[str, Any]] = {}

    def _make_row(name: str, level: int) -> Dict[str, Any]:
        return {"categoria": name, "nivel": level, "meses": _empty_months()}

    for group in groups:
        group_id = str(group.id)
        group_row = _make_row(group.name, 0)
        rows.append(group_row)
        group_rows[group_id] = group_row

        for sub in subgroup_by_group.get(group_id, []):
            sub_id = str(sub.id)
            sub_row = _make_row(sub.name, 1)
            rows.append(sub_row)
            subgroup_rows[sub_id] = sub_row

            for account in account_by_subgroup.get(sub_id, []):
                account_id = str(account.id)
                acc_row = _make_row(account.name, 2)
                rows.append(acc_row)
                account_rows[account_id] = acc_row

    # Realizados
    realizados_query = (
        db.query(LancamentoDiario)
        .filter(
            LancamentoDiario.tenant_id == tenant_id,
            LancamentoDiario.is_active.is_(True),
            LancamentoDiario.data_movimentacao >= start_dt,
            LancamentoDiario.data_movimentacao <= end_dt,
        )
    )
    if business_unit_id:
        realizados_query = realizados_query.filter(LancamentoDiario.business_unit_id == business_unit_id)
    realizados = realizados_query.all()

    for tx in realizados:
        month_label = MONTH_LABELS[tx.data_movimentacao.month - 1]
        amount = _decimal_to_float(tx.valor)
        conta_row = account_rows.get(str(tx.conta_id))
        if conta_row:
            conta_row["meses"][month_label]["realizado"] += amount
        sub_row = subgroup_rows.get(str(tx.subgrupo_id))
        if sub_row:
            sub_row["meses"][month_label]["realizado"] += amount
        grp_row = group_rows.get(str(tx.grupo_id))
        if grp_row:
            grp_row["meses"][month_label]["realizado"] += amount

    # Previsto
    previstos_query = (
        db.query(LancamentoPrevisto)
        .filter(
            LancamentoPrevisto.tenant_id == tenant_id,
            LancamentoPrevisto.is_active.is_(True),
            LancamentoPrevisto.data_prevista >= start_dt,
            LancamentoPrevisto.data_prevista <= end_dt,
        )
    )
    if business_unit_id:
        previstos_query = previstos_query.filter(LancamentoPrevisto.business_unit_id == business_unit_id)
    previstos = previstos_query.all()

    for forecast in previstos:
        month_label = MONTH_LABELS[forecast.data_prevista.month - 1]
        amount = _decimal_to_float(forecast.valor)
        conta_row = account_rows.get(str(forecast.conta_id))
        if conta_row:
            conta_row["meses"][month_label]["previsto"] += amount
        sub_row = subgroup_rows.get(str(forecast.subgrupo_id))
        if sub_row:
            sub_row["meses"][month_label]["previsto"] += amount
        grp_row = group_rows.get(str(forecast.grupo_id))
        if grp_row:
            grp_row["meses"][month_label]["previsto"] += amount

    # Totais por mês para cálculo da análise vertical
    total_realizado_por_mes: Dict[str, float] = {
        label: sum(
            row["meses"][label]["realizado"]
            for row in rows
            if row["nivel"] == 0
        )
        for label in MONTH_LABELS
    }

    for row in rows:
        for month_label in MONTH_LABELS:
            bucket = row["meses"][month_label]
            previsto = bucket["previsto"]
            realizado = bucket["realizado"]
            if previsto > 0:
                bucket["ah"] = (realizado / previsto) * 100
            elif realizado > 0:
                bucket["ah"] = 100.0
            else:
                bucket["ah"] = 0.0

            total_mes = total_realizado_por_mes.get(month_label, 0.0)
            if total_mes > 0:
                bucket["av"] = (realizado / total_mes) * 100
            else:
                bucket["av"] = 0.0

    return {
        "success": True,
        "year": target_year,
        "data": rows,
    }


@router.get("/cash-flow/daily")
def cash_flow_daily(
    year: Optional[int] = Query(default=None, ge=1900),
    month: Optional[int] = Query(default=None, ge=1, le=12),
    group_id: Optional[str] = Query(default=None, description="ID do grupo"),
    subgroup_id: Optional[str] = Query(default=None, description="ID do subgrupo"),
    account_id: Optional[str] = Query(default=None, description="ID da conta"),
    transaction_type: Optional[str] = Query(default=None, description="Tipo de transação"),
    status: Optional[str] = Query(default=None, description="Status"),
    cost_center_id: Optional[str] = Query(default=None, description="ID do centro de custo"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Fluxo de caixa diário agregando valores realizados por grupo/subgrupo/conta.
    
    Replica fielmente a estrutura e ordem da planilha do cliente:
    - Ordem explícita dos grupos (não alfabética)
    - Todas as contas aparecem mesmo quando zeradas
    - Subtotais calculados (Receita Líquida, Lucro Bruto, etc.)
    - Estrutura hierárquica completa
    """
    today = datetime.utcnow()
    target_year = year or today.year
    target_month = month or today.month

    if target_month < 1 or target_month > 12:
        raise HTTPException(status_code=400, detail="Mês inválido.")

    tenant_id = str(current_user.tenant_id)
    business_unit_id = _require_business_unit(current_user)

    try:
        result = CashFlowService.get_monthly_cash_flow(
            db=db,
            tenant_id=tenant_id,
            business_unit_id=business_unit_id,
            year=target_year,
            month=target_month,
        )
        
        return {
            "success": True,
            "year": result["year"],
            "month": result["month"],
            "days_in_month": result["days_in_month"],
            "data": result["rows"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Erro ao gerar fluxo de caixa: {e}")
        print(f"📋 Traceback:\n{error_trace}")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar fluxo de caixa: {str(e)}")


@router.get("/saldo-disponivel")
def saldo_disponivel(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Endpoint de compatibilidade utilizado pelo frontend para fallback de carteira.
    """
    tenant_id = str(current_user.tenant_id)
    business_unit_id = _require_business_unit(current_user)

    contas_query = (
        db.query(func.sum(ContaBancaria.saldo_atual))
        .filter(
            ContaBancaria.tenant_id == tenant_id,
            ContaBancaria.is_active.is_(True),
        )
    )
    if business_unit_id:
        contas_query = contas_query.filter(ContaBancaria.business_unit_id == business_unit_id)
    contas_total = contas_query.scalar()
    
    caixas_query = (
        db.query(func.sum(Caixa.saldo_atual))
        .filter(
            Caixa.tenant_id == tenant_id,
            Caixa.is_active.is_(True),
        )
    )
    if business_unit_id:
        caixas_query = caixas_query.filter(Caixa.business_unit_id == business_unit_id)
    caixas_total = caixas_query.scalar()
    
    investimentos_query = (
        db.query(func.sum(Investimento.valor_atual))
        .filter(
            Investimento.tenant_id == tenant_id,
            Investimento.is_active.is_(True),
        )
    )
    if business_unit_id:
        investimentos_query = investimentos_query.filter(Investimento.business_unit_id == business_unit_id)
    investimentos_total = investimentos_query.scalar()

    contas_filter = (
        db.query(ContaBancaria)
        .filter(
            ContaBancaria.tenant_id == tenant_id,
            ContaBancaria.is_active.is_(True),
        )
    )
    if business_unit_id:
        contas_filter = contas_filter.filter(ContaBancaria.business_unit_id == business_unit_id)
    contas = contas_filter.all()
    
    caixas_filter = (
        db.query(Caixa)
        .filter(
            Caixa.tenant_id == tenant_id,
            Caixa.is_active.is_(True),
        )
    )
    if business_unit_id:
        caixas_filter = caixas_filter.filter(Caixa.business_unit_id == business_unit_id)
    caixas = caixas_filter.all()
    
    investimentos_filter = (
        db.query(Investimento)
        .filter(
            Investimento.tenant_id == tenant_id,
            Investimento.is_active.is_(True),
        )
    )
    if business_unit_id:
        investimentos_filter = investimentos_filter.filter(Investimento.business_unit_id == business_unit_id)
    investimentos = investimentos_filter.all()

    total_contas = _decimal_to_float(contas_total)
    total_caixas = _decimal_to_float(caixas_total)
    total_investimentos = _decimal_to_float(investimentos_total)

    return {
        "success": True,
        "saldo_disponivel": {
            "contas_bancarias": {
                "total": total_contas,
                "detalhes": [
                    {"banco": conta.banco, "saldo": _decimal_to_float(conta.saldo_atual)}
                    for conta in contas
                ],
            },
            "caixas": {
                "total": total_caixas,
                "detalhes": [
                    {"nome": caixa.nome, "saldo": _decimal_to_float(caixa.saldo_atual)}
                    for caixa in caixas
                ],
            },
            "investimentos": {
                "total": total_investimentos,
                "detalhes": [
                    {
                        "tipo": investimento.tipo,
                        "instituicao": investimento.instituicao,
                        "valor": _decimal_to_float(investimento.valor_atual),
                    }
                    for investimento in investimentos
                ],
            },
            "total_geral": total_contas + total_caixas + total_investimentos,
        },
    }


@router.get("/lancamentos-diarios")
def listar_lancamentos_simples(
    limit: int = Query(default=100, ge=1, le=10000),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """
    Retorna uma lista simplificada de lançamentos diários.
    Utilizado como fallback pelo frontend.
    """
    tenant_id = str(current_user.tenant_id)
    business_unit_id = _require_business_unit(current_user)

    query = (
        db.query(LancamentoDiario)
        .filter(
            LancamentoDiario.tenant_id == tenant_id,
            LancamentoDiario.is_active.is_(True),
        )
    )
    if business_unit_id:
        query = query.filter(LancamentoDiario.business_unit_id == business_unit_id)
    
    lancamentos = (
        query
        .order_by(LancamentoDiario.data_movimentacao.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": lanc.id,
            "data_movimentacao": lanc.data_movimentacao.isoformat(),
            "valor": _decimal_to_float(lanc.valor),
            "observacoes": lanc.observacoes,
            "transaction_type": lanc.transaction_type.value if lanc.transaction_type else None,
            "conta": {
                "id": lanc.conta_id,
                "name": lanc.conta.name if getattr(lanc, "conta", None) else None,
            },
        }
        for lanc in lancamentos
    ]

