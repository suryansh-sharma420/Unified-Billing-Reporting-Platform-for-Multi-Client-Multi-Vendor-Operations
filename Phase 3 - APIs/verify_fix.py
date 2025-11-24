import sys
import os
import logging
from unittest.mock import MagicMock, patch

# Add Phase 2 to sys.path dynamically
phase2_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Phase 2 - core logic OOP'))
if phase2_path not in sys.path:
    sys.path.insert(0, phase2_path)

from billing.repository import PostgresRepository

# Configure logging
logging.basicConfig(level=logging.INFO)

def verify_fix():
    client_id = "c0000000-0000-0000-0000-000000000001"
    repo = PostgresRepository()
    
    # Mock the connection object
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    # Mock cursor.execute to fail
    mock_cursor.execute.side_effect = Exception("Simulated DB Error inside repository")
    
    print("--- Test: Call fetch_trip_context (should fail and rollback) ---")
    try:
        repo.fetch_trip_context("trip1", client_id, conn=mock_conn)
    except Exception as e:
        print(f"Caught expected exception: {e}")
    
    if mock_conn.rollback.called:
        print("✅ SUCCESS: conn.rollback() was called inside repository!")
    else:
        print("❌ FAILURE: conn.rollback() was NOT called inside repository!")

if __name__ == "__main__":
    verify_fix()
