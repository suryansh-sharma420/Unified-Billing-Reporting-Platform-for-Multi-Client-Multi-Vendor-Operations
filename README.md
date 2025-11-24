# MoveInSync - Unified Billing & Reporting Platform

A comprehensive multi-client, multi-vendor billing and reporting platform with JWT-based RBAC security and enterprise-grade architecture.

## Project Structure

| Phase | Directory | Purpose |
|-------|-----------|---------|
| **1** | Phase 1 - Database | PostgreSQL schema, indexes, and seed data |
| **2** | Phase 2 - core logic OOP | Core billing logic with Strategy pattern |
| **3** | Phase 3 - APIs | FastAPI REST service with security |
| **4** | Phase 4 - UI | Streamlit frontend application |
| **5** | Phase 5 - optimizations | Performance and optimization scripts |
| **6** | Phase 6 - RBAC | JWT-based security and role management |

## Prerequisites

- Python 3.9+
- PostgreSQL 12+
- pip and virtual environment

## Quick Start

### 1. Setup Database
```powershell
# Navigate to database folder
cd "Phase 1 - Database\MoveInSync_DB"
# Run SQL scripts in order: tables, indexes, seed data
```

### 2. Configure Environment
```powershell
# Create .env from example (in root directory)
copy .env.example .env
# Edit .env with your PostgreSQL credentials
```

### 3. Install Dependencies
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Start Backend API
```powershell
cd "Phase 3 - APIs"
python -m uvicorn main_api:app --reload --host 0.0.0.0 --port 8000
```

### 5. Start Frontend (in new terminal)
```powershell
cd "Phase 4 - UI"
streamlit run app.py
```

## Authentication

- **Default Login:** admin@client.com / Password@123
- **JWT Token Expiry:** 60 minutes
- **Roles:** SUPER_ADMIN, CLIENT_ADMIN, VENDOR_ADMIN, VIEWER
- See Phase 6 - RBAC for security documentation

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
