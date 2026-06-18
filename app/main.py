from __future__ import annotations

import json
import os
import re
import zipfile
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.calculations import calculate_age, calculate_report_totals, format_currency
from app.database import REPORT_DIR, get_db, init_db
from app.models import Account, Client, Deductible, Liability, Person, Report, ReportSnapshot
from app.pdf import generate_sacs_pdf, generate_tcc_pdf
from app.schemas import (
    list_from_form,
    parse_date,
    parse_float,
    parse_optional_float,
    row_is_blank,
    validate_report_payload,
)
from app.seed import seed_database


PROJECT_ROOT = Path(__file__).resolve().parent.parent

app = FastAPI(title="AW Client Report Portal")
app.mount("/static", StaticFiles(directory=str(PROJECT_ROOT / "static")), name="static")
templates = Jinja2Templates(directory=str(PROJECT_ROOT / "templates"))
templates.env.filters["currency"] = format_currency


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    db = next(get_db())
    try:
        seed_database(db)
    finally:
        db.close()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def clean_filename(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-")
    return cleaned or "report"


def get_client(db: Session, client_id: int) -> Client:
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


def get_report(db: Session, report_id: int) -> Report:
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


def person_for(client: Client, role: str) -> Person | None:
    return next((person for person in client.people if person.role == role), None)


def serialize_client(client: Client) -> dict[str, Any]:
    return {
        "id": client.id,
        "household_name": client.household_name,
        "marital_status": client.marital_status,
        "monthly_inflow": client.monthly_inflow,
        "monthly_outflow": client.monthly_outflow,
        "private_reserve_balance": client.private_reserve_balance,
        "private_reserve_target_override": client.private_reserve_target_override,
        "property_address": client.property_address,
        "property_value": client.property_value,
    }


def serialize_people(client: Client) -> list[dict[str, Any]]:
    people = []
    for person in sorted(client.people, key=lambda item: item.role):
        people.append(
            {
                "id": person.id,
                "role": person.role,
                "first_name": person.first_name,
                "last_name": person.last_name,
                "dob": person.dob.isoformat(),
                "age": calculate_age(person.dob),
                "ssn_last4": person.ssn_last4,
            }
        )
    return people


def serialize_accounts(client: Client) -> list[dict[str, Any]]:
    return [
        {
            "id": account.id,
            "owner": account.owner,
            "category": account.category,
            "account_type": account.account_type,
            "institution": account.institution,
            "account_last4": account.account_last4,
            "balance": account.balance,
            "cash_balance": account.cash_balance,
        }
        for account in client.accounts
    ]


def serialize_liabilities(client: Client) -> list[dict[str, Any]]:
    return [
        {
            "id": liability.id,
            "liability_type": liability.liability_type,
            "lender": liability.lender,
            "interest_rate": liability.interest_rate,
            "balance": liability.balance,
        }
        for liability in client.liabilities
    ]


def serialize_deductibles(client: Client) -> list[dict[str, Any]]:
    return [
        {
            "id": deductible.id,
            "label": deductible.label,
            "amount": deductible.amount,
        }
        for deductible in client.deductibles
    ]


def current_payload_for_client(client: Client) -> dict[str, Any]:
    payload = {
        "client": serialize_client(client),
        "people": serialize_people(client),
        "accounts": serialize_accounts(client),
        "liabilities": serialize_liabilities(client),
        "deductibles": serialize_deductibles(client),
        "inflow": client.monthly_inflow,
        "outflow": client.monthly_outflow,
        "private_reserve_balance": client.private_reserve_balance,
        "property_value": client.property_value,
    }
    payload["totals"] = calculate_report_totals(payload)
    return payload


def latest_snapshot(db: Session, client_id: int) -> dict[str, Any] | None:
    report = (
        db.query(Report)
        .filter(Report.client_id == client_id)
        .order_by(Report.created_at.desc(), Report.id.desc())
        .first()
    )
    if not report or not report.snapshot:
        return None
    return json.loads(report.snapshot.snapshot_json)


def previous_value_maps(snapshot: dict[str, Any] | None) -> dict[str, Any]:
    if not snapshot:
        return {"fields": {}, "accounts": {}, "liabilities": {}, "deductibles": {}}
    return {
        "fields": snapshot,
        "accounts": {str(item["id"]): item for item in snapshot.get("accounts", [])},
        "liabilities": {str(item["id"]): item for item in snapshot.get("liabilities", [])},
        "deductibles": {str(item["id"]): item for item in snapshot.get("deductibles", [])},
    }


def default_report_values(client: Client) -> dict[str, str]:
    values = {
        "inflow": str(client.monthly_inflow),
        "outflow": str(client.monthly_outflow),
        "private_reserve_balance": str(client.private_reserve_balance),
        "property_value": str(client.property_value),
    }
    for account in client.accounts:
        values[f"account_balance_{account.id}"] = str(account.balance)
        values[f"account_cash_balance_{account.id}"] = "" if account.cash_balance is None else str(account.cash_balance)
    for liability in client.liabilities:
        values[f"liability_balance_{liability.id}"] = str(liability.balance)
        values[f"liability_interest_rate_{liability.id}"] = str(liability.interest_rate)
    for deductible in client.deductibles:
        values[f"deductible_amount_{deductible.id}"] = str(deductible.amount)
    return values


def values_from_form(client: Client, form: Any) -> dict[str, str]:
    values = default_report_values(client)
    for key in list(values.keys()) + ["quarter_label", "report_date"]:
        if key in form:
            values[key] = str(form.get(key))
    return values


def required_report_float(form: Any, key: str, missing: set[str]) -> float:
    value = form.get(key)
    if value is None or str(value).strip() == "":
        missing.add(key)
        return 0.0
    return parse_float(value)


def optional_report_float(form: Any, key: str) -> float | None:
    value = form.get(key)
    return parse_optional_float(value)


def build_report_payload_from_form(client: Client, form: Any) -> dict[str, Any]:
    missing: set[str] = set()
    payload = {
        "client": serialize_client(client),
        "people": serialize_people(client),
        "quarter_label": str(form.get("quarter_label") or "Quarterly Report").strip(),
        "report_date": parse_date(str(form.get("report_date") or date.today().isoformat())).isoformat(),
        "inflow": required_report_float(form, "inflow", missing),
        "outflow": required_report_float(form, "outflow", missing),
        "private_reserve_balance": required_report_float(form, "private_reserve_balance", missing),
        "property_value": required_report_float(form, "property_value", missing),
        "accounts": [],
        "liabilities": [],
        "deductibles": [],
    }

    for account in client.accounts:
        balance_key = f"account_balance_{account.id}"
        cash_key = f"account_cash_balance_{account.id}"
        payload["accounts"].append(
            {
                "id": account.id,
                "owner": account.owner,
                "category": account.category,
                "account_type": account.account_type,
                "institution": account.institution,
                "account_last4": account.account_last4,
                "balance": required_report_float(form, balance_key, missing),
                "cash_balance": optional_report_float(form, cash_key),
            }
        )

    for liability in client.liabilities:
        balance_key = f"liability_balance_{liability.id}"
        rate_key = f"liability_interest_rate_{liability.id}"
        payload["liabilities"].append(
            {
                "id": liability.id,
                "liability_type": liability.liability_type,
                "lender": liability.lender,
                "interest_rate": required_report_float(form, rate_key, missing),
                "balance": required_report_float(form, balance_key, missing),
            }
        )

    for deductible in client.deductibles:
        amount_key = f"deductible_amount_{deductible.id}"
        payload["deductibles"].append(
            {
                "id": deductible.id,
                "label": deductible.label,
                "amount": required_report_float(form, amount_key, missing),
            }
        )

    payload["_missing"] = missing
    payload["totals"] = calculate_report_totals(payload)
    return payload


def update_profile_from_report(client: Client, payload: dict[str, Any]) -> None:
    client.monthly_inflow = payload["inflow"]
    client.monthly_outflow = payload["outflow"]
    client.private_reserve_balance = payload["private_reserve_balance"]
    client.property_value = payload["property_value"]
    account_map = {account["id"]: account for account in payload["accounts"]}
    liability_map = {liability["id"]: liability for liability in payload["liabilities"]}
    deductible_map = {deductible["id"]: deductible for deductible in payload["deductibles"]}
    for account in client.accounts:
        if account.id in account_map:
            account.balance = account_map[account.id]["balance"]
            account.cash_balance = account_map[account.id]["cash_balance"]
    for liability in client.liabilities:
        if liability.id in liability_map:
            liability.balance = liability_map[liability.id]["balance"]
            liability.interest_rate = liability_map[liability.id]["interest_rate"]
    for deductible in client.deductibles:
        if deductible.id in deductible_map:
            deductible.amount = deductible_map[deductible.id]["amount"]


def parse_client_form(client: Client, form: Any) -> list[str]:
    errors: list[str] = []
    household_name = str(form.get("household_name") or "").strip()
    marital_status = str(form.get("marital_status") or "single").strip()
    if not household_name:
        errors.append("Household name is required.")

    client.household_name = household_name or "Untitled Household"
    client.marital_status = marital_status if marital_status in {"single", "married"} else "single"
    client.monthly_inflow = parse_float(form.get("monthly_inflow"))
    client.monthly_outflow = parse_float(form.get("monthly_outflow"))
    client.private_reserve_balance = parse_float(form.get("private_reserve_balance"))
    client.private_reserve_target_override = parse_optional_float(form.get("private_reserve_target_override"))
    client.property_address = str(form.get("property_address") or "").strip()
    client.property_value = parse_float(form.get("property_value"))

    for collection in (client.people, client.accounts, client.liabilities, client.deductibles):
        for item in list(collection):
            collection.remove(item)

    def required_text(name: str, label: str) -> str:
        value = str(form.get(name) or "").strip()
        if not value:
            errors.append(f"{label} is required.")
        return value

    try:
        client.people.append(
            Person(
                role="client1",
                first_name=required_text("client1_first_name", "Client 1 first name"),
                last_name=required_text("client1_last_name", "Client 1 last name"),
                dob=parse_date(required_text("client1_dob", "Client 1 DOB")),
                ssn_last4=required_text("client1_ssn_last4", "Client 1 SSN last 4")[:4],
            )
        )
    except ValueError:
        errors.append("Client 1 DOB must be a valid date.")

    if client.marital_status == "married":
        try:
            client.people.append(
                Person(
                    role="client2",
                    first_name=required_text("client2_first_name", "Client 2 first name"),
                    last_name=required_text("client2_last_name", "Client 2 last name"),
                    dob=parse_date(required_text("client2_dob", "Client 2 DOB")),
                    ssn_last4=required_text("client2_ssn_last4", "Client 2 SSN last 4")[:4],
                )
            )
        except ValueError:
            errors.append("Client 2 DOB must be a valid date.")

    deductible_labels = list_from_form(form, "deductible_label[]")
    deductible_amounts = list_from_form(form, "deductible_amount[]")
    for idx in range(max(len(deductible_labels), len(deductible_amounts))):
        label = deductible_labels[idx] if idx < len(deductible_labels) else ""
        amount = deductible_amounts[idx] if idx < len(deductible_amounts) else ""
        if row_is_blank(label, amount):
            continue
        client.deductibles.append(Deductible(label=label or "Insurance deductible", amount=parse_float(amount)))

    owners = list_from_form(form, "account_owner[]")
    categories = list_from_form(form, "account_category[]")
    types = list_from_form(form, "account_type[]")
    institutions = list_from_form(form, "account_institution[]")
    last4s = list_from_form(form, "account_last4[]")
    balances = list_from_form(form, "account_balance[]")
    cash_balances = list_from_form(form, "account_cash_balance[]")
    rows = max(len(owners), len(categories), len(types), len(institutions), len(last4s), len(balances), len(cash_balances))
    for idx in range(rows):
        owner = owners[idx] if idx < len(owners) else ""
        category = categories[idx] if idx < len(categories) else ""
        account_type = types[idx] if idx < len(types) else ""
        institution = institutions[idx] if idx < len(institutions) else ""
        last4 = last4s[idx] if idx < len(last4s) else ""
        balance = balances[idx] if idx < len(balances) else ""
        cash_balance = cash_balances[idx] if idx < len(cash_balances) else ""
        if row_is_blank(owner, category, account_type, institution, last4, balance, cash_balance):
            continue
        client.accounts.append(
            Account(
                owner=owner or "other",
                category=category or "non_retirement",
                account_type=account_type or "Account",
                institution=institution or "Manual",
                account_last4=last4[:4],
                balance=parse_float(balance),
                cash_balance=parse_optional_float(cash_balance),
            )
        )

    liability_types = list_from_form(form, "liability_type[]")
    lenders = list_from_form(form, "liability_lender[]")
    rates = list_from_form(form, "liability_interest_rate[]")
    liability_balances = list_from_form(form, "liability_balance[]")
    rows = max(len(liability_types), len(lenders), len(rates), len(liability_balances))
    for idx in range(rows):
        liability_type = liability_types[idx] if idx < len(liability_types) else ""
        lender = lenders[idx] if idx < len(lenders) else ""
        rate = rates[idx] if idx < len(rates) else ""
        balance = liability_balances[idx] if idx < len(liability_balances) else ""
        if row_is_blank(liability_type, lender, rate, balance):
            continue
        client.liabilities.append(
            Liability(
                liability_type=liability_type or "other",
                lender=lender or "Manual",
                interest_rate=parse_float(rate),
                balance=parse_float(balance),
            )
        )

    return errors


def client_form_context(request: Request, client: Client | None, errors: list[str] | None = None) -> dict[str, Any]:
    if client:
        client1 = person_for(client, "client1")
        client2 = person_for(client, "client2")
        accounts = client.accounts or [Account(owner="client1", category="retirement", account_type="", institution="", account_last4="", balance=0)]
        deductibles = client.deductibles or [Deductible(label="", amount=0)]
        liabilities = client.liabilities or [Liability(liability_type="", lender="", interest_rate=0, balance=0)]
    else:
        client1 = client2 = None
        accounts = [Account(owner="client1", category="retirement", account_type="", institution="", account_last4="", balance=0)]
        deductibles = [Deductible(label="", amount=0)]
        liabilities = [Liability(liability_type="", lender="", interest_rate=0, balance=0)]
    return {
        "request": request,
        "client": client,
        "client1": client1,
        "client2": client2,
        "accounts": accounts,
        "deductibles": deductibles,
        "liabilities": liabilities,
        "errors": errors or [],
    }


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    clients = db.query(Client).order_by(Client.household_name).all()
    reports = db.query(Report).order_by(Report.created_at.desc()).limit(6).all()
    total_reports = db.query(Report).count()
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "clients": clients,
            "client_count": len(clients),
            "report_count": total_reports,
            "recent_reports": reports,
        },
    )


