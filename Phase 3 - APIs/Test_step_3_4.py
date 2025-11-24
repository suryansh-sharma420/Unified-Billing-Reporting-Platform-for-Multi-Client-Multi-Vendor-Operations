import requests
import time
import logging

# Configure logging to see retry attempts
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:8000"
CLIENT_ID = "c0000000-0000-0000-0000-000000000001"
HEADERS = {"X-Client-ID": CLIENT_ID}

def test_health():
    """Test basic API connectivity"""
    logger.info("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    logger.info(f"Health check status: {response.status_code}")
    logger.info(f"Response: {response.json()}")

def test_retry_logic():
    """Test retry logic with an invalid trip ID"""
    logger.info("\nTesting retry logic...")
    invalid_trip_id = "invalid-trip-id"
    try:
        response = requests.get(
            f"{BASE_URL}/billing/{invalid_trip_id}",
            headers=HEADERS
        )
        logger.info(f"Response status: {response.status_code}")
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")

def test_logging():
    """Test if logging is working"""
    logger.info("\nTesting logging...")
    # Make a few requests to generate logs
    for _ in range(3):
        response = requests.get(f"{BASE_URL}/health")
        time.sleep(0.5)  # Small delay to see timestamps change

if __name__ == "__main__":
    test_health()
    test_retry_logic()
    test_logging()
    print("\nCheck moveinsync_app.log for detailed request/response logs")