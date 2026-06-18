import json
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.calculations import calculate_report_totals
from app.database import Base
from app.models import Account, Client, Deductible, Liability, Person, Report, ReportSnapshot
from app.pdf import generate_sacs_pdf, generate_tcc_pdf


def pdf_payload():
    payload = {
        "client": {
            "id": 1,
            "household_name": "Demo Household",
            "marital_status": "married",
            "property_address": "100 Main Street",
            "property_value": 500000,
        },
        "people": [
            {"first_name": "Alex", "last_name": "Demo", "age": 50, "dob": "1976-01-01", "ssn_last4": "1234"},
            {"first_name": "Sam", "last_name": "Demo", "age": 48, "dob": "1978-01-01", "ssn_last4": "5678"},
        ],
        "quarter_label": "Q2 2026",
        "report_date": "2026-06-18",
        "inflow": 18000,
        "outflow": 11000,
        "private_reserve_balance": 95000,
        "property_value": 500000,
        "deductibles": [{"id": 1, "label": "Home", "amount": 2500}],
        "accounts": [
            {
                "id": 1,
                "owner": "client1",
                "category": "retirement",
                "account_type": "401K",
                "institution": "Schwab",
                "account_last4": "1111",
                "balance": 300000,
                "cash_balance": 12000,
            },
            {
                "id": 2,
                "owner": "client2",
                "category": "retirement",
                "account_type": "IRA",
                "institution": "Vanguard",
                "account_last4": "2222",
                "balance": 250000,
                "cash_balance": 5000,
            },
            {
                "id": 3,
                "owner": "joint",
                "category": "non_retirement",
                "account_type": "Brokerage",
                "institution": "Fidelity",
                "account_last4": "3333",
                "balance": 100000,
                "cash_balance": 8500,
            },
        ],
        "liabilities": [
            {"id": 1, "liability_type": "mortgage", "lender": "Demo Bank", "interest_rate": 4.5, "balance": 275000}
        ],
    }
    payload["totals"] = calculate_report_totals(payload)
    return payload


def test_pdf_generation_creates_non_empty_files(tmp_path):
    payload = pdf_payload()
    sacs_path = generate_sacs_pdf(payload, tmp_path / "sacs.pdf")
    tcc_path = generate_tcc_pdf(payload, tmp_path / "tcc.pdf")
    assert sacs_path.exists()
    assert tcc_path.exists()
    assert sacs_path.stat().st_size > 1000
    assert tcc_path.stat().st_size > 1000


def test_report_history_stores_and_retrieves_generated_records():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    client = Client(
        household_name="History Household",
        marital_status="single",
        monthly_inflow=10000,
        monthly_outflow=6500,
        private_reserve_balance=50000,
        property_address="10 History Lane",
        property_value=350000,
    )
    client.people = [Person(role="client1", first_name="Casey", last_name="History", dob=date(1988, 1, 1), ssn_last4="9999")]
    client.accounts = [Account(owner="client1", category="retirement", account_type="IRA", institution="Schwab", account_last4="4444", balance=150000)]
    client.deductibles = [Deductible(label="Home", amount=2000)]
    client.liabilities = [Liability(liability_type="mortgage", lender="Bank", interest_rate=5.0, balance=240000)]
    db.add(client)
    db.commit()

    report = Report(client_id=client.id, quarter_label="Q2 2026", report_date=date(2026, 6, 18), sacs_pdf_path="sacs.pdf", tcc_pdf_path="tcc.pdf")
    db.add(report)
    db.flush()
    db.add(ReportSnapshot(report_id=report.id, snapshot_json=json.dumps(pdf_payload())))
    db.commit()

    stored = db.query(Report).filter(Report.client_id == client.id).one()
    assert stored.quarter_label == "Q2 2026"
    assert stored.snapshot is not None
    assert json.loads(stored.snapshot.snapshot_json)["totals"]["liabilities_total"] == 275000
    db.close()
