# System Architecture Documentation
## MoveInSync Unified Billing Platform

**Document Version:** 1.0  
**Last Updated:** November 25, 2025  
**Author:** Suryansh Sharma

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Component Architecture](#3-component-architecture)
4. [Data Flow](#4-data-flow)
5. [Security Architecture](#5-security-architecture)
6. [Deployment Architecture](#6-deployment-architecture)
7. [Technology Stack](#7-technology-stack)

---

## 1. System Overview

### 1.1 Purpose

The MoveInSync platform is a **multi-tenant billing and reporting system** designed to handle complex billing scenarios for corporate transportation services across multiple clients and vendors.

### 1.2 Key Characteristics

- **Multi-Tenant:** Complete data isolation between clients
- **Flexible Billing:** Supports multiple billing models (HYBRID, PER_TRIP, FIXED_PACKAGE)
- **Secure:** JWT-based authentication with 4-tier RBAC
- **Scalable:** Designed for horizontal scaling
- **Observable:** Real-time monitoring and logging

### 1.3 System Boundaries

```
┌─────────────────────────────────────────────────────────┐
│                    MoveInSync Platform                  │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │   UI     │  │   API    │  │ Database │            │
│  │(Streamlit)│→│(FastAPI) │→│(PostgreSQL)│           │
│  └──────────┘  └──────────┘  └──────────┘            │
│                                                         │
└─────────────────────────────────────────────────────────┘
         ↑                                    ↑
         │                                    │
    End Users                          System Admins
```

---

## 2. High-Level Architecture

### 2.1 Layered Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Presentation Layer                     │
│              (Streamlit UI - Phase 4)                   │
│  - Login/Logout                                         │
│  - Billing Calculator                                   │
│  - Analytics Dashboard                                  │
│  - System Monitor                                       │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP + JWT Bearer Token
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   API Layer                             │
│              (FastAPI - Phase 3)                        │
│  - Authentication (/auth/login)                         │
│  - Billing Endpoints (/secure/billing/*)               │
│  - Admin Endpoints (/admin/*)                          │
│  - Connection Pool Management                           │
└────────────────────┬────────────────────────────────────┘
                     │ Function Calls
                     ▼
┌─────────────────────────────────────────────────────────┐
│                Business Logic Layer                     │
│           (Python OOP - Phase 2)                        │
│  - BillingService (orchestration)                       │
│  - Strategy Pattern (billing models)                    │
│  - Repository Pattern (data access)                     │
│  - LRU Cache (contract caching)                         │
└────────────────────┬────────────────────────────────────┘
                     │ SQL Queries (psycopg2)
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   Data Layer                            │
│            (PostgreSQL - Phase 1)                       │
│  - Users (authentication)                               │
│  - Clients (tenants)                                    │
│  - Vendors (service providers)                          │
│  - Contracts (billing rules - JSONB)                    │
│  - Trips (transaction data)                             │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Component Interaction

```
┌──────────┐
│  Browser │
└─────┬────┘
      │ 1. Login Request (email/password)
      ▼
┌─────────────┐
│ Streamlit UI│
└─────┬───────┘
      │ 2. POST /auth/login
      ▼
┌─────────────┐
│  FastAPI    │──────┐
└─────┬───────┘      │ 3. Verify password (bcrypt)
      │              │ 4. Create JWT token
      │              ▼
      │         ┌──────────┐
      │         │ auth.py  │
      │         └──────────┘
      │ 5. Return JWT
      ▼
┌─────────────┐
│ Streamlit UI│ (stores JWT in session)
└─────┬───────┘
      │ 6. GET /secure/billing/{trip_id}
      │    Authorization: Bearer <JWT>
      ▼
┌─────────────┐
│  FastAPI    │──────┐
└─────┬───────┘      │ 7. Validate JWT
      │              │ 8. Extract client_id
      │              ▼
      │         ┌──────────────┐
      │         │dependencies.py│
      │         └──────────────┘
      │ 9. Call BillingService
      ▼
┌──────────────┐
│BillingService│──────┐
└─────┬────────┘      │ 10. Fetch trip + contract
      │               │ 11. Select strategy
      │               │ 12. Calculate cost
      │               ▼
      │         ┌──────────────┐
      │         │ Repository   │
      │         │ + Strategies │
      │         └──────┬───────┘
      │                │ 13. SQL Query
      │                ▼
      │         ┌──────────────┐
      │         │ PostgreSQL   │
      │         └──────────────┘
      │ 14. Return result
      ▼
┌─────────────┐
│  FastAPI    │
└─────┬───────┘
      │ 15. JSON Response
      ▼
┌─────────────┐
│ Streamlit UI│ (displays results)
└─────────────┘
```

---

## 3. Component Architecture

### 3.1 Phase 1: Database Layer

**Purpose:** Persistent storage with multi-tenant schema

**Components:**

```
PostgreSQL Database
├── users
│   ├── id (UUID, PK)
│   ├── email (VARCHAR, UNIQUE)
│   ├── password_hash (VARCHAR)
│   ├── role (VARCHAR) - SUPER_ADMIN, CLIENT_ADMIN, VENDOR_ADMIN, VIEWER
│   ├── client_id (UUID, FK) - Nullable
│   └── vendor_id (UUID, FK) - Nullable
│
├── clients
│   ├── client_id (UUID, PK)
│   ├── client_name (VARCHAR)
│   └── created_at (TIMESTAMP)
│
├── vendors
│   ├── vendor_id (UUID, PK)
│   ├── vendor_name (VARCHAR)
│   └── created_at (TIMESTAMP)
│
├── contracts
│   ├── contract_id (UUID, PK)
│   ├── client_id (UUID, FK)
│   ├── vendor_id (UUID, FK)
│   ├── billing_model (VARCHAR) - HYBRID, PER_TRIP, FIXED_PACKAGE
│   ├── rules_config (JSONB) - Flexible billing rules
│   ├── start_date (DATE)
│   ├── end_date (DATE)
│   └── is_active (BOOLEAN)
│
└── trips
    ├── trip_id (UUID, PK)
    ├── client_id (UUID, FK)
    ├── vendor_id (UUID, FK)
    ├── employee_id (UUID, FK)
    ├── distance_km (DECIMAL)
    ├── start_time (TIMESTAMP)
    ├── end_time (TIMESTAMP)
    ├── is_carpool (BOOLEAN)
    └── created_at (TIMESTAMP)
```

**Key Design Decisions:**
- **JSONB for rules_config:** Allows flexible billing rules without schema changes
- **UUID for all IDs:** Globally unique, secure, distributed-system friendly
- **Indexes on client_id:** Fast tenant-isolated queries

### 3.2 Phase 2: Business Logic Layer

**Purpose:** Encapsulate billing calculation logic using OOP principles

**Architecture:**

```
billing/
├── __init__.py
├── schemas.py           # Data classes
│   ├── TripData
│   ├── ContractRuleConfig
│   └── CalculationResult
│
├── strategies.py        # Strategy Pattern
│   ├── BillingStrategy (ABC)
│   ├── HybridStrategy
│   ├── PerTripStrategy
│   ├── FixedPackageStrategy
│   └── StrategyFactory
│
└── repository.py        # Repository Pattern
    └── PostgresRepository
        ├── fetch_trip_context()
        ├── fetch_active_contract()
        └── fetch_client_trips()
```

**Design Patterns:**

**1. Strategy Pattern:**
```python
class BillingStrategy(ABC):
    @abstractmethod
    def calculate_cost(self, trip, rules) -> CalculationResult:
        pass

class HybridStrategy(BillingStrategy):
    def calculate_cost(self, trip, rules):
        # Package + Per-Trip logic
        ...

# Usage:
strategy = StrategyFactory.get_strategy(BillingModelType.HYBRID)
result = strategy.calculate_cost(trip_data, rules_config)
```

**2. Repository Pattern:**
```python
class PostgresRepository:
    def fetch_trip_context(self, trip_id, client_id, conn):
        # Encapsulates SQL query
        # Returns: (TripData, billing_model, rules_dict)
        ...
```

### 3.3 Phase 3: API Layer

**Purpose:** RESTful API with authentication and authorization

**Architecture:**

```
Phase 3 - APIs/
├── main_api.py          # FastAPI application
│   ├── /auth/login (POST)
│   ├── /secure/billing/{trip_id} (GET)
│   ├── /secure/billing/export-csv (GET)
│   ├── /secure/billing/stats (GET)
│   └── /admin/users (POST)
│
├── auth.py              # JWT management
│   ├── create_access_token()
│   ├── decode_token()
│   ├── hash_password()
│   └── verify_password()
│
├── dependencies.py      # Dependency Injection
│   ├── get_db_conn()
│   ├── get_current_user()
│   └── require_role()
│
├── service.py           # Business logic orchestration
│   └── BillingService
│       ├── calculate_trip_cost()
│       ├── get_client_billing_data()
│       └── generate_client_report()
│
├── api_models.py        # Pydantic models
│   ├── LoginRequest
│   ├── TokenResponse
│   ├── UserCreate
│   └── UserOut
│
└── exceptions.py        # Custom exceptions
    ├── BillingError
    ├── TripNotFoundError
    └── ContractNotFoundError
```

**Connection Pool:**
```python
connection_pool = SimpleConnectionPool(
    minconn=1,
    maxconn=5,
    host=os.getenv('DB_HOST'),
    ...
)
```

**Caching:**
```python
@lru_cache(maxsize=128)
def get_cached_active_contract(client_id: str) -> tuple:
    # Cache contract data for 128 clients
    ...
```

### 3.4 Phase 4: Presentation Layer

**Purpose:** Interactive web dashboard for users

**Architecture:**

```
Phase 4 - UI/
└── app.py               # Streamlit application
    ├── Session State Management
    ├── Login/Logout Flow
    ├── Tab Navigation (Role-Based)
    │   ├── Billing Calculator
    │   ├── Contract Viewer
    │   ├── Analytics Dashboard
    │   ├── System Monitor
    │   ├── Billing Reports
    │   └── Admin Config (SUPER_ADMIN only)
    └── API Integration (requests library)
```

**Role-Based UI Rendering:**
```python
if user_role == "SUPER_ADMIN":
    tabs = ["Calculator", "Contract", "Analytics", "Monitor", "Admin", "Reports"]
elif user_role == "CLIENT_ADMIN":
    tabs = ["Calculator", "Contract", "Analytics", "Monitor", "Reports"]
else:  # VIEWER
    tabs = ["Contract", "Analytics", "Reports"]
```

---

## 4. Data Flow

### 4.1 Authentication Flow

```
┌──────┐
│ User │
└──┬───┘
   │ 1. Enter email + password
   ▼
┌─────────────┐
│ Streamlit UI│
└──┬──────────┘
   │ 2. POST /auth/login
   │    {email, password}
   ▼
┌─────────────┐
│  FastAPI    │
└──┬──────────┘
   │ 3. Query users table
   ▼
┌─────────────┐
│ PostgreSQL  │
└──┬──────────┘
   │ 4. Return user record
   ▼
┌─────────────┐
│  FastAPI    │
└──┬──────────┘
   │ 5. Verify password (bcrypt)
   │ 6. Create JWT token
   │    {sub, role, client_id, exp}
   │ 7. Sign with SECRET_KEY
   ▼
┌─────────────┐
│ Streamlit UI│
└──┬──────────┘
   │ 8. Store JWT in session_state
   │ 9. Display user info
   ▼
┌──────┐
│ User │ (Authenticated)
└──────┘
```

### 4.2 Billing Calculation Flow

```
┌──────┐
│ User │ Enters trip_id
└──┬───┘
   │ 1. Click "Calculate Billing"
   ▼
┌─────────────┐
│ Streamlit UI│
└──┬──────────┘
   │ 2. GET /secure/billing/{trip_id}
   │    Authorization: Bearer <JWT>
   ▼
┌─────────────┐
│  FastAPI    │
└──┬──────────┘
   │ 3. Validate JWT
   │ 4. Extract client_id from token
   ▼
┌──────────────┐
│BillingService│
└──┬───────────┘
   │ 5. Check LRU cache for contract
   │    Cache hit? → Skip DB query
   │    Cache miss? → Fetch from DB
   ▼
┌─────────────┐
│ Repository  │
└──┬──────────┘
   │ 6. SQL Query:
   │    SELECT t.*, c.billing_model, c.rules_config
   │    FROM trips t
   │    JOIN contracts c ON ...
   │    WHERE t.trip_id = $1 AND t.client_id = $2
   ▼
┌─────────────┐
│ PostgreSQL  │
└──┬──────────┘
   │ 7. Return trip + contract data
   ▼
┌──────────────┐
│BillingService│
└──┬───────────┘
   │ 8. Select strategy (Factory pattern)
   │    billing_model = "HYBRID"
   │    → HybridStrategy
   ▼
┌──────────────┐
│HybridStrategy│
└──┬───────────┘
   │ 9. Calculate cost:
   │    - Package cost
   │    - Extra km charges
   │    - Carpool discount
   │    - Tax
   ▼
┌──────────────┐
│BillingService│
└──┬───────────┘
   │ 10. Return CalculationResult
   ▼
┌─────────────┐
│  FastAPI    │
└──┬──────────┘
   │ 11. JSON Response:
   │     {base_cost, tax_amount, total_cost, breakdown}
   ▼
┌─────────────┐
│ Streamlit UI│
└──┬──────────┘
   │ 12. Display results
   ▼
┌──────┐
│ User │ (Views billing details)
└──────┘
```

### 4.3 CSV Export Flow

```
User → Streamlit UI → FastAPI → BillingService → Repository → PostgreSQL
                                      │
                                      ├─ Fetch all trips for client
                                      ├─ Calculate cost for each trip
                                      ├─ Format as CSV
                                      └─ Return CSV bytes

PostgreSQL → Repository → BillingService → FastAPI → Streamlit UI → User
                                                          │
                                                          └─ Download CSV file
```

---

## 5. Security Architecture

### 5.1 Authentication & Authorization

```
┌─────────────────────────────────────────────────────────┐
│                  Security Layers                        │
├─────────────────────────────────────────────────────────┤
│ Layer 1: Password Security                             │
│  - Bcrypt hashing with automatic salting               │
│  - No plaintext passwords stored                       │
├─────────────────────────────────────────────────────────┤
│ Layer 2: JWT Token                                     │
│  - Signed with HS256 algorithm                         │
│  - 60-minute expiry                                    │
│  - Contains: user_id, role, client_id, vendor_id      │
├─────────────────────────────────────────────────────────┤
│ Layer 3: Role-Based Access Control (RBAC)             │
│  - SUPER_ADMIN: System-wide access                    │
│  - CLIENT_ADMIN: Full client access                   │
│  - VENDOR_ADMIN: Vendor-specific access               │
│  - VIEWER: Read-only access                           │
├─────────────────────────────────────────────────────────┤
│ Layer 4: Tenant Isolation                             │
│  - Every query filters by client_id                    │
│  - Cross-tenant access blocked at query level         │
└─────────────────────────────────────────────────────────┘
```

### 5.2 Data Flow Security

```
Request → JWT Validation → Role Check → Tenant Filter → Response
            ↓                  ↓             ↓
         Invalid?          Forbidden?    Wrong tenant?
            ↓                  ↓             ↓
         401 Error         403 Error    403 Error
```

---

## 6. Deployment Architecture

### 6.1 Development Environment

```
┌─────────────────────────────────────────────────────────┐
│                  Local Development                      │
├─────────────────────────────────────────────────────────┤
│ Terminal 1: FastAPI                                    │
│  uvicorn main_api:app --reload --port 8000             │
├─────────────────────────────────────────────────────────┤
│ Terminal 2: Streamlit                                  │
│  streamlit run app.py                                  │
├─────────────────────────────────────────────────────────┤
│ PostgreSQL: localhost:5432                             │
│  Database: moveinsync_db                               │
└─────────────────────────────────────────────────────────┘
```

### 6.2 Production Architecture (Recommended)

```
┌─────────────────────────────────────────────────────────┐
│                    Load Balancer                        │
│                   (NGINX / AWS ALB)                     │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│  Streamlit UI   │     │  Streamlit UI   │
│   (Instance 1)  │     │   (Instance 2)  │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   Load Balancer       │
         │   (API Gateway)       │
         └───────────┬───────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│   FastAPI       │     │   FastAPI       │
│  (Instance 1)   │     │  (Instance 2)   │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   Redis Cache         │
         │  (Distributed Cache)  │
         └───────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   PostgreSQL          │
         │  (Primary + Replica)  │
         └───────────────────────┘
```

---

## 7. Technology Stack

### 7.1 Complete Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Database** | PostgreSQL | 12+ | Persistent storage |
| **Backend** | Python | 3.9+ | Application logic |
| **API Framework** | FastAPI | 0.104+ | RESTful API |
| **UI Framework** | Streamlit | 1.28+ | Web dashboard |
| **Authentication** | python-jose | 3.3+ | JWT tokens |
| **Password Hashing** | passlib (bcrypt) | 1.7+ | Secure passwords |
| **Database Driver** | psycopg2 | 2.9+ | PostgreSQL connector |
| **Data Validation** | Pydantic | 2.4+ | Request/response models |
| **Caching** | functools.lru_cache | Built-in | In-memory cache |
| **Monitoring** | psutil | 5.9+ | System metrics |
| **HTTP Client** | requests | 2.31+ | API calls from UI |
| **Data Processing** | pandas | 2.0+ | Analytics |

### 7.2 Development Tools

| Tool | Purpose |
|------|---------|
| Git | Version control |
| VS Code | Code editor |
| pgAdmin / DBeaver | Database management |
| Postman / cURL | API testing |
| OBS Studio / Loom | Demo recording |

---

## Conclusion

This architecture provides:

✅ **Scalability** - Can handle growing user base  
✅ **Security** - Multi-layered authentication and authorization  
✅ **Maintainability** - Clean separation of concerns  
✅ **Flexibility** - Easy to add new billing models  
✅ **Observability** - Real-time monitoring and logging  

The system is designed to evolve from a monolithic MVP to a distributed microservices architecture as requirements grow.

---

**Document Prepared By:** Suryansh Sharma  
**Date:** November 25, 2025  
**Version:** 1.0
