from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
import os
import calendar
from functools import lru_cache
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import User
from app.models.conta_bancaria import ContaBancaria, TipoContaBancaria
from app.models.lancamento_diario import LancamentoDiario, TransactionType
from app.services.dependencies import get_current_active_user
from google.oauth2 import service_account
from googleapiclient.discovery import build

router = APIRouter(prefix="/contas-bancarias", tags=["bank-accounts"])

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

DEFAULT_SHEET_ID = os.getenv(
    "GOOGLE_SHEETS_DEFAULT_ID",
    "1rWMdDhwiNoC7iMycmQGWWDIacrePr1gB7c_mbt1patQ",
)
GOOGLE_CREDENTIALS_PATH = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS", "google_credentials.json"
)


class BankAccountBase(BaseModel):
    banco: str
    agencia: Optional[str] = None
    numero_conta: Optional[str] = None
    tipo: TipoContaBancaria = TipoContaBancaria.CORRENTE
    saldo_inicial: Decimal = Field(default=Decimal("0.0"), ge=0)


class BankAccountCreate(BankAccountBase):
    pass


class BankAccountUpdate(BaseModel):
    banco: Optional[str] = None
    agencia: Optional[str] = None
    numero_conta: Optional[str] = None
    tipo: Optional[TipoContaBancaria] = None


def _require_business_unit(user: User) -> str:
    business_unit_id = getattr(user, "business_unit_id", None)
    if not business_unit_id:
        raise HTTPException(
            status_code=400,
            detail="Usuário precisa selecionar uma unidade de negócio para acessar contas bancárias.",
        )
    return str(business_unit_id)


def _decimal_to_float(value: Optional[Decimal]) -> float:
    if value is None:
        return 0.0
    return float(value)


def _parse_date(value: Optional[str], default: datetime) -> datetime:
    if value:
        return datetime.fromisoformat(value)
    return default


def _normalize_label(label: str) -> str:
    return "".join(
        char
        for char in label.lower().strip()
        if char not in {" ", "-", "_", "/"}
    )


@lru_cache(maxsize=1)
def _get_sheet_service():
    try:
        credentials = service_account.Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS_PATH,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
        )
        return build("sheets", "v4", credentials=credentials)
    except Exception:
        return None


def _sheet_suffix(year: int, month: int) -> Optional[str]:
    if year != 2025:
        return None
    for suffix, number in MONTH_SHEETS:
        if number == month:
            return suffix
    return None


def _parse_sheet_amount(text: str) -> Decimal:
    if not text:
        return Decimal("0")
    clean = (
        text.replace("R$", "")
        .replace(" ", "")
        .replace(".", "")
        .replace(",", ".")
        .strip()
    )
    if not clean or clean in {"-", "--"}:
        return Decimal("0")
    try:
        return Decimal(clean)
    except Exception:
        return Decimal("0")



@router.get("")
def list_bank_accounts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    tenant_id = str(current_user.tenant_id)
    business_unit_id = _require_business_unit(current_user)

    accounts: List[ContaBancaria] = (
        db.query(ContaBancaria)
        .filter(
            ContaBancaria.tenant_id == tenant_id,
            ContaBancaria.business_unit_id == business_unit_id,
            ContaBancaria.is_active.is_(True),
        )
        .order_by(ContaBancaria.banco.asc(), ContaBancaria.numero_conta.asc())
        .all()
    )

    payload = [
        {
            "id": str(account.id),
            "banco": account.banco,
            "agencia": account.agencia,
            "numero_conta": account.numero_conta,
            "tipo": account.tipo.value if isinstance(account.tipo, TipoContaBancaria) else account.tipo,
            "saldo_inicial": _decimal_to_float(account.saldo_inicial),
            "saldo_atual": _decimal_to_float(account.saldo_atual),
            "created_at": account.created_at.isoformat() if account.created_at else None,
        }
        for account in accounts
    ]

    return {"success": True, "contas": payload}


