from __future__ import annotations

"""
Importador das contas bancárias a partir da planilha de Fluxo de Caixa Diário.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
import unicodedata
from typing import Dict, List, Tuple

from google.oauth2 import service_account
from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from app.models.conta_bancaria import ContaBancaria, TipoContaBancaria
from app.models.caixa import Caixa
from app.models.investimento import Investimento, TipoInvestimento


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


IGNORED_PREFIXES = {
    "saldo disponibilidades",
    "verificacao de saldo",
    "diferenca de fluxo",
}

BANK_PREFIXES = {
    "cef",
    "sicoob",
    "bb",
    "banco do brasil",
    "itau",
    "bradesco",
    "santander",
    "nubank",
    "inter",
    "c6",
    "sicredi",
}

CASH_PREFIXES = {
    "caixa",
    "caixa/dinheiro",
    "caixa dinheiro",
}

INVESTMENT_PREFIXES = {
    "aplicacao",
    "aplicacao ",
    "aplicacao(",
    "aplicacao (",
    "investimento",
}


@dataclass
class _AccountEntry:
    display_name: str
    base_name: str
    key: Tuple[int, str]
    order: int
    category: str  # bank, cash, investment
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
        bank_names: Dict[str, _AccountEntry] = {}
        name_counts: Dict[str, int] = {}
        created = 0
        updated = 0
        cash_created = 0
        cash_updated = 0
        investments_created = 0
        investments_updated = 0

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
                normalized = self._normalize_label(base_name)
                if not normalized:
                    continue

                category = self._classify_label(normalized)
                if category is None:
                    continue

                amount = self._parse_amount(row[1] if len(row) >= 2 else "")
                key = (row_idx, normalized)
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
                        category=category,
                    )
                    entries[key] = entry
                    if category == "bank":
                        bank_names[self._normalize_label(display_name)] = entry
                entry.balances[month_num] = amount

        if not entries:
            return {
                "success": False,
                "created": 0,
                "updated": 0,
                "cash_created": 0,
                "cash_updated": 0,
                "investments_created": 0,
                "investments_updated": 0,
                "message": "Nenhuma conta identificada na planilha.",
            }

        # Criar/atualizar contas no banco
        month_order = sorted([month for _, month in MONTH_SHEETS], reverse=True)

        # Desativar contas bancárias que não aparecem mais
        existing_accounts = (
            db.query(ContaBancaria)
            .filter(
                ContaBancaria.tenant_id == tenant_id,
                ContaBancaria.business_unit_id == business_unit_id,
                ContaBancaria.is_active.is_(True),
            )
            .all()
        )
        valid_bank_keys = {
            self._normalize_label(entry.display_name)
            for entry in entries.values()
            if entry.category == "bank"
        }
        for account in existing_accounts:
            if self._normalize_label(account.banco) not in valid_bank_keys:
                account.is_active = False

        for entry in sorted(entries.values(), key=lambda item: item.order):
            latest_balance = Decimal("0")
            for month in month_order:
                if month in entry.balances:
                    latest_balance = entry.balances[month]
                    if latest_balance != 0:
                        break

            saldo_decimal = latest_balance
            if entry.category == "bank":
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
                    if account.saldo_inicial is None:
                        account.saldo_inicial = saldo_decimal
                    updated += 1

            elif entry.category == "cash":
                cash = (
                    db.query(Caixa)
                    .filter(
                        Caixa.tenant_id == tenant_id,
                        Caixa.business_unit_id == business_unit_id,
                        Caixa.nome == entry.display_name,
                        Caixa.is_active.is_(True),
                    )
                    .first()
                )

                if cash is None:
                    cash = Caixa(
                        tenant_id=tenant_id,
                        business_unit_id=business_unit_id,
                        nome=entry.display_name,
                        descricao="Importado da planilha (verificação de saldo)",
                        saldo_inicial=saldo_decimal,
                        saldo_atual=saldo_decimal,
                        created_by=user_id,
                    )
                    db.add(cash)
                    cash_created += 1
                else:
                    cash.saldo_atual = saldo_decimal
                    if cash.saldo_inicial is None:
                        cash.saldo_inicial = saldo_decimal
                    cash_updated += 1

            elif entry.category == "investment":
                investment = (
                    db.query(Investimento)
                    .filter(
                        Investimento.tenant_id == tenant_id,
                        Investimento.business_unit_id == business_unit_id,
                        Investimento.instituicao == entry.display_name,
                        Investimento.is_active.is_(True),
                    )
                    .first()
                )

                if investment is None:
                    investment = Investimento(
                        tenant_id=tenant_id,
                        business_unit_id=business_unit_id,
                        tipo=TipoInvestimento.OUTRO,
                        instituicao=entry.display_name,
                        descricao="Importado da planilha (verificação de saldo)",
                        valor_aplicado=saldo_decimal,
                        valor_atual=saldo_decimal,
                        data_aplicacao=date.today(),
                        created_by=user_id,
                    )
                    db.add(investment)
                    investments_created += 1
                else:
                    investment.valor_atual = saldo_decimal
                    investments_updated += 1

        db.commit()

        return {
            "success": True,
            "created": created,
            "updated": updated,
             "cash_created": cash_created,
             "cash_updated": cash_updated,
             "investments_created": investments_created,
             "investments_updated": investments_updated,
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

    @staticmethod
    def _normalize_label(label: str) -> str:
        normalized = unicodedata.normalize("NFD", label)
        without_accents = "".join(
            char for char in normalized if unicodedata.category(char) != "Mn"
        )
        return without_accents.lower().strip()

    def _classify_label(self, normalized_label: str) -> Optional[str]:
        if any(normalized_label.startswith(prefix) for prefix in IGNORED_PREFIXES):
            return None
        if any(normalized_label.startswith(prefix) for prefix in BANK_PREFIXES):
            return "bank"
        if any(normalized_label.startswith(prefix) for prefix in CASH_PREFIXES):
            return "cash"
        if any(normalized_label.startswith(prefix) for prefix in INVESTMENT_PREFIXES):
            return "investment"
        return None

