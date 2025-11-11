from __future__ import annotations

"""
Importador das contas bancárias a partir da planilha de Fluxo de Caixa Diário.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Tuple

from google.oauth2 import service_account
from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from app.models.conta_bancaria import ContaBancaria, TipoContaBancaria


MONTH_SHEETS: List[Tuple[str, int]] = [
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


SKIP_LABELS = {
    "",
    "saldo disponibilidades",
    "verificação de saldo",
    "saldo disponibilidades ",
}


@dataclass
class _AccountEntry:
    display_name: str
    base_name: str
    key: Tuple[int, str]
    order: int
    balances: Dict[int, Decimal] = field(default_factory=dict)


class LLMBankAccountsImporter:
    def __init__(self, credentials_path: str = "google_credentials.json") -> None:
        self.credentials_path = credentials_path
        self.service = None

    def authenticate(self) -> bool:
        """Autenticar no Google Sheets."""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
            )
            self.service = build("sheets", "v4", credentials=credentials)
            return True
        except Exception as exc:  # noqa: BLE001
            print(f"[BANK IMPORT] Autenticação falhou: {exc}")
            return False

    def import_bank_accounts(
        self,
        spreadsheet_id: str,
        tenant_id: str,
        business_unit_id: str,
        db: Session,
        user_id: str,
    ) -> Dict[str, object]:
        """
        Lê as abas FC-diário-{mes} e cria/atualiza contas bancárias no sistema.
        """
        if not self.service:
            raise RuntimeError("Importer not authenticated")

        entries: Dict[Tuple[int, str], _AccountEntry] = {}
        name_counts: Dict[str, int] = {}
        created = 0
        updated = 0

        for sheet_suffix, month_num in MONTH_SHEETS:
            range_label = f"'FC-diário-{sheet_suffix}'!B174:C184"
            try:
                result = (
                    self.service.spreadsheets()
                    .values()
                    .get(spreadsheetId=spreadsheet_id, range=range_label)
                    .execute()
                )
            except Exception as exc:  # noqa: BLE001
                print(f"[BANK IMPORT] Falha ao ler {range_label}: {exc}")
                continue

            values = result.get("values", [])
            for row_idx, row in enumerate(values):
                if not row:
                    continue
                base_name = row[0].strip() if len(row) >= 1 and row[0] else ""
                if base_name.lower() in SKIP_LABELS:
                    continue

                amount = self._parse_amount(row[1] if len(row) >= 2 else "")
                key = (row_idx, base_name.lower())
                entry = entries.get(key)
                if entry is None:
                    name_counts[base_name] = name_counts.get(base_name, 0) + 1
                    occurrence = name_counts[base_name]
                    display_name = (
                        base_name if occurrence == 1 else f"{base_name} ({occurrence})"
                    )
                    entry = _AccountEntry(
                        display_name=display_name,
                        base_name=base_name,
                        key=key,
                        order=len(entries),
                    )
                    entries[key] = entry
                entry.balances[month_num] = amount

        if not entries:
            return {
                "success": False,
                "created": 0,
                "updated": 0,
                "message": "Nenhuma conta identificada na planilha.",
            }

        # Criar/atualizar contas no banco
        month_order = sorted([month for _, month in MONTH_SHEETS], reverse=True)

        for entry in sorted(entries.values(), key=lambda item: item.order):
            latest_balance = Decimal("0")
            for month in month_order:
                if month in entry.balances:
                    latest_balance = entry.balances[month]
                    if latest_balance != 0:
                        break

            account = (
                db.query(ContaBancaria)
                .filter(
                    ContaBancaria.tenant_id == tenant_id,
                    ContaBancaria.business_unit_id == business_unit_id,
                    ContaBancaria.banco == entry.display_name,
                    ContaBancaria.is_active.is_(True),
                )
                .first()
            )

            saldo_decimal = latest_balance
            saldo_float = float(saldo_decimal)

            if account is None:
                account = ContaBancaria(
                    tenant_id=tenant_id,
                    business_unit_id=business_unit_id,
                    banco=entry.display_name,
                    agencia=None,
                    numero_conta=None,
                    tipo=TipoContaBancaria.CORRENTE,
                    saldo_inicial=saldo_decimal,
                    saldo_atual=saldo_decimal,
                    created_by=user_id,
                )
                db.add(account)
                created += 1
            else:
                account.saldo_atual = saldo_decimal
                if not account.saldo_inicial:
                    account.saldo_inicial = saldo_decimal
                updated += 1

        db.commit()

        return {
            "success": True,
            "created": created,
            "updated": updated,
            "total_detected": len(entries),
        }

    @staticmethod
    def _parse_amount(raw: str) -> Decimal:
        if raw is None:
            return Decimal("0")
        value = str(raw).strip()
        if not value:
            return Decimal("0")
        normalized = (
            value.replace("R$", "")
            .replace(" ", "")
            .replace(".", "")
            .replace(",", ".")
        )
        if normalized in {"", "-", "--"}:
            return Decimal("0")
        try:
            return Decimal(normalized)
        except InvalidOperation:
            return Decimal("0")

