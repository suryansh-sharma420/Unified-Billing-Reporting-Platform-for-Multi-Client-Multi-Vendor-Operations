# Phase 3: API Layer with Caching, Connection Pooling & Error Handling

This directory contains the FastAPI application that wraps your Phase 2 BillingEngine with enterprise-grade features:

## Files Overview

### `dependencies.py`
**What it does:**
- Manages a `psycopg2.pool.SimpleConnectionPool` for efficient database connection reuse
- Provides FastAPI dependency functions for injection

**Key exports:**
- `get_db_conn()` — Yields a pooled connection per request; returns it to the pool after request completes
- `get_client_id(x_client_id: Header)` — Validates `X-Client-ID` header as UUID format; raises HTTP 400 if invalid

**Why this matters:**
- Connection pooling avoids opening/closing connections for every request (expensive)
- Header injection ensures every endpoint has client context without boilerplate

---

### `api_models.py`
**What it does:**
- Defines Pydantic models for API request/response validation

**Key exports:**
- `TripInput` — Validates trip creation requests (distance_km, start_time, end_time, vendor_id, vehicle_type)

**Why this matters:**
- Automatic request validation; malformed JSON returns 422 Unprocessable Entity
- Type hints and defaults make API self-documenting

---

### `service.py`
**What it does:**
- Service layer that wraps repository calls and adds caching

**Key exports:**
- `BillingService` class with methods:
  - `calculate_trip_cost(trip_id, client_id, conn)` — Calculates billing for a trip
  - `get_active_contract(client_id, conn)` — Fetches contract (uses `lru_cache` if no conn)
  - `insert_new_trip(...)` — Inserts a new trip into the database

**Why this matters:**
- Separates business logic from HTTP layer
- `@lru_cache` decorator on `get_cached_active_contract` means repeated calls for the same client hit in-memory cache (128 client limit, configurable)
- Cache key is just `client_id`, so calling `/contracts` twice for the same client on the second call returns instant response from memory

**Caching Details:**
```python
@staticmethod
@lru_cache(maxsize=128)
def get_cached_active_contract(client_id: str) -> tuple:
    # Queries DB only once per unique client_id within cache lifetime
    # Subsequent calls return tuple from memory instantly
```

---

### `exceptions.py`
**What it does:**
- Defines custom exception classes for billing domain
- Provides a global exception handler middleware

**Key exports:**
- Exception classes: `BillingError`, `TripNotFoundError`, `ContractNotFoundError`, `InvalidClientError`
- `global_exception_handler()` — Catches all exceptions and returns clean JSON

**Why this matters:**
- Structured error responses (no raw Python tracebacks leaked to clients)
- 404 for not found, 400 for validation, 500 for unexpected errors
- Consistent error schema across all endpoints

