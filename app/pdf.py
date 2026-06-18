from __future__ import annotations

from pathlib import Path
from textwrap import shorten
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from app.calculations import format_currency


BLUE = colors.HexColor("#1D5FEA")
DEEP_BLUE = colors.HexColor("#0D2E66")
LIGHT_GREEN = colors.HexColor("#C9F7D8")
GREEN = colors.HexColor("#4CCB7A")
OFF_WHITE = colors.HexColor("#F7FBFF")
BORDER = colors.HexColor("#DCEAF5")
TEXT = colors.HexColor("#102033")
RED = colors.HexColor("#E85C5C")
GRAY = colors.HexColor("#EEF4FA")


def _header(c: canvas.Canvas, payload: dict[str, Any], title: str) -> None:
    width, height = LETTER
    c.setFillColor(OFF_WHITE)
    c.rect(0, height - 0.82 * inch, width, 0.82 * inch, fill=1, stroke=0)
    c.setStrokeColor(BORDER)
    c.line(0.5 * inch, height - 0.82 * inch, width - 0.5 * inch, height - 0.82 * inch)
    c.setFillColor(DEEP_BLUE)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(0.65 * inch, height - 0.42 * inch, title)
    c.setFont("Helvetica", 9)
    c.setFillColor(TEXT)
    household = payload["client"]["household_name"]
    c.drawRightString(width - 0.65 * inch, height - 0.36 * inch, household)
    c.drawRightString(width - 0.65 * inch, height - 0.56 * inch, str(payload.get("report_date", "")))


def _currency_label(c: canvas.Canvas, value: Any, x: float, y: float, size: int = 12, fill=TEXT) -> None:
    c.setFillColor(fill)
    c.setFont("Helvetica-Bold", size)
    c.drawCentredString(x, y, format_currency(value))


def _arrow(c: canvas.Canvas, x1: float, y1: float, x2: float, y2: float, color=BLUE) -> None:
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(2)
    c.line(x1, y1, x2, y2)
    direction = 1 if x2 >= x1 else -1
    c.line(x2, y2, x2 - direction * 9, y2 + 5)
    c.line(x2, y2, x2 - direction * 9, y2 - 5)


def _pill(c: canvas.Canvas, x: float, y: float, w: float, h: float, fill, title: str, value: str, subtitle: str = "") -> None:
    c.setFillColor(fill)
    c.setStrokeColor(BORDER)
    c.roundRect(x, y, w, h, 10, fill=1, stroke=1)
    c.setFillColor(DEEP_BLUE)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x + 12, y + h - 18, shorten(title, width=32, placeholder="..."))
    c.setFillColor(TEXT)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(x + 12, y + h - 38, value)
    if subtitle:
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor("#516171"))
        c.drawString(x + 12, y + 12, shorten(subtitle, width=42, placeholder="..."))