@app.get("/clients", response_class=HTMLResponse)
def clients_list(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    clients = db.query(Client).order_by(Client.household_name).all()
    latest_reports = {}
    for client in clients:
        latest_reports[client.id] = (
            db.query(Report)
            .filter(Report.client_id == client.id)
            .order_by(Report.created_at.desc(), Report.id.desc())
            .first()
        )
    return templates.TemplateResponse(
        "clients.html",
        {"request": request, "clients": clients, "latest_reports": latest_reports},
    )


@app.get("/clients/new", response_class=HTMLResponse)
def new_client(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("client_form.html", client_form_context(request, None))


@app.post("/clients/new", response_class=HTMLResponse)
async def create_client(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    form = await request.form()
    client = Client(household_name="", marital_status="single")
    errors = parse_client_form(client, form)
    if errors:
        return templates.TemplateResponse("client_form.html", client_form_context(request, client, errors), status_code=422)
    db.add(client)
    db.commit()
    db.refresh(client)
    return RedirectResponse(url=f"/clients/{client.id}", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/clients/{client_id}", response_class=HTMLResponse)
def client_detail(client_id: int, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    client = get_client(db, client_id)
    payload = current_payload_for_client(client)
    return templates.TemplateResponse(
        "client_detail.html",
        {
            "request": request,
            "client": client,
            "client1": person_for(client, "client1"),
            "client2": person_for(client, "client2"),
            "payload": payload,
            "totals": payload["totals"],
        },
    )


@app.get("/clients/{client_id}/edit", response_class=HTMLResponse)
def edit_client(client_id: int, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    return templates.TemplateResponse("client_form.html", client_form_context(request, get_client(db, client_id)))


@app.post("/clients/{client_id}/edit", response_class=HTMLResponse)
async def update_client(client_id: int, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    client = get_client(db, client_id)
    form = await request.form()
    errors = parse_client_form(client, form)
    if errors:
        return templates.TemplateResponse("client_form.html", client_form_context(request, client, errors), status_code=422)
    db.add(client)
    db.commit()
    return RedirectResponse(url=f"/clients/{client.id}", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/clients/{client_id}/reports/new", response_class=HTMLResponse)
def new_report(client_id: int, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    client = get_client(db, client_id)
    today = date.today()
    quarter = ((today.month - 1) // 3) + 1
    snapshot = latest_snapshot(db, client.id)
    return templates.TemplateResponse(
        "report_form.html",
        {
            "request": request,
            "client": client,
            "client1": person_for(client, "client1"),
            "client2": person_for(client, "client2"),
            "values": default_report_values(client),
            "quarter_label": f"Q{quarter} {today.year}",
            "report_date": today.isoformat(),
            "previous": previous_value_maps(snapshot),
            "errors": [],
            "missing_fields": set(),
        },
    )


@app.post("/clients/{client_id}/reports", response_class=HTMLResponse)
async def create_report(client_id: int, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    client = get_client(db, client_id)
    form = await request.form()
    payload = build_report_payload_from_form(client, form)
    errors = validate_report_payload(payload)
    if errors:
        snapshot = latest_snapshot(db, client.id)
        return templates.TemplateResponse(
            "report_form.html",
            {
                "request": request,
                "client": client,
                "client1": person_for(client, "client1"),
                "client2": person_for(client, "client2"),
                "values": values_from_form(client, form),
                "quarter_label": str(form.get("quarter_label") or ""),
                "report_date": str(form.get("report_date") or date.today().isoformat()),
                "previous": previous_value_maps(snapshot),
                "errors": errors,
                "missing_fields": payload["_missing"],
            },
            status_code=422,
        )

    payload.pop("_missing", None)
    update_profile_from_report(client, payload)
    report = Report(
        client_id=client.id,
        quarter_label=payload["quarter_label"],
        report_date=parse_date(payload["report_date"]),
    )
    db.add(report)
    db.flush()

    report_dir = REPORT_DIR / str(client.id) / str(report.id)
    base_name = clean_filename(f"{client.household_name}-{report.quarter_label}")
    sacs_path = report_dir / f"{base_name}-SACS.pdf"
    tcc_path = report_dir / f"{base_name}-TCC.pdf"
    generate_sacs_pdf(payload, sacs_path)
    generate_tcc_pdf(payload, tcc_path)
    report.sacs_pdf_path = str(sacs_path)
    report.tcc_pdf_path = str(tcc_path)
    db.add(ReportSnapshot(report_id=report.id, snapshot_json=json.dumps(payload, indent=2, sort_keys=True)))
    db.commit()
    return RedirectResponse(url=f"/clients/{client.id}", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/reports/{report_id}/sacs")
def download_sacs(report_id: int, db: Session = Depends(get_db)) -> FileResponse:
    report = get_report(db, report_id)
    path = Path(report.sacs_pdf_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="SACS PDF not found")
    return FileResponse(path, media_type="application/pdf", filename=path.name)


@app.get("/reports/{report_id}/tcc")
def download_tcc(report_id: int, db: Session = Depends(get_db)) -> FileResponse:
    report = get_report(db, report_id)
    path = Path(report.tcc_pdf_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="TCC PDF not found")
    return FileResponse(path, media_type="application/pdf", filename=path.name)


@app.get("/reports/{report_id}/download-both")
def download_both(report_id: int, db: Session = Depends(get_db)) -> FileResponse:
    report = get_report(db, report_id)
    sacs_path = Path(report.sacs_pdf_path)
    tcc_path = Path(report.tcc_pdf_path)
    if not sacs_path.exists() or not tcc_path.exists():
        raise HTTPException(status_code=404, detail="One or more PDFs are missing")
    zip_path = sacs_path.parent / f"{clean_filename(report.client.household_name)}-{report.quarter_label}-PDFs.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(sacs_path, sacs_path.name)
        archive.write(tcc_path, tcc_path.name)
    return FileResponse(zip_path, media_type="application/zip", filename=zip_path.name)


@app.get("/reports/{report_id}/canva")
def canva_export(report_id: int, db: Session = Depends(get_db)) -> JSONResponse:
    report = get_report(db, report_id)
    payload = json.loads(report.snapshot.snapshot_json) if report.snapshot else {}
    connected = bool(os.getenv("CANVA_API_KEY"))
    message = (
        "Canva export payload is ready."
        if connected
        else "Canva export is not connected in this environment. PDF download is ready."
    )
    return JSONResponse(
        {
            "connected": connected,
            "message": message,
            "report_id": report.id,
            "quarter_label": report.quarter_label,
            "data": payload,
        }
    )
