from typing import Any, Dict, Optional, Callable
import sys
import os
import uuid
import logging
import time
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, Response
import uuid
import psycopg2.extras

# Add Phase 2 to sys.path dynamically
phase2_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Phase 2 - core logic OOP'))
if phase2_path not in sys.path:
    sys.path.insert(0, phase2_path)

from dependencies import (
    get_db_conn,
    get_client_id,           # legacy
    get_current_user,        # JWT
    require_role,            # RBAC helper
)
from service import BillingService  # type: ignore
from api_models import TripInput, LoginRequest, TokenResponse, UserOut, UserCreate  # type: ignore
from exceptions import global_exception_handler, BillingError  # type: ignore
from auth import verify_password, create_access_token, hash_password  # type: ignore
from dependencies import connection_pool  # type: ignore


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('moveinsync_app.log', mode='a', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
,
    force=True  # override any existing logging config set by uvicorn
)
logger = logging.getLogger("moveinsync")
logger.setLevel(logging.INFO)

app = FastAPI(
    title="MoveInSync Billing API",
    description="Phase 3 API: Multi-tenant billing with connection pooling, caching, and error handling",
    version="1.0.0",
)

# Register the global exception handler
app.add_exception_handler(Exception, global_exception_handler)

# ----------------------------------------------------------------------------
# Startup: ensure users table and a seed user for testing
# ----------------------------------------------------------------------------
@app.on_event("startup")
def _ensure_users_table_and_seed():
    try:
        conn = connection_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id UUID PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        role TEXT NOT NULL,
                        client_id UUID NULL,
                        vendor_id UUID NULL,
                        CHECK (
                            (role = 'SUPER_ADMIN' AND client_id IS NULL AND vendor_id IS NULL)
                         OR (role IN ('CLIENT_ADMIN','VIEWER') AND client_id IS NOT NULL AND vendor_id IS NULL)
                         OR (role = 'VENDOR_ADMIN' AND vendor_id IS NOT NULL)
                        )
                    );
                    """
                )
                # seed a test client admin if not present
                cur.execute("SELECT 1 FROM users WHERE email=%s", ("admin@client.com",))
                exists = cur.fetchone()
                if not exists:
                    test_id = str(uuid.uuid4())
                    pwd = hash_password("Password@123")
                    # Use sample seeded client id from dataset
                    client_uuid = "c0000000-0000-0000-0000-000000000001"
                    cur.execute(
                        """
                        INSERT INTO users (id,email,password_hash,role,client_id,vendor_id)
                        VALUES (%s,%s,%s,%s,%s,%s)
                        """,
                        (test_id, "admin@client.com", pwd, "CLIENT_ADMIN", client_uuid, None),
                    )
                conn.commit()
        finally:
            connection_pool.putconn(conn)
    except Exception as e:
        logger.error(f"Startup user/DDL init failed: {e}")

# Logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next: Callable):
    # Log request details
    client_id = request.headers.get('X-Client-ID', 'unknown')
    logger.info(f"Request: {request.method} {request.url} - Client: {client_id}")
    
    # Process the request and measure time
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    
    # Log response details
    logger.info(f"Response: {request.method} {request.url} - Status: {response.status_code} - {process_time:.2f}ms")
    
    return response


@app.get("/billing/export-csv")
def export_billing_csv(client_id: str = Depends(get_client_id), conn=Depends(get_db_conn)) -> Response:
    """Download CSV report for authenticated client."""
    service = BillingService()
    csv_bytes = service.generate_client_report(client_id, conn)
    return Response(content=csv_bytes,
                    media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=client_billing_report.csv"})

# ----------------------------------------------------------------------------
# Auth endpoints
# ----------------------------------------------------------------------------
@app.post("/auth/login", response_model=TokenResponse)
def login(data: LoginRequest, conn=Depends(get_db_conn)) -> TokenResponse:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT id, email, password_hash, role, client_id, vendor_id FROM users WHERE email=%s",
            (data.email,),
        )
        row = cur.fetchone()
        if not row or not verify_password(data.password, row["password_hash"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(
        user_id=uuid.UUID(row["id"]),
        role=row["role"],
        client_id=str(row["client_id"]) if row["client_id"] else None,
        vendor_id=str(row["vendor_id"]) if row["vendor_id"] else None,
    )
    return TokenResponse(
        access_token=token,
        role=row["role"],
        client_id=str(row["client_id"]) if row["client_id"] else None,
        vendor_id=str(row["vendor_id"]) if row["vendor_id"] else None,
    )


@app.get("/health")
def health() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "MoveInSync Billing API"}


@app.get("/billing/{trip_id}")
def get_billing(
    trip_id: str,
    client_id: str = Depends(get_client_id),
    conn=Depends(get_db_conn),
    is_carpool: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Calculate billing for a specific trip.

    **Explanation of what this endpoint does:**
    - Extracts the X-Client-ID header and validates it as a UUID (via get_client_id dependency)
    - Gets a pooled DB connection (via get_db_conn dependency)
    - Calls the BillingService to calculate the trip cost
    - Returns a structured JSON response with costs and breakdown

    **Returns:**
    - trip_id, billing_model, base_cost, tax_amount, total_cost, breakdown

    **Example Request:**
    ```
    GET /billing/d0000000-0000-0000-0000-000000000001
    Headers: X-Client-ID: c0000000-0000-0000-0000-000000000001
    ```
    """
    service = BillingService()
    result = service.calculate_trip_cost(trip_id, client_id, conn, override_is_carpool=is_carpool)
    return result

