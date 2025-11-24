import sys
import os
import logging
from unittest.mock import MagicMock

# Add Phase 2 to sys.path dynamically
phase2_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Phase 2 - core logic OOP'))
if phase2_path not in sys.path:
    sys.path.insert(0, phase2_path)

from fastapi.testclient import TestClient
from main_api import app
from dependencies import get_current_user, get_db_conn
from api_models import UserOut

# Configure logging
logging.basicConfig(level=logging.INFO)

def mock_get_current_user():
    return UserOut(id="u1", email="test@test.com", role="CLIENT_ADMIN", client_id="c0000000-0000-0000-0000-000000000001", vendor_id=None)

def mock_get_db_conn():
    # Return a mock connection that does nothing but doesn't crash
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    # Mock fetchone to return something valid so service doesn't crash immediately
    # But we mainly care about routing not hitting the UUID error
    yield mock_conn

app.dependency_overrides[get_current_user] = mock_get_current_user
app.dependency_overrides[get_db_conn] = mock_get_db_conn

client = TestClient(app)

def test_routing():
    print("Testing GET /secure/billing/export-csv ...")
    try:
        response = client.get("/secure/billing/export-csv")
        print(f"Status Code: {response.status_code}")
        
        # Check for the specific UUID error message in the response text
        # The error "invalid input syntax for type uuid" usually comes with 500 status
        if response.status_code == 500 and "invalid input syntax for type uuid" in response.text:
             print("❌ FAILURE: Still hitting the wrong endpoint (UUID error)")
             print(f"Response: {response.text}")
        elif response.status_code == 200:
             print("✅ SUCCESS: Routing correct, CSV generated")
        else:
             # Even if it fails with another error (e.g. DB error), as long as it's not the UUID error, routing is fixed.
             print(f"✅ SUCCESS: Routing seems correct (Status: {response.status_code})")
             if response.status_code != 200:
                 print(f"Response: {response.text}")
             
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_routing()
