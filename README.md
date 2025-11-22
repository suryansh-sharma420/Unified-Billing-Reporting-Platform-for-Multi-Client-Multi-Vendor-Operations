# Unified Billing & Reporting Engine

## Project Overview

**MoveInSync** is a backend billing and reporting platform built for multi-tenant, vendor-client operations. The project is database-first and uses **PostgreSQL** for persistence and **Python (OOP)** for billing logic.

### Key Features
- Flexible billing logic implemented with the Strategy pattern
- Multi-tenant-aware design (tenant and vendor scoping)
- Audit-oriented data model (billing records and JSON logs)
- Database-first schema with JSONB for extensible contract rules

---

## Architecture

### System Architecture
![Architecture Diagram](./Diagrams/Phase%201%20-%20DB/MoveInSync_DB_HLD(architecture).png)

### Entity Relationship Diagram (ERD)
![ERD Diagram](./Diagrams/Phase%201%20-%20DB/MoveInSync_DB_DetailedERD(architecture).png)

---

## Project Structure

```
MoveInSync_Project/
├── Phase 1 - Database/          # Database schema and seed data
│   ├── MoveInSync_DB/
│   │   ├── 01_schema_design/
│   │   │   ├── 01_tables.sql
│   │   │   └── 02_indexes.sql
│   │   └── 02_seed_data/
│   │       ├── 01_seed_users.sql
│   │       ├── 02_seed_contracts.sql
│   │       └── 03_renewal.sql
│
├── Phase 2 - core logic OOP/    # Python application logic
│   ├── main.py                  # Application entry point
│   ├── diagnosis.py             # Diagnostic utilities
│   └── billing/                 # Billing engine module
│       ├── __init__.py
│       ├── repository.py        # Data access (uses python-dotenv for config)
│       ├── schemas.py           # Dataclasses used by the billing engine
│       └── strategies.py        # Strategy pattern implementations
│
└── Diagrams/                    # Architecture and ERD images

```

---

## Prerequisites

- Python 3.9+
- PostgreSQL 12+

Recommended Python libraries (provided in `requirements.txt`):

- `psycopg2-binary` — PostgreSQL driver
- `python-dotenv` — load `.env` into environment

---

## How to Run (safe, accurate steps)

### 1) Prepare the database

1. Create a PostgreSQL database named `moveinsync_db` (via pgAdmin, DBeaver, or psql).

2. Open the SQL files in a GUI client (DBeaver / pgAdmin) and execute them in order to avoid shell quoting issues on Windows:

   - `Phase 1 - Database/MoveInSync_DB/01_schema_design/01_tables.sql`
   - `Phase 1 - Database/MoveInSync_DB/01_schema_design/02_indexes.sql`
   - `Phase 1 - Database/MoveInSync_DB/02_seed_data/01_seed_users.sql`
   - `Phase 1 - Database/MoveInSync_DB/02_seed_data/02_seed_contracts.sql`
   - `Phase 1 - Database/MoveInSync_DB/02_seed_data/03_renewal.sql`

> Tip: Using a GUI ensures files with spaces in paths are handled safely on Windows.

### 2) Configure environment variables

Create a `.env` file in the project root with these entries (this project already supports `python-dotenv` in `repository.py`):

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=moveinsync_db
DB_USER=postgres
DB_PASSWORD=your_password_here
```

The repository reads the database config from environment variables. Do not commit the `.env` file.

### 3) Create a virtual environment and install dependencies

Windows (PowerShell):

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 4) Run the billing engine

From the repository root:

```powershell
python "Phase 2 - core logic OOP/main.py" d0000000-0000-0000-0000-000000000001
```

Replace the example trip/tenant id with a real ID from your seeded data.

---

## Notes / Known Limitations

- This repository contains the database schema and the Python OOP billing engine. There are no automated tests or CI configured in this project yet.
- Linting/formatting and test tooling are not configured; do not rely on `pytest`, `black`, or `flake8` unless you add them.
- The recommended `requirements.txt` is included but keep it up-to-date by running `pip freeze > requirements.txt` when you add more packages.

---

## Contact

For questions or feedback, open an issue on the GitHub repository or contact the project owner.

---

**Last updated:** November 2025
