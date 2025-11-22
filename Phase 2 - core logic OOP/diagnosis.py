import psycopg2
import psycopg2.extras
import sys

# --- CONFIG ---
DB_CONFIG = {
    "dbname": "moveinsync_db",
    "user": "postgres",
    "password": "postgre123",
    "host": "localhost",
    "port": "5432"
}

def run_diagnostics(trip_id):
    # Sanitize input: remove accidental spaces
    trip_id = trip_id.strip()

    print(f"\n🔍 DIAGNOSTICS FOR TRIP: '{trip_id}'")
    print("="*60)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return

    # 1. CHECK TRIP EXISTENCE
    print("\n1️⃣  CHECKING TRIP DETAILS...")
    cursor.execute("SELECT id, client_id, vendor_id, start_time FROM trips WHERE id = %s", (trip_id,))
    trip = cursor.fetchone()
    
    if not trip:
        print(f"❌ TRIP NOT FOUND: '{trip_id}'")
        print("\n🔎 LISTING ALL TRIPS ACTUALLY IN THE DATABASE:")
        print("-" * 40)
        cursor.execute("SELECT id FROM trips")
        all_trips = cursor.fetchall()
        
        if not all_trips:
            print("   (The 'trips' table is completely EMPTY!)")
            print("   👉 FIX: You need to run the INSERT SQL script and COMMIT the changes.")
        else:
            for t in all_trips:
                print(f"   Found: {t['id']}")
            print("-" * 40)
            print("   👉 TIP: Copy one of the IDs above exactly.")
        return
    
    # If found, proceed...
    t_client = trip['client_id']
    t_vendor = trip['vendor_id']
    t_start = trip['start_time']
    print(f"   ✅ Found Trip!")
    print(f"      - Client ID: {t_client}")
    print(f"      - Vendor ID: {t_vendor}")
    print(f"      - Start Time: {t_start}")

    # 2. CHECK FOR MATCHING CONTRACT
    print("\n2️⃣  SEARCHING FOR CONTRACT...")
    cursor.execute("""
        SELECT id, client_id, vendor_id, status 
        FROM contracts 
        WHERE client_id = %s AND vendor_id = %s
    """, (t_client, t_vendor))
    contract = cursor.fetchone()

    if not contract:
        print(f"❌ NO CONTRACT FOUND linking Client {t_client} and Vendor {t_vendor}.")
        
        # DEBUG: List what contracts DO exist
        print("   ... Listing available contracts for this client:")
        cursor.execute("SELECT id, vendor_id FROM contracts WHERE client_id = %s", (t_client,))
        others = cursor.fetchall()
        if not others:
            print("       (No contracts found for this client at all)")
        for o in others:
            print(f"       - Found Contract {o['id']} but for Vendor {o['vendor_id']}")
        return
    
    c_id = contract['id']
    print(f"   ✅ Found Contract: {c_id}")

    # 3. CHECK FOR VALID VERSION
    print(f"\n3️⃣  CHECKING CONTRACT VERSIONS for Contract {c_id}...")
    cursor.execute("""
        SELECT id, valid_from, valid_until, rules_config 
        FROM contract_versions 
        WHERE contract_id = %s
    """, (c_id,))
    versions = cursor.fetchall()

    if not versions:
        print("❌ CONTRACT FOUND, BUT NO VERSIONS EXIST!")
        return

    found_valid = False
    for v in versions:
        v_id = v['id']
        v_start = v['valid_from']
        v_end = v['valid_until']
        
        # Check logic
        is_after_start = t_start >= v_start
        is_before_end = (v_end is None) or (t_start <= v_end)
        
        print(f"   - Version {v_id}")
        print(f"     Range: {v_start} TO {v_end or 'Forever'}")
        
        if is_after_start and is_before_end:
            print("     ✅ MATCH! This version covers the trip time.")
            found_valid = True
        else:
            print("     ❌ MISMATCH: Trip time is outside this range.")

    if not found_valid:
        print("\n⚠️  CONCLUSION: Contract exists, but no version covers the Trip Start Time.")
        print("   👉 Fix: Update 'contract_versions.valid_from' to be EARLIER than Trip Start.")
    else:
        print("\n✅ CONCLUSION: Data looks perfect. 'main.py' should work now.")

    conn.close()

if __name__ == "__main__":
    target_id = sys.argv[1] if len(sys.argv) > 1 else "c0000000-0000-0000-0000-000000000001"
    run_diagnostics(target_id)