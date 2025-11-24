import sys
import os
import logging
from contextlib import contextmanager

# Add Phase 2 to sys.path dynamically
phase2_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Phase 2 - core logic OOP'))
if phase2_path not in sys.path:
    sys.path.insert(0, phase2_path)

from service import BillingService
from dependencies import connection_pool

# Configure logging
logging.basicConfig(level=logging.INFO)

@contextmanager
def get_db_conn_ctx():
    conn = connection_pool.getconn()
    try:
        yield conn
    finally:
        # We intentionally do NOT rollback here to simulate a dirty connection if we want
        # But for this test, we want to see if a dirty connection CAUSES the failure in service
        try:
            conn.rollback()
        except:
            pass
        connection_pool.putconn(conn)

def reproduce():
    client_id = "c0000000-0000-0000-0000-000000000001"
    service = BillingService()
    print(f"Attempting to generate report for client: {client_id} with DIRTY connection")
    
    try:
        with get_db_conn_ctx() as conn:
            # 1. Corrupt the connection
            print("Corrupting connection...")
            try:
                cur = conn.cursor()
                cur.execute("SELECT * FROM non_existent_table")
            except Exception as e:
                print(f"Connection corrupted as expected: {e}")
            
            # 2. Call service
            print("Calling generate_client_report...")
            csv_bytes = service.generate_client_report(client_id, conn=conn)
            print("Success! CSV generated.")
            print(csv_bytes.decode('utf-8')[:200])
    except Exception as e:
        print("Caught exception during report generation:")
        print(e)
        # import traceback
        # traceback.print_exc()

if __name__ == "__main__":
    reproduce()
