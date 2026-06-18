# Acceptance Checklist

## Client Profile Management

- [x] Add, edit, view, and list clients.
- [x] Client list shows last report date when a report exists.
- [x] Stores household, client 1, optional client 2, DOB, calculated age, SSN last 4, inflow, outflow, private reserve, target override, deductibles, property details, accounts, and liabilities.
- [x] SQLite tables store clients, people/spouses, accounts, liabilities, deductibles, reports, and report snapshot JSON.

## Quarterly Report Data Entry

- [x] Client detail page includes `Generate Quarterly Report`.
- [x] Report entry shows SACS fields first and TCC fields second.
- [x] Static profile data is prefilled into dynamic report inputs.
- [x] Previous report values appear beside dynamic fields when history exists.
- [x] `Use last value` buttons are available for previous dynamic values.
- [x] Required missing fields are highlighted and block report generation.
- [x] Totals update live in the browser.

## Calculations

- [x] SACS Excess = Inflow - Outflow.
- [x] Private Reserve Target = 6 x monthly expenses + deductibles.
- [x] Client 1 retirement total sums client1 retirement accounts.
- [x] Client 2 retirement total sums client2 retirement accounts.
- [x] Non-retirement total excludes trust/property value.
- [x] Grand total includes trust/property value.
- [x] Liabilities total is displayed separately and is not subtracted from net worth.
- [x] Backend independently recalculates totals before PDF generation.

## PDF Generation

- [x] SACS PDF is generated as a separate file.
- [x] SACS PDF includes household/date header, cashflow diagram, inflow/outflow/excess/private reserve flow, and page 2 summary.
- [x] TCC PDF is generated as a separate file.
- [x] TCC PDF includes client bubbles, retirement/non-retirement account bubbles, property center, liabilities, and summary boxes.
- [x] TCC layout handles expected V1 account/liability counts and continues overflow accounts.

## Report History And Downloads

- [x] Report records are saved in SQLite.
- [x] Calculation snapshots are saved as JSON.
- [x] SACS/TCC PDF paths are saved.
- [x] Client detail shows report history.
- [x] SACS and TCC PDFs can be downloaded.
- [x] `Download Both PDFs` returns a ZIP.

## Canva Export

- [x] `Export to Canva` button is present in report history.
- [x] Missing `CANVA_API_KEY` returns the required friendly message.
- [x] JSON report export is available without external API calls.

## Seed Data

- [x] First startup seeds one married household.
- [x] First startup seeds one single household.
- [x] Seed data has realistic fake values and is ready for immediate report generation.

## UI

- [x] Dashboard, client list, add/edit form, detail page, report entry flow, live summary, history, downloads, and Canva placeholder are implemented.
- [x] Responsive white/light-green/blue financial-planning UI.
- [x] Empty states and validation states are present.

## Testing And Verification

- [x] Age calculation test.
- [x] SACS excess test.
- [x] Private Reserve Target test.
- [x] Client 1 retirement total test.
- [x] Client 2 retirement total test.
- [x] Non-retirement excludes trust/property test.
- [x] Grand total includes trust/property test.
- [x] Liabilities are not subtracted test.
- [x] Missing required fields block report generation test.
- [x] PDF generation creates non-empty files test.
- [x] Report history stores and retrieves generated records test.
- [x] `python -m compileall app tests` passes.
- [x] `pytest` passes.
- [x] FastAPI app boots locally.
- [x] Seeded database exists.
- [x] PDF generation works from seed data.

## Railway Deployment Readiness

- [x] `railway.json` added with Railpack, start command, healthcheck, and restart policy.
- [x] `/health` route added for deployment checks.
- [x] Storage layer supports `RAILWAY_VOLUME_MOUNT_PATH` and `RAILWAY_DATABASE_PATH`.
- [ ] Actual Railway deployment verified in a live Railway project. Blocked locally because Railway CLI is not installed/authenticated in this environment.

## Vercel Deployment Readiness

- [x] `app/index.py` added as the Vercel-detectable FastAPI entrypoint.
- [x] `vercel.json` added with Python Function routing and runtime limits.
- [x] Storage layer automatically uses `/tmp/aw-portal` on Vercel when no external `DATABASE_URL` is configured.
- [x] Storage layer supports `DATABASE_URL` and `POSTGRES_URL` for durable Postgres-backed Vercel deployments.
- [x] Missing PDF files can be regenerated from saved report snapshots.
- [ ] Durable Vercel production persistence configured. Requires an external database/storage service; `/tmp` is ephemeral.
