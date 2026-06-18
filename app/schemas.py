from __future__ import annotations

from datetime import date
from typing import Any


def parse_date(value: str | None, fallback: date | None = None) -> date:
    if value:
        return date.fromisoformat(value)
    if fallback:
        return fallback
    return date.today()


def parse_optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return round(float(value), 2)


def parse_float(value: Any, default: float = 0.0) -> float:
    parsed = parse_optional_float(value)
    return default if parsed is None else parsed


def list_from_form(form: Any, name: str) -> list[str]:
    values = form.getlist(name)
    return [str(value).strip() for value in values]


def row_is_blank(*values: str | None) -> bool:
    return all((value is None or str(value).strip() == "") for value in values)


def validate_report_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required_number_fields = {
        "inflow": "Inflow",
        "outflow": "Outflow",
        "private_reserve_balance": "Private reserve balance",
        "property_value": "Zillow/home value",
    }
    missing = payload.get("_missing", set())
    for key, label in required_number_fields.items():
        if key in missing:
            errors.append(f"{label} is required.")

    for account in payload.get("accounts", []):
        account_name = f"{account.get('institution', 'Account')} {account.get('account_last4', '')}".strip()
        if f"account_balance_{account['id']}" in missing:
            errors.append(f"Balance is required for {account_name}.")

    for liability in payload.get("liabilities", []):
        liability_name = f"{liability.get('lender', 'Liability')} {liability.get('liability_type', '')}".strip()
        if f"liability_balance_{liability['id']}" in missing:
            errors.append(f"Balance is required for {liability_name}.")
        if f"liability_interest_rate_{liability['id']}" in missing:
            errors.append(f"Interest rate is required for {liability_name}.")

    for deductible in payload.get("deductibles", []):
        if f"deductible_amount_{deductible['id']}" in missing:
            errors.append(f"Deductible amount is required for {deductible.get('label', 'deductible')}.")

    return errors
