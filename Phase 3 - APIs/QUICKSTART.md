# Quick Start: Running Phase 3 API Locally

## Prerequisites

Ensure you have:
1. PostgreSQL running with the MoveInSync database and tables (from Phase 1)
2. Sample data inserted (from Phase 1 seed scripts)
3. Python packages installed:
   ```powershell
   pip install -r ../requirements.txt
   ```

## Environment Setup

Create or update your `.env` file in the project root:

```
DB_NAME=moveinsync_db
DB_USER=postgres
DB_PASSWORD=postgre123
DB_HOST=localhost
DB_PORT=5432
DB_POOL_MINCONN=1
DB_POOL_MAXCONN=5
```

## Start the Server

From the project root or Phase 3 folder:

```powershell
cd "Phase 3 - APIs"
uvicorn main_api:app --reload --host 127.0.0.1 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

## Access Documentation

- **Swagger UI (Interactive):** http://localhost:8000/docs
- **ReDoc (Alternative):** http://localhost:8000/redoc

## Testing Endpoints

All endpoints require the `X-Client-ID` header (must be a valid UUID).

### 1. Health Check

```powershell
$headers = @{ "X-Client-ID" = "c0000000-0000-0000-0000-000000000001" }
Invoke-RestMethod -Uri "http://localhost:8000/health" -Headers $headers
```

**Expected Response:**
```json
{
  "status": "ok",
  "service": "MoveInSync Billing API"
}
```

### 2. Get Billing for a Trip

```powershell
$headers = @{ "X-Client-ID" = "c0000000-0000-0000-0000-000000000001" }
Invoke-RestMethod -Uri "http://localhost:8000/billing/d0000000-0000-0000-0000-000000000001" -Headers $headers
```

**Expected Response:**
```json
{
  "trip_id": "d0000000-0000-0000-0000-000000000001",
  "billing_model": "HYBRID",
  "base_cost": 100.0,
  "tax_amount": 18.0,
  "total_cost": 118.0,
  "breakdown": {
    "night_shift_surcharge": 0.0,
    "note": "Not a night shift trip",
    "distance_cost": 100.0,
    "rate_per_km": 10.0
  }
}
```

### 3. Get Active Contract (Demonstrates Caching)

**First call (hits database):**
```powershell
$headers = @{ "X-Client-ID" = "c0000000-0000-0000-0000-000000000001" }
Measure-Command { Invoke-RestMethod -Uri "http://localhost:8000/contracts" -Headers $headers } | Select-Object TotalMilliseconds
```

**Second call (hits cache):**
```powershell
$headers = @{ "X-Client-ID" = "c0000000-0000-0000-0000-000000000001" }
Measure-Command { Invoke-RestMethod -Uri "http://localhost:8000/contracts" -Headers $headers } | Select-Object TotalMilliseconds
```

**Notice:** Second call is significantly faster (cached in memory).

**Expected Response:**
```json
{
  "contract_id": "con-123",
  "vendor_id": "v0000000-0000-0000-0000-000000000001",
  "billing_model": "HYBRID",
  "rules_config": {
    "currency": "USD",
    "base_monthly_fee": 5000.0,
    "free_km_included": 1000.0,
    "night_shift_surcharge": 50.0,
    "per_km_rate_after_limit": 10.0
  }
}
```

### 4. Create a New Trip

```powershell
$headers = @{
    "X-Client-ID" = "c0000000-0000-0000-0000-000000000001"
    "Content-Type" = "application/json"
}

