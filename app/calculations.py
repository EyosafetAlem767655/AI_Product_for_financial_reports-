from __future__ import annotations

from datetime import date
from typing import Any


def money(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    return round(float(value), 2)


def calculate_age(dob: date, as_of: date | None = None) -> int:
    as_of = as_of or date.today()
    years = as_of.year - dob.year
    if (as_of.month, as_of.day) < (dob.month, dob.day):
        years -= 1
    return years


def sacs_excess(inflow: float, outflow: float) -> float:
    return money(inflow) - money(outflow)


def private_reserve_target(monthly_expenses: float, deductibles: list[dict[str, Any]]) -> float:
    deductible_total = sum(money(item.get("amount")) for item in deductibles)
    return money((6 * money(monthly_expenses)) + deductible_total)


def client_retirement_total(accounts: list[dict[str, Any]], owner: str) -> float:
    return money(
        sum(
            money(account.get("balance"))
            for account in accounts
            if account.get("category") == "retirement" and account.get("owner") == owner
        )
    )


def non_retirement_total(accounts: list[dict[str, Any]]) -> float:
    return money(
        sum(
            money(account.get("balance"))
            for account in accounts
            if account.get("category") == "non_retirement"
        )
    )


def liabilities_total(liabilities: list[dict[str, Any]]) -> float:
    return money(sum(money(item.get("balance")) for item in liabilities))


def calculate_report_totals(payload: dict[str, Any]) -> dict[str, float]:
    accounts = payload.get("accounts", [])
    liabilities = payload.get("liabilities", [])
    deductibles = payload.get("deductibles", [])
    client1_retirement = client_retirement_total(accounts, "client1")
    client2_retirement = client_retirement_total(accounts, "client2")
    non_retirement = non_retirement_total(accounts)
    property_value = money(payload.get("property_value"))
    grand_total = money(client1_retirement + client2_retirement + non_retirement + property_value)
    liability_total = liabilities_total(liabilities)
    return {
        "sacs_excess": money(sacs_excess(payload.get("inflow", 0), payload.get("outflow", 0))),
        "private_reserve_target": private_reserve_target(payload.get("outflow", 0), deductibles),
        "client1_retirement_total": client1_retirement,
        "client2_retirement_total": client2_retirement,
        "non_retirement_total": non_retirement,
        "grand_total_net_worth": grand_total,
        "liabilities_total": liability_total,
    }


def format_currency(value: Any) -> str:
    return f"${money(value):,.2f}"
