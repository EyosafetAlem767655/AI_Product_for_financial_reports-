# Notes

- V1 intentionally has no RightCapital, Schwab, Pinnacle Bank, Zillow, Dropbox, Plaid, email, or AI integrations.
- All client financial data is manually entered by the team.
- Canva export is not connected unless `CANVA_API_KEY` is provided. Without it, the app returns a safe JSON payload and the message: `Canva export is not connected in this environment. PDF download is ready.`
- Exact client-provided SACS/TCC sample PDFs were not available, so the PDF layouts were implemented from the PRD descriptions.
- Authentication and role-based permissions are not included in V1.
- SQLite and generated PDF files are local runtime artifacts.
- Railway deployment config is included. A real Railway deployment still requires the Railway CLI or GitHub integration plus an authenticated Railway account/project.