@router.post("")
def create_bank_account(
    data: BankAccountCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    tenant_id = str(current_user.tenant_id)
    business_unit_id = _require_business_unit(current_user)

    account = ContaBancaria(
        tenant_id=tenant_id,
        business_unit_id=business_unit_id,
        banco=data.banco,
        agencia=data.agencia,
        numero_conta=data.numero_conta,
        tipo=data.tipo,
        saldo_inicial=data.saldo_inicial,
        saldo_atual=data.saldo_inicial,
        created_by=str(current_user.id),
    )

    db.add(account)
    db.commit()
    db.refresh(account)

    return {
        "success": True,
        "message": "Conta bancária criada com sucesso",
        "conta": {
            "id": str(account.id),
            "banco": account.banco,
            "agencia": account.agencia,
            "numero_conta": account.numero_conta,
            "tipo": account.tipo.value if isinstance(account.tipo, TipoContaBancaria) else account.tipo,
            "saldo_atual": _decimal_to_float(account.saldo_atual),
        },
    }


@router.put("/{conta_id}")
def update_bank_account(
    conta_id: str,
    data: BankAccountUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    tenant_id = str(current_user.tenant_id)
    business_unit_id = _require_business_unit(current_user)

    try:
        account_uuid = UUID(conta_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="ID de conta inválido") from exc

    account = (
        db.query(ContaBancaria)
        .filter(
            ContaBancaria.id == account_uuid,
            ContaBancaria.tenant_id == tenant_id,
            ContaBancaria.business_unit_id == business_unit_id,
            ContaBancaria.is_active.is_(True),
        )
        .first()
    )

    if not account:
        raise HTTPException(status_code=404, detail="Conta bancária não encontrada")

    if data.banco is not None:
        account.banco = data.banco
    if data.agencia is not None:
        account.agencia = data.agencia
    if data.numero_conta is not None:
        account.numero_conta = data.numero_conta
    if data.tipo is not None:
        account.tipo = data.tipo

    db.commit()

    return {"success": True, "message": "Conta bancária atualizada com sucesso"}


@router.delete("/{conta_id}")
def delete_bank_account(
    conta_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    tenant_id = str(current_user.tenant_id)
    business_unit_id = _require_business_unit(current_user)

    try:
        account_uuid = UUID(conta_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="ID de conta inválido") from exc

    account = (
        db.query(ContaBancaria)
        .filter(
            ContaBancaria.id == account_uuid,
            ContaBancaria.tenant_id == tenant_id,
            ContaBancaria.business_unit_id == business_unit_id,
            ContaBancaria.is_active.is_(True),
        )
        .first()
    )

    if not account:
        raise HTTPException(status_code=404, detail="Conta bancária não encontrada")

    account.is_active = False
    db.commit()

    return {"success": True, "message": "Conta bancária removida com sucesso"}


def _build_daily_entries(lancamentos: List[LancamentoDiario]) -> List[Dict[str, Any]]:
    diário: Dict[str, Dict[str, Any]] = {}

    for lancamento in lancamentos:
        data_key = lancamento.data_movimentacao.date().isoformat()
        bucket = diário.setdefault(
            data_key,
            {"data": data_key, "entradas": 0.0, "saidas": 0.0, "saldo_dia": 0.0, "lancamentos": []},
        )

        valor = _decimal_to_float(lancamento.valor)
        if lancamento.transaction_type == TransactionType.RECEITA:
            bucket["entradas"] += valor
        elif lancamento.transaction_type in (TransactionType.DESPESA, TransactionType.CUSTO):
            bucket["saidas"] += valor

        bucket["lancamentos"].append(
            {
                "id": lancamento.id,
                "conta": lancamento.conta.name if lancamento.conta else "N/A",
                "descricao": lancamento.observacoes or "Lançamento",
                "valor": valor,
                "tipo": lancamento.transaction_type.value if lancamento.transaction_type else None,
                "liquidacao": lancamento.liquidacao.isoformat() if lancamento.liquidacao else None,
            }
        )

    saldo_acumulado = 0.0
    for data in sorted(diário.keys()):
        bucket = diário[data]
        saldo_acumulado += bucket["entradas"] - bucket["saidas"]
        bucket["saldo_dia"] = saldo_acumulado

    # Retornar ordenado por data crescente
    return [diário[data] for data in sorted(diário.keys())]


def _build_sheet_extract(
    account_name: str, start: datetime, end: datetime
) -> List[Dict[str, Any]]:
    service = _get_sheet_service()
    if service is None or not DEFAULT_SHEET_ID:
        return []

    normalized_target = _normalize_label(account_name)
    if not normalized_target:
        return []

    month_cursor = datetime(start.year, start.month, 1)
    end_month = datetime(end.year, end.month, 1)

    balances: Dict[datetime, Decimal] = {}

    while month_cursor <= end_month:
        suffix = _sheet_suffix(month_cursor.year, month_cursor.month)
        if not suffix:
            month_cursor = (month_cursor.replace(day=28) + timedelta(days=4)).replace(day=1)
            continue

        range_label = f"'FC-diário-{suffix}'!B175:AF184"
        try:
            result = (
                service.spreadsheets()
                .values()
                .get(spreadsheetId=DEFAULT_SHEET_ID, range=range_label)
                .execute()
            )
        except Exception:
            month_cursor = (month_cursor.replace(day=28) + timedelta(days=4)).replace(day=1)
            continue

        values = result.get("values", [])
        target_row: Optional[List[str]] = None
        for row in values:
            if not row:
                continue
            if _normalize_label(row[0]) == normalized_target:
                target_row = row
                break

        if not target_row:
            month_cursor = (month_cursor.replace(day=28) + timedelta(days=4)).replace(day=1)
            continue

        days_in_month = calendar.monthrange(month_cursor.year, month_cursor.month)[1]
        for day_index in range(1, min(len(target_row), days_in_month + 1)):
            try:
                date_value = datetime(month_cursor.year, month_cursor.month, day_index)
            except ValueError:
                continue
            balances[date_value] = _parse_sheet_amount(target_row[day_index])

        month_cursor = (month_cursor.replace(day=28) + timedelta(days=4)).replace(day=1)

    if not balances:
        return []

    sorted_dates = sorted(balances.keys())
    extrato: List[Dict[str, Any]] = []
    prev_balance: Optional[Decimal] = None

    for date_value in sorted_dates:
        if date_value < start:
            prev_balance = balances[date_value]
            continue
        if date_value > end:
            break

        balance = balances[date_value]
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
                "data": date_value.date().isoformat(),
                "entradas": float(entradas),
                "saidas": float(saidas),
                "saldo_dia": float(balance),
                "lancamentos": [],
            }
        )

    return extrato


@router.get("/{conta_id}/extrato")
def bank_account_extract(
    conta_id: str,
    data_inicio: Optional[str] = Query(default=None),
    data_fim: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    tenant_id = str(current_user.tenant_id)
    business_unit_id = _require_business_unit(current_user)

    account = (
        db.query(ContaBancaria)
        .filter(
            ContaBancaria.id == conta_id,
            ContaBancaria.tenant_id == tenant_id,
            ContaBancaria.business_unit_id == business_unit_id,
            ContaBancaria.is_active.is_(True),
        )
        .first()
    )

    if not account:
        raise HTTPException(status_code=404, detail="Conta bancária não encontrada")

    end_default = datetime.utcnow()
    start_default = end_default - timedelta(days=30)

    start = _parse_date(data_inicio, start_default).replace(hour=0, minute=0, second=0, microsecond=0)
    end = _parse_date(data_fim, end_default).replace(hour=23, minute=59, second=59, microsecond=999999)

    entries = (
        db.query(LancamentoDiario)
        .filter(
            LancamentoDiario.tenant_id == tenant_id,
            LancamentoDiario.business_unit_id == business_unit_id,
            LancamentoDiario.is_active.is_(True),
            LancamentoDiario.conta_id == str(account.id),
            LancamentoDiario.data_movimentacao >= start,
            LancamentoDiario.data_movimentacao <= end,
        )
        .order_by(LancamentoDiario.data_movimentacao.asc())
        .all()
    )

    extrato = _build_daily_entries(entries)
    if not extrato:
        extrato = _build_sheet_extract(account.banco, start, end)

    return {
        "success": True,
        "conta": {
            "id": str(account.id),
            "banco": account.banco,
            "agencia": account.agencia,
            "conta": account.numero_conta,
            "saldo_atual": _decimal_to_float(account.saldo_atual),
        },
        "periodo": {"inicio": start.date().isoformat(), "fim": end.date().isoformat()},
        "extrato": extrato,
    }


@router.get("/extrato-diario")
def bank_accounts_daily_extract(
    data_inicio: Optional[str] = Query(default=None),
    data_fim: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    tenant_id = str(current_user.tenant_id)
    business_unit_id = _require_business_unit(current_user)

    end_default = datetime.utcnow()
    start_default = end_default - timedelta(days=30)

    start = _parse_date(data_inicio, start_default).replace(hour=0, minute=0, second=0, microsecond=0)
    end = _parse_date(data_fim, end_default).replace(hour=23, minute=59, second=59, microsecond=999999)

    entries = (
        db.query(LancamentoDiario)
        .filter(
            LancamentoDiario.tenant_id == tenant_id,
            LancamentoDiario.business_unit_id == business_unit_id,
            LancamentoDiario.is_active.is_(True),
            LancamentoDiario.data_movimentacao >= start,
            LancamentoDiario.data_movimentacao <= end,
        )
        .order_by(LancamentoDiario.data_movimentacao.asc())
        .all()
    )

    extrato = _build_daily_entries(entries)

    return {
        "success": True,
        "periodo": {"inicio": start.date().isoformat(), "fim": end.date().isoformat()},
        "extrato": extrato,
    }


@router.get("/totalizadores-mensais")
def bank_accounts_monthly_totals(
    ano: int = Query(default=datetime.utcnow().year, ge=1900),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    tenant_id = str(current_user.tenant_id)
    business_unit_id = _require_business_unit(current_user)

    start = datetime(ano, 1, 1)
    end = datetime(ano, 12, 31, 23, 59, 59)

    entries = (
        db.query(LancamentoDiario)
        .filter(
            LancamentoDiario.tenant_id == tenant_id,
            LancamentoDiario.business_unit_id == business_unit_id,
            LancamentoDiario.is_active.is_(True),
            LancamentoDiario.data_movimentacao >= start,
            LancamentoDiario.data_movimentacao <= end,
        )
        .all()
    )

    monthly: Dict[int, Dict[str, Any]] = {
        month: {"mes": month, "entradas": 0.0, "saidas": 0.0, "saldo_final": 0.0, "quantidade_lancamentos": 0}
        for month in range(1, 13)
    }

    for lancamento in entries:
        month = lancamento.data_movimentacao.month
        valor = _decimal_to_float(lancamento.valor)
        bucket = monthly[month]
        bucket["quantidade_lancamentos"] += 1

        if lancamento.transaction_type == TransactionType.RECEITA:
            bucket["entradas"] += valor
        elif lancamento.transaction_type in (TransactionType.DESPESA, TransactionType.CUSTO):
            bucket["saidas"] += valor

    saldo_acumulado = 0.0
    for month in range(1, 13):
        bucket = monthly[month]
        saldo_acumulado += bucket["entradas"] - bucket["saidas"]
        bucket["saldo_final"] = saldo_acumulado

    return {
        "success": True,
        "ano": ano,
        "totalizadores": [monthly[month] for month in range(1, 13)],
    }

