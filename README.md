# AW Client Report Portal

Internal FastAPI portal for entering client financial planning data, calculating SACS/TCC totals, and generating quarterly SACS and TCC PDF reports.

## Setup

```bash
python -m pip install -r requirements.txt
```

## Run

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`.

On first startup the app creates `data/aw_portal.sqlite3` and seeds two fake demo households:

- Miller Family Household: married household with retirement accounts, non-retirement accounts, property value, deductibles, and liabilities.
- Taylor Greene Household: single household with fewer accounts and liabilities.

Generated reports are saved under `generated_reports/{client_id}/{report_id}/`.

## Railway Deployment

The repo includes `railway.json` with:

- Railpack builder.
- Start command: `python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}`.
- Healthcheck path: `/health`.
- Restart policy: on failure.

For persistent SQLite/report storage on Railway, attach a volume and use one of these options:

- Preferred: rely on Railway's `RAILWAY_VOLUME_MOUNT_PATH`; the app stores `aw_portal.sqlite3` and generated reports inside that volume.
- Optional explicit file: set `RAILWAY_DATABASE_PATH=/data/aw_portal.sqlite3`.

If no Railway volume variables are present, local development defaults remain:

- Database: `data/aw_portal.sqlite3`
- PDFs: `generated_reports/{client_id}/{report_id}/`

Railway CLI deployment, once authenticated:

```bash
railway init
railway up
```

## Demo Flow

1. Open the dashboard.
2. Go to `Clients`.
3. Open `Miller Family Household`.
4. Click `Generate Quarterly Report`.
5. Review the SACS section first, then the TCC section.
6. Change any dynamic value and confirm the live summary updates.
7. Submit `Generate SACS + TCC PDFs`.
8. Use report history to download SACS, TCC, both PDFs as ZIP, or the Canva JSON placeholder.

## Test

```bash
python -m compileall app tests
pytest
```

Pytest is configured to use `.pytest_tmp/` inside the project so Windows temp-folder permissions do not block the PDF tests.

## Canva

`/reports/{report_id}/canva` always returns export-ready report JSON. If `CANVA_API_KEY` is not set, it returns:

```text
Canva export is not connected in this environment. PDF download is ready.
```

No external Canva API calls are made in V1.