# Secure version using JWT
# Secure CSV export
@app.get("/secure/billing/export-csv")
def secure_export_billing_csv(current_user: UserOut = Depends(get_current_user), conn=Depends(get_db_conn)) -> Response:
    if not current_user.client_id:
        raise HTTPException(status_code=400, detail="User not bound to a client")
    service = BillingService()
    csv_bytes = service.generate_client_report(current_user.client_id, conn)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"billing_report_{current_user.client_id}_{timestamp}.csv"
    
    return Response(content=csv_bytes,
                    media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={filename}"})


@app.get("/secure/billing/stats")
async def secure_get_billing_stats(
    current_user: UserOut = Depends(get_current_user),
    conn=Depends(get_db_conn)
):
    """
    Get raw billing statistics for the client.
    Returns a list of all trips with calculated costs.
    """
    if not current_user.client_id:
        raise HTTPException(status_code=400, detail="User not bound to a client")
    
    service = BillingService()
    try:
        stats = service.get_client_billing_data(current_user.client_id, conn)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/secure/billing/{trip_id}")
def secure_get_billing(
    trip_id: str,
    current_user: UserOut = Depends(get_current_user),
    conn=Depends(get_db_conn),
    is_carpool: Optional[bool] = None,
) -> Dict[str, Any]:
    service = BillingService()
    if not current_user.client_id:
        raise HTTPException(status_code=400, detail="User not bound to a client")
    result = service.calculate_trip_cost(trip_id, current_user.client_id, conn, override_is_carpool=is_carpool)
    return result


@app.get("/contracts")
def get_contracts(client_id: str = Depends(get_client_id), conn=Depends(get_db_conn)) -> Dict[str, Any]:
    """
    Get the currently active contract for the client.

    **Explanation of what this endpoint does:**
    - Validates X-Client-ID header
    - Uses BillingService.get_active_contract() which:
      - Calls repository to fetch contract
      - Returns cached result if no conn provided (for repeated calls)
      - With conn provided, always fetches fresh from DB
    - Returns contract details and billing rules

    **Caching behavior:**
    - If this is called multiple times for the same client_id, results are cached in-memory
    - Cache stores up to 128 unique clients (configurable)
    - Cache invalidates after process restart

    **Returns:**
    - contract_id, vendor_id, billing_model, rules_config

    **Example Request:**
    ```
    GET /contracts
    Headers: X-Client-ID: c0000000-0000-0000-0000-000000000001
    ```
    """
    service = BillingService()
    contract = service.get_active_contract(client_id, conn)
    return {
        "contract_id": contract["contract_id"],
        "vendor_id": contract["vendor_id"],
        "billing_model": contract["billing_model"],
        "rules_config": contract["rules_config"],
    }

# Secure contracts
@app.get("/secure/contracts")
def secure_get_contracts(current_user: UserOut = Depends(get_current_user), conn=Depends(get_db_conn)) -> Dict[str, Any]:
    if not current_user.client_id:
        raise HTTPException(status_code=400, detail="User not bound to a client")
    service = BillingService()
    contract = service.get_active_contract(current_user.client_id, conn)
    return {
        "contract_id": contract["contract_id"],
        "vendor_id": contract["vendor_id"],
        "billing_model": contract["billing_model"],
        "rules_config": contract["rules_config"],
    }


# duplicate removed
# removed duplicate function export_billing_csv(client_id: str = Depends(get_client_id), conn=Depends(get_db_conn)):
    """
    Export billing report CSV for the authenticated client.

    Returns a CSV file as attachment. Uses X-Client-ID for tenant isolation.
    """
    service = BillingService()
    csv_bytes = service.generate_client_report(client_id, conn)

    headers = {
        "Content-Disposition": "attachment; filename=client_billing_report.csv"
    }

    return Response(content=csv_bytes, media_type="text/csv", headers=headers)


@app.post("/trips")
def create_trip(
    trip_input: TripInput,
    client_id: str = Depends(get_client_id),
    conn=Depends(get_db_conn),
) -> Dict[str, Any]:
    """
    Create a new trip record (simulates a ride ending and being logged).

    **Explanation of what this endpoint does:**
    - Validates X-Client-ID header
    - Validates TripInput model (distance_km >= 0, datetime format, etc.)
    - Generates a unique trip_id (UUID v4)
    - Calls BillingService.insert_new_trip() which:
      - Inserts trip into database with client_id for multi-tenancy
      - Commits transaction
      - Returns inserted trip details
    - Returns 201 Created with the inserted trip

    **Why we insert trips here:**
    - Simulates a real fleet management scenario where trips are logged as they complete
    - Demonstrates write operations with client isolation

    **Request Body (JSON):**
    ```json
    {
      "distance_km": 15.5,
      "start_time": "2025-11-23T10:30:00",
      "end_time": "2025-11-23T10:45:00",
      "vendor_id": "v0000000-0000-0000-0000-000000000001",
      "vehicle_type": "Sedan"
    }
    ```

    **Returns:**
    - trip_id, client_id, vendor_id, distance_km, start_time, end_time

    **Example Request:**
    ```
    POST /trips
    Headers: X-Client-ID: c0000000-0000-0000-0000-000000000001
    Body: { "distance_km": 10.5, "start_time": "...", "end_time": "...", "vendor_id": "..." }
    ```
    """
    service = BillingService()
    
    # Generate a unique trip_id if not provided
    trip_id = str(uuid.uuid4())
    # Validate vendor_id is a proper UUID to avoid DB errors
    try:
        uuid.UUID(trip_input.vendor_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid vendor_id: must be a UUID")
    
    result = service.insert_new_trip(
        trip_id=trip_id,
        client_id=client_id,
        vendor_id=trip_input.vendor_id,
        distance_km=trip_input.distance_km,
        start_time=trip_input.start_time.isoformat(),
        end_time=trip_input.end_time.isoformat() if trip_input.end_time else None,
        is_carpool=getattr(trip_input, 'is_carpool', False),
        conn=conn,
    )
    
    return {
        "status": "created",
        "trip_id": result["trip_id"],
        "client_id": result["client_id"],
        "vendor_id": result["vendor_id"],
        "distance_km": result["distance_km"],
        "start_time": result["start_time"],
        "end_time": result["end_time"],
    }

# Secure create trip (RBAC: disallow VIEWER)
@app.post("/secure/trips")
def secure_create_trip(
    trip_input: TripInput,
    current_user: UserOut = Depends(require_role("SUPER_ADMIN", "CLIENT_ADMIN", "VENDOR_ADMIN")),
    conn=Depends(get_db_conn),
) -> Dict[str, Any]:
    service = BillingService()
    trip_id = str(uuid.uuid4())

    # Determine tenant & enforce vendor scope for vendor admins
    if not current_user.client_id and current_user.role != "SUPER_ADMIN":
        raise HTTPException(status_code=400, detail="User not bound to a client")

    effective_client_id = current_user.client_id if current_user.client_id else None
    # Vendor admin can only write their own vendor
    if current_user.role == "VENDOR_ADMIN":
        if not current_user.vendor_id:
            raise HTTPException(status_code=400, detail="Vendor admin missing vendor scope")
        if trip_input.vendor_id != current_user.vendor_id:
            raise HTTPException(status_code=403, detail="Cannot create trips for another vendor")

    try:
        uuid.UUID(trip_input.vendor_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid vendor_id: must be a UUID")

    # SUPER_ADMIN must specify client via query? keep simple: block if no client_id
    if current_user.role == "SUPER_ADMIN" and not effective_client_id:
        raise HTTPException(status_code=400, detail="SUPER_ADMIN must be bound to a client for this operation")

    result = service.insert_new_trip(
        trip_id=trip_id,
        client_id=effective_client_id,
        vendor_id=trip_input.vendor_id,
        distance_km=trip_input.distance_km,
        start_time=trip_input.start_time.isoformat(),
        end_time=trip_input.end_time.isoformat() if trip_input.end_time else None,
        is_carpool=getattr(trip_input, 'is_carpool', False),
        conn=conn,
    )

    return {
        "status": "created",
        "trip_id": result["trip_id"],
        "client_id": result["client_id"],
        "vendor_id": result["vendor_id"],
        "distance_km": result["distance_km"],
        "start_time": result["start_time"],
        "end_time": result["end_time"],
    }




# ============================================================================
# Admin Endpoints (SUPER_ADMIN only)
# ============================================================================

@app.post("/admin/users", status_code=201)
def create_user_admin(
    user_data: UserCreate,
    current_user: UserOut = Depends(require_role("SUPER_ADMIN")),
    conn=Depends(get_db_conn),
) -> Dict[str, Any]:
    """
    Create a new user (SUPER_ADMIN only).
    
    Only SUPER_ADMIN can create users. The created user will have the specified role and tenant bindings.
    
    **Request Body:**
    ```json
    {
      "email": "user@example.com",
      "password": "SecurePassword123",
      "role": "CLIENT_ADMIN",
      "client_id": "c0000000-0000-0000-0000-000000000001",
      "vendor_id": null
    }
    ```
    
    **Returns:** Created user details (without password hash)
    """
    # Validate role constraints
    if user_data.role == "SUPER_ADMIN":
        if user_data.client_id or user_data.vendor_id:
            raise HTTPException(
                status_code=400,
                detail="SUPER_ADMIN must not have client_id or vendor_id"
            )
    elif user_data.role in ("CLIENT_ADMIN", "VIEWER"):
        if not user_data.client_id:
            raise HTTPException(
                status_code=400,
                detail=f"{user_data.role} requires a client_id"
            )
        if user_data.vendor_id:
            raise HTTPException(
                status_code=400,
                detail=f"{user_data.role} must not have vendor_id"
            )
    elif user_data.role == "VENDOR_ADMIN":
        if not user_data.vendor_id:
            raise HTTPException(
                status_code=400,
                detail="VENDOR_ADMIN requires a vendor_id"
            )
    
    # Check if email already exists
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT 1 FROM users WHERE email=%s", (user_data.email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create new user
        new_user_id = str(uuid.uuid4())
        hashed_pwd = hash_password(user_data.password)
        
        cur.execute(
            """
            INSERT INTO users (id, email, password_hash, role, client_id, vendor_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                new_user_id,
                user_data.email,
                hashed_pwd,
                user_data.role,
                user_data.client_id,
                user_data.vendor_id,
            ),
        )
        conn.commit()
    
    logger.info(f"New user created: {user_data.email} (role: {user_data.role}) by {current_user.email}")
    
    return {
        "id": new_user_id,
        "email": user_data.email,
        "role": user_data.role,
        "client_id": user_data.client_id,
        "vendor_id": user_data.vendor_id,
    }
