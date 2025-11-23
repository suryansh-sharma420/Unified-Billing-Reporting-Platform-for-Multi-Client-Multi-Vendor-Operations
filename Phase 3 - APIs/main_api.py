from typing import Any, Dict
import sys
import os
import uuid

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse

# Add Phase 2 to sys.path dynamically
phase2_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Phase 2 - core logic OOP'))
if phase2_path not in sys.path:
    sys.path.insert(0, phase2_path)

from dependencies import get_db_conn, get_client_id  # type: ignore
from service import BillingService  # type: ignore
from api_models import TripInput  # type: ignore
from exceptions import global_exception_handler, BillingError  # type: ignore


app = FastAPI(
    title="MoveInSync Billing API",
    description="Phase 3 API: Multi-tenant billing with connection pooling, caching, and error handling",
    version="1.0.0",
)

# Register the global exception handler
app.add_exception_handler(Exception, global_exception_handler)


@app.get("/health")
def health() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "MoveInSync Billing API"}


@app.get("/billing/{trip_id}")
def get_billing(
    trip_id: str,
    client_id: str = Depends(get_client_id),
    conn=Depends(get_db_conn),
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
    result = service.calculate_trip_cost(trip_id, client_id, conn)
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
    
    result = service.insert_new_trip(
        trip_id=trip_id,
        client_id=client_id,
        vendor_id=trip_input.vendor_id,
        distance_km=trip_input.distance_km,
        start_time=trip_input.start_time.isoformat(),
        end_time=trip_input.end_time.isoformat() if trip_input.end_time else None,
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

