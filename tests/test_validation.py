from app.schemas import validate_report_payload


def test_report_cannot_generate_with_missing_required_fields():
    payload = {
        "_missing": {
            "inflow",
            "account_balance_10",
            "liability_balance_20",
            "liability_interest_rate_20",
            "deductible_amount_30",
        },
        "accounts": [{"id": 10, "institution": "Schwab", "account_last4": "1111"}],
        "liabilities": [{"id": 20, "lender": "Regional Bank", "liability_type": "mortgage"}],
        "deductibles": [{"id": 30, "label": "Homeowners"}],
    }
    errors = validate_report_payload(payload)
    assert "Inflow is required." in errors
    assert any("Balance is required for Schwab 1111" in error for error in errors)
    assert any("Interest rate is required for Regional Bank mortgage" in error for error in errors)
    assert any("Deductible amount is required for Homeowners" in error for error in errors)
