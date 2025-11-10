from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import User
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

router = APIRouter(tags=["dashboard"])


def _require_business_unit(user: User) -> str:
    business_unit_id = getattr(user, "business_unit_id", None)
    if not business_unit_id:
        raise HTTPException(
            status_code=400,
            detail="Usuário precisa selecionar uma unidade de negócio para acessar o dashboard.",
        )
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
            LancamentoDiario.business_unit_id == business_unit_id,
            LancamentoDiario.is_active.is_(True),
        )
    )

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
    """
    target_year = year or datetime.utcnow().year
    tenant_id = str(current_user.tenant_id)
    business_unit_id = _require_business_unit(current_user)

    start_dt = datetime(target_year, 1, 1)
    end_dt = datetime(target_year, 12, 31, 23, 59, 59)

    transactions: List[LancamentoDiario] = (
        db.query(LancamentoDiario)
        .filter(
            LancamentoDiario.tenant_id == tenant_id,
            LancamentoDiario.business_unit_id == business_unit_id,
            LancamentoDiario.is_active.is_(True),
            LancamentoDiario.data_movimentacao >= start_dt,
            LancamentoDiario.data_movimentacao <= end_dt,
        )
        .all()
    )

    monthly: Dict[int, Dict[str, float]] = {
        month: {"month": month, "revenue": 0.0, "expense": 0.0, "cost": 0.0}
        for month in range(1, 13)
    }

    for tx in transactions:
        if tx.transaction_type is None:
            continue
        month = tx.data_movimentacao.month
        amount = _decimal_to_float(tx.valor)
        if tx.transaction_type == TransactionType.RECEITA:
            monthly[month]["revenue"] += amount
        elif tx.transaction_type == TransactionType.DESPESA:
            monthly[month]["expense"] += amount
        elif tx.transaction_type == TransactionType.CUSTO:
            monthly[month]["cost"] += amount

    totals = {"revenue": 0.0, "expense": 0.0, "cost": 0.0}
    monthly_list: List[Dict[str, float]] = []
    for month in range(1, 13):
        bucket = monthly[month]
        totals["revenue"] += bucket["revenue"]
        totals["expense"] += bucket["expense"]
        totals["cost"] += bucket["cost"]
        monthly_list.append(bucket)

    return {
        "year": target_year,
        "totals": totals,
        "monthly": monthly_list,
    }


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

    bank_accounts = (
        db.query(ContaBancaria)
        .filter(
            ContaBancaria.tenant_id == tenant_id,
            ContaBancaria.business_unit_id == business_unit_id,
            ContaBancaria.is_active.is_(True),
        )
        .all()
    )
    cash_accounts = (
        db.query(Caixa)
        .filter(
            Caixa.tenant_id == tenant_id,
            Caixa.business_unit_id == business_unit_id,
            Caixa.is_active.is_(True),
        )
        .all()
    )
    investments = (
        db.query(Investimento)
        .filter(
            Investimento.tenant_id == tenant_id,
            Investimento.business_unit_id == business_unit_id,
            Investimento.is_active.is_(True),
        )
        .all()
    )

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

    transactions = (
        db.query(LancamentoDiario)
        .filter(
            LancamentoDiario.tenant_id == tenant_id,
            LancamentoDiario.business_unit_id == business_unit_id,
            LancamentoDiario.is_active.is_(True),
            LancamentoDiario.data_movimentacao >= start_dt,
            LancamentoDiario.data_movimentacao <= end_dt,
        )
        .all()
    )

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


def _empty_months() -> Dict[str, Dict[str, float]]:
    return {
        label: {"previsto": 0.0, "realizado": 0.0, "ah": 0.0, "av": 0.0}
        for label in MONTH_LABELS
    }


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

    def _load_entities(model, tenant_field):
        tenant_items = (
            db.query(model)
            .filter(
                tenant_field == tenant_id,
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
                tenant_field.is_(None),
                model.is_active.is_(True),
            )
            .order_by(model.code)
            .all()
        )

    groups = _load_entities(ChartAccountGroup, ChartAccountGroup.tenant_id)
    subgroups = _load_entities(ChartAccountSubgroup, ChartAccountSubgroup.tenant_id)
    accounts = _load_entities(ChartAccount, ChartAccount.tenant_id)

    subgroup_by_group: Dict[str, List[ChartAccountSubgroup]] = defaultdict(list)
    for sub in subgroups:
        subgroup_by_group[str(sub.group_id)].append(sub)

    account_by_subgroup: Dict[str, List[ChartAccount]] = defaultdict(list)
    for account in accounts:
        account_by_subgroup[str(account.subgroup_id)].append(account)

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
    realizados = (
        db.query(LancamentoDiario)
        .filter(
            LancamentoDiario.tenant_id == tenant_id,
            LancamentoDiario.business_unit_id == business_unit_id,
            LancamentoDiario.is_active.is_(True),
            LancamentoDiario.data_movimentacao >= start_dt,
            LancamentoDiario.data_movimentacao <= end_dt,
        )
        .all()
    )

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
    previstos = (
        db.query(LancamentoPrevisto)
        .filter(
            LancamentoPrevisto.tenant_id == tenant_id,
            LancamentoPrevisto.business_unit_id == business_unit_id,
            LancamentoPrevisto.is_active.is_(True),
            LancamentoPrevisto.data_prevista >= start_dt,
            LancamentoPrevisto.data_prevista <= end_dt,
        )
        .all()
    )

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

    contas_total = (
        db.query(func.sum(ContaBancaria.saldo_atual))
        .filter(
            ContaBancaria.tenant_id == tenant_id,
            ContaBancaria.business_unit_id == business_unit_id,
            ContaBancaria.is_active.is_(True),
        )
        .scalar()
    )
    caixas_total = (
        db.query(func.sum(Caixa.saldo_atual))
        .filter(
            Caixa.tenant_id == tenant_id,
            Caixa.business_unit_id == business_unit_id,
            Caixa.is_active.is_(True),
        )
        .scalar()
    )
    investimentos_total = (
        db.query(func.sum(Investimento.valor_atual))
        .filter(
            Investimento.tenant_id == tenant_id,
            Investimento.business_unit_id == business_unit_id,
            Investimento.is_active.is_(True),
        )
        .scalar()
    )

    contas = (
        db.query(ContaBancaria)
        .filter(
            ContaBancaria.tenant_id == tenant_id,
            ContaBancaria.business_unit_id == business_unit_id,
            ContaBancaria.is_active.is_(True),
        )
        .all()
    )
    caixas = (
        db.query(Caixa)
        .filter(
            Caixa.tenant_id == tenant_id,
            Caixa.business_unit_id == business_unit_id,
            Caixa.is_active.is_(True),
        )
        .all()
    )
    investimentos = (
        db.query(Investimento)
        .filter(
            Investimento.tenant_id == tenant_id,
            Investimento.business_unit_id == business_unit_id,
            Investimento.is_active.is_(True),
        )
        .all()
    )

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

    lancamentos = (
        db.query(LancamentoDiario)
        .filter(
            LancamentoDiario.tenant_id == tenant_id,
            LancamentoDiario.business_unit_id == business_unit_id,
            LancamentoDiario.is_active.is_(True),
        )
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