**Global Handler Behavior:**
- `BillingError` subclasses → return their custom status code + message
- `ValueError` → 400 with message
- `RequestValidationError` (Pydantic) → 422 with validation details
- All others → 500 with generic "Internal Server Error" (don't leak internals)

---

### `main_api.py`
**What it does:**
- FastAPI application with three endpoints

**Endpoints:**

#### 1. `GET /health`
- Simple health check
- Returns `{"status": "ok", "service": "MoveInSync Billing API"}`

#### 2. `GET /billing/{trip_id}`
- **Purpose:** Calculate billing for a specific trip
- **Headers:** `X-Client-ID: <uuid>` (required)
- **Process:**
  1. Validate client ID header
  2. Get pooled DB connection
  3. Call `service.calculate_trip_cost(trip_id, client_id, conn)`
  4. Return: trip_id, billing_model, base_cost, tax_amount, total_cost, breakdown
- **Client Isolation:** Only returns trips for the authenticated client

#### 3. `GET /contracts`
- **Purpose:** Get the currently active contract for the client
- **Headers:** `X-Client-ID: <uuid>` (required)
- **Caching:** Uses `lru_cache` — second call for same client returns instant result
- **Return:** contract_id, vendor_id, billing_model, rules_config

#### 4. `POST /trips`
- **Purpose:** Create a new trip (simulates a completed ride being logged)
- **Headers:** `X-Client-ID: <uuid>` (required)
- **Request Body (JSON):**
  ```json
  {
    "distance_km": 15.5,
    "start_time": "2025-11-23T10:30:00",
    "end_time": "2025-11-23T10:45:00",
    "vendor_id": "v0000000-0000-0000-0000-000000000001",
    "vehicle_type": "Sedan"
  }
  ```
- **Process:**
  1. Validate client ID header
  2. Validate TripInput (Pydantic validation)
  3. Generate unique trip_id (UUID v4)
  4. Insert into DB with client_id for multi-tenancy
  5. Return: trip_id, client_id, vendor_id, distance_km, start_time, end_time
- **Client Isolation:** Trip always associated with authenticated client

---

## Running the API

### Prerequisites
1. Install dependencies:
   ```powershell
   pip install -r ../requirements.txt
   ```

2. Ensure PostgreSQL is running and `.env` file is configured with:
   ```
   DB_NAME=moveinsync_db
   DB_USER=postgres
   DB_PASSWORD=<your_password>
   DB_HOST=localhost
   DB_PORT=5432
   DB_POOL_MINCONN=1
   DB_POOL_MAXCONN=5
   ```

### Start the Server
```powershell
cd "Phase 3 - APIs"
uvicorn main_api:app --reload --host 0.0.0.0 --port 8000
```

Output should show:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete
```

### Access API Documentation
- **Interactive Docs (Swagger UI):** http://localhost:8000/docs
- **Alternative Docs (ReDoc):** http://localhost:8000/redoc

---

## Example Requests

### 1. Health Check
```powershell
$headers = @{ "X-Client-ID" = "c0000000-0000-0000-0000-000000000001" }
Invoke-RestMethod -Uri "http://localhost:8000/health" -Headers $headers
```

### 2. Calculate Billing for a Trip
```powershell
$headers = @{ "X-Client-ID" = "c0000000-0000-0000-0000-000000000001" }
Invoke-RestMethod -Uri "http://localhost:8000/billing/d0000000-0000-0000-0000-000000000001" -Headers $headers
```

### 3. Get Active Contract
```powershell
$headers = @{ "X-Client-ID" = "c0000000-0000-0000-0000-000000000001" }
Invoke-RestMethod -Uri "http://localhost:8000/contracts" -Headers $headers
```

### 4. Create a New Trip
```powershell
$headers = @{ "X-Client-ID" = "c0000000-0000-0000-0000-000000000001"; "Content-Type" = "application/json" }
$body = @{
    distance_km = 25.5
    start_time = "2025-11-23T14:00:00"
    end_time = "2025-11-23T14:45:00"
    vendor_id = "v0000000-0000-0000-0000-000000000001"
    vehicle_type = "Sedan"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/trips" -Method Post -Headers $headers -Body $body
```

---

## Architecture Summary

```
Client Request (with X-Client-ID header)
    ↓
FastAPI Route Handler
    ├→ get_client_id() — Validates header, extracts client_id
    ├→ get_db_conn() — Gets pooled connection
    ├→ Service Layer — Business logic
    │   ├→ Repository — Raw DB access
    │   ├→ lru_cache — In-memory caching for reads
    │   └→ Strategy Pattern — Billing calculation
    ├→ global_exception_handler() — Catches errors
    └→ JSON Response (with client isolation guaranteed)
```

---

## Key Design Patterns

### 1. **Dependency Injection**
- FastAPI `Depends()` injects client_id and connection without boilerplate
- Makes testing easier (can mock dependencies)

### 2. **Connection Pooling**
- `SimpleConnectionPool` reuses connections
- Per-request pattern: get → use → return
- Faster than opening/closing per request

### 3. **Service Layer Caching**
- `@lru_cache` on contract fetching
- 128 unique clients cached in memory
- Cache is process-local (invalidates on restart)

### 4. **Client Isolation**
- Every endpoint requires `X-Client-ID` header
- All queries filter by `client_id`
- Impossible for Client A to access Client B's data

### 5. **Error Handling**
- Global exception handler catches all errors
- Custom exceptions for domain errors (404, 400)
- 500 for truly unexpected errors (with no leak of internals)

---

## What You've Learned (Phase 3 Concepts)

✅ **Connection Pooling** — Efficient resource management for high-concurrency APIs  
✅ **Multi-tenancy** — Isolating data by client_id at repository level  
✅ **Caching** — In-memory LRU cache for read-heavy operations  
✅ **Service Layer** — Separation of concerns (HTTP vs. Business Logic)  
✅ **Dependency Injection** — Clean, testable code without global state  
✅ **Error Handling** — Structured exception responses  
✅ **API Documentation** — Auto-generated Swagger/ReDoc from code  

---

## Next Steps

1. **Test the API locally** with the example requests above
2. **Verify client isolation** by testing with different `X-Client-ID` values
3. **Monitor caching** — Call `/contracts` twice for the same client; second call is instant
4. **Add middleware** for logging, authentication, rate limiting
5. **Deploy to production** (e.g., Docker container, cloud platform)

