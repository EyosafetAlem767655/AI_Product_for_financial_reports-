from datetime import date

from app.calculations import (
    calculate_age,
    calculate_report_totals,
    client_retirement_total,
    non_retirement_total,
    private_reserve_target,
    sacs_excess,
)


def sample_payload():
    return {
        "inflow": 20000,
        "outflow": 12000,
        "private_reserve_balance": 80000,
        "property_value": 600000,
        "deductibles": [
            {"label": "Home", "amount": 2500},
            {"label": "Auto", "amount": 1000},
        ],
        "accounts": [
            {"owner": "client1", "category": "retirement", "balance": 300000},
            {"owner": "client1", "category": "retirement", "balance": 125000},
            {"owner": "client2", "category": "retirement", "balance": 250000},
            {"owner": "joint", "category": "non_retirement", "balance": 90000},
            {"owner": "trust", "category": "non_retirement", "balance": 40000},
        ],
        "liabilities": [
            {"balance": 300000},
            {"balance": 25000},
        ],
    }


def test_age_calculation_from_dob():
    assert calculate_age(date(1980, 6, 18), date(2026, 6, 18)) == 46
    assert calculate_age(date(1980, 6, 19), date(2026, 6, 18)) == 45


def test_sacs_excess_calculation():
    assert sacs_excess(20000, 12000) == 8000


def test_private_reserve_target_calculation():
    assert private_reserve_target(12000, [{"amount": 2500}, {"amount": 1000}]) == 75500


def test_client_retirement_totals():
    accounts = sample_payload()["accounts"]
    assert client_retirement_total(accounts, "client1") == 425000
    assert client_retirement_total(accounts, "client2") == 250000


def test_non_retirement_total_excludes_trust_property_value():
    payload = sample_payload()
    totals = calculate_report_totals(payload)
    assert non_retirement_total(payload["accounts"]) == 130000
    assert totals["non_retirement_total"] == 130000
    assert payload["property_value"] not in [totals["non_retirement_total"]]


def test_grand_total_includes_trust_property_value():
    totals = calculate_report_totals(sample_payload())
    assert totals["grand_total_net_worth"] == 1405000


def test_liabilities_total_not_subtracted_from_net_worth():
    totals = calculate_report_totals(sample_payload())
    assert totals["liabilities_total"] == 325000
    assert totals["grand_total_net_worth"] == 1405000