$body = @{
    distance_km = 25.5
    start_time = "2025-11-23T14:30:00"
    end_time = "2025-11-23T15:00:00"
    vendor_id = "v0000000-0000-0000-0000-000000000001"
    vehicle_type = "Sedan"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/trips" -Method Post -Headers $headers -Body $body
```

**Expected Response:**
```json
{
  "status": "created",
  "trip_id": "550e8400-e29b-41d4-a716-446655440000",
  "client_id": "c0000000-0000-0000-0000-000000000001",
  "vendor_id": "v0000000-0000-0000-0000-000000000001",
  "distance_km": 25.5,
  "start_time": "2025-11-23T14:30:00",
  "end_time": "2025-11-23T15:00:00"
}
```

## Testing Client Isolation

Try accessing data with different client IDs:

```powershell
# Client A
$clientA = @{ "X-Client-ID" = "c0000000-0000-0000-0000-000000000001" }
Invoke-RestMethod -Uri "http://localhost:8000/contracts" -Headers $clientA

# Client B  
$clientB = @{ "X-Client-ID" = "c0000000-0000-0000-0000-000000000005" }
Invoke-RestMethod -Uri "http://localhost:8000/contracts" -Headers $clientB
```

**Result:** Each client sees only their own data (even if both call the same endpoint).

## Testing Error Handling

### Invalid Client ID (not a UUID)

```powershell
$headers = @{ "X-Client-ID" = "not-a-uuid" }
Invoke-RestMethod -Uri "http://localhost:8000/contracts" -Headers $headers
```

**Expected Response (400):**
```json
{
  "detail": "Invalid X-Client-ID header; must be a UUID"
}
```

### Missing Client ID

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/contracts"
```

**Expected Response (403):**
```json
{
  "detail": "Missing X-Client-ID header"
}
```

### Trip Not Found

```powershell
$headers = @{ "X-Client-ID" = "c0000000-0000-0000-0000-000000000001" }
Invoke-RestMethod -Uri "http://localhost:8000/billing/nonexistent-trip-id" -Headers $headers
```

**Expected Response (404):**
```json
{
  "error": "ValueError",
  "detail": "No active contract found for Trip ID: nonexistent-trip-id",
  "path": "/billing/nonexistent-trip-id"
}
```

## Troubleshooting

### `ModuleNotFoundError: No module named 'billing'`

**Cause:** sys.path not including Phase 2 directory  
**Fix:** Ensure you're running from the correct directory and all imports use absolute paths (already fixed in this code)

### `psycopg2.OperationalError: could not connect to server`

**Cause:** PostgreSQL not running or credentials wrong  
**Fix:**
1. Start PostgreSQL service
2. Verify `.env` file has correct credentials
3. Test connection manually: `psql -U postgres -d moveinsync_db`

### `No active contract found for Client ID`

**Cause:** No contract data in the database for this client  
**Fix:** 
1. Run Phase 1 seed scripts to populate contracts
2. Verify the client_id exists in the database

## Architecture Diagram

```
Client Request with X-Client-ID Header
    ↓
FastAPI Dependency Injection
    ├→ get_client_id() — Validates UUID format
    ├→ get_db_conn() — Gets pooled connection
    ↓
BillingService Layer
    ├→ calculate_trip_cost() → Repository → Strategies
    ├→ get_active_contract() → [LRU Cache] or Repository
    ├→ insert_new_trip() → Repository → Commits to DB
    ↓
Global Exception Handler
    ├→ BillingError → 400/404 with custom message
    ├→ ValueError → 400 Bad Request
    ├→ Unexpected → 500 (no internals leaked)
    ↓
JSON Response (Client Isolated)
```

## Performance Notes

- **Connection Pooling:** Reuses connections, reduces overhead per request
- **Caching:** `/contracts` endpoint uses in-memory LRU cache (128 clients max)
- **Client Isolation:** Enforced at repository level via `WHERE client_id = %s` in all queries
- **Async Ready:** FastAPI is designed for async/concurrent requests (can add async methods later)

## Next Steps

1. ✅ Run the server locally
2. ✅ Test all endpoints with different client IDs
3. ✅ Verify caching (measure response times)
4. ✅ Test error scenarios
5. 🔲 Add logging/monitoring
6. 🔲 Add authentication (OAuth2, JWT)
7. 🔲 Deploy to production (Docker, Kubernetes, Cloud)

