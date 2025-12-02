"""
API de gestão de Investimentos.

Nenhum dado é mockado: os endpoints respondem com valores persistidos no banco
ou com totais extraídos da planilha oficial.
"""

from __future__ import annotations

import calendar
import unicodedata
from collections import defaultdict
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from googleapiclient.errors import HttpError
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.dependencies import get_current_active_user
from app.config import Settings
from app.models.investimento import Investimento, TipoInvestimento
from app.models.auth import User
from app.services.llm_sheet_importer import LLMSheetImporter

router = APIRouter(prefix="/api/v1/investimentos", tags=["Investimentos"])

MONTH_SHEETS = [
    ("Jan2025", 1),
    ("Fev2025", 2),
    ("Mar2025", 3),
    ("Abr2025", 4),
    ("Mai2025", 5),
    ("Jun2025", 6),
    ("Jul2025", 7),
    ("Ago2025", 8),
    ("Set2025", 9),
    ("Out2025", 10),
    ("Nov2025", 11),
    ("Dez2025", 12),
]

INVESTMENT_LABELS = {"aplicacao", "aplicacao2", "investimento", "investimentos"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalize_label(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return "".join(ch for ch in ascii_only.lower().strip() if ch not in {" ", "-", "_", "/", "(", ")"})


def _get_spreadsheet_id() -> str:
    settings = Settings()
    if settings.SPREADSHEET_ID:
        return settings.SPREADSHEET_ID
    return "1rWMdDhwiNoC7iMycmQGWWDIacrePr1gB7c_mbt1patQ"


def _require_business_unit(current_user: User) -> str:
    business_unit_id = getattr(current_user, "business_unit_id", None)
    if not business_unit_id:
        raise HTTPException(
            status_code=400,
            detail="Selecione uma unidade de negócios antes de acessar os dados.",
        )
    return str(business_unit_id)


def _decimal_to_float(value: Decimal | None) -> float:
    return float(value or Decimal("0"))


def _parse_sheet_amount(value: str) -> Decimal:
    cleaned = value.replace("R$", "").replace(".", "").replace(" ", "").replace(",", ".")
    if cleaned in {"", "-", "--"}:
        return Decimal("0")
    return Decimal(cleaned)


def _collect_sheet_balances(
    labels: List[str],
    start: datetime,
    end: datetime,
) -> Dict[date, Decimal]:
    importer = LLMSheetImporter()
    if not importer.authenticate():
        return {}

    spreadsheet_id = _get_spreadsheet_id()
    normalized_targets = {_normalize_label(label) for label in labels}

    balances: Dict[date, Decimal] = defaultdict(lambda: Decimal("0"))

    month_cursor = datetime(start.year, start.month, 1)
    final_month = datetime(end.year, end.month, 1)

    while month_cursor <= final_month:
        sheet_suffix = next(
            (suffix for suffix, number in MONTH_SHEETS if number == month_cursor.month),
            None,
        )
        if not sheet_suffix:
            month_cursor = (month_cursor.replace(day=28) + timedelta(days=4)).replace(day=1)
            continue

        try:
            result = importer.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=f"'FC-diário-{sheet_suffix}'!B174:AF184",
            ).execute()
        except HttpError:
            month_cursor = (month_cursor.replace(day=28) + timedelta(days=4)).replace(day=1)
            continue

        rows = result.get("values", [])
        relevant_rows = [
            row for row in rows if row and _normalize_label(row[0]) in normalized_targets
        ]

        if not relevant_rows:
            month_cursor = (month_cursor.replace(day=28) + timedelta(days=4)).replace(day=1)
            continue

        days_in_month = calendar.monthrange(month_cursor.year, month_cursor.month)[1]
        for day_index in range(1, days_in_month + 1):
            try:
                current_date = datetime(month_cursor.year, month_cursor.month, day_index).date()
            except ValueError:
                continue
            if current_date < start.date() or current_date > end.date():
                continue
            total = Decimal("0")
            for row in relevant_rows:
                if day_index < len(row):
                    total += _parse_sheet_amount(row[day_index])
            balances[current_date] += total

        month_cursor = (month_cursor.replace(day=28) + timedelta(days=4)).replace(day=1)

    return balances


def _build_monthly_totals(
    labels: List[str],
    ano: int,
) -> List[Dict[str, Any]]:
    start = datetime(ano, 1, 1)
    end = datetime(ano, 12, 31, 23, 59, 59)

    balances = _collect_sheet_balances(labels, start, end)
    monthly_totals: Dict[int, Dict[str, Any]] = {
        month: {
            "mes": month,
            "entradas": 0.0,
            "saidas": 0.0,
            "saldo_final": 0.0,
            "quantidade_lancamentos": 0,
        }
        for month in range(1, 13)
    }

    if not balances:
        return [monthly_totals[month] for month in range(1, 13)]

    sorted_items = sorted(balances.items())
    prev_balance: Optional[Decimal] = None
    saldo_acumulado = Decimal("0")

    for current_date, balance in sorted_items:
        if current_date.year != ano:
            prev_balance = balance
            continue

        entradas = Decimal("0")
        saidas = Decimal("0")
        if prev_balance is not None:
            diff = balance - prev_balance
            if diff >= 0:
                entradas = diff
            else:
                saidas = -diff
        prev_balance = balance

        bucket = monthly_totals[current_date.month]
        if entradas > 0 or saidas > 0:
            bucket["quantidade_lancamentos"] += 1
        bucket["entradas"] += float(entradas)
        bucket["saidas"] += float(saidas)

    for month in range(1, 13):
        bucket = monthly_totals[month]
        saldo_acumulado += Decimal(str(bucket["entradas"])) - Decimal(str(bucket["saidas"]))
        bucket["saldo_final"] = float(saldo_acumulado)

    return [monthly_totals[month] for month in range(1, 13)]


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class InvestimentoCreate(BaseModel):
    tipo: str = Field(..., max_length=50)
    instituicao: str = Field(..., max_length=150)
    descricao: Optional[str] = Field(default=None, max_length=255)
    valor_aplicado: Decimal = Field(..., ge=Decimal("0"))
    valor_atual: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    data_aplicacao: datetime
    data_vencimento: Optional[datetime] = None
    taxa_rendimento: Decimal = Field(default=Decimal("0"))


# ---------------------------------------------------------------------------
# Rotas
# ---------------------------------------------------------------------------


@router.get("")
def list_investments(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    tenant_id = str(current_user.tenant_id)
    business_unit_id = _require_business_unit(current_user)

    investimentos = (
        db.query(Investimento)
        .filter(
            Investimento.tenant_id == tenant_id,
            Investimento.business_unit_id == business_unit_id,
            Investimento.is_active.is_(True),
        )
        .order_by(Investimento.data_aplicacao.desc())
        .all()
    )

    payload = [
        {
            "id": str(inv.id),
            "tipo": inv.tipo if isinstance(inv.tipo, str) else inv.tipo.value,
            "instituicao": inv.instituicao,
            "descricao": inv.descricao,
            "valor_aplicado": _decimal_to_float(inv.valor_aplicado),
            "valor_atual": _decimal_to_float(inv.valor_atual),
            "data_aplicacao": inv.data_aplicacao.isoformat() if inv.data_aplicacao else None,
            "data_vencimento": inv.data_vencimento.isoformat() if inv.data_vencimento else None,
            "taxa_rendimento": _decimal_to_float(inv.taxa_rendimento),
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
        }
        for inv in investimentos
    ]

    return {"success": True, "investimentos": payload}


@router.post("")
def create_investment(
    data: InvestimentoCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    tenant_id = str(current_user.tenant_id)
    business_unit_id = _require_business_unit(current_user)

    tipo_value = data.tipo
    try:
        tipo_enum = TipoInvestimento(tipo_value)
    except ValueError:
        tipo_enum = TipoInvestimento.OUTRO

    investimento = Investimento(
        tenant_id=tenant_id,
        business_unit_id=business_unit_id,
        tipo=tipo_enum,
        instituicao=data.instituicao,
        descricao=data.descricao,
        valor_aplicado=data.valor_aplicado,
        valor_atual=data.valor_atual or data.valor_aplicado,
        data_aplicacao=data.data_aplicacao.date(),
        data_vencimento=data.data_vencimento.date() if data.data_vencimento else None,
        taxa_rendimento=data.taxa_rendimento,
        created_by=str(current_user.id),
    )

    db.add(investimento)
    db.commit()
    db.refresh(investimento)

    return {
        "success": True,
        "message": "Investimento criado com sucesso",
        "investimento": {
            "id": str(investimento.id),
            "tipo": investimento.tipo.value,
            "instituicao": investimento.instituicao,
            "descricao": investimento.descricao,
            "valor_aplicado": _decimal_to_float(investimento.valor_aplicado),
            "valor_atual": _decimal_to_float(investimento.valor_atual),
            "data_aplicacao": investimento.data_aplicacao.isoformat(),
            "data_vencimento": investimento.data_vencimento.isoformat()
            if investimento.data_vencimento
            else None,
        },
    }


@router.delete("/{investimento_id}")
def delete_investment(
    investimento_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    tenant_id = str(current_user.tenant_id)
    business_unit_id = _require_business_unit(current_user)

    try:
        investimento_uuid = UUID(investimento_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="ID de investimento inválido.") from exc

    investimento = (
        db.query(Investimento)
        .filter(
            Investimento.id == investimento_uuid,
            Investimento.tenant_id == tenant_id,
            Investimento.business_unit_id == business_unit_id,
            Investimento.is_active.is_(True),
        )
        .first()
    )

    if not investimento:
        raise HTTPException(status_code=404, detail="Investimento não encontrado.")

    investimento.is_active = False
    db.commit()

    return {"success": True, "message": "Investimento removido com sucesso"}


@router.get("/{investimento_id}/extrato")
def investment_extract(
    investimento_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    tenant_id = str(current_user.tenant_id)
    business_unit_id = _require_business_unit(current_user)

    try:
        investimento_uuid = UUID(investimento_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="ID de investimento inválido.") from exc

    investimento = (
        db.query(Investimento)
        .filter(
            Investimento.id == investimento_uuid,
            Investimento.tenant_id == tenant_id,
            Investimento.business_unit_id == business_unit_id,
            Investimento.is_active.is_(True),
        )
        .first()
    )

    if not investimento:
        raise HTTPException(status_code=404, detail="Investimento não encontrado.")

    valor_aplicado = _decimal_to_float(investimento.valor_aplicado)
    valor_atual = _decimal_to_float(investimento.valor_atual)
    rentabilidade = valor_atual - valor_aplicado

    extrato = [
        {
            "data": investimento.data_aplicacao.isoformat() if investimento.data_aplicacao else None,
            "tipo": "Aplicação",
            "descricao": investimento.descricao or investimento.instituicao,
            "valor_aplicado": valor_aplicado,
            "valor_atual": valor_atual,
            "rentabilidade": rentabilidade,
            "observacoes": None,
        }
    ]

    return {
        "success": True,
        "investimento": {
            "id": str(investimento.id),
            "tipo": investimento.tipo.value,
            "instituicao": investimento.instituicao,
            "descricao": investimento.descricao,
            "valor_aplicado": valor_aplicado,
            "valor_atual": valor_atual,
            "data_aplicacao": investimento.data_aplicacao.isoformat(),
            "data_vencimento": investimento.data_vencimento.isoformat()
            if investimento.data_vencimento
            else None,
        },
        "periodo": {
            "inicio": investimento.data_aplicacao.isoformat() if investimento.data_aplicacao else None,
            "fim": datetime.utcnow().date().isoformat(),
        },
        "extrato": extrato,
    }


@router.get("/resumo")
def investments_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    tenant_id = str(current_user.tenant_id)
    business_unit_id = _require_business_unit(current_user)

    investimentos = (
        db.query(Investimento)
        .filter(
            Investimento.tenant_id == tenant_id,
            Investimento.business_unit_id == business_unit_id,
            Investimento.is_active.is_(True),
        )
        .all()
    )

    quantidade = len(investimentos)
    total_aplicado = sum(_decimal_to_float(inv.valor_aplicado) for inv in investimentos)
    total_atual = sum(_decimal_to_float(inv.valor_atual) for inv in investimentos)

    rentabilidade_percentual = 0.0
    if total_aplicado > 0:
        rentabilidade_percentual = ((total_atual - total_aplicado) / total_aplicado) * 100

    return {
        "success": True,
        "resumo": {
            "quantidade": quantidade,
            "total_aplicado": total_aplicado,
            "total_atual": total_atual,
            "rentabilidade_percentual": rentabilidade_percentual,
        },
    }


@router.get("/totalizadores-mensais")
def investments_monthly_totals(
    ano: int = Query(default=datetime.utcnow().year, ge=1900),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    _require_business_unit(current_user)

    labels = list(INVESTMENT_LABELS)
    totalizadores = _build_monthly_totals(labels, ano)

    return {"success": True, "ano": ano, "totalizadores": totalizadores}


