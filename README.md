# Unified Billing & Reporting Engine (MoveInSync)

This repository contains three development phases for a multi-client, multi-vendor billing platform:

- Phase 1 — Database schema and seed data (PostgreSQL)
- Phase 2 — Core billing logic implemented with Python (OOP, Strategy pattern)
- Phase 3 — FastAPI service: connection pooling, caching, client isolation, and error handling

This README is intentionally concise and suitable for public GitHub distribution. For detailed internal notes, check `PHASE_3_SUMMARY.md` (keep private).

Quick links

- Phase 1: `Phase 1 - Database/`
- Phase 2: `Phase 2 - core logic OOP/`
- Phase 3: `Phase 3 - APIs/`

Prerequisites


### 1. Clone the Repository
```bash
git clone [https://github.com/yourusername/MoveInSync.git](https://github.com/suryansh-sharma420/Unified-Billing-Reporting-Platform-for-Multi-Client-Multi-Vendor-Operations.git)
cd MoveInSync
```

- Python 3.9+
- PostgreSQL 12+


Recommended Python libraries (provided in `requirements.txt`):

Quick start


1. Create the database and run the SQL scripts in `Phase 1 - Database/MoveInSync_DB/` (tables, indexes, seed data).
2. Create a `.env` in the repository root with DB credentials (do not commit `.env`). See `.env.example`.
3. Create and activate a virtual environment and install requirements:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

4. Start the Phase 3 API (after DB is seeded):

```powershell
cd "Phase 3 - APIs"
uvicorn main_api:app --reload --host 0.0.0.0 --port 8000
```

What to include when pushing to GitHub

Include the following (public code and assets):
- `Phase 1 - Database/` (schema and seed SQL files)
- `Phase 2 - core logic OOP/` (billing logic: `billing/`, `main.py`, `diagnosis.py`)
- `Phase 3 - APIs/` (API code: `main_api.py`, `service.py`, `dependencies.py`, `api_models.py`, `exceptions.py`, `README.md`, `QUICKSTART.md`)
- `requirements.txt`, `.env.example`, `Diagrams/` and project-level documentation (concise READMEs)

Keep these files private (do NOT push to GitHub):
- `.env` or any file containing secrets (database passwords, API keys)
- `PHASE_3_SUMMARY.md` or any private notes / chat transcripts
- Local environment directories and caches: `venv/`, `__pycache__/`, `*.pyc`, `.vscode/`

Suggested `.gitignore` entries (add to project root):
```
# Environment
venv/
.env
.env.*

# Python
__pycache__/
*.pyc

# IDE
.vscode/
.idea/

# Private notes
PHASE_3_SUMMARY.md
```

Support and next steps

- Run the Quickstart in `Phase 3 - APIs/QUICKSTART.md` to test endpoints locally.
- Verify client isolation by making requests with different client IDs.
- If you plan to publish the repo, confirm `PHASE_3_SUMMARY.md` and any chat logs are removed or excluded via `.gitignore`.

If you want, I can prepare a ready-to-commit `.gitignore` and a minimal release checklist before you push to GitHub.

**Last updated:** November 2025
### 2) Configure environment variables
