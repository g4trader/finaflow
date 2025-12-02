"""
API de gestão de Caixas (dinheiro físico).

As respostas utilizam exclusivamente dados reais armazenados no banco de dados
ou na planilha compartilhada (fluxo de caixa diário). Não há dados mock.
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
from app.models.caixa import Caixa, MovimentacaoCaixa, TipoMovimentacaoCaixa
from app.models.auth import User
from app.services.llm_sheet_importer import LLMSheetImporter

router = APIRouter(prefix="/api/v1/caixa", tags=["Caixa"])

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

DEFAULT_SHEET_LABELS = {"caixa", "caixadinheiro", "caixa/dinheiro"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalize_label(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return "".join(ch for ch in ascii_only.lower().strip() if ch not in {" ", "-", "_"})


def _get_spreadsheet_id() -> str:
    settings = Settings()
    if settings.SPREADSHEET_ID:
        return settings.SPREADSHEET_ID
    # fallback para o último ID fornecido pelo usuário
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
    label: str,
    start: datetime,
    end: datetime,
) -> Dict[date, Decimal]:
    """
    Lê os saldos diários do caixa na planilha. Retorna um dicionário
    {data: saldo}, limitado ao intervalo solicitado.
    """
    importer = LLMSheetImporter()
    if not importer.authenticate():
        return {}

    normalized_label = _normalize_label(label)
    spreadsheet_id = _get_spreadsheet_id()

    balances: Dict[date, Decimal] = {}
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
        target_row: Optional[List[str]] = None
        for row in rows:
            if row and _normalize_label(row[0]) == normalized_label:
                target_row = row
                break

        if not target_row:
            month_cursor = (month_cursor.replace(day=28) + timedelta(days=4)).replace(day=1)
            continue

        days_in_month = calendar.monthrange(month_cursor.year, month_cursor.month)[1]
        for day_index in range(1, min(len(target_row), days_in_month + 1)):
            try:
                current_date = datetime(month_cursor.year, month_cursor.month, day_index).date()
            except ValueError:
                continue
            if current_date < start.date() or current_date > end.date():
                continue
            value = target_row[day_index] if day_index < len(target_row) else ""
            balances[current_date] = _parse_sheet_amount(value or "0")

        month_cursor = (month_cursor.replace(day=28) + timedelta(days=4)).replace(day=1)

    return balances


def _build_sheet_extract(label: str, start: datetime, end: datetime) -> List[Dict[str, Any]]:
    balances = _collect_sheet_balances(label, start, end)
    if not balances:
        return []

    sorted_dates = sorted(balances.keys())
    extrato: List[Dict[str, Any]] = []
    prev_balance: Optional[Decimal] = None

    for current_date in sorted_dates:
        balance = balances[current_date]
        entradas = Decimal("0")
        saidas = Decimal("0")
        if prev_balance is not None:
            diff = balance - prev_balance
            if diff >= 0:
                entradas = diff
            else:
                saidas = -diff
        prev_balance = balance

        extrato.append(
            {
                "data": current_date.isoformat(),
                "entradas": float(entradas),
                "saidas": float(saidas),
                "saldo_dia": float(balance),
                "lancamentos": [],
            }
        )

    return extrato


def _aggregate_monthly_totals(
    labels: List[str],
    ano: int,
) -> List[Dict[str, Any]]:
    start = datetime(ano, 1, 1)
    end = datetime(ano, 12, 31, 23, 59, 59)

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

    for label in labels:
        balances = _collect_sheet_balances(label, start, end)
        if not balances:
            continue
        sorted_items = sorted(balances.items())
        prev_balance: Optional[Decimal] = None
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

    saldo_acumulado = Decimal("0")
    for month in range(1, 13):
        bucket = monthly_totals[month]
        saldo_acumulado += Decimal(str(bucket["entradas"])) - Decimal(str(bucket["saidas"]))
        bucket["saldo_final"] = float(saldo_acumulado)

    return [monthly_totals[month] for month in range(1, 13)]


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class CaixaBase(BaseModel):
    nome: str = Field(..., max_length=100)
    descricao: Optional[str] = Field(default=None, max_length=255)


class CaixaCreate(CaixaBase):
    saldo_inicial: Decimal = Field(default=Decimal("0"))


class CaixaUpdate(BaseModel):
    nome: Optional[str] = Field(default=None, max_length=100)
    descricao: Optional[str] = Field(default=None, max_length=255)


# ---------------------------------------------------------------------------
# Rotas
# ---------------------------------------------------------------------------


@router.get("")
def list_caixas(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    tenant_id = str(current_user.tenant_id)
    business_unit_id = _require_business_unit(current_user)

    caixas = (
        db.query(Caixa)
        .filter(
            Caixa.tenant_id == tenant_id,
            Caixa.business_unit_id == business_unit_id,
            Caixa.is_active.is_(True),
        )
        .order_by(Caixa.nome.asc())
        .all()
    )

    payload = [
        {
            "id": str(caixa.id),
            "nome": caixa.nome,
            "descricao": caixa.descricao,
            "saldo_inicial": _decimal_to_float(caixa.saldo_inicial),
            "saldo_atual": _decimal_to_float(caixa.saldo_atual),
            "created_at": caixa.created_at.isoformat() if caixa.created_at else None,
        }
        for caixa in caixas
    ]

    return {"success": True, "caixas": payload}


@router.post("")
def create_caixa(
    data: CaixaCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    tenant_id = str(current_user.tenant_id)
    business_unit_id = _require_business_unit(current_user)

    caixa = Caixa(
        tenant_id=tenant_id,
        business_unit_id=business_unit_id,
        nome=data.nome,
        descricao=data.descricao,
        saldo_inicial=data.saldo_inicial,
        saldo_atual=data.saldo_inicial,
        created_by=str(current_user.id),
    )

    db.add(caixa)
    db.commit()
    db.refresh(caixa)

    return {
        "success": True,
        "message": "Caixa criado com sucesso",
        "caixa": {
            "id": str(caixa.id),
            "nome": caixa.nome,
            "descricao": caixa.descricao,
            "saldo_inicial": _decimal_to_float(caixa.saldo_inicial),
            "saldo_atual": _decimal_to_float(caixa.saldo_atual),
            "created_at": caixa.created_at.isoformat() if caixa.created_at else None,
        },
    }


@router.put("/{caixa_id}")
def update_caixa(
    caixa_id: str,
    data: CaixaUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    tenant_id = str(current_user.tenant_id)
    business_unit_id = _require_business_unit(current_user)

    try:
        caixa_uuid = UUID(caixa_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="ID de caixa inválido.") from exc

    caixa = (
        db.query(Caixa)
        .filter(
            Caixa.id == caixa_uuid,
            Caixa.tenant_id == tenant_id,
            Caixa.business_unit_id == business_unit_id,
            Caixa.is_active.is_(True),
        )
        .first()
    )

    if not caixa:
        raise HTTPException(status_code=404, detail="Caixa não encontrado.")

    if data.nome is not None:
        caixa.nome = data.nome
    if data.descricao is not None:
        caixa.descricao = data.descricao

    db.commit()
    db.refresh(caixa)

    return {
        "success": True,
        "message": "Caixa atualizado com sucesso",
        "caixa": {
            "id": str(caixa.id),
            "nome": caixa.nome,
            "descricao": caixa.descricao,
            "saldo_inicial": _decimal_to_float(caixa.saldo_inicial),
            "saldo_atual": _decimal_to_float(caixa.saldo_atual),
            "created_at": caixa.created_at.isoformat() if caixa.created_at else None,
        },
    }


@router.delete("/{caixa_id}")
def delete_caixa(
    caixa_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    tenant_id = str(current_user.tenant_id)
    business_unit_id = _require_business_unit(current_user)

    try:
        caixa_uuid = UUID(caixa_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="ID de caixa inválido.") from exc

    caixa = (
        db.query(Caixa)
        .filter(
            Caixa.id == caixa_uuid,
            Caixa.tenant_id == tenant_id,
            Caixa.business_unit_id == business_unit_id,
            Caixa.is_active.is_(True),
        )
        .first()
    )

    if not caixa:
        raise HTTPException(status_code=404, detail="Caixa não encontrado.")

    caixa.is_active = False
    db.commit()

    return {"success": True, "message": "Caixa removido com sucesso."}


@router.get("/{caixa_id}/extrato")
def caixa_extract(
    caixa_id: str,
    data_inicio: Optional[str] = Query(default=None),
    data_fim: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    tenant_id = str(current_user.tenant_id)
    business_unit_id = _require_business_unit(current_user)

    try:
        caixa_uuid = UUID(caixa_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="ID de caixa inválido.") from exc

    caixa = (
        db.query(Caixa)
        .filter(
            Caixa.id == caixa_uuid,
            Caixa.tenant_id == tenant_id,
            Caixa.business_unit_id == business_unit_id,
            Caixa.is_active.is_(True),
        )
        .first()
    )

    if not caixa:
        raise HTTPException(status_code=404, detail="Caixa não encontrado.")

    end_default = datetime.utcnow()
    start_default = end_default - timedelta(days=30)

    def _parse_date(value: Optional[str], default: datetime) -> datetime:
        if value:
            try:
                parsed = datetime.fromisoformat(value)
                if parsed.tzinfo:
                    parsed = parsed.astimezone(tz=None).replace(tzinfo=None)
                return parsed
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="Data inválida.") from exc
        return default

    start = _parse_date(data_inicio, start_default).replace(hour=0, minute=0, second=0, microsecond=0)
    end = _parse_date(data_fim, end_default).replace(hour=23, minute=59, second=59, microsecond=999999)

    movements = (
        db.query(MovimentacaoCaixa)
        .filter(
            MovimentacaoCaixa.caixa_id == caixa_uuid,
            MovimentacaoCaixa.tenant_id == tenant_id,
            MovimentacaoCaixa.business_unit_id == business_unit_id,
            MovimentacaoCaixa.data_movimentacao >= start,
            MovimentacaoCaixa.data_movimentacao <= end,
        )
        .order_by(MovimentacaoCaixa.data_movimentacao.asc())
        .all()
    )

    extrato = []
    if movements:
        diaria: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"entradas": 0.0, "saidas": 0.0, "saldo_dia": 0.0, "lancamentos": []}
        )

        saldo = _decimal_to_float(caixa.saldo_inicial)
        before_range = (
            db.query(MovimentacaoCaixa)
            .filter(
                MovimentacaoCaixa.caixa_id == caixa_uuid,
                MovimentacaoCaixa.tenant_id == tenant_id,
                MovimentacaoCaixa.business_unit_id == business_unit_id,
                MovimentacaoCaixa.data_movimentacao < start,
            )
            .all()
        )
        for mov in before_range:
            valor = _decimal_to_float(mov.valor)
            if mov.tipo == TipoMovimentacaoCaixa.ENTRADA:
                saldo += valor
            else:
                saldo -= valor

        for mov in movements:
            date_key = mov.data_movimentacao.date().isoformat()
            valor = _decimal_to_float(mov.valor)
            if mov.tipo == TipoMovimentacaoCaixa.ENTRADA:
                diaria[date_key]["entradas"] += valor
                saldo += valor
            else:
                diaria[date_key]["saidas"] += valor
                saldo -= valor

            diaria[date_key]["saldo_dia"] = saldo
            diaria[date_key]["lancamentos"].append(
                {
                    "id": str(mov.id),
                    "descricao": mov.descricao or "Movimentação",
                    "valor": valor,
                    "tipo": mov.tipo.value.upper(),
                    "data": mov.data_movimentacao.isoformat(),
                }
            )

        extrato = [
            {
                "data": data,
                "entradas": bucket["entradas"],
                "saidas": bucket["saidas"],
                "saldo_dia": bucket["saldo_dia"],
                "lancamentos": bucket["lancamentos"],
            }
            for data in sorted(diaria.keys())
        ]

    if not extrato:
        extrato = _build_sheet_extract(caixa.nome, start, end)

    saldo_inicial = 0.0
    saldo_final = _decimal_to_float(caixa.saldo_atual)
    if extrato:
        saldo_inicial = extrato[0]["saldo_dia"] - extrato[0]["entradas"] + extrato[0]["saidas"]
        saldo_final = extrato[-1]["saldo_dia"]
    dias_periodo = max((end.date() - start.date()).days + 1, 1)
    media_diaria = saldo_final / dias_periodo

    return {
        "success": True,
        "caixa": {
            "id": str(caixa.id),
            "nome": caixa.nome,
            "descricao": caixa.descricao,
            "saldo_atual": _decimal_to_float(caixa.saldo_atual),
        },
        "periodo": {
            "inicio": start.date().isoformat(),
            "fim": end.date().isoformat(),
        },
        "meta": {
            "saldo_inicial": saldo_inicial,
            "saldo_final": saldo_final,
            "media_diaria": media_diaria,
        },
        "extrato": extrato,
    }


@router.get("/totalizadores-mensais")
def caixa_monthly_totals(
    ano: int = Query(default=datetime.utcnow().year, ge=1900),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    tenant_id = str(current_user.tenant_id)
    business_unit_id = _require_business_unit(current_user)

    caixas = (
        db.query(Caixa)
        .filter(
            Caixa.tenant_id == tenant_id,
            Caixa.business_unit_id == business_unit_id,
            Caixa.is_active.is_(True),
        )
        .all()
    )

    if not caixas:
        # Ainda assim retornamos estrutura completa com zeros para o dashboard
        empty = [
            {
                "mes": month,
                "entradas": 0.0,
                "saidas": 0.0,
                "saldo_final": 0.0,
                "quantidade_lancamentos": 0,
            }
            for month in range(1, 13)
        ]
        return {"success": True, "ano": ano, "totalizadores": empty}

    labels = list({*(caixa.nome for caixa in caixas), *DEFAULT_SHEET_LABELS})

    totalizadores = _aggregate_monthly_totals(labels, ano)

    return {"success": True, "ano": ano, "totalizadores": totalizadores}


