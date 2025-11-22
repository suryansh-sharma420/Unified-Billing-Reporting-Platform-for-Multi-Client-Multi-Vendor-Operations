import psycopg2
import psycopg2.extras
import os
from typing import Tuple, Dict, Any
from dotenv import load_dotenv
from .schemas import TripData, BillingModelType

# Load environment variables from .env file
load_dotenv()

class PostgresRepository:
    def __init__(self):
        self.db_config = {
            "dbname": os.getenv("DB_NAME", "moveinsync_db"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD"),
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5432")
        }

    def get_db_connection(self):
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise

    def fetch_trip_context(self, trip_id: str) -> Tuple[TripData, BillingModelType, Dict[str, Any]]:
        # SQL query without 'vehicle_type' to avoid crashes
        sql = """
        SELECT 
            t.id as trip_id,
            t.distance_km,
            t.start_time,
            t.end_time,
            cv.billing_model,
            cv.rules_config
        FROM trips t
        JOIN contracts c ON t.client_id = c.client_id AND t.vendor_id = c.vendor_id
        JOIN contract_versions cv ON c.id = cv.contract_id
        WHERE t.id = %s
          AND t.start_time >= cv.valid_from
          AND (cv.valid_until IS NULL OR t.start_time <= cv.valid_until)
        LIMIT 1;
        """

        conn = self.get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        try:
            cursor.execute(sql, (trip_id,))
            row = cursor.fetchone()

            if not row:
                raise ValueError(f"No active contract found for Trip ID: {trip_id}")

            start = row['start_time']
            end = row['end_time']
            
            if end and start:
                duration_minutes = (end - start).total_seconds() / 60.0
            else:
                duration_minutes = 0.0

            # FIX: Populating start_hour here
            trip_data = TripData(
                trip_id=str(row['trip_id']),
                distance_km=float(row['distance_km'] or 0.0),
                duration_minutes=duration_minutes,
                start_hour=start.hour,  # <--- Extracting hour from timestamp
                vehicle_type="Standard"
            )

            raw_model = row['billing_model'].upper()
            try:
                model_enum = BillingModelType(raw_model)
            except ValueError:
                model_enum = BillingModelType.HYBRID 
            
            rules_config = row['rules_config'] 

            return trip_data, model_enum, rules_config

        finally:
            cursor.close()
            conn.close()