def generate_sacs_pdf(payload: dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_path), pagesize=LETTER)
    width, height = LETTER
    totals = payload["totals"]

    _header(c, payload, "SACS Quarterly Cashflow Report")
    c.setFillColor(DEEP_BLUE)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, height - 1.35 * inch, "SACS Cashflow System")

    centers = [
        (1.45 * inch, 5.65 * inch, GREEN, "INFLOW", payload["inflow"]),
        (3.95 * inch, 5.65 * inch, RED, "OUTFLOW", payload["outflow"]),
        (6.45 * inch, 5.65 * inch, BLUE, "PRIVATE RESERVE", payload["private_reserve_balance"]),
    ]
    radius = 0.82 * inch
    for x, y, fill, label, value in centers:
        c.setFillColor(fill)
        c.circle(x, y, radius, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(x, y + 12, label)
        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(x, y - 8, format_currency(value))

    _arrow(c, 2.28 * inch, 5.65 * inch, 3.1 * inch, 5.65 * inch)
    _arrow(c, 4.78 * inch, 5.65 * inch, 5.62 * inch, 5.65 * inch)

    c.setFillColor(LIGHT_GREEN)
    c.setStrokeColor(BORDER)
    c.roundRect(2.62 * inch, 3.5 * inch, 2.25 * inch, 0.78 * inch, 12, fill=1, stroke=1)
    c.setFillColor(DEEP_BLUE)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(3.75 * inch, 3.98 * inch, "MONTHLY EXCESS")
    _currency_label(c, totals["sacs_excess"], 3.75 * inch, 3.72 * inch, size=14, fill=DEEP_BLUE)
    _arrow(c, 3.75 * inch, 4.3 * inch, 3.75 * inch, 4.88 * inch, GREEN)
    _arrow(c, 4.2 * inch, 3.9 * inch, 5.55 * inch, 5.08 * inch, GREEN)

    c.setFillColor(TEXT)
    c.setFont("Helvetica", 9)
    c.drawCentredString(width / 2, 2.52 * inch, "Inflow funds agreed spending first. Remaining excess is directed toward reserve strength and investment discipline.")

    c.showPage()
    _header(c, payload, "SACS Quarterly Cashflow Report")
    c.setFillColor(DEEP_BLUE)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(0.7 * inch, height - 1.35 * inch, "Private Reserve & Investment Summary")

    _pill(c, 0.7 * inch, 8.0 * inch, 2.25 * inch, 0.72 * inch, OFF_WHITE, "Private Reserve Balance", format_currency(payload["private_reserve_balance"]))
    _pill(c, 3.15 * inch, 8.0 * inch, 2.25 * inch, 0.72 * inch, LIGHT_GREEN, "Target Savings Number", format_currency(totals["private_reserve_target"]))
    _pill(c, 5.6 * inch, 8.0 * inch, 2.25 * inch, 0.72 * inch, OFF_WHITE, "Monthly Excess", format_currency(totals["sacs_excess"]))

    investment_total = (
        totals["client1_retirement_total"]
        + totals["client2_retirement_total"]
        + totals["non_retirement_total"]
    )
    _pill(c, 0.7 * inch, 7.02 * inch, 7.15 * inch, 0.72 * inch, GRAY, "Investment Account Balance Summary", format_currency(investment_total), "Retirement and non-retirement accounts only; property value is tracked in TCC.")

    c.setFillColor(DEEP_BLUE)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(0.8 * inch, 6.28 * inch, "Account Summary")
    y = 5.9 * inch
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(colors.HexColor("#516171"))
    c.drawString(0.8 * inch, y, "TYPE")
    c.drawString(2.0 * inch, y, "INSTITUTION")
    c.drawString(4.3 * inch, y, "LAST 4")
    c.drawRightString(7.5 * inch, y, "BALANCE")
    y -= 0.22 * inch
    c.setStrokeColor(BORDER)
    c.line(0.8 * inch, y + 8, 7.5 * inch, y + 8)
    c.setFont("Helvetica", 8)
    c.setFillColor(TEXT)
    for account in payload.get("accounts", [])[:16]:
        c.drawString(0.8 * inch, y, shorten(account["account_type"], width=18, placeholder="..."))
        c.drawString(2.0 * inch, y, shorten(account["institution"], width=28, placeholder="..."))
        c.drawString(4.3 * inch, y, account.get("account_last4", ""))
        c.drawRightString(7.5 * inch, y, format_currency(account["balance"]))
        y -= 0.25 * inch
    c.save()
    return output_path


def _bubble(c: canvas.Canvas, x: float, y: float, w: float, h: float, fill, title: str, lines: list[str]) -> None:
    c.setFillColor(fill)
    c.setStrokeColor(BORDER)
    c.roundRect(x, y, w, h, 14, fill=1, stroke=1)
    c.setFillColor(DEEP_BLUE)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(x + 10, y + h - 15, shorten(title, width=28, placeholder="..."))
    c.setFillColor(TEXT)
    c.setFont("Helvetica", 7.5)
    line_y = y + h - 29
    for line in lines[:4]:
        c.drawString(x + 10, line_y, shorten(line, width=32, placeholder="..."))
        line_y -= 10


def _summary_box(c: canvas.Canvas, x: float, y: float, label: str, value: Any) -> None:
    _pill(c, x, y, 1.72 * inch, 0.58 * inch, GRAY, label, format_currency(value))


def generate_tcc_pdf(payload: dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_path), pagesize=LETTER)
    width, height = LETTER
    totals = payload["totals"]

    _header(c, payload, "TCC Total Client Capital Report")
    c.setFillColor(DEEP_BLUE)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 1.23 * inch, "Total Client Capital Overview")

    people = payload.get("people", [])
    person_slots = [(0.65 * inch, 8.65 * inch), (5.05 * inch, 8.65 * inch)]
    for idx, person in enumerate(people[:2]):
        name = f"{person['first_name']} {person['last_name']}"
        lines = [f"Age {person.get('age', '')}", f"DOB {person.get('dob', '')}", f"SSN last four {person.get('ssn_last4', '')}"]
        _bubble(c, person_slots[idx][0], person_slots[idx][1], 2.45 * inch, 0.78 * inch, LIGHT_GREEN, name, lines)

    _summary_box(c, 0.65 * inch, 7.78 * inch, "Client 1 Retirement Total", totals["client1_retirement_total"])
    _summary_box(c, 2.48 * inch, 7.78 * inch, "Client 2 Retirement Total", totals["client2_retirement_total"])
    _summary_box(c, 4.31 * inch, 7.78 * inch, "Non-Retirement Total", totals["non_retirement_total"])
    _summary_box(c, 6.14 * inch, 7.78 * inch, "Liabilities Total", totals["liabilities_total"])

    _pill(
        c,
        2.8 * inch,
        6.92 * inch,
        2.9 * inch,
        0.72 * inch,
        LIGHT_GREEN,
        "Grand Total Net Worth",
        format_currency(totals["grand_total_net_worth"]),
        "Liabilities displayed separately; not subtracted.",
    )

    _bubble(
        c,
        2.55 * inch,
        5.95 * inch,
        3.35 * inch,
        0.75 * inch,
        OFF_WHITE,
        "Trust / Property Value",
        [payload["client"].get("property_address", ""), format_currency(payload.get("property_value", 0))],
    )

    retirement = [a for a in payload.get("accounts", []) if a["category"] == "retirement"]
    non_retirement = [a for a in payload.get("accounts", []) if a["category"] == "non_retirement"]
    accounts_to_draw = retirement[:12] + non_retirement[:8]
    overflow = retirement[12:] + non_retirement[8:]

    c.setFillColor(DEEP_BLUE)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(0.65 * inch, 5.58 * inch, "Account Structure")
    x_positions = [0.65 * inch, 2.7 * inch, 4.75 * inch, 6.8 * inch]
    y = 4.92 * inch
    index = 0
    for account in accounts_to_draw:
        x = x_positions[index % 4]
        row = index // 4
        ay = y - (row * 0.72 * inch)
        cash = account.get("cash_balance")
        lines = [
            f"{account['institution']} ...{account.get('account_last4', '')}",
            format_currency(account["balance"]),
            f"Cash {format_currency(cash)}" if cash is not None else "Cash n/a",
        ]
        fill = LIGHT_GREEN if account["category"] == "retirement" else OFF_WHITE
        _bubble(c, x, ay, 1.72 * inch, 0.58 * inch, fill, account["account_type"], lines)
        index += 1

    c.setFillColor(DEEP_BLUE)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(0.65 * inch, 1.92 * inch, "Liabilities")
    y = 1.52 * inch
    liabilities = payload.get("liabilities", [])
    if not liabilities:
        c.setFillColor(colors.HexColor("#516171"))
        c.setFont("Helvetica", 8)
        c.drawString(0.65 * inch, y, "No liabilities entered for this reporting period.")
    for liability in liabilities[:3]:
        _bubble(
            c,
            0.65 * inch + (liabilities.index(liability) * 2.45 * inch),
            y,
            2.18 * inch,
            0.58 * inch,
            GRAY,
            liability["liability_type"].title(),
            [liability["lender"], f"{liability['interest_rate']:.2f}% interest", format_currency(liability["balance"])],
        )

    if overflow:
        c.showPage()
        _header(c, payload, "TCC Total Client Capital Report")
        c.setFillColor(DEEP_BLUE)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(0.65 * inch, height - 1.25 * inch, "Continuation Accounts")
        y = height - 1.75 * inch
        for account in overflow:
            _bubble(
                c,
                0.65 * inch,
                y,
                7.15 * inch,
                0.42 * inch,
                OFF_WHITE,
                account["account_type"],
                [
                    f"{account['owner']} | {account['category']} | {account['institution']} ...{account.get('account_last4', '')}",
                    format_currency(account["balance"]),
                ],
            )
            y -= 0.52 * inch
            if y < 0.8 * inch:
                c.showPage()
                _header(c, payload, "TCC Total Client Capital Report")
                y = height - 1.25 * inch

    c.save()
    return output_path
