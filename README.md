# Unified Billing & Reporting Engine

## Project Overview

**MoveInSync** is a comprehensive, enterprise-grade billing and reporting platform built with a focus on **multi-tenancy**, **scalability**, and **maintainability**. The system leverages object-oriented design patterns and PostgreSQL to provide a robust solution for managing complex billing scenarios across multiple contracts and tenant organizations.

### Key Characteristics
- **Database-First Architecture**: Normalized PostgreSQL schema with audit trails
- **Strategic Billing Logic**: Extensible strategy pattern for diverse billing models
- **Multi-Tenant Support**: Isolated data and operations per tenant
- **Production-Ready**: Comprehensive seed data and real-world scenarios

---

## Architecture Overview

### System Architecture
![Architecture Diagram](./Diagrams/Phase%201%20-%20DB/architecture-diagram.png)

### Entity Relationship Diagram (ERD)
![ERD Diagram](./Diagrams/Phase%201%20-%20DB/erd-diagram.png)

---

## Features

✅ **Multi-Tenancy Support** - Isolated tenant environments with secure data separation  
✅ **Strategy Pattern Implementation** - Flexible, extensible billing algorithms  
✅ **Comprehensive Audit Logs** - Track all billing transactions and state changes  
✅ **Contract Management** - Support for multiple contract types and renewal cycles  
✅ **User Management** - Role-based access control and tenant assignments  
✅ **Automated Seed Data** - Pre-populated test data for development  

---

## Prerequisites

Before running this project, ensure you have:

- **Python**: Version 3.9 or higher
  - Download from [python.org](https://www.python.org/downloads/)
  
- **PostgreSQL**: Version 12 or higher
  - Download from [postgresql.org](https://www.postgresql.org/download/)
  - Ensure PostgreSQL service is running
  
- **pip**: Python package manager (included with Python 3.9+)

---

## Project Structure

```
MoveInSync_Project/
├── Phase 1 - Database/          # Database schema and seed data
│   ├── 01_schema_design/        # Core database tables and indexes
│   │   ├── 01_tables.sql       # User, Contract, Billing tables
│   │   └── 02_indexes.sql      # Performance optimization indexes
│   └── 02_seed_data/            # Test data scripts
│       ├── 01_seed_users.sql   # Sample user accounts
│       ├── 02_seed_contracts.sql # Sample contracts
│       └── 03_renewal.sql       # Contract renewal logic
│
├── Phase 2 - Core Logic OOP/    # Python application logic
│   ├── main.py                  # Application entry point
│   ├── diagnosis.py             # Diagnostic utilities
│   ├── repository.py            # Data access layer
│   ├── schemas.py               # Data models and validation
│   └── billing/                 # Billing engine module
│       ├── __init__.py
│       ├── strategies.py        # Strategy pattern implementations
│       └── repository.py        # Billing-specific queries
│
├── Diagrams/                    # Architecture and design documentation
│   └── Phase 1 - DB/            # Visual architecture documentation
│
├── .gitignore                   # Git exclusion rules
└── README.md                    # This file
```

### Phase 1: Database
Establishes the foundation with PostgreSQL schema including:
- **Users Table**: Tenant user accounts with authentication
- **Contracts Table**: Billing contracts with terms and renewal dates
- **Billing Records**: Transaction logs and audit trails
- **Indexes**: Query optimization for production performance

### Phase 2: Core Logic (OOP)
Python application implementing:
- **Strategy Pattern**: Different billing calculation algorithms
- **Repository Pattern**: Data access abstraction layer
- **Schemas**: Pydantic models for data validation
- **Main Module**: Orchestrates billing operations for tenants

---

## How to Run

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/MoveInSync.git
cd MoveInSync
```

### 2. Set Up PostgreSQL Database

#### Create Database
```sql
CREATE DATABASE moveinsync_db;
```

#### Run Schema Setup
```bash
psql -U postgres -d moveinsync_db -f "Phase 1 - Database/MoveInSync_DB/01_schema_design/01_tables.sql"
psql -U postgres -d moveinsync_db -f "Phase 1 - Database/MoveInSync_DB/01_schema_design/02_indexes.sql"
```

#### Load Seed Data
```bash
psql -U postgres -d moveinsync_db -f "Phase 1 - Database/MoveInSync_DB/02_seed_data/01_seed_users.sql"
psql -U postgres -d moveinsync_db -f "Phase 1 - Database/MoveInSync_DB/02_seed_data/02_seed_contracts.sql"
psql -U postgres -d moveinsync_db -f "Phase 1 - Database/MoveInSync_DB/02_seed_data/03_renewal.sql"
```

### 3. Set Up Python Environment

#### Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=moveinsync_db
DB_USER=postgres
DB_PASSWORD=your_password
```

### 5. Run the Application
```bash
python "Phase 2 - core logic OOP/main.py" <tenant_id>
```

Example:
```bash
python "Phase 2 - core logic OOP/main.py" d0000000-0000-0000-0000-000000000001
```

---

## API / Usage Examples

### Running Billing Calculations
```python
from Phase_2___core_logic_OOP.main import BillingEngine

engine = BillingEngine(tenant_id="d0000000-0000-0000-0000-000000000001")
results = engine.calculate_billing()
```

### Querying Contracts
```python
from Phase_2___core_logic_OOP.repository import ContractRepository

repo = ContractRepository()
contracts = repo.get_contracts_by_tenant(tenant_id="d0000000-0000-0000-0000-000000000001")
```

---

## Development

### Running Tests
```bash
pytest tests/ -v
```

### Code Style
This project follows **PEP 8** guidelines. Ensure compliance with:
```bash
black "Phase 2 - core logic OOP/"
flake8 "Phase 2 - core logic OOP/"
```

---

## Database Connection Details

| Property | Value |
|----------|-------|
| **Host** | localhost |
| **Port** | 5432 |
| **Database** | moveinsync_db |
| **Default User** | postgres |
| **Auth Type** | PostgreSQL Native |

---

## Troubleshooting

### PostgreSQL Connection Error
- Verify PostgreSQL service is running
- Check credentials in `.env` file
- Ensure database exists: `psql -l`

### Python Module Import Errors
- Activate virtual environment: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (macOS/Linux)
- Reinstall dependencies: `pip install -r requirements.txt`

### Port Conflicts
If port 5432 is in use:
- Check: `netstat -ano | findstr :5432` (Windows)
- Change `DB_PORT` in `.env`

---

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Commit changes: `git commit -am 'Add new feature'`
3. Push to branch: `git push origin feature/your-feature`
4. Submit a Pull Request

---

## License

This project is licensed under the **MIT License** — see LICENSE file for details.

---

## Contact & Support

For issues, questions, or collaboration:
- 📧 Email: your-email@example.com
- 💬 GitHub Issues: [Create an Issue](https://github.com/yourusername/MoveInSync/issues)

---

**Last Updated**: November 2025
